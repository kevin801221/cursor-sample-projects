"""檢索鏈：把「向量庫」和「LLM」接起來的地方。

RAG 四階段的第 3、4 階段（檢索 + 生成）。

這個檔案示範鐵律 5：**retriever 是一層抽象**。
底下換成 OpenAI 還是離線抽取器、ChromaDB 還是別的向量庫，
`create_qa_chain()` 以上的程式碼（app.py、evaluate.py）一行都不用改。
"""

from __future__ import annotations

import os

from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from src.embeddings import active_provider, get_chroma_collection
from src.memory import create_memory
from src.prompts import (
    ASSISTANT_TAG,
    USER_TAG,
    condense_question_prompt,
    document_prompt,
    loose_qa_prompt,
    qa_prompt,
)

LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4.1-mini")

# ─────────────────────────────────────────────────────────────────────
# 鐵律 2 的第 3、4 個數字
# ─────────────────────────────────────────────────────────────────────

# RETRIEVAL_K：每次檢索取幾個最相似的區塊當證據。
#   太小 → 證據不足；答案的關鍵條件散在第 5、第 6 塊裡，LLM 看不到就答不全。
#   太大 → 注意力稀釋；把 50 塊文字塞進 prompt，LLM 在裡面找重點會找歪，
#           而且每一塊都要付 token 費用。
#   4 是「涵蓋一個主題的前後文」跟「不塞垃圾」之間的常用起點。
RETRIEVAL_K = 4

# TEMPERATURE：LLM 的隨機性。
#   0    → 同一個問題永遠得到同一個答案。RAG 系統必須這樣，
#          因為使用者會拿答案去做決策，今天問跟明天問不能不一樣。
#   >0   → 開始「創意發揮」，也就是開始腦補。RAG 最不想要的東西。
#   查公司規章不是寫文案，這個值沒有調高的理由。
TEMPERATURE = 0

# MAX_TOKENS：回答的長度上限。
#   太小 → 答案被硬生生截斷（「年假為每年 30 天……」然後就沒了）。
#   太大 → 沒有壞處，只是可能多花一點錢。
#   1000 大約可以寫完一段含條列的完整規章說明。
MAX_TOKENS = 1000


def get_llm() -> BaseChatModel:
    """依 provider 回傳 LLM。上層只知道它是 `BaseChatModel`。

    有 key → 真的 ChatOpenAI；沒有 key（或 DEMO_OFFLINE=1）→ 離線抽取式回答器。
    兩者都吃同一份 prompt、同一份證據、回傳同一種物件。
    """
    if active_provider() == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=LLM_MODEL, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)

    from src.offline_llm import ExtractiveChatModel

    return ExtractiveChatModel()


def get_retriever(collection_name: str = "knowledge_base", k: int = RETRIEVAL_K):
    """向量庫 → retriever。這一層就是鐵律 5 說的抽象邊界。"""
    vectorstore = get_chroma_collection(collection_name)
    return vectorstore.as_retriever(search_kwargs={"k": k})


def format_chat_history(chat_history: list[BaseMessage] | list[tuple[str, str]]) -> str:
    """把記憶裡的訊息排成固定格式的文字，供「改寫問題」那一步使用。

    自己控制格式而不是用 LangChain 的預設，是為了讓離線改寫器有穩定的東西可以解析。
    """
    lines: list[str] = []
    for item in chat_history:
        if isinstance(item, tuple):
            human, ai = item
            lines.append(f"{USER_TAG}{human}")
            lines.append(f"{ASSISTANT_TAG}{ai}")
        else:
            tag = USER_TAG if item.type == "human" else ASSISTANT_TAG
            lines.append(f"{tag}{item.content}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# 單輪問答（RetrievalQA）
# ─────────────────────────────────────────────────────────────────────


def create_qa_chain(collection_name: str = "knowledge_base", strict: bool = True) -> RetrievalQA:
    """建立單輪問答鏈。

    strict=True  → 用有防幻覺條款的 qa_prompt（正式版）
    strict=False → 用拿掉那條的 loose_qa_prompt（課堂上的「壞掉版」）

    注意：兩者**只差一個 prompt 物件**，chain、retriever、向量庫、LLM 全部相同。
    課堂上要證明「system prompt 才是防幻覺的關鍵」，靠的就是這個對照。
    """
    return RetrievalQA.from_chain_type(
        llm=get_llm(),
        chain_type="stuff",  # 直接把區塊塞進 prompt，最單純也最好懂
        retriever=get_retriever(collection_name),
        chain_type_kwargs={
            "prompt": qa_prompt if strict else loose_qa_prompt,
            # 讓每個文件片段自帶出處，LLM 才標得出「第 12 頁」
            "document_prompt": document_prompt,
        },
        return_source_documents=True,
    )


def ask(question: str, collection_name: str = "knowledge_base", strict: bool = True) -> dict:
    """單輪查詢。回傳 {"answer": str, "sources": list[Document]}。"""
    chain = create_qa_chain(collection_name, strict=strict)
    result = chain.invoke({"query": question})
    return {"answer": result["result"], "sources": result["source_documents"]}


# ─────────────────────────────────────────────────────────────────────
# 多輪對話（ConversationalRetrievalChain）—— 鐵律 3
# ─────────────────────────────────────────────────────────────────────


def create_conversational_qa_chain(
    collection_name: str = "knowledge_base",
    strict: bool = True,
) -> tuple[ConversationalRetrievalChain, object]:
    """建立支援多輪對話的鏈，回傳 (chain, memory)。

    跟單輪版最大的差別：檢索之前會多一步「改寫問題」。
    「那病假呢？」這四個字向量化之後誰都認不出來，
    但先用對話歷史把它補成「病假規則是什麼？」，檢索就準了。

    memory 要一起回傳，因為 Streamlit 的「清除對話」按鈕需要拿到它（memory.clear()）。
    """
    memory = create_memory()

    return (
        ConversationalRetrievalChain.from_llm(
            llm=get_llm(),
            retriever=get_retriever(collection_name),
            memory=memory,
            # 改寫問題那一步用的 prompt
            condense_question_prompt=condense_question_prompt,
            # 作答那一步用的 prompt（含 system prompt 與出處格式）
            combine_docs_chain_kwargs={
                "prompt": qa_prompt if strict else loose_qa_prompt,
                "document_prompt": document_prompt,
            },
            get_chat_history=format_chat_history,
            return_source_documents=True,
            # 把改寫後的問題也吐出來——課堂上一定要放到螢幕上，
            # 學生才看得到「那病假呢？」變成了什麼。
            return_generated_question=True,
            # ← 重要：不指定的話，來源清單會被寫進對話記憶，把歷史污染成一團亂碼
            output_key="answer",
        ),
        memory,
    )


def ask_conversational(chain: ConversationalRetrievalChain, question: str) -> dict:
    """多輪查詢。chain 自己帶著 memory，所以不用把歷史傳進來。

    回傳 {"answer", "sources", "generated_question"}。
    """
    result = chain.invoke({"question": question})
    return {
        "answer": result["answer"],
        "sources": result.get("source_documents", []),
        "generated_question": result.get("generated_question", question),
    }


def format_sources(documents) -> list[str]:
    """把來源整理成「員工手冊.md｜第四章 病假規定」這種可以直接印的字串。"""
    seen: list[str] = []
    for doc in documents:
        label = f"{doc.metadata.get('source', '未知來源')}｜{doc.metadata.get('locator', '')}"
        if label not in seen:
            seen.append(label)
    return seen
