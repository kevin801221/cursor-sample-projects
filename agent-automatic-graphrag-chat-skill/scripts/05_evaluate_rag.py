#!/usr/bin/env python3
"""
Step 5: 方法驗證——用數據證明「目前的 RAG 方法在當前狀態下最好」
================================================================
需先啟動 Phase 4+5 的 chatbot server（強 RAG 走 HTTP API）。
需安裝: uv sync
需環境變數: GOOGLE_API_KEY

「證明」的正確定義（上課要先講，避免同學誤解）:
  不是宇宙最優，而是：在「你自己的評估集」上，現行方法以數據
  勝過所有已測候選方法，且與官方文件的最佳實務對齊。
  這是工程上唯一誠實、也唯一可辯護的「最好」。

流程:
  1. --generate: 從 transcript 自動出題（LLM 產生 QA 評估集，人工複核後定版）
  2. --run: 對每題跑兩條路線
       A) naive baseline: Chroma top-5 直接生成
       B) 強 RAG: POST /chat (Multi-Query + RRF + 圖譜擴展)
     LLM-as-judge 盲評（隨機交換 A/B 位置，防位置偏誤），
     依 faithfulness / completeness / citation 三維度給 1-5 分
  3. 輸出 eval_report.json + 勝負表 → 這就是 decision record 的數據附件

用法:
  uv run python scripts/05_evaluate_rag.py --generate source.json --n 10 --out eval_set.json
  # （人工看過 eval_set.json、刪掉爛題之後）
  uv run python scripts/05_evaluate_rag.py --run eval_set.json --api http://localhost:8000
"""
import argparse
import json
import os
import random
from pathlib import Path

CHAT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")
# judge 與受測 pipeline 同級模型的偏誤風險，見 references/method-validation.md 誠實條款
JUDGE_MODEL = os.environ.get("GEMINI_JUDGE_MODEL", CHAT_MODEL)
DIMS = ("faithfulness", "completeness", "citation")

JUDGE_PROMPT = """你是嚴格的 RAG 回答評審。針對同一問題有兩個匿名回答。
參考答案要點: {reference}
問題: {question}

回答一:
{ans1}

回答二:
{ans2}

依三個維度各給 1-5 分（5 最好）:
- faithfulness: 是否只根據影片內容、無腦補
- completeness: 是否涵蓋參考要點
- citation: 是否附上可用的影片時間戳引用

嚴格只輸出 JSON:
{{"answer1": {{"faithfulness": n, "completeness": n, "citation": n}},
  "answer2": {{"faithfulness": n, "completeness": n, "citation": n}}}}"""

GEN_PROMPT = """根據以下影片逐字稿片段，出 1 題「看過影片的人答得出來」的問題。
避免「這段講什麼」這種空題，要問具體概念或關係。
嚴格只輸出 JSON: {"question": "...", "reference": "答案要點（一兩句）"}

片段:
"""


def parse_json_loose(raw: str) -> dict | None:
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def generate_eval_set(transcript_path: Path, n: int, out: Path):
    """從 transcript 均勻取樣段落出題。出完必須人工複核——評估集品質決定結論可信度。"""
    from langchain_google_genai import ChatGoogleGenerativeAI
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ingest", Path(__file__).parent / "02_ingest_vectordb.py")
    ingest_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ingest_mod)

    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    # youtube 才做秒級時間窗聚合；pdf/docx/url 的 start 是頁碼/段序，
    # 套 60「秒」窗會誤把 60 頁併成一段（曾實際踩到的跨腳本一致性 bug）
    if transcript.get("source_type", "youtube") == "youtube":
        blocks = ingest_mod.aggregate_segments(transcript["segments"])
    else:
        blocks = transcript["segments"]
    # 均勻取樣，避免題目全集中在影片開頭
    step = max(1, len(blocks) // n)
    sampled = blocks[::step][:n]

    llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0.3)
    qa = []
    for i, b in enumerate(sampled):
        data = parse_json_loose(llm.invoke(GEN_PROMPT + b["text"]).text)
        if data and data.get("question"):
            qa.append({"id": i, "question": data["question"],
                       "reference": data.get("reference", ""), "source_start": int(b["start"])})
            print(f"[*] Q{i}: {data['question']}")
    out.write_text(json.dumps({"video_id": transcript["video_id"], "qa": qa},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] {len(qa)} 題已存至 {out}。請人工複核後再 --run。")


def naive_rag(question: str, collection: str, persist_dir: str) -> str:
    """Baseline: 純向量 top-5，無 Multi-Query、無 RRF、無圖譜。"""
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    vectordb = Chroma(collection_name=collection,
                      embedding_function=GoogleGenerativeAIEmbeddings(model=EMBED_MODEL),
                      persist_directory=persist_dir)
    docs = vectordb.similarity_search(question, k=5)
    context = "\n\n".join(
        f"[{d.metadata['url_at_time']}]\n{d.page_content}" for d in docs)
    llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0)
    return llm.invoke(
        f"只根據以下影片片段回答，引用時附時間戳連結，"
        f"資料中沒有的就說不知道。\n\n{context}\n\n問題: {question}").text


