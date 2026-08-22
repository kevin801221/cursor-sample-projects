# WALKTHROUGH：Cursor Agent 驅動的 GraphRAG 實戰全指南

> **這是一份兼具「系統實作」與「教學心法」的完整手冊。**  
> 無論你是帶班的講師，還是透過 Cursor Agent 實作的開發者，這份文件將帶你從零到一搞懂：**Cursor Agent 是如何讀取 `.cursor/` 內的技能（Skills）、調用 MCP 工具，並協調向量庫與知識圖譜完成龐大的 GraphRAG 任務。**

---

## 🧭 核心架構：Cursor Agent 如何透過 Skill 完成任務？

在進入實作前，必須先理解 Cursor 是如何與我們編寫的 Skill 體系協同運作的：

```
                    ┌──────────────────────────────────────────────┐
                    │               Cursor Agent                   │
                    └──────────────────────┬───────────────────────┘
                                           │ 1. 自動讀取規則
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │  .cursor/rules/yt-graphrag-bot.mdc           │
                    │  (強制指引：讀取技能包、使用 uv、遵守流程)    │
                    └──────────────────────┬───────────────────────┘
                                           │ 2. 深入技能真相來源
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │  .cursor/skills/yt-graphrag-bot/SKILL.md     │
                    │  (包含 Phase 0~6 確定性步驟與驗證標準)        │
                    └──────┬───────────────┬───────────────┬───────┘
                           │ 呼叫腳本       │ 即時查詢驗證   │ 觸發指令
                           ▼               ▼               ▼
                 .cursor/scripts/   .cursor/mcp.json   .cursor/commands/
                 (00~05 Python 工具) (Neo4j & Chroma)  (/ingest, /run-app…)
```

### 1. 規則層 (`.cursor/rules/*.mdc`)
- **`yt-graphrag-bot.mdc`**：設定 `alwaysApply: true`，在每次與 Agent 對話時常駐生效，強制約束 Agent 使用 `uv` 環境、依循分階段構建流程。
- **`neo4j-graph.mdc`**：規範圖譜 Schema（`Video`, `Chunk`, `Entity`, `REL`）與 Cypher 語法。
- **`ingest-pipeline.mdc`**：規範四種來源（YouTube, PDF, DOCX, 網頁）的資料正規化標準。

### 2. 技能真相來源 (`.cursor/skills/yt-graphrag-bot/SKILL.md`)
- 包含全套管線的編排邏輯、LLM Prompt 定義、錯誤降級策略與成功的判斷依據。Agent 動手前會優先閱讀此處。

### 3. 即時驗證層 (`.cursor/mcp.json`)
- Agent 具備連接地端 **Neo4j Cypher MCP** 與 **Chroma MCP** 的能力，能邊建構邊用自然語言確認資料庫狀態。

---

## ⚡ Cursor Slash Commands 完整解剖

本專案將複雜的 GraphRAG 操作封裝為 5 個直觀的 Cursor 斜線指令（位於 `.cursor/commands/`）。老師在課堂上可一步步引導學生輸入：

| 指令 (Slash Command) | 觸發動作與目的 | Agent 背後呼叫的模組 / 工具 | 預期輸出結果 |
| :--- | :--- | :--- | :--- |
| **`/check-setup`** | **起飛前環境檢查**<br>驗證 uv、套件、API Key、Gemini 模型與 Neo4j 連線。 | `.cursor/scripts/check_setup.py` | `ALL CHECKS PASSED — 可以開始 Phase 1` |
| **`/ingest <來源>`** | **多來源端到端入庫**<br>將 YouTube、PDF、DOCX 或網頁轉為向量與知識圖譜。 | `ingest_pipeline.py` (整合 00~03 腳本) | 輸出解析段數、向量 Chunks 數與抽取三元組數量。 |
| **`/run-app`** | **啟動全套服務**<br>同時在背景啟動 FastAPI 後端與 Vite React 前端。 | `chatbot_server.py` (Port 8000)<br>`frontend/` (Port 5180) | 前端 `localhost:5180`、後端 `localhost:8000` 正常運作。 |
| **`/evaluate`** | **A/B 效果盲評**<br>產出評測集並盲評 Naive Vector RAG vs Strong GraphRAG。 | `.cursor/scripts/05_evaluate_rag.py` | 產出 `eval_report.json` 與兩者勝負勝率。 |
| **`/yt-graphrag-bot`** | **總控流程指引**<br>完整檢查環境、自動引導各階段建構。 | 讀取 `.cursor/skills/yt-graphrag-bot/SKILL.md` | 逐步引導使用者完成整個專案建置。 |

