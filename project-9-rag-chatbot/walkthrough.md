# Walkthrough：在 Cursor 上把 RAG 知識庫 Chatbot 一步一步做出來

> 這份文件帶你從零做出 **RAG 知識庫 Chatbot**——一個能查公司文件並附出處的聊天機器人，讓 LLM 不再腦補答案。
> 你會學到一件事：**查完再答比聰明更值錢**——每個回答都附上來源、找不到就明說「我不知道」、讓使用者能核對真假。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先準備好這五件事）

1. **OpenAI API key 額度要夠**——跑一遍完整流程（載 PDF、建索引、問 5 個問題）會呼叫 embedding API 和 LLM API，估算費用 $0.5–1。先檢查帳戶有沒有額度，避免中途超額。
2. **先跑一次 `uv sync` 與 `streamlit run app.py`**——第一次裝依賴和啟動 Streamlit 會比較慢（可能 2–3 分鐘），先在機器上跑過一次，之後調整程式碼時會快很多。
3. **準備一份測試文件**（PDF、Markdown 或網頁連結）——千萬別用教科書全文，用公司手冊、FAQ 或員工規範那種 5–10 頁的文件就夠，避免索引時間太長。
4. **每個「✅ 預期看到」瀏覽一遍**——知道正常畫面長怎樣，當碰到卡關時才判斷得出「這是對的」還是「出問題了」；特別是「第二個問題答對」和「來源真的被附上」這兩個重要的里程碑。
5. **網路或額度吃緊的備用方案**：把第 3、4、5 階段的關鍵輸出（chunks 數量、indexed 數量、sample answer with sources）先在家截圖存起來，有問題時直接用截圖討論概念。

