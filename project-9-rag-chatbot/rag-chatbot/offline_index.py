"""離線索引建立（CLI 工具）—— 鐵律 5 的前半段。

RAG 分成兩條時間線：

  【離線索引】← 這支程式。一次性、慢、要錢（呼叫 embedding API），但只做一次。
       載入 → 切塊 → 向量化 → 寫進 ChromaDB

  【線上查詢】← app.py。每次提問都跑、要快（幾百毫秒）。
       問題 → 檢索 → 組 prompt → LLM → 附出處回答

分開的理由：如果 Streamlit 一啟動就重建索引，開一次 app 要等好幾分鐘，
而且每次改一行程式碼 Streamlit 重跑，就再等一次。

用法：
    uv run offline_index.py                        # 用預設語料建索引
    uv run offline_index.py --reset                # 砍掉重練
    uv run offline_index.py --input data/faqs.md   # 指定文件（可給多個，也可給網址）
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from src import PROJECT_ROOT
from src.chunker import CHUNK_OVERLAP, CHUNK_SIZE, chunk_documents
from src.embeddings import (
    CHROMA_DB_PATH,
    add_documents_to_chroma,
    count_documents,
    provider_label,
    reset_collection,
    resolve_collection_name,
)
from src.loader import load_any

DEFAULT_INPUTS = [
    os.path.join(PROJECT_ROOT, "data", "sample_handbook.pdf"),
    os.path.join(PROJECT_ROOT, "data", "faqs.md"),
]


def build_index(
    inputs: list[str],
    collection_name: str = "knowledge_base",
    reset: bool = False,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> int:
    print(f"Provider：{provider_label()}")
    print(f"向量庫路徑：{CHROMA_DB_PATH}")
    print(f"Collection：{resolve_collection_name(collection_name)}")
    print(f"切塊參數：chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    print("-" * 70)

    if reset:
        reset_collection(collection_name)
        print("已清空舊索引（--reset）")

    total_chunks = 0
    started = time.time()

    for path in inputs:
        if not path.startswith(("http://", "https://")) and not os.path.exists(path):
            print(f"✗ 找不到檔案：{path}", file=sys.stderr)
            continue

        docs = load_any(path)
        chunks = chunk_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        added = add_documents_to_chroma(chunks, collection_name)
        total_chunks += added

        unit = "頁" if path.lower().endswith(".pdf") else "節"
        print(f"✓ {os.path.basename(path)}：載入 {len(docs)} {unit} → 切出 {len(chunks)} 個區塊 → 已加入 {added} 個")

    elapsed = time.time() - started
    print("-" * 70)
    print(f"Added {total_chunks} chunks to ChromaDB（耗時 {elapsed:.1f} 秒）")
    print(f"目前索引總量：{count_documents(collection_name)} 個區塊")
    print(f"./chroma_db exists: {os.path.isdir(CHROMA_DB_PATH)}")
    return total_chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="建立 / 更新 RAG 知識庫的向量索引")
    parser.add_argument(
        "--input",
        nargs="+",
        default=DEFAULT_INPUTS,
        help="要索引的檔案或網址（可給多個）。預設是 data/ 底下的示範語料。",
    )
    parser.add_argument("--collection", default="knowledge_base", help="ChromaDB collection 名稱")
    parser.add_argument("--reset", action="store_true", help="先清空這個 collection 再建")
    parser.add_argument(
        "--persist",
        action="store_true",
        help="（保留給教材的旗標）索引本來就一定會持久化到 CHROMA_DB_PATH，加不加都一樣",
    )
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=CHUNK_OVERLAP)
    args = parser.parse_args()

    added = build_index(
        inputs=args.input,
        collection_name=args.collection,
        reset=args.reset,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    return 0 if added else 1


if __name__ == "__main__":
    raise SystemExit(main())