---

## 👣 逐步實戰教學流程 (Step-by-Step Teaching Flow)

---

### Step 0：環境準備與起飛前檢查

#### 🎯 目標與原理
在執行任何耗時的 LLM 或入庫動作前，**先將必然會發生的錯誤前移**。腳本會實際向 Google 查詢可用模型（避免模型改名炸掉），並與地端 Neo4j 進行 Bolt 協議握手。

#### 🤖 Agent 參考技能與動作
- 參考：`.cursor/rules/yt-graphrag-bot.mdc`
- 執行：`.cursor/scripts/check_setup.py`

#### 💻 帶班實作步驟

1. **配置環境變數 (`.env`)**：
   ```ini
   GOOGLE_API_KEY=AIzaSy...
   GEMINI_API_KEY=AIzaSy...
   NEO4J_PASSWORD=teach12345
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   ```
2. **啟動地端 Neo4j (Docker)**：
   ```bash
   docker run -d --name neo4j-teach -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/teach12345 neo4j:5
   ```
3. **在 Cursor 輸入斜線指令**：
   > `/check-setup`

#### ✅ 成功判準
```text
=== 1/4 套件檢查 ===
[✓] 套件 yt-dlp ... fastapi ... neo4j
=== 2/4 環境變數檢查 ===
[✓] GOOGLE_API_KEY 或 GEMINI_API_KEY
[✓] NEO4J_PASSWORD
=== 3/4 Gemini 模型檢查 ===
[✓] Gemini API 連線 (gemini-3.5-flash / gemini-embedding-001)
=== 4/4 Neo4j 連線檢查 ===
[✓] Neo4j 連線

ALL CHECKS PASSED — 可以開始 Phase 1
```

#### 💡 課堂教學亮點
- **防呆設計**：Google 模型代號迭代快（1.5 ➔ 2.5 ➔ 3.5），透過 API 動態檢查可用清單，避免同學在 Phase 3 抽取圖譜時才因 404 報錯中斷。

---

### Step 1：多來源知識擷取與正規化 (Ingestion)

#### 🎯 目標與原理
將不規則的各類外部資料（YouTube 字幕、PDF 頁面、Word 文件、網頁文章）統一正規化為 `source.json`。**所有片段都必須帶有可回溯的 `ref` 欄位**（影片時間戳連結、PDF 頁碼錨點等）。

#### 🤖 Agent 參考技能與動作
- 參考：`.cursor/rules/ingest-pipeline.mdc`
- 呼叫：`.cursor/scripts/00_ingest_source.py` 或 `ingest_pipeline.py`

#### 💻 帶班實作步驟

在 Cursor 對話框輸入 `/ingest` 並附上來源，或執行對應指令：

```bash
# 1. YouTube 影片 (自動抓取手動字幕或 ASR 自動字幕)
uv run --env-file .env python .cursor/scripts/00_ingest_source.py "https://www.youtube.com/watch?v=wjZofJX0v4M" --out source.json

# 2. PDF 文件
uv run --env-file .env python .cursor/scripts/00_ingest_source.py paper.pdf --out source.json

# 3. Word DOCX 文件 (段落 + 表格)
uv run --env-file .env python .cursor/scripts/00_ingest_source.py spec.docx --out source.json

# 4. 網頁 URL
uv run --env-file .env python .cursor/scripts/00_ingest_source.py "https://example.com/article" --out source.json
```

#### ✅ 成功判準
印出 `[✓] <來源類型> 來源 N 段已存至 source.json`，且 `source.json` 中每段皆含有 `ref` 與 `start`。

#### 💡 課堂教學亮點
- **引用可回溯性**：做 RAG 最能被使用者信任的不是回答本身，而是「我可以點擊出處並跳到影片第幾分幾秒（或 PDF 第幾頁）親自驗證」。

---

### Step 2：語意聚合切塊與向量入庫 (ChromaDB)

#### 🎯 目標與原理
字幕的單句往往只有 2~3 秒（例如「所以呢」），直接轉成向量沒有語意價值。因此採取**「先時間窗聚合（~60 秒），再進行遞迴字元切塊（800 字元）」**的策略。

