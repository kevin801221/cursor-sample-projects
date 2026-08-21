"""文字切塊：長文件 → 一堆帶出處的小區塊。

RAG 四階段的第 1 階段。這裡有兩個關鍵數字（鐵律 2：四個數字不是隨便訂的）。
"""

from __future__ import annotations

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ─────────────────────────────────────────────────────────────────────
# 鐵律 2 的第 1、2 個數字
# ─────────────────────────────────────────────────────────────────────

# CHUNK_SIZE：一個區塊最多幾個字符。
#   太小 → 一句話被切成兩半，上下文斷掉，檢索到也讀不懂。
#   太大 → 精準度被稀釋；一個 5000 字的區塊裡只有 50 字在講年假，
#           剩下 4950 字全是雜訊，LLM 的注意力被拉走。
#   1000 字符對中文大約是 300–500 個漢字，剛好是「一個完整小節」的長度。
CHUNK_SIZE = 1000

# CHUNK_OVERLAP：相鄰兩個區塊重疊幾個字符。
#   太小 → 關鍵句剛好被切在區塊邊界，兩邊都只有半句，檢索時直接消失。
#   太大 → 同一段話在向量庫裡出現很多次，top-k 被重複內容佔滿，等於變相減少 k。
#   200 = CHUNK_SIZE 的 20%，是「邊界保險」與「不浪費 k」之間的常用折衷。
CHUNK_OVERLAP = 200

# 中文標點要排在英文標點前面，不然 splitter 會在英文句號都找不到的情況下
# 退化成硬切字元，把「年假為每年 14 天」切成「年假為每年 1」+「4 天」。
SEPARATORS = ["\n\n", "\n", "。", "；", "，", " ", ""]


def chunk_documents(
    documents: list[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """切塊，並且**原封不動保留每個 Document 的 metadata**。

    保留 metadata 是整個引用機制的命脈：切完之後每個小區塊都還記得
    自己來自哪個檔案、第幾頁，回答才附得出出處。
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=SEPARATORS,
        length_function=len,
    )

    chunks: list[Document] = []
    for doc in documents:
        for i, split in enumerate(splitter.split_text(doc.page_content)):
            chunks.append(
                Document(
                    page_content=split,
                    metadata={**doc.metadata, "chunk_index": i},
                )
            )
    return chunks


if __name__ == "__main__":
    import os

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    from src.loader import load_markdown

    docs = load_markdown(os.path.join(here, "data", "員工手冊.md"))

    # ── 自我檢查 1：metadata 有沒有活著穿過切塊 ──
    chunks = chunk_documents(docs)
    assert chunks, "切不出任何區塊"
    assert all(c.metadata.get("locator") for c in chunks), "切塊之後出處掉了"
    assert all(len(c.page_content) <= CHUNK_SIZE for c in chunks), "有區塊超過 CHUNK_SIZE"
    print(f"✓ 切塊保住出處：{len(docs)} 個章節 → {len(chunks)} 個區塊，metadata 全數存活")

    # ── 自我檢查 2：overlap 真的有重疊 ──
    # 文件要夠長，重疊造成的差異才看得出來：
    # overlap=200 時每塊前進 800 字，overlap=0 時前進 1000 字，
    # 文件短的話兩者會湊巧切出一樣多塊，測了等於沒測。
    long_doc = [Document(page_content="甲" * 5000, metadata={"source": "t", "page": 1, "locator": "t"})]
    a = chunk_documents(long_doc, chunk_size=1000, chunk_overlap=200)
    b = chunk_documents(long_doc, chunk_size=1000, chunk_overlap=0)
    assert len(a) > len(b), f"overlap=200 應該切出比 overlap=0 更多的區塊（{len(a)} vs {len(b)}）"
    print(f"✓ overlap 生效：overlap=200 切出 {len(a)} 塊，overlap=0 切出 {len(b)} 塊")

    # ── 旋鈕實驗：chunk_size 調大會發生什麼事（鐵律 2 / 鐵律 4）──
    #
    # 注意這裡刻意把整份手冊當成「一坨長文」再切，而不是照章節切。
    # 因為每一章本來就只有幾百字，照章節切的話 chunk_size 設 1000 還是 5000
    # 切出來一模一樣，實驗會做不出差異——這本身也是個重點：
    # **文件本來就有結構時，順著結構切贏過調 chunk_size。**
    from src.embeddings import LocalHashingEmbeddings

    emb = LocalHashingEmbeddings()
    question = "病假規則是什麼？"
    answer_text = next(d.page_content for d in docs if "病假規定" in d.metadata["locator"])
    filler = "\n".join(
        d.page_content for d in docs if "病假規定" not in d.metadata["locator"]
    )

    print(f"\n【旋鈕實驗】同一段病假條文，塞進不同大小的區塊裡，問「{question}」：")
    print(f"{'區塊大小':>9} | {'病假條文佔比':>11} | {'相似度':>8} | 意思")
    print("-" * 76)
    for size in (300, 500, CHUNK_SIZE, 3000, 5000):
        block = (answer_text + "\n" + filler)[:size]
        share = 100 * min(len(answer_text), size) / size
        score = emb.similarity(question, block)
        note = "← 建議值" if size == CHUNK_SIZE else ""
        print(f"{size:>9} | {share:>10.0f}% | {score:>8.3f} | {note}")

    print("\n讀法：區塊越大，同一段病假條文在裡面的佔比越低，相似度就跟著掉——")
    print("      這就是「精準度被稀釋」。檢索排名靠的是整塊的相似度，不是塊裡那一句。")
    print("      但也不能無限調小：切太碎會讓一條規定被拆成兩半，兩邊都答不完整。")