def aggregate(rows: list[dict]) -> dict:
    """彙總各維度平均分與勝負。回傳報告 dict。"""
    dims = list(DIMS)
    summary = {"baseline": {d: 0.0 for d in dims}, "strong_rag": {d: 0.0 for d in dims},
               "wins": {"baseline": 0, "strong_rag": 0, "tie": 0}}
    for r in rows:
        b_total = sum(r["scores"]["baseline"].values())
        s_total = sum(r["scores"]["strong_rag"].values())
        key = ("strong_rag" if s_total > b_total
               else "baseline" if b_total > s_total else "tie")
        summary["wins"][key] += 1
        for d in dims:
            summary["baseline"][d] += r["scores"]["baseline"][d]
            summary["strong_rag"][d] += r["scores"]["strong_rag"][d]
    n = max(len(rows), 1)
    for side in ("baseline", "strong_rag"):
        for d in dims:
            summary[side][d] = round(summary[side][d] / n, 2)
    return summary


def run_eval(eval_path: Path, api: str, collection: str, persist_dir: str):
    import requests
    from langchain_google_genai import ChatGoogleGenerativeAI

    eval_set = json.loads(eval_path.read_text(encoding="utf-8"))
    # 想讓 judge 比受測 pipeline 強時: export GEMINI_JUDGE_MODEL=<更強的模型>
    judge = ChatGoogleGenerativeAI(model=JUDGE_MODEL, temperature=0)
    rows = []
    for item in eval_set["qa"]:
        q = item["question"]
        print(f"[*] 評測: {q}")
        ans_base = naive_rag(q, collection, persist_dir)
        ans_strong = requests.post(f"{api}/chat", json={"question": q},
                                   timeout=120).json()["answer"]

        # 盲評 + 隨機換位，防 LLM judge 的位置偏誤
        flip = random.random() < 0.5
        a1, a2 = (ans_strong, ans_base) if flip else (ans_base, ans_strong)
        verdict = parse_json_loose(judge.invoke(JUDGE_PROMPT.format(
            reference=item.get("reference", ""), question=q,
            ans1=a1, ans2=a2)).text)
        # 只驗 JSON 合法還不夠：judge 常少給某個維度，漏掉會讓 aggregate 在
        # 跑完全部題目後才 KeyError 炸掉，整輪評測白做。這裡當場擋下。
        if not verdict or not all(
                isinstance(verdict.get(side), dict) and all(d in verdict[side] for d in DIMS)
                for side in ("answer1", "answer2")):
            print("[!] judge 輸出缺欄位或解析失敗，此題略過")
            continue
        base_key, strong_key = ("answer2", "answer1") if flip else ("answer1", "answer2")
        rows.append({
            "question": q,
            "scores": {"baseline": verdict[base_key], "strong_rag": verdict[strong_key]},
            "answers": {"baseline": ans_base, "strong_rag": ans_strong},
        })

    summary = aggregate(rows)
    report = {"summary": summary, "details": rows}
    Path("eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n===== 勝負 =====")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("[✓] 完整報告: eval_report.json（附進 decision record 當數據證據）")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate", type=Path, help="從 transcript.json 產生評估集")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--out", type=Path, default=Path("eval_set.json"))
    ap.add_argument("--run", type=Path, help="執行 A/B 評測（給 eval_set.json）")
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--collection", default="yt_rag")
    ap.add_argument("--persist", default="./chroma_db")
    args = ap.parse_args()
    if args.generate:
        generate_eval_set(args.generate, args.n, args.out)
    elif args.run:
        run_eval(args.run, args.api, args.collection, args.persist)
    else:
        ap.print_help()
