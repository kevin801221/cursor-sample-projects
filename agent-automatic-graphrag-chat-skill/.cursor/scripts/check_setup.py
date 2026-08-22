#!/usr/bin/env python3
"""
起飛前檢查：執行任何 Phase 之前先跑這支。
每一項檢查失敗都會印出「修復指令」，照著貼上執行即可。
全部通過會印出 ALL CHECKS PASSED。

用法:
  uv run python scripts/check_setup.py           # 檢查必要項目
  uv run python scripts/check_setup.py --full    # 連選填的付費金鑰一起檢查
"""
import argparse
import importlib
import os
import sys

REQUIRED_PACKAGES = [
    # (import 名, pip 安裝名)
    ("yt_dlp", "yt-dlp"),
    ("langchain_text_splitters", "langchain-text-splitters"),
    ("langchain_google_genai", "langchain-google-genai"),
    ("langchain_chroma", "langchain-chroma"),
    ("chromadb", "chromadb"),
    ("neo4j", "neo4j"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn[standard]"),
    ("requests", "requests"),
    ("pymupdf", "pymupdf"),
    ("docx", "python-docx"),
    ("trafilatura", "trafilatura"),
]

CHAT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# SDK 兩個名字都吃（google-genai 與 langchain-google-genai 皆然），
# 所以檢查也要兩個都認——只認一個會擋掉一把其實能用的金鑰。
API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

ok = True


def check(label: str, passed: bool, fix: str):
    global ok
    mark = "✓" if passed else "✗"
    print(f"[{mark}] {label}")
    if not passed:
        ok = False
        print(f"    修復 → {fix}")


def check_gemini_models():
    """真的去問一次 Google：你的金鑰看得到哪些模型、設定的那兩支在不在。

    為什麼值得多這一步：Google 的模型名會改（gemini-1.5 → 2.5 → 3.x），
    寫死的預設值遲早過期。與其讓全班在 Phase 2 才炸掉，不如在 Phase 0
    就把「可用模型清單」印出來，改個環境變數即可繼續。
    """
    try:
        from google import genai
        client = genai.Client(api_key=API_KEY)
        names = [m.name.removeprefix("models/") for m in client.models.list()]
    except Exception as e:
        check("Gemini API 連線", False,
              "確認 GOOGLE_API_KEY 正確且有額度（aistudio.google.com）"
              f"｜錯誤: {type(e).__name__}: {e}")
        return

    check("Gemini API 連線", True, "")
    for label, want, envvar in (("對話模型", CHAT_MODEL, "GEMINI_MODEL"),
                                ("嵌入模型", EMBED_MODEL, "GEMINI_EMBED_MODEL")):
        hit = want in names
        kind = "embedding" if "embedding" in want else "flash"
        hint = ", ".join(n for n in names if kind in n)[:200] or "（清單為空）"
        check(f"{label} {want}", hit,
              f'export {envvar}="<下列其一>" 後重跑本檢查｜可用: {hint}')


def main(full: bool):
    print("=== 1/4 套件檢查 ===")
    for mod, pipname in REQUIRED_PACKAGES:
        try:
            importlib.import_module(mod)
            check(f"套件 {pipname}", True, "")
        except ImportError:
            check(f"套件 {pipname}", False, "uv sync（在 skill 根目錄執行）")

    print("=== 2/4 環境變數檢查 ===")
    check("GOOGLE_API_KEY 或 GEMINI_API_KEY", bool(API_KEY),
          'export GOOGLE_API_KEY="AIza..."（aistudio.google.com 免費取得）'
          '；放在 .env 的話指令要加 --env-file，例：'
          'uv run --env-file .env python scripts/check_setup.py')
    check("NEO4J_PASSWORD", bool(os.environ.get("NEO4J_PASSWORD")),
          'export NEO4J_PASSWORD="你docker設定的密碼"')
    if full:
        check("LLAMA_CLOUD_API_KEY（選填，PDF 付費引擎）",
              bool(os.environ.get("LLAMA_CLOUD_API_KEY")),
              'export LLAMA_CLOUD_API_KEY="llx-..."（cloud.llamaindex.ai）')
        check("TAVILY_API_KEY（選填，URL 付費引擎）",
              bool(os.environ.get("TAVILY_API_KEY")),
              'export TAVILY_API_KEY="tvly-..."（tavily.com）')

    print("=== 3/4 Gemini 模型檢查 ===")
    if API_KEY:
        check_gemini_models()
    else:
        check("Gemini 模型", False, "先設定 GOOGLE_API_KEY 或 GEMINI_API_KEY 再重跑本檢查")

    print("=== 4/4 Neo4j 連線檢查 ===")
    if os.environ.get("NEO4J_PASSWORD"):
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
                auth=(os.environ.get("NEO4J_USER", "neo4j"),
                      os.environ["NEO4J_PASSWORD"]))
            driver.verify_connectivity()
            driver.close()
            check("Neo4j 連線", True, "")
        except Exception as e:
            check("Neo4j 連線", False,
                  "docker run -d --name neo4j-teach -p 7474:7474 -p 7687:7687 "
                  '-e NEO4J_AUTH=neo4j/你的密碼 neo4j:5 （啟動需等約 20 秒再重跑檢查）'
                  f"｜錯誤: {type(e).__name__}")
    else:
        check("Neo4j 連線", False, "先設定 NEO4J_PASSWORD 再重跑本檢查")

    print()
    if ok:
        print("ALL CHECKS PASSED — 可以開始 Phase 1")
        sys.exit(0)
    else:
        print("有項目未通過。照上面的「修復 →」逐條執行後，重跑本腳本直到全綠。")
        sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="連選填付費金鑰一起檢查")
    args = ap.parse_args()
    main(args.full)