## 🗺️ 學習地圖（建議 3 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 第 1 節概念 | 25 分 | 閱讀理解（這是全篇靈魂，慢慢看） |
| 第 2 節環境設定 | 10 分 | 閱讀理解 + 動手配置 |
| 第 3 節載入與切塊 | 20 分 | 動手做（跑 loader + chunker，看 chunks 輸出） |
| 第 4 節向量化與索引 | 25 分 | 動手做（add_documents_to_chroma 的那一刻是第一個里程碑） |
| 第 5 節檢索鏈 + system prompt | 30 分 | 動手做；同時試試「不接 RAG」vs「接 RAG」的對比（一定要親自試的一幕） |
| 第 6 節多輪對話 | 15 分 | 動手做，測試「那病假呢？」 |
| 第 7 節 Streamlit 介面 | 20 分 | 動手做，啟動應用並試上傳 |
| 第 8 節排錯 + 第 9 節練習 | 15 分 | 閱讀理解 + 選做 |
| 帶走的三句話 | 10 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `./rag-chatbot/`，遙控器是 `./demo.sh`（位於 `project-9-rag-chatbot/` 根目錄，腳本自動轉發至 `rag-chatbot/demo.sh`）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 預設走離線模式（`DEMO_OFFLINE=1`）：全 10 幕完全離線、不需要 OpenAI API key、不耗網路；若要展示連線真實 API 可設定 `DEMO_OFFLINE=0`。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd project-9-rag-chatbot/rag-chatbot && uv sync` | 第一次同步虛擬環境下載依賴（約 1–2 分鐘）。課前做完後，課堂上全離線秒開 |
| 2 | `./demo.sh 1` 與 `./demo.sh 4` | 產生示範用的 `sample_handbook.pdf` 並建立 Chroma 向量索引。後續第 5–10 幕才不用等待 |
| 3 | 跑一次 `./demo.sh 9`（評估驗收） | 確認 10 題評估輸出 9/10 正確率，確保環境無誤 |
| 4 | 確認 8501 埠沒有殘留行程 | 第 10 幕 Streamlit 需要 8501 埠，被占用時會自動跳 8502 |

### 放映時間軸

時間軸切成 8 段，對應上方學習地圖（合計 180 分鐘），全長 **3 小時**。

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:25 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §1.5 | 閉卷考 vs 開書考對照表、RAG 核心架構圖、五大鐵律 | 查完再答、出處引用、無幻覺承諾 |
| 0:25–0:35 | 第 1 幕：環境與語料 | `./demo.sh 1` | `rag-chatbot/make_sample_pdf.py` | provider 標示為離線模式、8 頁 PDF 產生成功並通過中文抽取驗證 | 課堂不依賴 API key；離線也能跑完完整 RAG |
| 0:35–0:55 | 第 2 幕：載入與出處 | `./demo.sh 2` | `rag-chatbot/src/loader.py` | PDF 8 頁、Markdown 17 章，每個區塊印出 source 與頁碼/章節 | 引用能力不是最後才加——出處要在載入的第一步就塞進 metadata |
| 0:55–1:15 | 第 3 幕：切塊兩個旋鈕 | `./demo.sh 3` | `rag-chatbot/src/chunker.py` | 對照表：chunk_size 越大相似度從 0.178 降至 0.105 | 鐵律 2：太大稀釋精準度，太小切斷上下文 |
| 1:15–1:40 | 第 4 幕：建立向量索引 ⭐ | `./demo.sh 4` | `rag-chatbot/offline_index.py` | Added 21 chunks to ChromaDB、chroma_db 目錄生成 | 鐵律 5：離線索引與線上查詢分家，線上查詢才能秒回 |
| 1:40–1:55 | 第 5 幕：先看檢索本身 | `./demo.sh 5` | `rag-chatbot/src/embeddings.py` | top-4 區塊與距離；「休閒假」距離逼近 2.0（正交無關） | 區分「找不到」還是「找到但講錯」；檢索永遠回傳 k 個結果 |
| 1:55–2:10 | 第 6 幕：壞掉的版本 ⭐ | `./demo.sh 6` | `rag-chatbot/src/prompts.py` | 問「休閒假怎麼請？」→ 系統拿出差規定自信硬掰 | 沒有防幻覺 system prompt 的 RAG 一樣會腦補 |
| 2:10–2:25 | 第 7 幕：修好的版本 ⭐ | `./demo.sh 7` | `rag-chatbot/src/prompts.py` | 同一問題 →「找不到相關內容」；問年假附出處與頁碼 | 鐵律 1：查完再答、附出處、誠實比聰明值錢 |
| 2:25–2:40 | 第 8 幕：多輪對話 ⭐ | `./demo.sh 8` | `rag-chatbot/src/memory.py` | 追問「那病假呢？」被改寫成完整問題；無記憶對照組失敗 | 鐵律 3：追問要補完問題，記憶是查得到與查不到的關鍵 |
| 2:40–2:50 | 第 9 幕：數字驗收 | `./demo.sh 9` | `rag-chatbot/evaluate.py` | 10 題評估答案與來源正確率達 9/10 | 「答對」與「來源對」分開量，避免模型矇對 |
| 2:50–3:00 | 第 10 幕：Streamlit 介面 | `./demo.sh 10` | `rag-chatbot/app.py` | 瀏覽器開啟聊天室、可切換防幻覺開關、可即時上傳檔案問答 | 整合成果展示與互動體驗 |

### ⭐ 全場最值得停下來的一幕

**第 6 幕與第 7 幕的對照（`./demo.sh 6` vs `./demo.sh 7`）。**
同一個資料庫、同一個檢索演算法、同一個不存在的「休閒假」，只因為 system prompt 少了兩行防幻覺限制，第 6 幕就自信滿滿地拿「出差住宿補助」去回答休閒假；第 7 幕加上限制後，立刻誠實回答「找不到休閒假相關內容」。在第 6 幕停 3 分鐘，讓全班看清「AI 腦補不是因為資料庫沒資料，而是因為 Prompt 逼它說話」。

### 🧯 現場翻車備案

| 翻什麼 | 徵狀 | 30 秒內的救援 |
|---|---|---|
| 找不到向量索引 | 第 5–10 幕提示「向量庫是空的」 | 跑 `./demo.sh 4` 重建索引（約 3 秒完成） |
| Streamlit 埠被占用 | 瀏覽器打不開 8501 | 改用 `cd rag-chatbot && uv run streamlit run app.py --server.port 8502` |
| 中文字型在 Linux 變方塊 | PDF 產生或圖表出現問號 | 示範語料使用內建 reportlab CJK 字型，若系統異常可直接查看 `data/員工手冊.md` |
| 想要切換真實 OpenAI API | 離線模式回答固定 | 設 `export OPENAI_API_KEY=sk-...` 並執行 `DEMO_OFFLINE=0 ./demo.sh 7` |

---

## 🎬 開場故事：閉卷考試 vs 開書考試

假設現在要考一場「員工手冊規則」的考試。有兩種模式：

第一種是**閉卷考**。你走進考場沒有任何資料，光靠印象答題。「年假幾天？」你印象中好像是三十天，就寫下去；但你根本不確定，或者手冊改過規則你卻不知道。有時候題目問的是「休閒假怎麼請」——手冊根本沒寫這個，但你想要幫忙，就硬掰一個答案。老師看你的答卷說不出哪裡錯，因為你沒附證據。

第二種是**開書考**。你帶著員工手冊走進去，「年假幾天？」你翻到第 12 頁一看，清清楚楚寫著「30 天」，你就在答卷上寫「30 天（第 12 頁）」；問「休閒假怎麼請」你翻遍全書找不到，你就直接寫「根據本手冊，找不到相關內容」。每個答案都有根據，老師能核對，同學也能驗證。

今天要學的 RAG，就是把你的 Chatbot 從「閉卷考」改成「開書考」。

這個比喻會貫穿全篇。先把對照表記在心裡：

| 考試 | RAG 系統 | 技術名詞 |
|---|---|---|
| 翻書找答案 | 檢索相關文件區塊 | **retrieval** |
| 書裡的某一頁 | 文件被切成的小區塊 | **chunk** |
| 用「意思」快速翻到相關內容 | 向量相似度搜尋 | **embedding** + **向量資料庫** |
| 在答案旁邊寫「第 12 頁」 | 回答時附上出處 | **citation** |
| 找不到就說「找不到」 | system prompt 禁止幻覺 | **無幻覺承諾** |

---

## 0. 課前準備

- 安裝 Cursor、Python 3.10+、uv（[安裝指南](https://docs.astral.sh/uv/getting-started/)）
- 註冊 [OpenAI API](https://platform.openai.com/api/keys)，確認帳戶有額度
- 一份公司文件試手（PDF 或 Markdown，5–10 頁足夠）

> 🔍 **名詞卡：LLM（Large Language Model）**
> 白話：一個超大的文字預測機器，訓練資料吃過網際網路大量文章，所以它知道很多「常識」。但只有印象，沒有真憑實據。
> 比喻：一個讀過很多書的博學老爺爺，但記憶力不一定準確——他「印象中」好像讀過某件事，但不一定是真的。
>
> 🔍 **名詞卡：API（Application Programming Interface）**
> 白話：程式跟程式之間的「點餐窗口」。你的 Python 程式透過 API 窗口去呼叫 OpenAI 的 embedding 和 LLM 服務。
>
> 🔍 **名詞卡：uv**
> 白話：比 pip 快 10 倍的 Python 套件管理器。把專案的依賴寫一份，`uv sync` 一行搞定，團隊成員就能跑一樣的環境。

---

## 1. 先懂概念：RAG 四階段與五個反模式

### 1.1 RAG 是什麼（人工版本更清楚）

RAG 看名字很高科技，其實就是我們剛才說的「開書考」自動化。四個步驟環環相扣，一個沒做好整個垮。

想像你在幫公司回員工問題。正確流程：

1. **前置**：把員工手冊按章節剪開、每章用一句話標題標記
2. **使用者問**：「年假規則？」
3. **查**：在目錄裡翻找「年假」的章節，找到第 12 章
4. **答**：「根據手冊第 12 章，年假為……」**附上出處和頁碼**

RAG 就是把這套流程自動化：

```
【準備】文件 ──切塊→ 每塊標記來源 ──向量化→ 丟進向量庫（ChromaDB）
         ↓          ↓                ↓
      員工手冊    "年假為每年..." 向量(0.1, 0.3, ..., 0.7)

【回答】問題 ──向量化→ 在庫裡找最相近的 k 塊 ──給 LLM → LLM 寫答案 + 標記出處
        ↓       ↓                      ↓          ↓
     "年假？"  向量(0.09, 0.29, ...)  前 4 塊    "根據第 12 頁..."
