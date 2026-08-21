"""System prompt 與 prompt templates —— RAG 系統的看門人。

鐵律 1 就寫在這個檔案裡。整個「不腦補、找不到就說不知道」的行為，
不是靠程式碼的 if-else，而是靠底下這幾段文字。

這個檔案刻意提供**兩套** prompt：
  嚴謹版（qa_prompt）      ── 上線要用的，明確禁止腦補
  寬鬆版（loose_qa_prompt）── 課堂上「壞掉的版本」，故意把那條禁令拿掉

兩套走同一條 chain、同一個 retriever、同一份文件，
差別只有這幾行字——這就是課堂上最有戲的一幕。
"""

from langchain_core.prompts import PromptTemplate

# ─────────────────────────────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────────────────────────────

QA_SYSTEM_PROMPT = """你是公司內部知識庫助手。回答必須遵守以下原則：

1. 只根據提供的文件內容回答問題。
2. 如果文件中找不到相關資訊，明確說「根據提供的文件，我找不到 [主題] 的相關內容」。
3. 絕不進行推測或使用訓練資料中的其他知識。
4. 每個回答都必須明確標記資訊的來源，例如「根據員工手冊第 12 頁」或「根據 FAQ 文件」。

你是一個可信的助手，寧可說「我不知道」，也不要胡編亂造。"""

# 「壞掉的版本」：一個看起來人畜無害、但少了防幻覺條款的 system prompt。
# 少的就是上面第 2、3 條。課堂上跑一次就知道差多少。
LOOSE_SYSTEM_PROMPT = """你是公司內部知識庫助手。
請參考提供的文件內容，盡量幫使用者解答問題，讓回答聽起來專業而完整。"""

# 離線回答器靠這句話判斷「現在是嚴謹模式還是寬鬆模式」。
# 刻意不用人工標記，而是直接偵測 system prompt 裡那條禁令在不在——
# 因為這正是要教的事：**行為的差別來自 prompt 本身，不是來自另外一支程式。**
STRICT_RULE_MARKER = "寧可說「我不知道」"

# ─────────────────────────────────────────────────────────────────────
# 問答 prompt
# ─────────────────────────────────────────────────────────────────────

# 用明確的分隔線把「文件」框起來，有兩個好處：
# 1. LLM 比較不會把文件內容誤當成使用者的指令（prompt injection 的基本防線）
# 2. 離線回答器可以精準地把 context 切出來
CONTEXT_BEGIN = "===文件開始==="
CONTEXT_END = "===文件結束==="
QUESTION_PREFIX = "問題："

QA_PROMPT_TEMPLATE = f"""{QA_SYSTEM_PROMPT}

使用以下文件片段回答問題。

{CONTEXT_BEGIN}
{{context}}
{CONTEXT_END}

{QUESTION_PREFIX}{{question}}

請根據上述文件內容回答，並標明來源。如果文件中沒有相關資訊，請明確說明「根據提供的文件，我找不到相關內容」。"""

LOOSE_QA_PROMPT_TEMPLATE = f"""{LOOSE_SYSTEM_PROMPT}

以下是一些參考資料。

{CONTEXT_BEGIN}
{{context}}
{CONTEXT_END}

{QUESTION_PREFIX}{{question}}

請回答上述問題。"""

qa_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=QA_PROMPT_TEMPLATE,
)

loose_qa_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=LOOSE_QA_PROMPT_TEMPLATE,
)

# ─────────────────────────────────────────────────────────────────────
# 文件片段的格式：出處要跟著內容一起進 prompt
# ─────────────────────────────────────────────────────────────────────

# 預設的 stuff chain 只會把 page_content 串起來，metadata 整個丟掉——
# 那樣 LLM 根本不知道每段話來自哪裡，當然標不出「第 12 頁」。
# 把出處寫進每個片段的開頭，引用能力就是這樣來的。
SOURCE_PREFIX = "【出處："
DOCUMENT_PROMPT_TEMPLATE = SOURCE_PREFIX + "{source}｜{locator}】\n{page_content}"

document_prompt = PromptTemplate(
    input_variables=["page_content", "source", "locator"],
    template=DOCUMENT_PROMPT_TEMPLATE,
)

# ─────────────────────────────────────────────────────────────────────
# 多輪對話：把「那病假呢？」補成完整問題
# ─────────────────────────────────────────────────────────────────────

CONDENSE_MARKER = "改寫成一個獨立、完整的問題"

CONDENSE_QUESTION_TEMPLATE = f"""以下是一段對話，以及使用者接下來提出的最新問題。
請把最新問題{CONDENSE_MARKER}，讓它脫離對話也看得懂。
只輸出改寫後的問題本身，不要加任何說明或標點以外的文字。

對話紀錄：
{{chat_history}}

最新問題：{{question}}
改寫後的獨立問題："""

condense_question_prompt = PromptTemplate(
    input_variables=["chat_history", "question"],
    template=CONDENSE_QUESTION_TEMPLATE,
)

# 對話紀錄的角色標籤。離線改寫器靠 USER_TAG 找出「上一輪使用者問了什麼」。
USER_TAG = "使用者："
ASSISTANT_TAG = "助手："

# 找不到答案時的標準句型。evaluate.py 與測試都用這個字串判斷「有沒有誠實說不知道」。
NOT_FOUND_TEMPLATE = "根據提供的文件，我找不到「{topic}」的相關內容。"
