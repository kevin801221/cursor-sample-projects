# RAG 知識庫 Chatbot — 查完再答

> Cursor 課程 Project 9（第 30 章）：LangChain + ChromaDB + Streamlit。
> 一句話：**查完再答，讓公司文件秒回答案還附上出處**——不是 LLM 的記憶，而是你給它的證據。

## 專案規格

| | |
|---|---|
| **最終成果** | 能上傳 PDF、Markdown、網頁並附來源引用的問答機器人；支援多輪對話；追問也能答對 |
| **技術棧** | LangChain、ChromaDB、OpenAI embeddings、Streamlit |
| **預估時間** | 6–8 小時，含索引建立到聊天介面的全部流程 |
| **前置需求** | 具備 OpenAI API 金鑰，已安裝 Cursor 與 uv |

## 這個 Chatbot 做什麼

- 載入公司文件（PDF、Markdown、網頁）並建立持久化向量索引
- 使用者提問時，自動找到最相關的文件片段作為「證據」
- 生成的每個回答都附上來源引用與頁碼，讓人能核對真實性
- 支援多輪對話：追問「那病假呢？」也能理解是在問病假規則（不是重起對話）
- **關鍵需求**：答案來自文件，找不到就明說「我不知道」，不腦補、不幻覺

## RAG 四階段流程

```
【離線索引】                              【線上查詢】
文件 → 切塊 → 嵌入 → 向量庫             問題 → 檢索 → 組 prompt → LLM → 附出處回答
       ↓      ↓      ↓               ↓      ↓        ↓          ↓
    1000字  300維   ChromaDB        文本  top-k  上下文+記憶  引用+位置
   /塊  重  高維   持久化           embedding 證據  system     消除幻覺
   疊20%   向量   保存本地          相似度  區塊  prompt
```

### 四個階段拆解

| 階段 | 輸入 | 處理 | 輸出 | 工具 |
|---|---|---|---|---|
| **1. 切塊** | 長文件 | RecursiveCharacterTextSplitter | 段落列表 | LangChain |
| **2. 嵌入** | 每段文字 | OpenAI embedding API | 高維向量 | OpenAI models |
| **3. 檢索** | 問題 + 向量庫 | 向量相似度搜尋 | top-k 最相關段落 | ChromaDB |
| **4. 生成** | 證據 + 問題 + 記憶 | LLM 生成回答 | 附來源引用的答案 | ChatOpenAI |

## 開發流程（五個階段，先建索引再做聊天）

| 階段 | 做什麼 | 驗收 |
|---|---|---|
| 1. 環境與模型設定 | 安裝依賴、設定 API 金鑰、選擇 embedding 與 LLM 模型 | `uv run app.py` 不報錯 |
| 2. 文件載入與切塊 | 支援 PDF / Markdown / 網頁，統一切塊參數 | 載入員工手冊成功，切出 100+ 區塊 |
| 3. 向量索引與持久化 | ChromaDB 存向量、設定持久化路徑、重開能復原 | `chroma_db/` 資料夾存在，重啟 app 後向量庫還在 |
| 4. 檢索鏈與 system prompt | RetrievalQA + 明確的「找不到就說不知道」指令 | 問已有的問題能附來源；問沒有的回答「找不到」 |
| 5. 多輪對話與聊天介面 | ConversationBufferMemory + Streamlit 聊天框 | 追問「那病假呢？」也答得對；記憶清除按鈕 |

## 專案結構

```
rag-chatbot/
├── data/
│   ├── sample_handbook.pdf         # 示例員工手冊
│   └── faqs.md                     # 示例 FAQ 文件
├── chroma_db/                      # ChromaDB 向量庫（持久化）
│   ├── 0/
│   │   ├── data.parquet
│   │   └── metadata.json
│   └── chroma.sqlite3
├── src/
│   ├── __init__.py
│   ├── loader.py                   # 文件載入器（PDF / Markdown / 網頁）
│   ├── chunker.py                  # 文字切塊邏輯
│   ├── embeddings.py               # 向量化與 ChromaDB 操作
│   ├── retriever.py                # 檢索鏈設定
│   ├── prompts.py                  # system prompt 與 prompt templates
│   └── memory.py                   # 多輪對話記憶管理
├── evaluate.py                     # 測試集評估腳本
├── offline_index.py                # 離線索引建立（CLI 工具）
├── app.py                          # Streamlit 聊天介面
├── pyproject.toml                  # uv 依賴定義
└── walkthrough.md                  # 完整逐步教學
```

## 五條鐵律（本課核心）

1. **查完再答，每個回答都附出處**——找到的證據片段要顯示，讓使用者能核對真假；沒找到就明說「我不知道」，不要腦補。
2. **四個數字不是隨便訂的**——`chunk_size=1000`、`chunk_overlap=200`、`k=4`、`temperature=0`，各自平衡不同取捨；調得不對答案會差天差地。
3. **多輪對話要補完問題，不是重起對話**——用 `ConversationBufferMemory` 記著前一輪，讓「那病假呢？」被理解成「公司的病假規則」，不是「什麼東西的病假」。
4. **切塊、檢索、生成各有各的調整旋鈕**——答案錯了先定位是哪個階段出問題：找不著是切塊太大、找著但不對是 temperature 太高或 k 太少、被截斷是 max_tokens 太小。
5. **離線索引與線上查詢分離，但共用一份向量庫**——建索引時一次性處理，查詢時用檢索鏈秒回；換向量資料庫時，retriever 抽象讓其餘程式碼幾乎不用改。

## 快速開始

```bash
# 1. 建立專案
git clone <repo>
cd project-9
uv sync

# 2. 設定環境
cat > .env.local << EOF
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4.1-mini
EOF

# 3. 建立離線索引（一次性，初始化知識庫）
uv run offline_index.py --input data/sample_handbook.pdf --persist

# 4. 啟動聊天介面
uv run streamlit run app.py

# 5. 開瀏覽器問問題
# 問：「年假規則是什麼？」
# 回：「根據《員工手冊第 12 頁》，年假為每年 ... 」
```

## 常見一次性設定

- **PDF 載入異常**：確認 `PyPDF2` 或 `pdfplumber` 已安裝
- **ChromaDB 資料夾權限**：`chroma_db/` 要可讀寫，`chmod 755` 或檢查硬碟空間
- **向量維度不符**：embedding model 改了要刪 `chroma_db/` 重建索引

完整建置步驟、RAG 原理深度講解、Cursor Agent 提示詞、常見坑排錯，見 **[walkthrough.md](./walkthrough.md)**。