```

核心觀念：**不是 LLM 的記憶，而是你給它的證據**。如果文件裡沒寫，LLM 就答不出來（除非它的訓練資料剛好包含，但那時已經不是「查文件」而是「靠記憶」了）。

> 🔍 **名詞卡：RAG（Retrieval-Augmented Generation）**
> 白話：「先檢索、再生成」——問題來了不要直接問 LLM，先去資料庫翻出相關文件，看著文件再讓 LLM 寫答案。「增強」的意思是：用真實證據增強了 LLM 的回答，讓它不會胡說八道。
>
> 🔍 **名詞卡：檢索（retrieval）**
> 白話：根據使用者的問題，從文件庫裡快速翻出最相關的幾頁。不是逐頁讀、而是靠某種「快速索引」的方式一秒內翻出來。
>
> 🔍 **名詞卡：幻覺（hallucination）**
> 白話：LLM 沒有根據、自己編造答案的行為。比如使用者問「我們公司有沒有 401k 退休計畫」，手冊根本沒寫，LLM 卻說「根據行業標準，通常都有」。不是真的根據你的文件。

### 1.2 四階段各自要平衡什麼

| 階段 | 關鍵數字 | 太小的後果 | 太大的後果 | 建議起點 |
|---|---|---|---|---|
| **切塊** | `chunk_size` | 失去上下文，斷句 | 稀釋精準度，「年假」淹沒在長篇裡 | 1000 字符（中文 300–500 字） |
| **切塊重疊** | `chunk_overlap` | 關鍵句被切在塊邊界，檢索時消失 | 重複區塊，答案被重複的證據稀釋 | 20%（chunk_size 的 1/5） |
| **檢索** | `k`（top-k） | 資訊不足，LLM 沒足夠證據 | 「注意力稀釋」，LLM 在 50 塊文字裡找重點累到不行 | 4 |
| **生成** | `temperature` | 每次答案不同，同一個問題回答飄移 | 太冷淡、機械化、重複詞彙 | 0（RAG 系統必須穩定） |

> 🔍 **名詞卡：切塊（chunking）**
> 白話：把一份長文件分成很多小段落。因為 LLM 一次只能讀這麼多字，太長的文件它讀不完；而且「找最相關的段落」比「讀完整份文件」快得多。
>
> 🔍 **名詞卡：embedding（向量）**
> 白話：把文字轉成一堆數字。「年假」轉成 (0.1, 0.3, ..., 0.7) 這樣 1536 個數字，「年度假期」也轉成差不多的數字，因為它們意思接近。靠這些數字可以快速找到「意思接近」的文字，不用死背文字本身。
>
> 🔍 **名詞卡：向量資料庫（vector database）**
> 白話：存放 embedding 向量的資料庫。傳統資料庫像 Excel，按欄位精確查（「名字=王小明」）；向量資料庫按「意思接近度」查（「『休假』這個向量最接近哪些文字」）。這堂課用 ChromaDB。
>
> 🔍 **名詞卡：相似度搜尋（similarity search）**
> 白話：「哪些文字最接近我這個問題」——不是精確匹配，是「意思最接近的」。就像在超市找「番茄醬」，可能也會推薦「蕃茄」、「辣椒醬」，因為都是「醬類」的概念。

### 1.3 五個常見反模式

#### 反模式 1：沒有 system prompt，讓 LLM 自作聰明
**症狀**：問「休閒假規則？」，手冊沒寫，LLM 卻說「通常是……」
**原因**：LLM 的訓練資料有休閒假常識，它自動填補空白
**修法**：加一句明確的 system prompt：

```
你是公司內部 Q&A 助手。回答一律基於提供的文件。
找不到答案時，明確說「根據提供的文件，我找不到 [主題] 的相關內容」，不要推測。
每個回答都要標記來源：「根據《員工手冊第 X 頁》」或「未在文件中找到」。
```

#### 反模式 2：chunk_size 設太大
**症狀**：搜一個「年假」詞匯，回傳的區塊裡 80% 是無關的福利政策
**原因**：一個塊是 5000 字，只有 50 字是年假內容
**修法**：降 chunk_size 到 1000，或加 chunk_overlap 確保邊界關鍵句不遺漏

#### 反模式 3：多輪對話時重起連線
**症狀**：
- 第一問：「年假規則？」回答正確
- 第二問：「那病假呢？」回答說「找不到」——明明手冊有病假內容
**原因**：每次提問都新建一個 chain 物件，記憶被清空，「那」指代不了前一個問題
**修法**：用 `ConversationBufferMemory` 記著對話歷史；Streamlit 裡用 `st.session_state` 只建一次 chain

#### 反模式 4：檢索時沒補全問題
**症狀**：追問「那病假呢？」時，系統去查「那病假呢？」的向量，沒有「公司的病假規則」上下文
**修法**：在 retriever 之前加一層「改寫問題」的步驟，讓 LLM 把「那病假呢？」改寫成「請告訴我公司的病假規則」，再去查

#### 反模式 5：答案被截斷
**症狀**：LLM 回答只有前一半：「年假為每年 30 天……」然後沒了
**原因**：`max_tokens` 設太小
**修法**：提高 ChatOpenAI 的 `max_tokens` 到 1000 或更高

### 1.4 概念確認題

❓ **想一想**：為什麼 RAG 是「開書考」而不是「開網路考」——即不是直接讓 LLM 去網路搜尋答案？

**答案**：因為我們要用自己公司的文件，不是從網路上找，這樣才有隱私和版本控制。

❓ **想一想**：如果 LLM 被 fine-tune（微調）過員工手冊，還需要 RAG 嗎？

**答案**：不一定。但 fine-tune 很貴、又慢；而且手冊改版了要重新 fine-tune。RAG 直接改文件就行，成本低、更新快。

### 1.5 離線索引 vs 線上查詢，為什麼要分開

**離線索引**（一次性）：
- 載入 100 個文件 → 切成 5000 個區塊 → 向量化（呼叫 OpenAI embedding API 5000 次） → 存進 ChromaDB
- 耗時：幾分鐘到幾小時，看檔案大小
- 費用：embedding API 有成本，但只付一次

**線上查詢**（實時）：
- 使用者提問 → 向量化這一個問題 → 在 ChromaDB 裡秒速查 top-4 → 給 LLM → 秒回
- 耗時：幾百毫秒
- 費用：embedding + LLM 費用，每次查詢都會產生，但總額不大

**為什麼要分開**：
- 避免「初始化時啥都做」導致 Streamlit 應用啟動超慢
- 支援「後上傳新文件」的更新流程（不用重新索引舊文件）
- 離線索引可以排程跑、預計成本、檢查品質

> 🔍 **名詞卡：索引（indexing）**
> 白話：把文件前置處理、切塊、向量化、存進資料庫的整套流程。像圖書館新書到貨時，不是直接放架上，而是先分類、編號、建索引卡，然後才放。
>
> 🔍 **名詞卡：ChromaDB**
> 白話：一個輕量的向量資料庫，專門存 embedding。比 Pinecone 或 Weaviate 輕、不用上雲，能存在本機；但功能也較少。對於初學或 demo 夠用。

---

## 2. 環境設定與依賴

### 2.1 建立專案結構

先搭好舞台，再開始表演。這一步就是裝道具。

```bash
mkdir -p project-9-rag-chatbot
cd project-9-rag-chatbot
uv init --name rag-chatbot
```

`.gitignore`：

```
.env.local
__pycache__/
*.pyc
chroma_db/
.streamlit/secrets.toml
```

### 2.2 設定環境變數

`.env.local`：

```bash
OPENAI_API_KEY=sk-...（你的 API 金鑰）
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4-turbo-preview
CHROMA_DB_PATH=./chroma_db
```

> 🔍 **名詞卡：環境變數（environment variable）**
> 白話：寫在 `.env.local` 裡的秘密設定（金鑰、路徑），程式跑起來時才讀進去，不會寫死在程式碼裡。.env 檔加進 `.gitignore`，金鑰就不會被 push 到 GitHub。

### 2.3 依賴清單（uv pyproject.toml）

對 Agent 說：

> 在 pyproject.toml 裡加上依賴。用 uv 管理，不用 pip。

產出重點（`pyproject.toml`）：

```toml
[project]
name = "rag-chatbot"
version = "0.1.0"
description = "RAG-based company knowledge base chatbot"

