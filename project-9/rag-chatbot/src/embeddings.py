"""向量化與 ChromaDB 操作 —— 以及本專案的 **provider 切換點**。

RAG 四階段的第 2 階段（嵌入）。

這個檔案是整堂課「離線也能上課」的關鍵。它提供兩種 embedding provider：

  openai  ── OpenAIEmbeddings，1536 維，要 API key，要花錢
  offline ── LocalHashingEmbeddings，4096 維，純本機計算，零成本、零網路

**重點：換 provider 不會動到 retriever／chain／prompt 任何一行。**
因為兩者都實作 LangChain 的 `Embeddings` 介面，對上層來說長得一模一樣。
這正是鐵律 5 說的「retriever 抽象讓其餘程式碼幾乎不用改」——
今天換的是 embedding provider，明天換 ChromaDB 成 Pinecone 也是同一招。
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from collections import Counter

import numpy as np
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from src import PROJECT_ROOT

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(PROJECT_ROOT, "chroma_db"))
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# 離線嵌入的維度。維度太小 hash 碰撞會多到把訊號蓋掉——
# 實測 512 維時「病假問題 vs 病假條文」跟「vs 資安條文」的相似度是 0.104 對 0.103，
# 完全分不開（一次碰撞就等於一次真命中）。4096 維之後檢索測試 top-1 全中。
# 調大只花記憶體不花時間，短句比對要準就別省這個。
OFFLINE_EMBEDDING_DIM = 4096


# ─────────────────────────────────────────────────────────────────────
# Provider 切換
# ─────────────────────────────────────────────────────────────────────


def active_provider() -> str:
    """現在到底走哪一條路？"openai" 或 "offline"。

    規則（由強到弱）：
      1. DEMO_OFFLINE=1  → 強制離線，就算有 key 也不打 API（課堂示範用）
      2. 有 OPENAI_API_KEY → openai
      3. 都沒有 → 自動退回 offline，而不是拋錯中斷
    """
    if os.getenv("DEMO_OFFLINE") == "1":
        return "offline"
    return "openai" if os.getenv("OPENAI_API_KEY") else "offline"


def provider_label() -> str:
    """給畫面上顯示用的一行字，讓人一眼知道現在的答案是誰生出來的。"""
    if active_provider() == "openai":
        return f"OpenAI（embedding: {EMBEDDING_MODEL}）"
    return f"離線模式（LocalHashingEmbeddings {OFFLINE_EMBEDDING_DIM} 維 + 抽取式回答器，不打任何 API）"


# ─────────────────────────────────────────────────────────────────────
# 離線嵌入：確定性的字元 n-gram hashing 向量
# ─────────────────────────────────────────────────────────────────────

_ASCII_WORD = re.compile(r"[a-z0-9]+")
_CJK_RUN = re.compile(r"[一-鿿]+")


def _tokens(text: str) -> Counter:
    """把一段文字拆成 token 袋。純字串處理，沒有模型、沒有網路。

    中文只取 bigram（「病假」「年假」），不取單字。
    實測加了單字反而更差——「假」「是」「的」這種字到處都是，
    等於把每個區塊都往同一個方向拉，反而蓋掉「病假」這種真正有鑑別力的訊號。
    """
    lowered = text.lower()
    bag: Counter = Counter()

    for word in _ASCII_WORD.findall(lowered):
        bag[word] += 1.0

    for run in _CJK_RUN.findall(lowered):
        for i in range(len(run) - 1):
            bag[run[i : i + 2]] += 1.0

    if not bag:
        # 保險絲：整段只有單個中文字（例如查詢就打一個「假」），
        # 沒有 bigram 可取時退回單字，免得產生全零向量讓所有距離都一樣。
        for run in _CJK_RUN.findall(lowered):
            for ch in run:
                bag[ch] += 1.0

    return bag


def _hash_slot(token: str) -> tuple[int, int]:
    """token → (維度索引, 正負號)。

    用 blake2b 而不是 Python 內建的 hash()，因為內建 hash 對字串會加隨機種子，
    換一次程序結果就變——那樣建好的索引下次啟動就對不上了。
    正負號是 signed hashing 的標準做法，用來抵銷 hash 碰撞造成的偏差。
    """
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    index = int.from_bytes(digest[:4], "big") % OFFLINE_EMBEDDING_DIM
    sign = 1 if digest[4] & 1 else -1
    return index, sign


# 只在「查詢」那一側丟掉的 token：問句的骨架詞。
#
# 「病假規則是什麼？」拆出 6 個 bigram，只有「病假」是使用者真正要查的東西，
# 其他 5 個（規則／則是／是什／什麼／的規）在一份公司規章裡到處都是，
# 會把整個查詢向量拉向「所有講規定的段落」。實測不丟的話，
# 問「病假規則是什麼？」排第一的是〈資訊安全與設備管理〉那一頁；丟掉之後才是病假 FAQ。
#
# 只丟查詢側、不丟文件側，是因為文件裡的「規定」是內容，問句裡的「規定」是語助詞。
_QUERY_STOP_BIGRAMS = frozenset(
    {
        "是什", "什麼", "怎麼", "麼樣", "麼算", "麼辦", "麼請", "麼做",
        "如何", "有哪", "哪些", "可以", "需要", "有沒", "沒有", "請問",
        "多少", "多久", "幾天", "幾日", "則是", "的規", "規則", "規定",
    }
)


def _embed(text: str, is_query: bool = False) -> list[float]:
    bag = _tokens(text)
    if is_query:
        stripped = Counter({t: c for t, c in bag.items() if t not in _QUERY_STOP_BIGRAMS})
        # 保險絲：整句都是問句骨架（例如使用者只打「是什麼？」）就不丟，
        # 免得產生全零向量讓所有文件的距離都一樣。
        if stripped:
            bag = stripped

    vec = np.zeros(OFFLINE_EMBEDDING_DIM, dtype=np.float32)
    for token, count in bag.items():
        # sublinear tf：出現 10 次不代表重要 10 倍，取 log 壓一下，
        # 免得「公司」「員工」這種到處都是的詞把向量方向整個拉走。
        weight = 1.0 + math.log(count)
        index, sign = _hash_slot(token)
        vec[index] += sign * weight

    norm = float(np.linalg.norm(vec))
    if norm == 0.0:
        return vec.tolist()
    # L2 normalize：長區塊與短區塊才能公平比較（cosine 相似度 = 正規化後的內積）
    return (vec / norm).tolist()


class LocalHashingEmbeddings(Embeddings):
    """符合 LangChain `Embeddings` 介面的離線嵌入。

    對 Chroma、retriever、chain 來說，它跟 OpenAIEmbeddings 完全可以互換——
    這就是「介面」的價值：上層程式碼一行都不用改。

    ponytail: 這是 TF 加權的 hashing 向量，不是神經網路嵌入。
    上限很明確——它認得「字面相近」（病假 ↔ 病假規則），
    但認不得「語義相近而字面不同」（年假 ↔ annual leave）。
    公司內部文件的問答八成是前者，所以離線 demo 夠用；
    要跨語言或同義詞檢索，就把 OPENAI_API_KEY 加回來換 provider。
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return _embed(text, is_query=True)

    def similarity(self, question: str, evidence: str) -> float:
        """問題與證據的 cosine 相似度，範圍大約 0–1。

        兩個參數不對稱：第一個當查詢處理（會丟掉問句骨架詞），第二個當文件處理。
        給抽取式回答器與切塊旋鈕實驗用。
        """
        vq = np.array(_embed(question, is_query=True), dtype=np.float32)
        ve = np.array(_embed(evidence), dtype=np.float32)
        return float(np.dot(vq, ve))


