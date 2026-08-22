#!/usr/bin/env python3
"""
Step 2: 逐字稿 -> LangChain 切塊 -> 嵌入 -> VectorDB (Chroma)
=============================================================
驗證環境: langchain-text-splitters 1.1.2 / Python 3.12
需另安裝: uv sync（見專案 pyproject.toml）
需環境變數: GOOGLE_API_KEY（aistudio.google.com 免費取得）
嵌入模型可用 GEMINI_EMBED_MODEL 覆蓋，一個 export 就同時改掉所有腳本。

設計重點（上課時要講）:
  1. 先「時間窗聚合」再切塊：字幕段落太碎（一段 2~3 秒），直接嵌入品質很差。
     先把 segments 聚合成 ~60 秒的自然段，保留 start/end 時間戳進 metadata。
  2. RecursiveCharacterTextSplitter 用 chunk_overlap 保留跨段語意。
  3. metadata 存 video_id / title / start / end / url_at_time ——
     RAG 回答時就能給「點此跳到影片 12:34」的引用連結。

用法:
  uv run python scripts/02_ingest_vectordb.py source.json --persist ./chroma_db --collection yt_rag
"""
import argparse
import json
import os
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")
WINDOW_SECONDS = 60          # 時間窗聚合大小
CHUNK_SIZE = 800             # 中文以「字元」計，800 字元 ≈ 一個完整論點
CHUNK_OVERLAP = 120


def aggregate_segments(segments: list[dict], window: int = WINDOW_SECONDS) -> list[dict]:
    """把碎片字幕聚合成 ~window 秒的自然段。回傳 [{start, end, text}]。"""
    blocks: list[dict] = []
    cur: dict | None = None
    for seg in segments:
        if cur is None:
            cur = {"start": seg["start"], "end": seg["end"], "text": seg["text"]}
            continue
        if seg["end"] - cur["start"] <= window:
            cur["text"] += " " + seg["text"]
            cur["end"] = seg["end"]
        else:
            blocks.append(cur)
            cur = {"start": seg["start"], "end": seg["end"], "text": seg["text"]}
    if cur:
        blocks.append(cur)
    return blocks


def to_documents(transcript: dict) -> list:
    """聚合 + 切塊，產出帶 metadata 的 LangChain Document。
    - youtube: 秒級碎片先做 60 秒時間窗聚合，ref = 帶時間戳深連結
    - pdf/docx/url (由 00_ingest_source.py 產生): 段落已聚合好，
      start 是頁碼/段序而非秒數，「時間窗」無意義故直接沿用，
      ref 用 segment 自帶的（file://...#page=N 或網址）
    """
    from langchain_core.documents import Document

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],  # 中文標點優先
    )
    source_type = transcript.get("source_type", "youtube")
    if source_type == "youtube":
        blocks = aggregate_segments(transcript["segments"])
        for b in blocks:
            b["ref"] = f"https://youtu.be/{transcript['video_id']}?t={int(b['start'])}"
    else:
        blocks = transcript["segments"]  # 已由 00 聚合，且各段自帶 ref

    docs = []
    idx = 0  # 全域 chunk 序號：與 Step 3 的 chunk_id (f"{video_id}_{idx}") 一一對齊
    for block in blocks:
        for chunk in splitter.split_text(block["text"]):
            docs.append(Document(
                page_content=chunk,
                metadata={
                    "video_id": transcript["video_id"],  # 即 source_id
                    "source_type": source_type,
                    "title": transcript.get("title") or "",
                    "chunk_index": idx,
                    "start": int(block["start"]),
                    "end": int(block["end"]),
                    # 可回溯引用：影片時間戳 / PDF 頁 / 網址，回答時直接可點
                    "url_at_time": block["ref"],
                },
            ))
            idx += 1
    return docs


def ingest(transcript_path: Path, persist_dir: str, collection: str, embeddings=None):
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    docs = to_documents(transcript)
    print(f"[*] 產生 {len(docs)} 個 chunks")

    # --- 嵌入模型：預設 Gemini；embeddings 參數是替換點（本地模型/測試假嵌入）---
    # langchain-google-genai 會自動對「入庫」用 RETRIEVAL_DOCUMENT、對「查詢」用
    # RETRIEVAL_QUERY 這兩種 task_type——非對稱嵌入是檢索品質的免費增益，上課可提。
    if embeddings is None:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)
        # 本地替代: from langchain_huggingface import HuggingFaceEmbeddings
        #           embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

    from langchain_chroma import Chroma
    vectordb = Chroma(
        collection_name=collection,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
    # 冪等性：同一支影片重跑先刪舊資料，避免重複 chunks 汙染檢索
    existing = vectordb.get(where={"video_id": transcript["video_id"]})
    if existing["ids"]:
        vectordb.delete(ids=existing["ids"])
        print(f"[*] 已清除舊資料 {len(existing['ids'])} 筆（重跑冪等）")

    vectordb.add_documents(docs)
    print(f"[✓] 已寫入 collection='{collection}' at {persist_dir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript", type=Path)
    ap.add_argument("--persist", default="./chroma_db")
    ap.add_argument("--collection", default="yt_rag")
    args = ap.parse_args()
    ingest(args.transcript, args.persist, args.collection)