dependencies = [
    "langchain>=0.1.0",
    "langchain-openai>=0.1.0",
    "langchain-chroma>=0.1.0",
    "chromadb>=0.4.0",
    "streamlit>=1.30.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "pypdf>=3.17.0",
    "requests>=2.31.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```bash
uv sync
```

✅ **預期看到**：`uv sync` 跑完會列出所有安裝的套件版本；終端機最後一行 `All dependencies installed`。

🧯 **卡住的話**：`pip install` 改成 `uv sync` 報錯？可能是 uv 沒裝。先 `pip install uv` 再試，或改用 `pip install -e .` 走 pip 的安裝。

> 🔍 **名詞卡：LangChain**
> 白話：一個 Python 工具庫，包裝好了跟 LLM 互動、記憶管理、檢索器等常見操作。不用自己寫 HTTP 請求，LangChain 都幫你做好。

---

## 3. 階段一：文件載入與切塊

### 3.1 核心概念：為什麼要切塊

想像你有一本 100 頁的員工手冊。直接把整本書丟給 LLM 看，它累到不行、注意力散成一灘水，讀不到重點。所以我們先把它剪成 100 張紙，告訴 LLM「只看這 3 張」，它就能專心讀。

LLM 有上下文限制（`gpt-4-turbo-preview` 約 8k token）。一份 100 頁 PDF 塞進去會超出，而且即使不超也會「注意力稀釋」（模型在一堆文字裡找重點累）。

所以必須**先切**：把大文件分成小塊，在必要時只取最相關的幾塊給 LLM。

### 3.2 對 Agent 說

```
建立 src/loader.py 與 src/chunker.py：
- loader.py：支援 PDF（用 PyPDF）、Markdown（直接讀）、網頁（requests 抓）
- chunker.py：用 LangChain 的 RecursiveCharacterTextSplitter，chunk_size=1000、chunk_overlap=200、separators=["\n\n", "\n", "。", "，", ""]

loader.py 裡有三個函式：
  load_pdf(path) → list[str]：每個元素是一個 PDF 頁的內容
  load_markdown(path) → str：讀檔案
  load_from_url(url) → str：用 requests 抓網頁內文
  
chunker.py 裡有一個函式：
  chunk_documents(documents: list[str], chunk_size=1000, chunk_overlap=200) → list[Document]
  回傳 LangChain Document 物件（有 page_content 與 metadata）

範例：
  docs = load_pdf("data/handbook.pdf")
  chunks = chunk_documents(docs)
  print(len(chunks), "chunks created")
```

**產出程式碼參考**（`src/loader.py`）：

```python
import os
from typing import Union
from langchain.schema import Document
from PyPDF2 import PdfReader
import requests

def load_pdf(filepath: str) -> list[Document]:
    """將 PDF 讀成 Document 清單，保留頁碼資訊"""
    docs = []
    with open(filepath, 'rb') as f:
        reader = PdfReader(f)
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            docs.append(Document(
                page_content=text,
                metadata={"source": os.path.basename(filepath), "page": page_num}
            ))
    return docs

def load_markdown(filepath: str) -> list[Document]:
    """讀 Markdown，全文當一個 Document"""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    return [Document(
        page_content=text,
        metadata={"source": os.path.basename(filepath)}
    )]

def load_from_url(url: str) -> list[Document]:
    """用 requests + beautifulsoup 抓網頁（簡化版）"""
    response = requests.get(url)
    response.encoding = 'utf-8'
    return [Document(
        page_content=response.text,
        metadata={"source": url}
    )]
```

（`src/chunker.py`）：

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

def chunk_documents(
    documents: list[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> list[Document]:
    """切塊，保留原 metadata"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "，", " ", ""],  # 中文標點優先
        length_function=len,
    )
    
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc.page_content)
        for i, split in enumerate(splits):
            chunks.append(Document(
                page_content=split,
                metadata={**doc.metadata, "chunk_index": i}
            ))
    return chunks
```

### 3.3 驗收

```bash
uv run python -c "
from src.loader import load_pdf
from src.chunker import chunk_documents
docs = load_pdf('data/sample_handbook.pdf')
chunks = chunk_documents(docs)
print(f'Loaded {len(docs)} pages, chunked into {len(chunks)} pieces')
print(f'First chunk: {chunks[0].page_content[:200]}')
print(f'Metadata: {chunks[0].metadata}')
"
```

✅ **預期看到**：
- 列出頁數和區塊數（例如 `Loaded 8 pages, chunked into 47 pieces`）
- 顯示第一個區塊的前 200 字符和元資料（來源、頁碼）

🧯 **卡住的話**：
- `PdfReader cannot extract text`：PDF 可能被加密或是掃描圖片。改用 Markdown 測試，或用 `pdfplumber` 試試。
- 區塊數異常多（例如 1000+ chunks）：chunk_size 可能沒生效，或文件重複了。確認 separators 有沒有中文標點。

> 🔍 **名詞卡：Document（LangChain 文件物件）**
> 白話：LangChain 統一的文件格式，有 `page_content`（文字內容）和 `metadata`（來源、頁碼等元資料）。這樣後面的步驟就知道「這段文字從哪裡來」。

---

## 4. 階段二：向量化與 ChromaDB 索引

### 4.1 核心概念：什麼是向量

向量是什麼？簡單來說，是把「意思」轉成「距離」。「年假有多少天」和「年假規則」這兩句話，意思接近，所以它們轉成的向量距離很近——這樣搜尋引擎才能秒速找到「意思接近的」文字。

文字 → 向量 = 把文字轉成一堆數字，使得「語義相近的文字距離近」。

OpenAI embedding 模型（`text-embedding-3-small`）把一個句子轉成 1536 維向量。兩個向量的「距離」（cosine similarity）就是相似度。

```python
# 概念示例
embedding("年假為每年 30 天") → (0.1, 0.3, ..., 0.7)  # 1536 維
embedding("年假有多少天？")  → (0.09, 0.29, ..., 0.69)  # 1536 維
# 兩個向量的 cosine similarity ≈ 0.98（非常近）

embedding("病假怎麼請？")   → (0.2, 0.1, ..., 0.3)   # 1536 維
# cosine similarity ≈ 0.3（很遠）
```

ChromaDB 就是一個向量資料庫：存 embedding，支援秒速的相似度搜尋。

### 4.2 對 Agent 說

```
建立 src/embeddings.py，功能：
- 初始化 ChromaDB collection（client 用 persistent_client，路徑 ./chroma_db）
- 把 Document 清單加進 collection（自動呼叫 OpenAI embedding API）
- 支援查詢：給定問題文本，返回前 k 最相似的區塊（metadata 要帶著）

函式：
  get_chroma_collection(name="knowledge_base") → ChromaDB Collection
    如果 ./chroma_db 存在就載入，不存在就建新的
    
  add_documents_to_chroma(documents: list[Document], collection_name="knowledge_base") → int
    回傳加進去的文件數
    
  query_collection(query: str, k=4, collection_name="knowledge_base") → list[dict]
    每個 dict 有："content"、"metadata"、"distance"

範例：
  collection = get_chroma_collection()
  num_added = add_documents_to_chroma(chunks)
  results = query_collection("年假規則", k=4)
  for r in results:
    print(r["metadata"], r["content"][:100])
```

**產出程式碼參考**（`src/embeddings.py`）：

```python
import os
from typing import Optional
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

def get_embeddings():
    """初始化 OpenAI embeddings"""
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)

def get_chroma_collection(collection_name: str = "knowledge_base"):
    """取得或建立 ChromaDB collection（持久化版）"""
    embeddings = get_embeddings()
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_PATH,
    )
    return vectorstore

def add_documents_to_chroma(
    documents: list[Document],
    collection_name: str = "knowledge_base"
) -> int:
    """把 Document 清單加進 ChromaDB"""
    vectorstore = get_chroma_collection(collection_name)
    # LangChain Chroma 的 add_documents 會自動向量化並持久化
    ids = vectorstore.add_documents(documents)
    return len(ids)

def query_collection(
    query: str,
    k: int = 4,
    collection_name: str = "knowledge_base"
) -> list[dict]:
    """查詢前 k 最相似的區塊"""
    vectorstore = get_chroma_collection(collection_name)
    
    # similarity_search 自動向量化 query，返回 Document 清單
    results = vectorstore.similarity_search(query, k=k)
    
    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "distance": None  # LangChain Chroma 不直接回傳距離，但相似度由順序反映
        }
        for doc in results
    ]
```

### 4.3 驗收

```bash
uv run python -c "
from src.loader import load_pdf
from src.chunker import chunk_documents
from src.embeddings import add_documents_to_chroma, query_collection
import os

# 清空舊索引（測試用）
import shutil
if os.path.exists('./chroma_db'):
    shutil.rmtree('./chroma_db')

# 載入、切塊、索引
docs = load_pdf('data/sample_handbook.pdf')
chunks = chunk_documents(docs)
num = add_documents_to_chroma(chunks)
print(f'Added {num} chunks to ChromaDB')

# 查詢
results = query_collection('年假規則')
print(f'Found {len(results)} results for 年假規則:')
for r in results[:2]:
    print(f'  Source: {r[\"metadata\"]}, Content: {r[\"content\"][:100]}...')

# 檢查持久化
print(f'./chroma_db exists: {os.path.exists(\"./chroma_db\")}')
"
```

✅ **預期看到**：
- 顯示加入了多少區塊（`Added 47 chunks to ChromaDB`）
- 查詢「年假規則」時返回相關區塊（前 4 個都跟年假有關）
- 顯示 `./chroma_db` 資料夾已建立

這一刻就是**第一個里程碑**——你已經有一個可搜尋的知識庫了。

🧯 **卡住的話**：
- `AuthenticationError: Incorrect API key`：.env.local 裡的 OPENAI_API_KEY 錯了，或帳戶額度超過。檢查帳戶頁面。
- `sqlite3.OperationalError: attempt to write a readonly database`：chroma_db 資料夾沒寫入權限。`chmod 755 chroma_db/` 或檢查磁碟空間。
- `ValueError: dimension mismatch`：embedding model 改了卻沒刪 chroma_db/；刪掉資料夾重新索引。

> 🔍 **名詞卡：持久化（persistence）**
> 白話：資料存進磁碟，重開程式還在。ChromaDB 指定了 `persist_directory`，索引就永久存著，不像記憶體開關就沒了。

---

## 5. 階段三：建立檢索鏈 + System Prompt

### 5.1 核心概念：RetrievalQA vs ConversationalRetrievalChain

現在我們有了「能查文件的能力」（前四個階段）。但查了之後怎麼讓 LLM 用好這些資料，又不會亂編？這就是 system prompt 的工作。

**RetrievalQA**：單一問題 → 檢索證據 → LLM 生成答案。適合「一次性」問答。

**ConversationalRetrievalChain**：多輪對話 → 把歷史對話加進檢索前 → 檢索更精準的證據 → LLM 生成答案。適合「聊天」場景。

現階段先做 RetrievalQA，第 6 階段再升級到 ConversationalRetrievalChain。

### 5.2 對 Agent 說

```
建立 src/prompts.py 與 src/retriever.py：

src/prompts.py：定義 system prompt 與 prompt template
  QA_SYSTEM_PROMPT：明確要求「只根據提供的文件回答」、「找不到就說不知道」
  QA_PROMPT_TEMPLATE：把檢索到的文件區塊與問題組合成完整 prompt
  
src/retriever.py：建立 RetrievalQA chain
  create_qa_chain(collection_name="knowledge_base") → RetrievalQA chain
  chain.invoke({"query": "年假規則？"}) → {"answer": "...", "source_documents": [...]}

範例：
  chain = create_qa_chain()
  result = chain.invoke({"query": "年假規則是什麼？"})
  print(result["answer"])
  for doc in result["source_documents"]:
    print(f"Source: {doc.metadata}")
```

**產出程式碼參考**（`src/prompts.py`）：

```python
from langchain_core.prompts import PromptTemplate

QA_SYSTEM_PROMPT = """
你是公司內部知識庫助手。回答必須遵守以下原則：

1. 只根據提供的文件內容回答問題。
2. 如果文件中找不到相關資訊，明確說「根據提供的文件，我找不到 [主題] 的相關內容」。
3. 絕不進行推測或使用訓練資料中的其他知識。
4. 每個回答都必須明確標記資訊的來源，例如「根據員工手冊第 12 頁」或「根據 FAQ 文件」。

你是一個可信的助手，寧可說「我不知道」，也不要胡編亂造。
"""

QA_PROMPT_TEMPLATE = """使用以下文件片段回答問題。

文件：
{context}

問題：{question}

請根據上述文件內容回答。如果文件中沒有相關資訊，請明確說明。"""

qa_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=QA_PROMPT_TEMPLATE,
)
```

（`src/retriever.py`）：

```python
import os
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from src.embeddings import get_chroma_collection
from src.prompts import QA_SYSTEM_PROMPT, qa_prompt

LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4-turbo-preview")

def create_qa_chain(collection_name: str = "knowledge_base"):
    """建立 RetrievalQA chain"""
    vectorstore = get_chroma_collection(collection_name)
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 4}  # 取前 4 最相似的區塊
    )
    
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0,  # 穩定答案，不要創意
        max_tokens=1000,  # 防止被截斷
    )
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # 簡單直接把區塊塞進 prompt
        retriever=retriever,
        chain_type_kwargs={
            "prompt": qa_prompt,
            "document_prompt": None,  # 不需要特殊格式化文件
        },
        return_source_documents=True,  # 回傳參考文件
    )
    
    return qa_chain

def ask(question: str, collection_name: str = "knowledge_base") -> dict:
    """簡化版查詢函式"""
    chain = create_qa_chain(collection_name)
    result = chain.invoke({"query": question})
    return {
        "answer": result["result"],
        "sources": result["source_documents"]
    }
```

### 5.3 驗收與一定要親自試的一幕 ⭐

現在來一個對比實驗。問同一個問題「休閒假怎麼請」——但第一次直接問 LLM（不用 RAG），第二次用你剛做的系統。看看差別有多大。

準備兩個測試：

**測試 A：不接 RAG（直接問 LLM）**

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
response = llm.invoke("根據員工手冊，休閒假怎麼請？")
print(response.content)
```

✅ **預期看到**：LLM 瞎掰一個答案，像「根據常見的人資規範，通常……」（完全沒有根據，因為文件沒寫）

**測試 B：接 RAG（用你的系統）**

```bash
uv run python -c "
from src.retriever import ask

result = ask('休閒假怎麼請？')
print('Answer:')
print(result['answer'])
print('\nSources:')
for doc in result['sources']:
    print(f'  - {doc.metadata}')
"
```

✅ **預期看到**：
- 回答應該是「根據提供的文件，我找不到『休閒假』的相關內容」
- Sources 為空或無關

看到差別了嗎？不用 RAG 的版本說得頭頭是道，但全是編的——文件根本沒寫。RAG 版本誠實多了：「我不知道」。誠實比聰明更值錢。

🧯 **卡住的話**：
- 如果 RAG 版本也瞎掰了，表示 system prompt 沒生效。檢查 `QA_SYSTEM_PROMPT` 有沒有正確傳進 chain；或試試提高 `temperature` 看是不是太高。
- 如果回答被截斷（「年假為每年 30 天……」後面沒了），提高 `max_tokens` 到 2000。

> 🔍 **名詞卡：system prompt**
> 白話：給 LLM 的「基本指示」，告訴它扮演什麼角色、有什麼限制。沒有 system prompt 就像沒有規則的自由表達——LLM 會憑訓練資料亂來。好的 system prompt 是 RAG 系統的看門人。

---

## 6. 階段四：多輪對話與記憶管理

### 6.1 核心問題：為什麼「那病假呢？」會答錯

場景：使用者先問「年假規則是什麼？」，你的系統回答對了。接著使用者只打「那病假呢？」——一句話沒有主詞、沒有「公司」、沒有「員工」，只有「那」和「病假」。一個閉著眼睛的人根本不知道「那」指的是什麼。RAG 系統如果每次都當作獨立問題，就會問錯問題、檢索錯資料。

```
使用者：「年假規則是什麼？」
助手：「根據手冊第 12 頁，年假為每年 30 天……」

使用者：「那病假呢？」
沒有上下文時系統去查：「那病假呢？」  ← 向量化之後和「病假規則」距離不夠近
助手：「對不起，我找不到『那』是什麼的資訊。」❌
```

### 6.2 解決方案：ConversationalRetrievalChain + ConversationBufferMemory

**ConversationBufferMemory**：記著每次對話的問題和答案。

**ConversationalRetrievalChain**：查詢前，用 LLM 把「那病假呢？」改寫成「請告訴我公司的病假規則」（補上前一輪的上下文），再去檢索。

### 6.3 對 Agent 說

```
改寫 src/retriever.py，替換掉 RetrievalQA，改用 ConversationalRetrievalChain：

新增函式：
  create_conversational_qa_chain(collection_name="knowledge_base") → ConversationalRetrievalChain
    用 ConversationBufferMemory 記著對話歷史
    設定 output_key="answer"（重要！防止記憶被來源清單污染）
    
  ask_conversational(question: str, chain, memory) → dict
    接收 chain 與 memory 物件（由 Streamlit session_state 維護）
    回傳 answer 與 sources

為了避免 Streamlit 每次重跑時重新建連，chain 與 memory 要存在 session_state。

記住五個檢查點：
1. 必須用 output_key="answer"，不然 LLM 的回答會混進記憶
2. ConversationBufferMemory 初始化時給 memory_key="chat_history"
3. retriever 作為 get_chat_history 參數（讓它知道怎麼從記憶取資料）
4. 第一次建 chain 後存進 st.session_state
5. 清除對話時只清 memory.clear()，不要重建 chain
```

**產出程式碼參考**（`src/retriever.py` 更新）：

```python
import os
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from src.embeddings import get_chroma_collection
from src.prompts import QA_SYSTEM_PROMPT, qa_prompt

LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4-turbo-preview")

def create_conversational_qa_chain(collection_name: str = "knowledge_base"):
    """建立支援多輪對話的鏈"""
    vectorstore = get_chroma_collection(collection_name)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",  # ← 重要：指定輸出鍵，避免來源被記進歷史
    )
    
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0,
        max_tokens=1000,
    )
    
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        output_key="answer",  # ← 再檢查一次
        system_message=QA_SYSTEM_PROMPT,  # 傳入 system prompt
    )
    
    return chain, memory
