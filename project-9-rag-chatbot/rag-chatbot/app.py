"""Streamlit 聊天介面 —— 線上查詢那一半。

離線索引（offline_index.py）已經把文件變成向量存好了，
這支程式只做「問題進來 → 檢索 → 組 prompt → 回答 → 附出處」，所以秒回。

跑法：
    DEMO_OFFLINE=1 uv run streamlit run app.py
"""

from __future__ import annotations

import os
import tempfile

import streamlit as st

from src.chunker import CHUNK_OVERLAP, CHUNK_SIZE
from src.embeddings import (
    CHROMA_DB_PATH,
    active_provider,
    add_documents_to_chroma,
    count_documents,
    provider_label,
)
from src.chunker import chunk_documents
from src.loader import load_any
from src.retriever import MAX_TOKENS, RETRIEVAL_K, TEMPERATURE, ask_conversational, create_conversational_qa_chain

st.set_page_config(page_title="RAG 知識庫 Chatbot", page_icon="📚", layout="wide")
st.title("📚 公司知識庫助手")
st.caption("查完再答，每個回答都附出處；找不到就說找不到。")

# ─────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────

st.sidebar.header("⚙️ 目前設定")

if active_provider() == "offline":
    st.sidebar.warning(f"**離線模式**\n\n{provider_label()}", icon="🔌")
    st.sidebar.caption("沒有 OPENAI_API_KEY（或設了 DEMO_OFFLINE=1）。整條 RAG 流程照跑，只是換掉 provider。")
else:
    st.sidebar.success(f"**OpenAI 模式**\n\n{provider_label()}", icon="🌐")

indexed = count_documents()
st.sidebar.metric("向量庫區塊數", indexed)
st.sidebar.caption(f"chunk_size={CHUNK_SIZE}｜chunk_overlap={CHUNK_OVERLAP}｜k={RETRIEVAL_K}｜temperature={TEMPERATURE}｜max_tokens={MAX_TOKENS}")

if indexed == 0:
    st.sidebar.error("向量庫是空的，請先在終端機跑：\n\n`uv run offline_index.py --reset`")

st.sidebar.divider()
st.sidebar.header("📖 知識庫管理")

uploaded_file = st.sidebar.file_uploader(
    "上傳文件（PDF / Markdown / txt）",
    type=["pdf", "md", "txt"],
    key="uploader",
)

if uploaded_file is not None and uploaded_file.name != st.session_state.get("last_upload"):
    suffix = os.path.splitext(uploaded_file.name)[1]
    # 用 tempfile 而不是寫死 /tmp：Windows 沒有 /tmp，課堂上有人用 Windows 就會炸
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_path = tmp.name
    try:
        with st.sidebar.status("正在處理文件…", expanded=False):
            docs = load_any(temp_path)
            chunks = chunk_documents(docs)
            # 上傳的檔案在暫存目錄裡叫做 tmpXXXX，出處要改回使用者認得的原始檔名
            for chunk in chunks:
                chunk.metadata["source"] = uploaded_file.name
            added = add_documents_to_chroma(chunks)
        st.sidebar.success(f"✓ 已加入 {added} 個區塊（不用重啟，直接問就查得到）")
        st.session_state.last_upload = uploaded_file.name
    finally:
        os.unlink(temp_path)

st.sidebar.divider()
st.sidebar.header("🧪 課堂實驗")

strict = st.sidebar.toggle(
    "開啟防幻覺 system prompt",
    value=True,
    help="關掉之後，system prompt 裡「找不到就說不知道」那條就不見了。"
    "其他東西完全一樣——同一個向量庫、同一個 retriever、同一個 LLM。",
)
if not strict:
    st.sidebar.error("防幻覺條款已關閉：現在問文件裡沒有的東西，它會硬掰。", icon="⚠️")

if st.sidebar.button("🗑️ 清除對話", use_container_width=True):
    st.session_state.messages = []
    if "memory" in st.session_state:
        # 只清記憶，不重建 chain——重建等於重連向量庫，沒必要而且會卡好幾秒
        st.session_state.memory.clear()
    st.rerun()

# ─────────────────────────────────────────────────────────────────────
# Session state：chain 與 memory 只建一次
# ─────────────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

# strict 切換會改變 prompt，所以要重建 chain；其他情況一律沿用既有的。
if "chain" not in st.session_state or st.session_state.get("strict") != strict:
    with st.spinner("⏳ 初始化知識庫…"):
        chain, memory = create_conversational_qa_chain(strict=strict)
        st.session_state.chain = chain
        st.session_state.memory = memory
        st.session_state.strict = strict


def render_sources(sources: list) -> None:
    if not sources:
        return
    with st.expander(f"📄 這個答案參考了 {len(sources)} 個文件片段（點開可核對）"):
        for doc in sources:
            st.markdown(f"**{doc.metadata.get('source', '未知來源')}｜{doc.metadata.get('locator', '')}**")
            st.caption(doc.page_content[:300].replace("\n", " ") + "…")


# ─────────────────────────────────────────────────────────────────────
# 聊天記錄
# ─────────────────────────────────────────────────────────────────────

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("rewritten"):
            st.caption(f"🔁 檢索前被改寫成：「{message['rewritten']}」")
        st.markdown(message["content"])
        render_sources(message.get("sources", []))

# ─────────────────────────────────────────────────────────────────────
# 新問題
# ─────────────────────────────────────────────────────────────────────

if prompt := st.chat_input("你想了解什麼？（例：年假規則是什麼？）"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("⏳ 查詢中…"):
            result = ask_conversational(st.session_state.chain, prompt)

        rewritten = result["generated_question"]
        # 追問被改寫的那一刻要讓人看見，這是多輪對話最重要的畫面
        if rewritten.strip() != prompt.strip():
            st.caption(f"🔁 檢索前被改寫成：「{rewritten}」")
        st.markdown(result["answer"])
        render_sources(result["sources"])

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "rewritten": rewritten if rewritten.strip() != prompt.strip() else "",
        }
    )

st.sidebar.divider()
st.sidebar.caption(f"向量庫路徑：`{CHROMA_DB_PATH}`")
