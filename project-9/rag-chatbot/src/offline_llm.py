"""離線 LLM 替身：抽取式回答器（Extractive Answerer）。

**這個檔案是「課堂不能翻車」的保險絲。**

沒有 OPENAI_API_KEY 的時候，整條 RAG 流程還是要能從頭跑到尾。
做法不是把 chain 拔掉走另一條路，而是做一個**符合 LangChain `BaseChatModel` 介面**的
假 LLM，塞進同一個 ConversationalRetrievalChain 裡。

它跟真 LLM 的差別只有一個：
  真 LLM  → 讀完證據，用自己的話「生成」答案
  這一支  → 讀完證據，把最相關的原句「抽出來」，一個字都不改

所以它永遠不可能幻覺——它根本不會造句。
反過來說，它也不會摘要、不會跨段落推理。這個上限是刻意的，
課堂上要示範「幻覺」時，靠的不是它會不會編，而是 prompt 有沒有那條禁令（見下面 strict/loose）。

它同時負責兩件事，靠 prompt 裡的句子判斷現在該做哪一件：
  1. 改寫追問（「那病假呢？」→「病假規則是什麼？」）
  2. 根據證據作答（或誠實地說找不到）
"""

from __future__ import annotations

import os
import re
from typing import Any, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from src.embeddings import LocalHashingEmbeddings
from src.prompts import (
    CONDENSE_MARKER,
    CONTEXT_BEGIN,
    CONTEXT_END,
    NOT_FOUND_TEMPLATE,
    QUESTION_PREFIX,
    SOURCE_PREFIX,
    STRICT_RULE_MARKER,
    USER_TAG,
)

# ─────────────────────────────────────────────────────────────────────
# 校準旋鈕
# ─────────────────────────────────────────────────────────────────────

# 「我到底有沒有找到答案」的門檻。
#
# 信心分數取兩個訊號的較大值，因為「有證據」有兩種長相：
#   a. 整個區塊都在講這件事      → 區塊相似度高（例：問「報帳多久拿到錢」命中整則 FAQ）
#   b. 區塊裡剛好有一句直接命中  → 單句相似度高（例：問「生日禮金多少」命中一條條文）
# 只用其中一個都會漏：長的 PDF 區塊會把單句訊號稀釋掉，
# 而 FAQ 的答句常常一個關鍵詞都不重複（問「報帳」，答句寫的是「撥款」「入帳」）。
#
# 0.16 是拿本專案語料實測出來的（37 題：27 題手冊裡有、10 題手冊裡沒有）：
#   手冊裡有的      0.167 ～ 0.640（只有「婚假有幾天？」掉到 0.136）
#   手冊裡沒有的    0.061 ～ 0.154
# 0.16 剛好落在 0.154 與 0.167 的正中間，37 題答對 36 題。
# 唯一的失手就是「婚假有幾天？」——「幾天」被當成問句骨架丟掉後，
# 查詢只剩「婚假」兩個字，向量太短撐不起分數。這是這條路線的真實上限，
# evaluate.py 會把它列出來，不藏。
#
# ponytail: 單一門檻是**跟著文件調的**，不是萬用常數。
# 換一份文件（例如講師在 Streamlit 上傳自己的 PDF）如果開始亂說「找不到」，
# 就用環境變數把它調低：OFFLINE_ANSWER_THRESHOLD=0.10
ANSWER_CONFIDENCE_THRESHOLD = float(os.getenv("OFFLINE_ANSWER_THRESHOLD", "0.16"))

# 一個答案最多引用幾句原文。太少會漏掉條件，太多就變成把整段貼回去。
MAX_EVIDENCE_SENTENCES = 4

# 短於這個長度的片段不當證據（多半是標題殘塊或「規定如下：」這種沒資訊的句子）
MIN_EVIDENCE_LENGTH = 12

_scorer = LocalHashingEmbeddings()


# ─────────────────────────────────────────────────────────────────────
# 從 prompt 裡把料撈出來
# ponytail: 假裝成 LLM 就得付這個代價——只拿得到一整串 prompt 字串。
# 所以 prompts.py 才會用 ===文件開始=== 這種明確的分隔線，parse 起來才不會猜。
# ─────────────────────────────────────────────────────────────────────