```

### 6.4 驗收（新增測試腳本）

對 Agent 說：

```
建立 test_conversation.py，測試多輪對話：
1. 建立 chain 與 memory
2. 問「年假規則是什麼？」
3. 問「那病假呢？」（沒有任何明確上下文）
4. 檢查第二個答案是否涉及病假內容，而不是「找不到」

預期：
- 第二個問題理解為「公司的病假規則」
- 回答應該涉及實際的病假條款
```

**程式碼**：

```python
from src.retriever import create_conversational_qa_chain

chain, memory = create_conversational_qa_chain()

# 第一輪
q1 = "年假規則是什麼？"
a1 = chain.invoke({"question": q1})
print(f"Q1: {q1}")
print(f"A1: {a1['answer'][:200]}...\n")

# 第二輪——沒有任何明確上下文
q2 = "那病假呢？"
a2 = chain.invoke({"question": q2})
print(f"Q2: {q2}")
print(f"A2: {a2['answer'][:200]}...\n")

# 檢查
if "病假" in a2['answer'] or "找不到" in a2['answer']:
    print("✓ 多輪對話正確理解上下文")
else:
    print("✗ 多輪對話可能有問題")
```

✅ **預期看到**：
- 第二個問題的答案涉及病假相關內容
- 或者如果文件沒有病假內容，回答「找不到」而不是瞎掰

> 🔍 **名詞卡：ConversationBufferMemory**
> 白話：RAG 系統的「記憶」，記著每一輪對話，這樣下一輪提問時 LLM 知道「那」指的是誰。不然每次都是從零開始，就像聊天對方每次都失憶。

❓ **想一想**：為什麼 ConversationBufferMemory 一直存著對話？什麼時候會爆掉？

**答案**：隨著對話累積，記憶會越來越長，LLM 的上下文視窗（context window）會被塞滿。解決方案是用「滑動窗口」只記最後 N 輪對話，或定期清空。

---

## 7. 階段五：Streamlit 聊天介面 + 線上查詢

### 7.1 對 Agent 說

```
建立 app.py（Streamlit 聊天介面）：