#### 🤖 Agent 參考技能與動作
- 參考：`.cursor/skills/yt-graphrag-bot/SKILL.md` (Phase 2)
- 執行：`.cursor/scripts/02_ingest_vectordb.py`

#### 💻 帶班實作步驟

```bash
uv run --env-file .env python .cursor/scripts/02_ingest_vectordb.py source.json --persist ./chroma_db
```

#### 驗證 ChromaDB 資料庫
```bash
uv run --env-file .env python -c "
import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
emb = GoogleGenerativeAIEmbeddings(model=os.environ.get('GEMINI_EMBED_MODEL','gemini-embedding-001'))
db = Chroma(collection_name='yt_rag', embedding_function=emb, persist_directory='./chroma_db')
print('Chunks 總數:', db._collection.count())
print('第一筆 Metadata:', db.get(limit=1)['metadatas'][0])
"
```

#### ✅ 成功判準
印出 `[*] 產生 28 個 chunks`，且 Metadata 內看得到 `chunk_index`、`url_at_time`、`video_id`。

---

### Step 3：LLM 知識圖譜抽取與 Neo4j 入庫

#### 🎯 目標與原理
利用 Gemini 對每個 Chunk 抽取 `(主體)-[關係]->(客體)` 三元組。每個實體節點 (`Entity`) 都透過 `[:MENTIONED_IN]` 關聯回原始切塊 (`Chunk`)，構建出圖譜與原文的立體關聯。

#### 🤖 Agent 參考技能與動作
- 參考：`.cursor/rules/neo4j-graph.mdc`
- 執行：`.cursor/scripts/03_build_graph.py`

#### 💻 帶班實作步驟

```bash
uv run --env-file .env python .cursor/scripts/03_build_graph.py source.json
```