def _extract_context(prompt: str) -> str:
    start = prompt.find(CONTEXT_BEGIN)
    end = prompt.find(CONTEXT_END)
    if start == -1 or end == -1 or end < start:
        return ""
    return prompt[start + len(CONTEXT_BEGIN) : end].strip()


def _extract_question(prompt: str) -> str:
    for line in prompt.splitlines():
        stripped = line.strip()
        if stripped.startswith(QUESTION_PREFIX):
            return stripped[len(QUESTION_PREFIX) :].strip()
    return ""


def _parse_evidence_blocks(context: str) -> list[tuple[str, str]]:
    """把 context 拆回 (出處, 內文) 的清單。

    context 長這樣（由 prompts.document_prompt 組出來）：
        【出處：員工手冊.md｜第四章 病假規定】
        員工因普通傷害……
        【出處：faqs.md｜Q4. 病假有給薪嗎？】
        一年內 30 日以內……
    """
    blocks: list[tuple[str, str]] = []
    citation = "未標示來源"
    buffer: list[str] = []

    for line in context.splitlines():
        if line.lstrip().startswith(SOURCE_PREFIX):
            if buffer:
                blocks.append((citation, "\n".join(buffer)))
            citation = line.lstrip()[len(SOURCE_PREFIX) :].rstrip().rstrip("】").strip()
            buffer = []
        else:
            buffer.append(line)
    if buffer:
        blocks.append((citation, "\n".join(buffer)))

    return [(c, b) for c, b in blocks if b.strip()]


_SENTENCE = re.compile(r"[^\n。！？!?；;]+[。！？!?；;]?")

# 章節標題不是答案。它已經在出處欄位裡了，再引用一次只是佔掉一個引用名額。
_HEADING_LINE = re.compile(r"^(#+\s|第[一二三四五六七八九十百]+[章條節]\s|Q\d+[.、])")