功能需求：
1. 側欄上傳 PDF 功能（st.file_uploader）
   - 上傳後即時加進 ChromaDB（調用 offline_index 邏輯）
   - 顯示「已加入 N 個區塊」

2. 主要區域：聊天介面
   - 頂部「清除對話」按鈕
   - st.chat_message 顯示歷史訊息
   - st.chat_input 接收新問題
   - 答案附上來源與頁碼

3. Session state 管理
   - chain 與 memory 只建一次（第一次進頁面時）
   - st.session_state 記住它們

技術細節：
- 用 st.session_state.messages 存聊天記錄
- 用 st.session_state.chain 存 ConversationalRetrievalChain
- 清除按鈕只清 memory 與 messages，不重建 chain
- 上傳新檔後不要重啟 app（會清空聊天記錄），只加進索引

Streamlit 的坑：
- app 重跑時 session_state 保留，但全局變數會重置
- 避免在 if st.button 裡做重操作，改用 session_state callback
```

**產出程式碼參考**（`app.py`）：

```python
import os
import streamlit as st
from src.retriever import create_conversational_qa_chain
from src.loader import load_pdf
from src.chunker import chunk_documents
from src.embeddings import add_documents_to_chroma
from dotenv import load_dotenv

load_dotenv(".env.local")

