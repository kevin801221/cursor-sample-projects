#!/usr/bin/env python3
"""
Step 3: 從 chunks 抽取知識圖譜 -> 寫入 Neo4j
=============================================
需安裝: uv sync
需環境變數: GOOGLE_API_KEY, NEO4J_PASSWORD（NEO4J_URI / NEO4J_USER 有預設）
（Neo4j 本機最快啟動方式見 SKILL.md Phase 0 的 docker 指令）

設計重點（上課時要講）:
  1. 用 LLM 做 (主體)-[關係]->(客體) 三元組抽取，並強制輸出 JSON。
  2. 每個 Entity 節點都掛回 Chunk 節點 (MENTIONED_IN)，
     這是 GraphRAG 的關鍵：圖譜負責「找到相關概念」，
     Chunk 負責「提供原文證據」。兩者缺一不可。
  3. MERGE 而非 CREATE：同一實體在多個 chunk 出現時去重合併，
     圖譜的價值正是把散落在影片各處的同一概念連起來。

用法:
  uv run python scripts/03_build_graph.py source.json
"""
import argparse
import json
import os
from pathlib import Path

CHAT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

EXTRACT_PROMPT = """你是知識圖譜抽取器。從以下影片逐字稿片段抽取三元組。
規則:
- entity 用正式名稱（如 "LangGraph"、"檢查點機制"），同義詞正規化為同一名稱
- relation 用簡短動詞片語（如 "包含"、"用於"、"解決"）
- 只抽取片段中明確陳述的關係，不要腦補
- 最多 8 個三元組
- 嚴格只輸出 JSON，不要 markdown 圍欄，格式:
{"triples": [{"subject": "...", "relation": "...", "object": "..."}]}

片段:
"""


def extract_triples(chunks: list[dict], model: str) -> list[dict]:
    """對每個 chunk 呼叫 LLM 抽取三元組。回傳 [{subject, relation, object, chunk_id}]"""
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(model=model, temperature=0)
    all_triples = []
    for i, chunk in enumerate(chunks):
        resp = llm.invoke(EXTRACT_PROMPT + chunk["text"])
        # 用 .text 不用 .content：LangChain 1.x 的 .content 是 content blocks 的 list
        # （裡面還夾著 signature 之類的 metadata），只有 .text 是純文字。
        raw = resp.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[!] chunk {i} JSON 解析失敗，跳過（這就是為什麼正式系統要用 structured output）")
            continue
        for t in data.get("triples", []):
            if all(k in t and t[k] for k in ("subject", "relation", "object")):
                t["chunk_id"] = chunk["chunk_id"]
                all_triples.append(t)
        print(f"[*] chunk {i+1}/{len(chunks)}: +{len(data.get('triples', []))} triples")
    return all_triples


def write_neo4j(triples: list[dict], chunks: list[dict], video: dict):
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as s:
        # 冪等：清掉同影片舊圖
        s.run("MATCH (c:Chunk {video_id: $vid}) DETACH DELETE c", vid=video["video_id"])
        s.run(
            "MERGE (v:Video {id: $vid}) SET v.title = $title, v.url = $url",
            vid=video["video_id"], title=video.get("title", ""), url=video.get("url", ""),
        )
        for c in chunks:
            s.run(
                """MERGE (ck:Chunk {id: $cid}) SET ck.text = $text, ck.start = $start,
                        ck.video_id = $vid, ck.url_at_time = $url
                   WITH ck MATCH (v:Video {id: $vid}) MERGE (ck)-[:PART_OF]->(v)""",
                cid=c["chunk_id"], text=c["text"], start=c["start"],
                vid=video["video_id"], url=c["url_at_time"],
            )
        for t in triples:
            # 關係型別動態化需 APOC；教學版把 relation 存為屬性，通用又免外掛
            s.run(
                """MERGE (a:Entity {name: $subj})
                   MERGE (b:Entity {name: $obj})
                   MERGE (a)-[r:REL {type: $rel}]->(b)
                   WITH a, b MATCH (ck:Chunk {id: $cid})
                   MERGE (a)-[:MENTIONED_IN]->(ck)
                   MERGE (b)-[:MENTIONED_IN]->(ck)""",
                subj=t["subject"].strip(), obj=t["object"].strip(),
                rel=t["relation"].strip(), cid=t["chunk_id"],
            )
    driver.close()
    print(f"[✓] 圖譜完成: {len(triples)} 條關係")


def main(transcript_path: Path, model: str):
    # 重用 Step 2 的聚合切塊邏輯，確保 chunk_id 與 vector DB 對得起來
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ingest", Path(__file__).parent / "02_ingest_vectordb.py")
    ingest_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ingest_mod)

    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    docs = ingest_mod.to_documents(transcript)
    chunks = [
        {"chunk_id": f"{transcript['video_id']}_{i}", "text": d.page_content,
         "start": d.metadata["start"], "url_at_time": d.metadata["url_at_time"]}
        for i, d in enumerate(docs)
    ]
    triples = extract_triples(chunks, model)
    write_neo4j(triples, chunks, transcript)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript", type=Path)
    ap.add_argument("--model", default=CHAT_MODEL,
                    help=f"Gemini 模型（預設 {CHAT_MODEL}，可用 GEMINI_MODEL 覆蓋）")
    args = ap.parse_args()
    main(args.transcript, args.model)