def _sentences(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or _HEADING_LINE.match(line):
            continue
        for sentence in _SENTENCE.findall(line):
            sentence = sentence.strip()
            if len(sentence) >= MIN_EVIDENCE_LENGTH:
                out.append(sentence)
    return out


# ─────────────────────────────────────────────────────────────────────
# 主題詞：拿來組「我找不到『XXX』的相關內容」那句話
# ─────────────────────────────────────────────────────────────────────

# 疑問詞切開之後，剩下最長的那一段通常就是使用者真正在問的東西。
_QUESTION_WORDS = re.compile(
    r"是什麼|有哪些|有沒有|怎麼樣|怎麼|如何|多少|幾天|幾日|幾次|可不可以|可以|需不需要|"
    r"需要|要不要|請問|嗎|呢|吧|了沒|？|\?|。|，|,|、|：|:"
)


def _topic_of(question: str) -> str:
    parts = [p.strip() for p in _QUESTION_WORDS.split(question) if p.strip()]
    if not parts:
        return question.strip() or "這個問題"
    return max(parts, key=len)


# ─────────────────────────────────────────────────────────────────────
# 功能 1：改寫追問（鐵律 3）
# ─────────────────────────────────────────────────────────────────────

# 省略句：「那病假呢？」「加班費呢？」——只有一個主題詞加一個語尾助詞。
_ELLIPTICAL = re.compile(r"^(?:那|那麼|然後|所以)?\s*(?P<topic>.{1,14}?)\s*(?:呢|咧)\s*[?？]?$")

# 從前一輪問題裡把「句型骨架」抓出來：「年假規則是什麼？」→「規則是什麼？」
_QUESTION_FRAME = re.compile(r"(?:規則|規定|政策|辦法|流程|條件|標準|上限|天數|費用|怎麼|如何).*$")

# 抓不到骨架時的預設補法
_DEFAULT_FRAME = "的規定是什麼？"


def _frame_from_history(chat_history: str) -> str:
    """從對話紀錄裡找出可以套用的「句型骨架」。

    由新到舊掃過使用者問過的話，取第一個帶得出骨架的完整問句。
    為什麼不能只看上一句？因為上一句很可能自己也是省略句——
    連問「那病假呢？」「那婚假呢？」時，骨架要一路回溯到最早那句
    「年假規則是什麼？」才找得到，不然會退化成沒有資訊的預設值。
    """
    asked = [
        line.strip()[len(USER_TAG) :].strip()
        for line in chat_history.splitlines()
        if line.strip().startswith(USER_TAG)
    ]
    for question in reversed(asked):
        match = _QUESTION_FRAME.search(question)
        if match:
            return match.group(0)
    return _DEFAULT_FRAME if asked else ""


def condense_question(question: str, chat_history: str) -> str:
    """把省略句補成獨立問題。沒有記憶就補不了——那正是鐵律 3 要演的東西。"""
    question = question.strip()
    match = _ELLIPTICAL.match(question)
    if not match:
        # 本來就是完整問題，不用動
        return question

    frame = _frame_from_history(chat_history)
    if not frame:
        # 沒有對話歷史 → 沒有上下文可以補 → 只能原封不動送去檢索（然後大概率查不準）
        return question

    return f"{match.group('topic')}{frame}"


# ─────────────────────────────────────────────────────────────────────
# 功能 2：根據證據作答
# ─────────────────────────────────────────────────────────────────────

OFFLINE_FOOTER = "（離線模式：以上句子由抽取式回答器從文件原文直接摘錄，一字未改，未經 LLM 生成。）"


def answer_from_context(question: str, context: str, strict: bool) -> str:
    """證據 + 問題 → 答案。

    strict=True  ── system prompt 裡有防幻覺條款：沒把握就說不知道
    strict=False ── system prompt 裡沒有那條：硬答，答非所問也照答（課堂上的「壞掉版」）
    """
    topic = _topic_of(question)
    blocks = _parse_evidence_blocks(context)

    # (排序分數, 出處, 句子, 句子在原文的順序) —— 順序留著，最後要照原文排回去才好讀
    candidates: list[tuple[float, str, str, int]] = []
    best_confidence = 0.0
    closest_citation = ""

    for citation, body in blocks:
        # 訊號 a：整個區塊跟問題有多像
        block_score = _scorer.similarity(question, f"{citation}\n{body}")
        sentences = _sentences(body)

        for order, sentence in enumerate(sentences):
            # 訊號 b：單句跟問題有多像。
            # 比對時把出處接在句子前面——章節標題（「第四章 病假規定」）本身就是證據的一部分，
            # 條文內文常常一個關鍵詞都不重複（問「病假給薪」，條文寫的是「工資折半發給」）。
            # 實測：加上出處之後，25 題有答案的最低 0.151、10 題沒答案的最高 0.144，
            # 才第一次分得開；不加的話兩邊會重疊。
            sentence_score = _scorer.similarity(question, f"{citation} {sentence}")
            confidence = max(block_score, sentence_score)
            if confidence > best_confidence:
                best_confidence, closest_citation = confidence, citation
            # 排序時把區塊分數當作先驗：好區塊裡的句子整體往前排，
            # 這樣「答句一個關鍵詞都沒重複」的 FAQ 也選得中。
            candidates.append((block_score + sentence_score, citation, sentence, order))

    if not candidates:
        return NOT_FOUND_TEMPLATE.format(topic=topic) + "\n\n（檢索沒有回傳任何可用的文件片段。）"

    if strict and best_confidence < ANSWER_CONFIDENCE_THRESHOLD:
        return (
            NOT_FOUND_TEMPLATE.format(topic=topic)
            + f"\n\n檢索到最接近的段落是《{closest_citation}》，但內容與你的問題無關，"
            "我不會拿它來推測答案。\n"
            f"（最高信心分數 {best_confidence:.3f}，低於門檻 {ANSWER_CONFIDENCE_THRESHOLD}）"
        )

    candidates.sort(key=lambda item: item[0], reverse=True)
    chosen = candidates[:MAX_EVIDENCE_SENTENCES]

    # 依出處分組；同一份文件的句子照原文順序排，讀起來才像一段話而不是搜尋結果
    grouped: dict[str, list[tuple[int, str]]] = {}
    for _, citation, sentence, order in chosen:
        grouped.setdefault(citation, []).append((order, sentence))

    parts: list[str] = []
    if not strict:
        # 寬鬆版的口氣：prompt 要它「聽起來專業而完整」，它就真的裝得很有把握。
        parts.append(f"關於「{topic}」，公司規定如下：\n")
    for citation, items in grouped.items():
        parts.append(f"根據《{citation}》：")
        parts.extend(f"　{sentence}" for _, sentence in sorted(items))
        parts.append("")

    parts.append(OFFLINE_FOOTER)
    return "\n".join(parts).strip()


# ─────────────────────────────────────────────────────────────────────
# 包成 LangChain 的 BaseChatModel
# ─────────────────────────────────────────────────────────────────────


class ExtractiveChatModel(BaseChatModel):
    """離線用的假 LLM。對 chain 來說，它跟 ChatOpenAI 完全可以互換。

    這就是本課鐵律 5 的實際示範：只要守住介面，
    換 provider（甚至換掉整個模型）都不需要動 retriever、chain、prompt 任何一行。
    """

    @property
    def _llm_type(self) -> str:
        return "extractive-offline"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = "\n".join(str(m.content) for m in messages)

        if CONDENSE_MARKER in prompt:
            # chain 現在要的是「改寫後的獨立問題」
            history = prompt.split("對話紀錄：", 1)[-1].split("最新問題：", 1)[0]
            question = prompt.split("最新問題：", 1)[-1].split("\n")[0].strip()
            reply = condense_question(question, history)
        else:
            # chain 現在要的是「根據證據的答案」
            reply = answer_from_context(
                question=_extract_question(prompt),
                context=_extract_context(prompt),
                # 行為的差別完全來自 prompt：那條禁令在，就守規矩；不在，就硬答。
                strict=STRICT_RULE_MARKER in prompt,
            )

        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=reply))])