st.set_page_config(page_title="RAG 知識庫 Chatbot", layout="wide")
st.title("📚 公司知識庫助手")
st.markdown("查完再答，每個回答都附出處。")

# ============ Sidebar：文件上傳 ============
st.sidebar.header("📖 知識庫管理")

uploaded_file = st.sidebar.file_uploader(
    "上傳 PDF 文件",
    type=["pdf"],
    key="pdf_uploader"
)

if uploaded_file:
    # 臨時存檔
    temp_path = f"/tmp/{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # 載入、切塊、索引
    with st.sidebar.spinner("正在處理文件…"):
        docs = load_pdf(temp_path)
        chunks = chunk_documents(docs)
        num_added = add_documents_to_chroma(chunks)
    
    st.sidebar.success(f"✓ 已加入 {num_added} 個區塊")
    os.remove(temp_path)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ 清除對話"):
    st.session_state.messages = []
    if "chain" in st.session_state and "memory" in st.session_state:
        st.session_state.memory.clear()
    st.rerun()

# ============ 初始化 Session State ============
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chain" not in st.session_state or "memory" not in st.session_state:
    with st.spinner("⏳ 初始化知識庫…"):
        chain, memory = create_conversational_qa_chain()
        st.session_state.chain = chain
        st.session_state.memory = memory

# ============ 聊天記錄展示 ============
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📄 參考資料"):
                for source in message["sources"]:
                    st.write(f"- **{source.metadata}**")
                    st.caption(source.page_content[:200] + "…")

# ============ 新問題輸入 ============
if prompt := st.chat_input("你想了解什麼？"):
    # 添加使用者訊息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 獲得答案
    with st.chat_message("assistant"):
        with st.spinner("⏳ 查詢中…"):
            response = st.session_state.chain.invoke({"question": prompt})
            answer = response["answer"]
            sources = response["source_documents"]
        
        st.markdown(answer)
        
        if sources:
            with st.expander("📄 參考資料"):
                for doc in sources:
                    st.write(f"- **來源：** {doc.metadata}")
                    st.caption(doc.page_content[:300])
    
    # 記住這輪對話
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })
```

### 7.2 驗收

現在啟動整個系統。這是第一次看到真實的 Streamlit 介面。

```bash
uv run streamlit run app.py
```

✅ **預期看到**：
1. 瀏覽器打開，側欄有「上傳 PDF」和「清除對話」按鈕
2. 問「年假規則是什麼？」→ 回答帶來源
3. 問「那病假呢？」→ 理解上下文
4. 上傳新 PDF → 立刻能問到新內容
5. 點「清除對話」→ 聊天記錄清空，但索引還在

🧯 **卡住的話**：
- `ModuleNotFoundError: No module named 'streamlit'`：uv sync 沒成功。重跑 `uv sync`。
- 聊天記錄一直刷不出來：session_state 初始化有問題；檢查 `if "messages" not in st.session_state` 這行有沒有執行。
- 上傳檔案後卡住：文件太大或網路慢；加 `st.spinner` 顯示進度（已在上面程式碼實現）。

> 🔍 **名詞卡：Streamlit**
> 白話：一個 Python 框架，不用寫 HTML/CSS/JavaScript，直接 Python 函式就能產生互動式網頁。適合資料科學家和工程師快速做 demo。缺點是功能不如 React 靈活。

---

## 8. 情境演練：「答案錯了」診斷

### 情境 A：答案被截斷

**症狀**：
```
Q: 年假規則的詳細說明？
A: 年假為每年 30 天……
```

只有前半部分，沒完沒了。

**診斷**：`max_tokens` 設太小

**修法**：在 `src/retriever.py` 中提高 `max_tokens` 到 2000

### 情境 B：答案合理但與文件不符

**症狀**：
```
Q: 休閒假怎麼請？
A: 通常公司會在……（模型自行腦補）
```

但手冊沒寫休閒假。

**診斷**：
1. system prompt 沒生效或 LLM 忽視了
2. `temperature` 不是 0
3. 沒有在 prompt 裡明確說「找不到就說不知道」

**修法**：
- 檢查 system_message 是否傳進 chain
- 降低 temperature 到 0
- 在 qa_prompt 裡加粗體的「必須說不知道」指令

### 情境 C：檢索到的區塊完全不相關

**症狀**：
```
Q: 年假能轉年假銀行嗎？
Search results: [福利政策、績效考評、……]（全都無關）
```

**診斷**：
1. chunk_size 太大，一個區塊裡 90% 是無關內容
2. 文件本身沒有這個主題

**修法**：
- 降 chunk_size 到 500
- 提高 chunk_overlap 到 30%
- 或加 metadata filter（只查「假期」章節）
- 告訴使用者「文件裡沒有這個資訊」

### 情境 D：中文段落被切得破碎

**症狀**：
```
Chunk 1: "員工年假為每年三十天。第五條規定……"（被截在中間）
Chunk 2: "……辭職要提前通知。" （完全無關）
```

**診斷**：separators 裡沒有包含中文標點

**修法**：在 `src/chunker.py` 的 separators 確認有 `"。"` 和 `"，"`

---

## 9. 動手練習（選做）

### 練習 1：加上文件上傳功能（已在 app.py 實現）

**完成標準**：
- ✓ 上傳後立刻可查
- ✓ 來源標示新文件
- ✓ 重開程式資料還在

### 練習 2：把評估集擴充到 10 題

對 Agent 說：

```
建立 evaluate.py，測試聊天機器人的品質：