def get_embeddings() -> Embeddings:
    """依 provider 回傳 embedding 物件。上層只知道它是 `Embeddings`。"""
    if active_provider() == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return LocalHashingEmbeddings()


# ─────────────────────────────────────────────────────────────────────
# ChromaDB
# ─────────────────────────────────────────────────────────────────────


def resolve_collection_name(collection_name: str = "knowledge_base") -> str:
    """離線與 OpenAI 的向量維度不同（4096 vs 1536），存進同一個 collection 會炸。

    所以離線版自動加後綴，兩套索引各自存活、互不干擾。
    這就是排錯表上「ValueError: dimension mismatch」那一列的預防針。
    """
    if active_provider() == "offline":
        return f"{collection_name}_offline"
    return collection_name


def get_chroma_collection(collection_name: str = "knowledge_base") -> Chroma:
    """取得或建立 ChromaDB collection（持久化版）。

    `persist_directory` 一給，索引就寫進磁碟；重開程式、重啟 Streamlit 都還在。
    """
    return Chroma(
        collection_name=resolve_collection_name(collection_name),
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_DB_PATH,
    )


def add_documents_to_chroma(
    documents: list[Document],
    collection_name: str = "knowledge_base",
) -> int:
    """把 Document 清單加進 ChromaDB，回傳實際加入的數量。

    add_documents 會自動呼叫 embedding provider 向量化，並寫進持久化目錄。
    """
    if not documents:
        return 0
    vectorstore = get_chroma_collection(collection_name)
    ids = vectorstore.add_documents(documents)
    return len(ids)