if __name__ == "__main__":
    # 自我檢查：這三個行為壞掉的話，課堂上最關鍵的三幕都會演不出來。
    assert _topic_of("休閒假怎麼請？") == "休閒假", _topic_of("休閒假怎麼請？")
    assert _topic_of("年假規則是什麼？") == "年假規則"
    print("✓ 主題詞抽取：「休閒假怎麼請？」→「休閒假」")

    history = f"{USER_TAG}年假規則是什麼？\n助手：根據員工手冊，年假依年資給假……"
    assert condense_question("那病假呢？", history) == "病假規則是什麼？"
    assert condense_question("那病假呢？", "") == "那病假呢？", "沒有記憶時不該憑空補上下文"
    assert condense_question("加班費怎麼算？", history) == "加班費怎麼算？", "完整問題不該被改寫"
    print("✓ 追問改寫：有記憶 →「病假規則是什麼？」／沒記憶 → 原封不動")

    # 用真的章節組 context。拿兩句合成短句來測 hashing 向量沒有意義——
    # 短文字只要一次 hash 碰撞就能造出漂亮的假分數，測起來會給錯誤的安全感。
    import os

    from src import PROJECT_ROOT
    from src.loader import load_markdown

    chapters = {
        doc.metadata["locator"]: doc.page_content
        for doc in load_markdown(os.path.join(PROJECT_ROOT, "data", "員工手冊.md"))
    }
    ctx = "\n".join(
        f"{SOURCE_PREFIX}員工手冊.md｜{locator}】\n{chapters[locator]}"
        for locator in ("第四章 病假規定", "第十三章 資訊安全與設備管理")
    )

    hit = answer_from_context("病假有給薪嗎？", ctx, strict=True)
    assert "病假" in hit and "找不到" not in hit, hit
    assert "第四章 病假規定" in hit, f"答對了卻沒附出處：\n{hit}"

    miss = answer_from_context("休閒假怎麼請？", ctx, strict=True)
    assert "找不到「休閒假」" in miss, miss

    loose = answer_from_context("休閒假怎麼請？", ctx, strict=False)
    assert "找不到" not in loose, loose

    print("✓ 嚴謹模式：答得出病假（附出處），答不出休閒假（誠實說找不到）")
    print("✓ 寬鬆模式：同一份證據、同一個問題，照樣硬掰出一個答案 ← 這就是幻覺的長相")
