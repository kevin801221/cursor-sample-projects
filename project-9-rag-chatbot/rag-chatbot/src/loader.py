"""文件載入器：PDF / Markdown / 網頁 → LangChain Document。

RAG 的第 0 步。這一步最重要的不是「把字讀出來」，
而是**把出處一起帶進來**——後面回答要附「第 12 頁」，靠的就是這裡塞進 metadata 的東西。

每個 Document 的 metadata 一律有三個鍵：
  source  : 檔名或網址（回答時要顯示給使用者核對）
  page    : 頁碼（PDF 是真的頁碼；Markdown 用章節序號）
  locator : 給人看的定位字串，例如「第 3 頁」或「第三章 年假規定」
"""

from __future__ import annotations

import os
import re

import requests
from langchain.schema import Document

# 網頁抓取逾時（秒）。課堂上網路不穩時寧可快速失敗，也不要讓畫面卡住。
URL_TIMEOUT_SECONDS = 10


# PDF 抽出來的文字是照「視覺換行」斷的，一個句子常常被切成好幾行。
# 不接回來的話，後面引用原文會出現「……逾期未休者由公」這種斷在半路的句子，
# 投影出去很難看，也讓人懷疑系統壞了。
_SENTENCE_END = re.compile(r"[。！？!?：:；;、]$")
_LIST_MARKER = re.compile(r"^\s*(?:[-•*]|\d+[.、)])\s")
_PDF_HEADING = re.compile(r"^\s*第[一二三四五六七八九十百]+[章條節]\s")


# 判斷「這一行是被排版硬切斷的」而不是「這一行自己就講完了」：
# 被切斷的行一定是排到滿版才換行的，所以長度會逼近該頁最長的那一行。
_WRAPPED_LINE_RATIO = 0.9


def _dewrap(text: str) -> str:
    """把被硬換行切開的句子接回去，保留條列與章節標題原本的換行。"""
    raw_lines = [line.strip() for line in text.splitlines()]
    page_width = max((len(line) for line in raw_lines), default=0)
    if page_width == 0:
        return text
    wrapped_threshold = page_width * _WRAPPED_LINE_RATIO

    lines: list[str] = []
    for line in raw_lines:
        if not line:
            lines.append("")
            continue

        previous = lines[-1] if lines else ""
        joinable = (
            previous
            # 上一行沒有標點收尾，而且是排到滿版才斷的 → 它是被切開的半句
            and len(previous) >= wrapped_threshold
            and not _SENTENCE_END.search(previous)
            and not _LIST_MARKER.match(line)
            and not _PDF_HEADING.match(line)
            and not _PDF_HEADING.match(previous)
        )
        if joinable:
            lines[-1] = previous + line
        else:
            lines.append(line)
    return "\n".join(lines)


def load_pdf(filepath: str) -> list[Document]:
    """把 PDF 讀成 Document 清單，**一頁一個 Document**，保留頁碼資訊。

    一頁一個是刻意的：這樣切塊之後每個區塊都還知道自己來自第幾頁，
    回答才有辦法寫「根據《員工手冊第 12 頁》」。
    """
    from pypdf import PdfReader  # 延遲 import：沒要讀 PDF 就不用付這個載入成本

    reader = PdfReader(filepath)
    source = os.path.basename(filepath)
    docs: list[Document] = []
    for page_num, page in enumerate(reader.pages, 1):
        text = _dewrap((page.extract_text() or "").strip())
        if not text:
            # 掃描檔或圖片頁會抽不出文字，跳過而不是塞空字串進向量庫
            continue
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": source,
                    "page": page_num,
                    "locator": f"第 {page_num} 頁",
                },
            )
        )
    return docs


# Markdown 的章節標題行，例如「## 第三章 年假規定」
_MD_HEADING = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)


def load_markdown(filepath: str) -> list[Document]:
    """讀 Markdown，**依 `##` 章節切成多個 Document**。

    為什麼不整份當一個 Document？因為章節標題本身就是最好的出處標記。
    分開之後回答可以寫「根據員工手冊 第四章 病假規定」，比「第 1 頁」有用得多。
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    source = os.path.basename(filepath)
    matches = list(_MD_HEADING.finditer(text))

    if not matches:
        # 沒有章節標題就整份當一塊，仍然補上 locator 讓下游不用做特例判斷
        return [
            Document(
                page_content=text,
                metadata={"source": source, "page": 1, "locator": "全文"},
            )
        ]

    docs: list[Document] = []
    preamble = text[: matches[0].start()].strip()
    if preamble:
        docs.append(
            Document(
                page_content=preamble,
                metadata={"source": source, "page": 1, "locator": "前言"},
            )
        )

    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.start() : end].strip()
        title = m.group("title")
        docs.append(
            Document(
                page_content=body,
                metadata={
                    "source": source,
                    "page": len(docs) + 1,
                    "locator": title,
                },
            )
        )
    return docs


_HTML_TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>|<[^>]+>", re.DOTALL | re.IGNORECASE)


def load_from_url(url: str) -> list[Document]:
    """抓網頁內文。

    ponytail: 用 regex 去標籤，不裝 beautifulsoup4。
    上限是遇到怪 HTML 會留下雜訊——真的要處理正式網站再換 bs4。
    注意：這條路徑需要網路，**不在課堂 demo 的核心路徑上**。
    """
    response = requests.get(url, timeout=URL_TIMEOUT_SECONDS)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    text = _HTML_TAG.sub(" ", response.text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return [Document(page_content=text, metadata={"source": url, "page": 1, "locator": url})]


def load_any(path_or_url: str) -> list[Document]:
    """依副檔名/協定自動分派。offline_index.py 與 Streamlit 上傳都走這裡。"""
    if path_or_url.startswith(("http://", "https://")):
        return load_from_url(path_or_url)

    ext = os.path.splitext(path_or_url)[1].lower()
    if ext == ".pdf":
        return load_pdf(path_or_url)
    if ext in (".md", ".markdown", ".txt"):
        return load_markdown(path_or_url)
    raise ValueError(f"不支援的檔案格式：{ext}（支援 .pdf / .md / .txt / http(s) 網址）")


if __name__ == "__main__":
    # 最小自我檢查：載入器最容易壞的地方是「出處掉了」，所以就檢查 metadata。
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs = load_markdown(os.path.join(here, "data", "員工手冊.md"))
    assert len(docs) >= 12, f"員工手冊應該切出 12 章以上，實際 {len(docs)}"
    assert all(d.metadata.get("source") for d in docs), "有 Document 掉了 source"
    assert all(d.metadata.get("locator") for d in docs), "有 Document 掉了 locator"
    print(f"✓ load_markdown：{len(docs)} 個章節，出處都在")
    print(f"  第一章 locator = {docs[1].metadata['locator']}")