#### 驗證 Neo4j 圖譜狀態
1. 打開 **[http://localhost:7474](http://localhost:7474)**（帳號：`neo4j` / 密碼：`teach12345`）。
2. 輸入 Cypher 查詢：
   ```cypher
   MATCH (a:Entity)-[r:REL]->(b:Entity) RETURN a, r, b LIMIT 100
   ```
3. 在終端機執行快速統計：
   ```bash
   uv run --env-file .env python -c "
   import os
   from neo4j import GraphDatabase
   d = GraphDatabase.driver(os.environ.get('NEO4J_URI','bolt://localhost:7687'), auth=(os.environ.get('NEO4J_USER','neo4j'), os.environ['NEO4J_PASSWORD']))
   with d.session() as s:
       n = s.run('MATCH (e:Entity) RETURN count(e) AS c').single()['c']
       r = s.run('MATCH ()-[x:REL]->() RETURN count(x) AS c').single()['c']
       print(f'Entity 節點數: {n}, REL 關係數: {r}')
   d.close()
   "
   ```

#### 💡 課堂教學亮點
- **MERGE 的去重威力**：同一概念（如 "Transformer"）在影片各處出現時會自動連通，打破文字段落的孤島，形成全域知識網絡。

---

### Step 4：啟動強 RAG (Hybrid GraphRAG) 後端

#### 🎯 目標與原理
整合 **Multi-Query 改寫**、**Chroma 向量檢索**、**RRF 倒數排名融合**、**Neo4j 圖譜一階鄰居擴展**，透過 FastAPI 對外提供高效能問答與圖譜 API。

```
問題 ➔ ① Multi-Query (改寫為 3 個視角) ➔ 向量檢索 (各取 top-4)
    ➔ ② RRF 融合去重
    ➔ ③ Neo4j 圖譜擴展 (反查命中 Chunk 的實體鄰居)
    ➔ ④ 組成 Context (原文證據 + 圖譜三元組) ➔ LLM 精準生成
```

#### 🤖 Agent 參考技能與動作
- 參考：`chatbot_server.py`
- 執行：`uv run --env-file .env uvicorn chatbot_server:app --port 8000`

#### 💻 帶班實作步驟

```bash
uv run --env-file .env uvicorn chatbot_server:app --port 8000
```

#### 驗證 API 端點
```bash
# 測試問答 API
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"question":"Transformer 的注意力機制是怎麼運作的？"}' \
  | uv run python -c "import json,sys; d=json.load(sys.stdin); print('回答:', d['answer']); print('關聯實體數:', len(d['graph_nodes']))"
```

---

### Step 5：方法驗證迴圈 (A/B 評測)

#### 🎯 目標與原理
**「加了圖譜真的比純向量 RAG 好嗎？」**  
透過 LLM-as-a-judge 進行盲評，隨機交換 A/B 位置防止位置偏誤，並從 **Faithfulness（忠實度）**、**Completeness（完整性）**、**Citation（引用準確度）** 三維度評分。

#### 🤖 Agent 參考技能與動作
- 參考：`.cursor/references/method-validation.md`
- 執行：`.cursor/scripts/05_evaluate_rag.py`

#### 💻 帶班實作步驟

在 Cursor 輸入指令 `/evaluate` 或手動執行：
```bash
# 1. 產出 10 題測試集
uv run --env-file .env python .cursor/scripts/05_evaluate_rag.py --generate source.json --n 10

# 2. 進行 A/B 盲評實測
uv run --env-file .env python .cursor/scripts/05_evaluate_rag.py --run eval_set.json --api http://localhost:8000
```

#### ✅ 成功判準
輸出兩者勝負報告（如 `wins.strong_rag: 7, wins.baseline: 2, tie: 1`），並落檔 `eval_report.json`。

---

### Step 6：前端視覺化介面與來源匯入 Modal

#### 🎯 目標與原理
提供三位一體的視覺化體驗：
1. **左側對話欄**：顯示結構化回答與可跳轉出處標籤。
2. **右側力導向圖譜**：回答時即時將相關節點轉為**琥珀色**，點擊任一實體展開鄰居。
3. **底部時間軸緞帶**：視覺化呈現檢索到的證據在整部影片/文件中的時間分布。
4. **`+ 匯入新來源` 模態視窗**：支援在前端直接丟入 YouTube 連結、PDF、DOCX 或網頁 URL，顯示階段進度並在完成後自動熱更新圖譜。
   - 上傳的檔案會保存在後端 `uploads/`，讓答案裡的 `file://...#page=N` 引用在入庫後仍可回溯；同一份檔案重複上傳會以內容雜湊冪等覆蓋，不會重複入庫。
   - 進度條為前端模擬（後端 `/ingest` 是同步處理），長影片入庫時卡在第 2 階段數分鐘屬正常。
   - 安全設計：`/ingest` 只接受 http(s) 網址，本機檔案一律走 `/ingest/file` 上傳，避免任意本機檔案讀取。

#### 💻 帶班實作步驟

在 Cursor 輸入指令 `/run-app` 或在終端機啟動：
```bash
cd frontend
npm install
npm run dev -- --port 5180
```

打開瀏覽器：**[http://localhost:5180](http://localhost:5180)**

---

## 🛠️ 疑難排解速查手冊 (Troubleshooting)

| 異常現象 | 可能原因 | 快速修復方式 |
| :--- | :--- | :--- |
| `Neo4j Connection Refused` | Docker 容器尚未啟動或 Port 撞車 | 執行 `docker ps`，確認 `neo4j-teach` 正在運行且 7687 埠未被佔用。 |
| `API Key Invalid / 404` | 金鑰未填或過期 | 檢查 `.env` 中的 `GOOGLE_API_KEY`，至 AI Studio 重新生成。 |
| 前端提示 `連不上後端 8000` | 後端伺服器未啟動 | 檢查 uvicorn 是否在運行：`uv run --env-file .env uvicorn chatbot_server:app --port 8000`。 |
| 圖譜節點太密或疊在一起 | 力的參數需要收斂 | 點擊右下角畫布拖曳一下，系統會自動觸發 `d3ReheatSimulation()` 重新排版。 |
| 上傳 `.doc` 被拒收 | 舊版 Word 二進位格式無法解析 | 用 Word 另存為 `.docx` 再上傳。 |
| `/ingest` 回「只接受 http(s) 網址」 | 貼了本機檔案路徑 | 本機 PDF/DOCX 請改用前端上傳（走 `/ingest/file`）。 |
| `/ingest` 回「拒絕存取內網/保留位址」 | SSRF 防護擋下 localhost/內網網址 | 教學或測試要灌本機網頁時，啟動後端前設 `ALLOW_PRIVATE_URLS=1`。 |
| 網頁匯入後內容是亂碼 | 舊版程式用 `resp.text` 解碼（已修正） | 更新到最新版程式碼後重新匯入該網址即可（冪等覆蓋）。 |
| 問 A 來源的問題卻高亮 B 來源的節點 | 檢索補位雜訊（已修正） | 已加入相對距離門檻 `DIST_RATIO`（`chatbot_server.py`），換嵌入模型時需重新校準該值。 |