1. 定義 10 道測試題，涵蓋三類：
   - 文件中明確寫到的（例如「年假是幾天？」）
   - 需要跨段落彙整的（例如「加班費加上年終獎金最多能拿多少？」）
   - 文件中根本沒有的（例如「休閒假怎麼請？」，期望回答是「找不到」）

2. 每題標註：
   - expected_answer（期望回答要包含的關鍵字）
   - expected_sources（期望參考文件應該提到的關鍵字）

3. evaluate.py 執行：
   - 跑每道測試題
   - 檢查回答是否包含期望關鍵字（不是精確匹配）
   - 檢查源文件是否真的包含期望關鍵字（能區分「答對但來源錯」）
   - 輸出兩欄：「答案正確率」與「來源正確率」

範例輸出：
```
test_1: "年假是幾天？"
  answer: ✓ (包含 "30 天")
  sources: ✓ (包含 "年假")
test_5: "休閒假怎麼請？"
  answer: ✓ (包含 "找不到")
  sources: ✗ (不應該有相關文件)

總結：
  答案正確率：9/10 (90%)
  來源正確率：9/10 (90%)
  危險題目（答對但來源錯）：題 7
```

完成標準：
- ✓ 至少 10 題
- ✓ 涵蓋 3 類問題
- ✓ 能區分答案對與來源對
```

### 練習 3：清除對話按鈕（已在 app.py 實現）

**完成標準**：
- ✓ 畫面訊息清空
- ✓ 追問不再受影響
- ✓ 沒有重新建立索引

---

## 10. 驗收清單

- [ ] `uv sync` 安裝依賴成功
- [ ] `.env.local` 裡 OpenAI API key 有效
- [ ] `uv run python -c "from src.loader import load_pdf; ..."` 能載入 PDF 並分頁
- [ ] `uv run python -c "from src.chunker import chunk_documents; ..."` 能切塊，輸出 100+ 區塊
- [ ] `uv run python -c "from src.embeddings import add_documents_to_chroma; ..."` 能建 ChromaDB 索引，`./chroma_db` 資料夾存在
- [ ] `uv run python -c "from src.retriever import ask; ..."` 單問「年假」能回答附來源
- [ ] 同一問題「不接 RAG」vs「接 RAG」對比，看到幻覺 vs 誠實的差別 ⭐
- [ ] 多輪對話測試：問「年假」→ 問「那病假呢？」→ 理解上下文，回答正確
- [ ] `uv run streamlit run app.py` 聊天介面啟動，能上傳 PDF
- [ ] 在 Streamlit 裡上傳新文件後立刻能問到內容（不用重啟）
- [ ] 問文件沒有的內容，回答「找不到」而非瞎掰
- [ ] 點「清除對話」後，新問題不受前一輪影響

---

## 11. 常見坑排錯速查表

| 問題 | 症狀 | 解法 |
|---|---|---|
| **OpenAI API 無效** | `AuthenticationError: Incorrect API key` | 檢查 `.env.local` 的 OPENAI_API_KEY；確認額度夠 |
| **ChromaDB 權限** | `sqlite3.OperationalError: attempt to write a readonly database` | `chmod 755 chroma_db/` 或檢查磁碟空間 |
| **向量維度不符** | `ValueError: dimension mismatch` | embedding model 改了卻沒刪 `chroma_db/`；刪掉資料夾重新索引 |
| **PDF 載入異常** | `PdfReader: cannot extract text` | PDF 可能被加密或損壞；用 `pdfplumber` 試試 |
| **多輪對話不記得** | 第二個問題「那病假呢？」回答「不知道」 | 檢查 memory 有沒有初始化；chain 有沒有存 session_state |
| **答案被截斷** | LLM 回答只有前一半 | 提高 ChatOpenAI 的 max_tokens 到 1000+ |
| **答案自行腦補** | 問「休閒假」，回答「通常……」而文件沒寫 | 檢查 temperature 是不是 0；system_message 有沒有傳進去 |
| **檢索到無關段落** | 搜「年假」卻返回「績效考評」 | 降 chunk_size；檢查 separators 有沒有中文標點 |
| **Streamlit 重跑後聊天記錄消失** | 改程式碼後整個對話清空 | 改成存 session_state；不是改完自動重跑 |
| **上傳檔案後 Streamlit 卡住** | 點「上傳」後介面沒反應超過 1 分鐘 | 檔案太大或網路慢；加 `st.spinner` 顯示進度 |

---

## 12. 帶走的三句話

如果只能記住三件事，就這三句。這三句話足以指導你做出任何 RAG 系統。

1. **RAG 四階段各自有調整旋鈕，答案不好不是 LLM 爛，是參數沒調對**——`chunk_size` 太大會稀釋精準度、`k` 太少會資訊不足、`temperature` 不是 0 會自行腦補、`max_tokens` 太小會被截斷。學會看症狀對號入座，診斷就成功一半。

2. **多輪對話要補完問題，不是重起對話**——「那病假呢？」只有 4 個字，向量化後和病假規則的相似度未必夠；用 `ConversationBufferMemory` 記著前一輪對話，檢索前讓 LLM 把問題改寫成「公司的病假規則」，才能找對文件。

3. **每個回答都要附來源，是整個系統的信任基礎**——能核對答案真假、能追溯決策依據、能審計 AI 有沒有瞎掰。反過來，找不到就明說「我不知道」；用 system prompt 明確禁止腦補；即使 LLM 訓練資料裡有相關知識，也要忍著不說。RAG 的本質不是「讓 AI 更聰明」，而是「讓 AI 誠實」。