def count_documents(collection_name: str = "knowledge_base") -> int:
    """目前索引裡有幾個區塊。app.py 用它判斷「是不是還沒建索引」。"""
    try:
        return get_chroma_collection(collection_name)._collection.count()
    except Exception:
        return 0


def reset_collection(collection_name: str = "knowledge_base") -> None:
    """砍掉重練。只砍目前 provider 的 collection，不會誤傷另一套索引。"""
    vectorstore = get_chroma_collection(collection_name)
    try:
        vectorstore.delete_collection()
    except Exception:
        pass


def query_collection(
    query: str,
    k: int = 4,
    collection_name: str = "knowledge_base",
) -> list[dict]:
    """查詢前 k 個最相似的區塊，每筆帶 content / metadata / distance。

    distance 越小越接近。課堂上把它印出來很有價值——
    學生可以親眼看到「問文件裡沒有的東西時，distance 明顯變大」。
    """
    vectorstore = get_chroma_collection(collection_name)
    results = vectorstore.similarity_search_with_score(query, k=k)
    return [
        {"content": doc.page_content, "metadata": doc.metadata, "distance": float(score)}
        for doc, score in results
    ]


if __name__ == "__main__":
    # 自我檢查：離線嵌入必須「確定性」而且「排得出相關性」，不然整條 RAG 都白搭。
    import os

    from src.loader import load_markdown

    emb = LocalHashingEmbeddings()

    # ── 檢查 1：確定性 ──
    v1 = emb.embed_query("病假規則是什麼？")
    v2 = emb.embed_query("病假規則是什麼？")
    assert v1 == v2, "同一段文字兩次嵌入結果不同 → 建好的索引下次啟動就對不上"
    assert len(v1) == OFFLINE_EMBEDDING_DIM

    # ── 檢查 2：用真的章節排序，而不是拿兩個短句比大小 ──
    # 短句只共用一個 bigram 時，一次 hash 碰撞就能造出一樣的分數，
    # 那種測試會給假的安全感。要驗證檢索能力就得用真實長度的文件。
    chapters = load_markdown(os.path.join(PROJECT_ROOT, "data", "員工手冊.md"))
    cases = {
        "病假規則是什麼？": "病假",
        "年假可以遞延嗎？": "年假",
        "加班費怎麼算？": "加班",
        "報帳單據有時效嗎？": "報帳",
    }
    for question, keyword in cases.items():
        best = max(chapters, key=lambda c: emb.similarity(question, c.page_content))
        assert keyword in best.page_content, (
            f"問「{question}」排第一的是《{best.metadata['locator']}》，裡面沒有「{keyword}」"
        )
        print(f"✓ 「{question}」→ 排第一：{best.metadata['locator']}")

    print(f"✓ 確定性：兩次嵌入完全相同（{OFFLINE_EMBEDDING_DIM} 維）")
    print(f"✓ 目前 provider：{provider_label()}")
