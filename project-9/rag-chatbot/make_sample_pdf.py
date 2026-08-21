"""把 data/員工手冊.md 轉成有真實頁碼的 data/sample_handbook.pdf。

為什麼要多這一步？因為本課最想教的引用格式是「根據《員工手冊第 12 頁》」，
而 Markdown 沒有頁碼。有一份真的 PDF，`load_pdf()` 抽出來的頁碼才是真的，
Streamlit 上傳 PDF 的那一幕也才有東西可以傳。

用 reportlab 內建的 CJK 字型 STSong-Light——**不需要下載任何字型檔**，
所以這支腳本離線也跑得起來。
"""

from __future__ import annotations

import os
import re

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE_MD = os.path.join(ROOT, "data", "員工手冊.md")
OUTPUT_PDF = os.path.join(ROOT, "data", "sample_handbook.pdf")

FONT_NAME = "STSong-Light"  # reportlab 內建的 CJK 字型，不用外部檔案
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 56
BODY_SIZE = 11
HEADING_SIZE = 15
LINE_HEIGHT = 19
# 一行放幾個字。A4 扣掉左右邊界約 483pt，中文字寬約等於字級，抓 11pt → 43 字。
CHARS_PER_LINE = 43


def wrap(text: str, width: int = CHARS_PER_LINE) -> list[str]:
    """中文沒有空白可以斷行，直接按字數硬斷就好。"""
    return [text[i : i + width] for i in range(0, len(text), width)] or [""]


def markdown_blocks(md: str) -> list[tuple[str, str]]:
    """把 Markdown 拆成 (類型, 文字)；類型是 heading 或 body。"""
    blocks: list[tuple[str, str]] = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line:
            blocks.append(("blank", ""))
        elif line.startswith("## "):
            blocks.append(("heading", line[3:].strip()))
        elif line.startswith("# "):
            blocks.append(("heading", line[2:].strip()))
        else:
            blocks.append(("body", re.sub(r"\*\*(.+?)\*\*", r"\1", line)))
    return blocks


def build_pdf(source_md: str = SOURCE_MD, output_pdf: str = OUTPUT_PDF) -> int:
    with open(source_md, "r", encoding="utf-8") as f:
        blocks = markdown_blocks(f.read())

    pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))
    c = canvas.Canvas(output_pdf, pagesize=A4)
    y = PAGE_HEIGHT - MARGIN
    pages = 1

    def new_page() -> float:
        nonlocal pages
        c.showPage()
        pages += 1
        return PAGE_HEIGHT - MARGIN

    for kind, text in blocks:
        if kind == "blank":
            y -= LINE_HEIGHT // 2
            continue

        size = HEADING_SIZE if kind == "heading" else BODY_SIZE
        # 章節標題不要落在頁尾當孤兒，剩不到三行就翻頁
        if kind == "heading" and y < MARGIN + LINE_HEIGHT * 3:
            y = new_page()

        for line in wrap(text, CHARS_PER_LINE if kind == "body" else CHARS_PER_LINE - 8):
            if y < MARGIN:
                y = new_page()
            c.setFont(FONT_NAME, size)
            c.drawString(MARGIN, y, line)
            y -= LINE_HEIGHT if kind == "body" else LINE_HEIGHT + 6

    c.save()
    return pages


if __name__ == "__main__":
    pages = build_pdf()
    print(f"✓ 已產生 {OUTPUT_PDF}（共 {pages} 頁）")

    # 自我檢查：產出來的 PDF 一定要抽得回中文，不然 load_pdf 拿到的是一堆亂碼，
    # 整條 RAG 都會建在垃圾上。這個檢查比「檔案存在」有用得多。
    from pypdf import PdfReader

    reader = PdfReader(OUTPUT_PDF)
    all_text = "\n".join((p.extract_text() or "") for p in reader.pages)
    for keyword in ("年假", "病假", "加班", "報帳"):
        assert keyword in all_text, f"PDF 抽不出「{keyword}」，文字層可能壞了"
    assert "休閒假" not in all_text, "手冊裡不該出現「休閒假」，那是課堂上要示範『查不到』的題目"
    print(f"✓ 文字層正常：{len(reader.pages)} 頁都抽得出中文，年假／病假／加班／報帳都在")
