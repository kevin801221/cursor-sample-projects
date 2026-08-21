---
name: yt-graphrag-bot
description: 從 YouTube 連結、PDF、DOCX 或任意網頁 URL 建出完整 GraphRAG 問答機器人的教學工作流：統一入口擷取（yt-dlp 字幕含無 CC/pymupdf 或 LlamaParse 解析 PDF/python-docx 解析 DOCX/trafilatura 或 Tavily 抓網頁）→ LangChain 切塊入 VectorDB → 強 RAG（Multi-Query + RRF + 圖譜擴展）→ LLM 抽取知識圖譜入 Neo4j → 方法驗證迴圈（文獻對齊 + A/B 實測 + decision record，證明現行方法為當前最佳）→ FastAPI 聊天後端 → React 力導向圖前端（點節點瞬間載入鄰居）。只要使用者提到「YouTube 影片做 RAG / 問答機器人」「PDF/DOCX/網頁做知識庫問答」「影片或文件轉知識圖譜」「GraphRAG 教學」「帶學生做 RAG 專案」「影片字幕向量化」，或想看 skill 如何協調 MCP（Chroma/Neo4j/CopilotKit/Langchain-docs）與腳本完成複雜流程，都要使用本 skill——即使他們沒有明講「GraphRAG」這個詞。
---

# YouTube → GraphRAG 問答機器人（教學工作流）

本 skill 的雙重目的：
1. **產出**：從一個 YouTube 連結，一路建到「能回答影片內容、且回答時
   瞬間高亮相關知識圖譜節點」的完整機器人。
2. **教學**：向同學展示 **skill = 腳本（確定性步驟）+ MCP（即時查詢驗證）
   + 分階段指引** 的組合模式。每個 Phase 結束都有「MCP 驗證點」，
   這是本課程的核心教學設計——邊建邊驗，而不是最後才 debug。

## 執行代理必讀：硬規則（能力較弱的模型也照這個執行）

本 skill 會被各種能力等級的 agent 執行（包含免費版編輯器內建模型）。
所以規則寫死如下，**逐條遵守，不要自行發揮**：

1. **照 Phase 順序執行，不跳步**：0 → 1 → 2 → 3 → 4+5 → 4.5 → 6。
   第一個動作永遠是 `uv run python scripts/check_setup.py`，沒有全綠不准往下。
2. **指令原樣複製執行**。文中「尖括號」如 `<你的影片網址>` 是唯一需要
   替換的地方，其餘一字不改。
   **所有 Python 一律走 `uv run`**，不要用系統 `python`、不要用 `pip`、
   不要自己建 venv 或 `source activate`——`uv run` 會自己處理環境，
   而且每次 shell 呼叫都獨立有效（agent 的 shell 狀態不保證跨指令保留）。
   工作目錄固定在 skill 根目錄（有 `pyproject.toml` 的那層）。
3. **每個 Phase 結尾都有「✅ 成功判準」**：實際輸出符合才算完成。
   不符合 → 先查該 Phase 的「❌ 失敗時」，再查文末「疑難排解速查」，
   都沒中 → 把完整錯誤訊息貼給使用者，**不要自己亂改腳本**。
4. **不要重寫或「優化」scripts/ 內的腳本**。它們已逐一驗證過。
   需要客製時只在指令列參數層調整（--engine、--n、--persist 等）。
5. **MCP 是選配**：每個「MCP 驗證點」都附「無 MCP 替代指令」。
   環境沒有該 MCP 就用替代指令，效果等價，不要因缺 MCP 而卡住。
6. **付費/免費路線必須先問使用者**（Phase 1 有一字不差的提問模板），
   在使用者回答前不得執行需要付費金鑰的指令。
7. **回報格式**：每完成一個 Phase，回報「Phase N 完成：<成功判準的
   實際輸出一行>」。失敗則回報「Phase N 卡住：<錯誤訊息> + 已嘗試的
   修復」。

## 整體資料流

```
YouTube URL ─┐
PDF / DOCX ──┼─ [Phase 1] 00_ingest_source.py 統一入口
網頁 URL ────┘   （每種來源都有 免費地端 / 付費雲端 兩條路線，執行前先問使用者）
                → 正規化 source.json（帶可回溯 ref：時間戳/頁碼/網址）
       └─ [Phase 2] 聚合 + LangChain 切塊 → Chroma VectorDB
       └─ [Phase 3] LLM 三元組抽取 → Neo4j 知識圖譜(Entity─REL─Entity─MENTIONED_IN─Chunk)
            └─ [Phase 4] 強 RAG: Multi-Query → 向量檢索 → RRF 融合 → 圖譜擴展 → 生成
                 └─ [Phase 5] FastAPI /chat + /graph API
                      └─ [Phase 4.5] 方法驗證迴圈: 文獻對齊(MCP+搜尋) ⇄ A/B 實測
                      │              → 證明「現行方法為當前最佳」的 decision record
                      └─ [Phase 6] React 力導向圖前端 + CopilotKit 對話
```

關鍵設計（帶課時反覆強調）：**VectorDB 和 GraphDB 不是二選一**。
圖譜負責「找到相關概念與其連結」，chunk 負責「提供原文證據與影片時間戳」。
兩者用 `chunk_index`（Phase 2 metadata）↔ `chunk_id`（Phase 3 節點）精確對齊。

## 執行模式判斷

先判斷使用者要什麼：
- **「幫我建」**：依 Phase 順序執行腳本，每 Phase 完成後報告驗證結果。
- **「教同學建」**（預設）：每個 Phase 先講「為什麼」（下方每 Phase 的
  教學重點），展示腳本關鍵段落，執行，然後用 MCP 帶同學驗證。
- 缺前置條件（API key、Neo4j、Node.js）時，在對應 Phase 開頭一次講清楚，
  不要跑到一半才失敗。
- 無論哪種模式、無論執行代理強弱，「硬規則」七條與各 Phase 的
  ✅ 成功判準都不可省略——它們是為最弱執行者設計的安全網。

## Phase 0：環境準備 + API Key 總表

套件一律用 **uv** 管理（版本在 `pyproject.toml`，不要用 pip 手動裝）：

```bash
uv sync                  # 建環境 + 裝所有相依，一行搞定
# 付費 PDF 路線才需要（選裝）: uv sync --extra paid
```

之後所有指令都以 `uv run` 開頭，不需要 activate 任何東西。

本 skill 已在以下版本組合實測相容：Python 3.12 / yt-dlp 2026.7.4 /
langchain-text-splitters 1.1.2 / langchain-google-genai 4.3.3 /
langchain-chroma 1.1.0 / chromadb 1.5.9 / neo4j 6.2.0 / fastapi 0.141.1 /
pymupdf 1.28.2 / python-docx 1.2.0 / trafilatura 2.2.0。
版本差距大時先用 Langchain-docs MCP 查當前 API 再跑。

### API Key 總表（開課前發給同學的 checklist）

| 環境變數 | 必要性 | 用在哪 | 去哪拿 / 費用感 |
|---|---|---|---|
| `GOOGLE_API_KEY` | **必要** | Phase 2 嵌入、Phase 3 抽取、Phase 4 生成、Phase 4.5 出題與評審 | **aistudio.google.com 免費申請**，有免費額度。跑完一支 20 分鐘影片全流程（含評估）在免費額度內通常就夠 |
| `NEO4J_PASSWORD` | **必要** | Phase 3 寫圖、Phase 4/5 查圖 | 自己設定，跟下方 docker 指令的 `NEO4J_AUTH` 一致即可，免費 |
| `NEO4J_URI` / `NEO4J_USER` | 選填 | 同上 | 預設 `bolt://localhost:7687` / `neo4j`，本機 docker 不用改 |
| `GEMINI_MODEL` | 選填 | 全部 LLM 步驟 | 預設 `gemini-3.5-flash`。Google 改模型名時改這個就好，**一個 export 同時改掉所有腳本** |
| `GEMINI_EMBED_MODEL` | 選填 | Phase 2 嵌入 | 預設 `gemini-embedding-001` |
| `GEMINI_JUDGE_MODEL` | 選填 | Phase 4.5 評審 | 預設同 `GEMINI_MODEL`。想讓 judge 比受測 pipeline 強時才改（見 Phase 4.5 誠實條款） |
| `LLAMA_CLOUD_API_KEY` | 選填 | Phase 1 PDF 走 `--engine llamaparse`（掃描件/複雜表格） | cloud.llamaindex.ai 免費註冊，有免費額度 |
| `TAVILY_API_KEY` | 選填 | Phase 1 網頁走 `--engine tavily`（JS 渲染/反爬頁面） | tavily.com 免費註冊，每月有免費額度 |

不需要任何 key 的部分（上課先講，降低同學心理門檻）：yt-dlp 抓字幕、
pymupdf 解析 PDF、python-docx 解析 DOCX、trafilatura 抓網頁、Chroma 本身
——全流程只靠一把免費的 `GOOGLE_API_KEY` 就能跑通。

金鑰有兩種放法，**開工前先確認使用者是哪一種**，選錯的話後面每條指令都會
說「缺金鑰」：

**(a) 直接 export**（本文所有指令原樣可用，推薦）：
```bash
export GOOGLE_API_KEY="AIza..."      # 用 GEMINI_API_KEY 這個名字也可以，SDK 兩個都吃
export NEO4J_PASSWORD="your-password"
# 選用: export LLAMA_CLOUD_API_KEY="llx-..." ; export TAVILY_API_KEY="tvly-..."
```
注意：`export` 只在**同一個 shell** 有效。agent 每次執行指令都是新的 process，
所以要嘛寫進 `~/.zshenv`（非互動 shell 只讀這支，**不讀 `~/.zshrc`**），
要嘛改用下面的 (b)。

**(b) 放在 `.env` 檔**（很多人的習慣）：
```bash
GOOGLE_API_KEY=AIza...
NEO4J_PASSWORD=your-password
```
這時**本文每一條 `uv run` 都要加 `--env-file`**，例如：
```bash
uv run --env-file .env python scripts/check_setup.py
```
`.env` 不在 skill 目錄裡就給相對或絕對路徑（如 `--env-file ../.env`）。
`uv` 沒辦法在 `pyproject.toml` 裡預設這個，只能每次帶——決定用 (b) 就整條
流程都要記得帶，中途漏一次就會出現「明明設了卻說沒設」。

**模型名會過期，這件事已經處理掉了**：`check_setup.py` 會拿你的金鑰真的去問
Google 一次「有哪些模型可用」，並確認上面兩個預設模型在不在清單裡。
不在就直接印出可用清單叫你 export——這是刻意把「Google 改名」這個必然
發生的失敗，從 Phase 2 的神秘 404 前移到 Phase 0 的一行提示。

Neo4j 一行啟動（原樣複製，只改密碼）：
```bash
docker run -d --name neo4j-teach -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/<你自訂的密碼> neo4j:5
```
各 MCP 設定（選配）：讀 `references/mcp-setup.md`。

**✅ 成功判準**：`uv run python scripts/check_setup.py` 輸出最後一行為
`ALL CHECKS PASSED — 可以開始 Phase 1`。
**❌ 失敗時**：腳本每個 ✗ 項目下方都有「修復 →」指令，照貼執行後
重跑檢查，直到全綠。Neo4j 啟動後要等約 20 秒才連得上。

## Phase 1：來源擷取——統一入口（scripts/00_ingest_source.py）

一支腳本吃四種來源，全部正規化成同一個 `source.json`，下游不用改：

```bash
uv run python scripts/00_ingest_source.py "https://www.youtube.com/watch?v=..." --out source.json
uv run python scripts/00_ingest_source.py report.pdf --out source.json
uv run python scripts/00_ingest_source.py spec.docx --out source.json
uv run python scripts/00_ingest_source.py "https://blog.example.com/post" --out source.json
```

### 教學點：付費 vs 免費工具的決策（agent 執行前必問）

PDF 與 URL 各有兩條路線。**執行前 agent 要先問使用者選哪條**——這個
「問」本身就是教學設計，讓同學體會工具選擇是成本效益判斷。
向使用者提問時使用以下模板（一字不差，依來源類型擇一）：

> 【PDF】這份 PDF 要用哪條解析路線？
> (a) 免費地端 pymupdf——純文字 PDF 效果好，不用金鑰（預設）
> (b) 付費雲端 LlamaParse——掃描件/複雜表格效果好，需 LLAMA_CLOUD_API_KEY
>     （cloud.llamaindex.ai 免費註冊有額度）

> 【網頁】這個網址要用哪條抓取路線？
> (a) 免費地端 trafilatura——一般文章頁可用，不用金鑰（預設）
> (b) 付費 Tavily Extract——JS 渲染/反爬頁面成功率高，需 TAVILY_API_KEY
>     （tavily.com 免費註冊每月有額度）

使用者選 (b) 才在指令加 `--engine llamaparse` 或 `--engine tavily`；
選 (a) 或沒回答就用預設（不加 --engine）。差異對照：

| 來源 | 免費地端（預設） | 付費雲端（`--engine`） | 什麼時候值得花錢 |
|---|---|---|---|
| PDF | pymupdf | LlamaParse（`llamaparse`，需 LLAMA_CLOUD_API_KEY） | 掃描件（需 OCR）、複雜表格、多欄排版 |
| URL | trafilatura | Tavily Extract（`tavily`，需 TAVILY_API_KEY） | JS 渲染頁、有反爬的網站 |
| DOCX | python-docx | ——無 | 這格刻意留白：不是每個環節都值得花錢，邊際效益為零就不買 |
| YouTube | yt-dlp | ——無 | 同上 |

免費路線失敗時腳本會明確提示改用付費引擎（如掃描版 PDF 抽不到字），
這是 graceful degradation 的另一個示範：先試便宜的、失敗訊息要能指路。

### 各來源實作重點（帶同學看程式碼時講）

- **YouTube**：三層 fallback：人工 CC → 自動字幕(ASR) → whisper 地端轉錄。
  「無 CC 也可以」的關鍵是 yt-dlp 的 `automatic_captions`；ASR 字幕 VTT 的
  「滾動式重複」由 `parse_vtt()` 處理（01_fetch_transcript.py，真實世界
  資料清理的好例子）。完全沒字幕時腳本會印出 whisper 指令：
  ```bash
  uv run yt-dlp -x --audio-format m4a -o audio.m4a "URL"
  uv run --with faster-whisper python -c "
  from faster_whisper import WhisperModel
  segs, _ = WhisperModel('small').transcribe('audio.m4a')
  print([(s.start, s.text) for s in segs][:3])
  "
  ```
- **PDF**：逐頁抽取，`ref` 帶 `file://...#page=N`——瀏覽器點了直接跳頁，
  和影片時間戳是同一個設計哲學：**引用必須可回溯**。
- **DOCX**：段落 + 表格都抽（表格常藏關鍵資料，用 python-docx 的
  `document.tables` 逐格取）。
- **URL**：trafilatura 抽正文、自動去 nav/footer 雜訊。
- 所有文件來源共用 `_pack_paragraphs()`：碎段聚合到 ≥200 字再輸出，
  和 YouTube 的 60 秒時間窗是同一個原則——**嵌入單位要是完整語意段**。

已知限制：YouTube 字幕有 rate limit，課堂多人抓同一支影片可能 429——
課前預抓 `source.json` 發放最穩。

**選材建議（會直接影響 Phase 4.5 的結論，開課前就要決定）**：挑
**20 分鐘以上、資訊密度高**的影片，或一次灌好幾份文件。
語料太小（總 chunk < ~30）時，naive baseline 的 `k=5` 就撈走大半語料，
強 RAG 再厲害也沒有發揮空間，Phase 4.5 一定測不出差異。
實測：一支 6 分鐘影片只產出 8 個 chunk，A/B 8 題有 6 題評分完全相同。

**✅ 成功判準**：終端印出 `[✓] <來源類型> 來源 N 段已存至 source.json`
（N ≥ 1，來源類型為 youtube/pdf/docx/url 其一），且下列指令能印出來源類型與段數：
```bash
uv run python -c "import json; d=json.load(open('source.json')); print(d['source_type'], len(d['segments']))"
```
**❌ 失敗時**：腳本的錯誤訊息已含下一步指引（如「改用 --engine llamaparse」
「改用 --engine tavily」「用 whisper 指令」），照做即可；YouTube 429 →
等 5 分鐘重試或換影片。

## Phase 2：向量化入庫（scripts/02_ingest_vectordb.py）

```bash
uv run python scripts/02_ingest_vectordb.py source.json --persist ./chroma_db
```

教學重點：
- **先聚合再切塊**：嵌入單位要是完整語意段。YouTube 的 2~3 秒碎片先聚成
  ~60 秒自然段（`aggregate_segments`）；PDF/DOCX/URL 已在 Phase 1 聚合過
  （腳本用 `source_type` 自動分流，帶同學看這個判斷）。之後統一用
  `RecursiveCharacterTextSplitter` 以中文標點優先序切塊。
- metadata 設計就是產品設計：`url_at_time` 讓引用可點、`chunk_index`
  讓 Phase 3 圖譜能對回原文。
- 腳本是**冪等**的：重跑會先刪同 video_id 舊資料。問同學為什麼這重要。

**MCP 驗證點**：用 Chroma MCP 查「collection yt_rag 的前 5 筆與 metadata」。
**無 MCP 替代指令**（原樣複製，效果等價）：
```bash
uv run python -c "
import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
emb = GoogleGenerativeAIEmbeddings(model=os.environ.get('GEMINI_EMBED_MODEL','gemini-embedding-001'))
db = Chroma(collection_name='yt_rag', embedding_function=emb, persist_directory='./chroma_db')
r = db.get(limit=3)
print('chunks 總數:', db._collection.count())
print('第一筆 metadata:', r['metadatas'][0] if r['metadatas'] else '空的!')
"
```

**✅ 成功判準**：ingest 印出 `[✓] 已寫入 collection='yt_rag'`，且上面
驗證指令印出的 metadata 含 `chunk_index`、`url_at_time`、`source_type`。
**❌ 失敗時**：metadata 是「空的!」→ persist 路徑不一致，確認 Phase 2
指令的 `--persist ./chroma_db` 和驗證指令的 `persist_directory` 相同；
MCP 查無資料 → 九成是 MCP 與腳本指向不同路徑（見 mcp-setup.md）。

## Phase 3：知識圖譜建構（scripts/03_build_graph.py）

```bash
uv run python scripts/03_build_graph.py source.json
```
（模型預設吃 `GEMINI_MODEL`；要單次覆蓋才加 `--model <模型名>`。）

教學重點：
- LLM 三元組抽取，prompt 內強制 JSON、限制「只抽明確陳述、不腦補」——
  這是 hallucination 控制在資料層的示範。
- 圖 schema：`(Entity)-[REL{type}]->(Entity)`、`(Entity)-[MENTIONED_IN]->(Chunk)`、
  `(Chunk)-[PART_OF]->(Video)`。REL 型別存屬性而非動態 label，免裝 APOC。
- `MERGE` 而非 `CREATE`：同一實體跨 chunk 自動合併——圖譜的價值正是把
  散落影片各處的同一概念連起來。
- 同義詞沒合併（如「LangGraph」vs「Lang Graph」）→ 回頭在抽取 prompt 加
  正規化規則。這個迭代過程本身就是很好的教學素材。

**MCP 驗證點**：用 Neo4j MCP 問「MENTIONED_IN 最多的前 10 個 Entity」；
同時開 http://localhost:7474 讓同學親眼看到圖長出來（課堂效果極好）。
**無 MCP 替代指令**（原樣複製）：
```bash
uv run python -c "
import os
from neo4j import GraphDatabase
d = GraphDatabase.driver(os.environ.get('NEO4J_URI','bolt://localhost:7687'), auth=(os.environ.get('NEO4J_USER','neo4j'), os.environ['NEO4J_PASSWORD']))
with d.session() as s:
    n = s.run('MATCH (e:Entity) RETURN count(e) AS c').single()['c']
    r = s.run('MATCH (a:Entity)-[x:REL]->(b:Entity) RETURN count(x) AS c').single()['c']
    print(f'Entity 節點: {n}, REL 關係: {r}')
d.close()
"
```

**✅ 成功判準**：執行時每個 chunk 印出 `+N triples`，結尾印
`[✓] 圖譜完成: N 條關係`；替代驗證指令印出的 Entity 與 REL 數均 > 0。
**❌ 失敗時**：Entity = 0 → 抽取全失敗，檢查 GOOGLE_API_KEY 是否有效、
免費額度是否用盡（Gemini 免費層有每分鐘請求上限，chunk 多時可能被限流，
稍等再重跑即可，腳本是冪等的）；連線錯誤 → 回 Phase 0 跑 check_setup.py。

## Phase 4+5：強 RAG + 聊天後端（scripts/04_chatbot_server.py）

```bash
cp scripts/04_chatbot_server.py chatbot_server.py   # 模組名不能數字開頭
uv run uvicorn chatbot_server:app --reload --port 8000
```
這支要保持在背景執行，Phase 4.5 與 Phase 6 都要打它。

強 RAG pipeline，每一步都要講「為什麼存在」：
1. **Multi-Query**：一個問題改寫成術語/白話/背景三個檢索視角——
   解決「使用者用詞和影片用詞不同」的 vocabulary mismatch。
2. **RRF 融合**（`score = Σ 1/(k+rank)`）：多路檢索結果免調權重的融合法。
3. **圖譜擴展**：從命中 chunks 反查 Entity 一階鄰居，把「影片別處提過的
   相關概念」帶進 context——這就是 GraphRAG 相對純向量 RAG 的增量。
4. **防脆弱設計**：Multi-Query 改寫失敗時退回原問題。加強元件永遠要有
   graceful degradation，不能讓 pipeline 因加強而更容易掛。

API：`POST /chat`（回 answer + 時間戳 sources + graph_nodes）、
`GET /graph`（全圖）、`GET /graph/{name}`（點節點瞬間載入鄰居子圖）。

**✅ 成功判準**（依序執行兩條，原樣複製）：
```bash
curl -s localhost:8000/graph | uv run python -c "import json,sys; d=json.load(sys.stdin); print('圖節點:', len(d['nodes']), '邊:', len(d['links']))"
curl -s -X POST localhost:8000/chat -H "Content-Type: application/json" -d '{"question":"這個內容主要在講什麼"}' | uv run python -c "import json,sys; d=json.load(sys.stdin); print('answer 前80字:', d['answer'][:80]); print('sources 數:', len(d['sources']), '| graph_nodes 數:', len(d['graph_nodes']))"
```
第一條印出節點/邊數 > 0；第二條印出非空 answer、sources ≥ 1。
**❌ 失敗時**：`Connection refused` → server 沒起來，回頭看 uvicorn 終端
的錯誤；answer 說「不知道」→ 正常（代表誠實），換一個與內容相關的問題再測；
graph_nodes = 0 但 answer 正常 → 圖譜擴展沒撈到東西，回 Phase 3 驗證
Entity 數 > 0。

## Phase 4.5：方法驗證——證明現行方法「當前最佳」（scripts/05_evaluate_rag.py）

server 跑起來之後、寫前端之前，執行這個 Phase。這是整門課方法論含金量
最高的一段：**agent 用「文獻對齊 + 實測數據」的迭代迴圈，產出可辯護的
「現行 RAG/Graph 方法在當前狀態下最好」的證據**。

先對同學講清楚「最好」的誠實定義（三條件缺一不可）：
與官方最佳實務對齊、在自己的評估集上數據不輸任何已測候選、
每個被否決的候選都留有紀錄。細節與 decision record 範本讀
`references/method-validation.md`。

執行順序：

1. **建評估集**（先於一切，且定版後不得中途改題）：
   ```bash
   uv run python scripts/05_evaluate_rag.py --generate source.json --n 10
   ```
   LLM 自動出題後**必須人工複核**——評估集品質決定整個結論的可信度。

2. **基準 A/B**：naive 向量 RAG vs 現行強 RAG，LLM-as-judge 盲評
   （腳本已做隨機換位防位置偏誤）：
   ```bash
   uv run python scripts/05_evaluate_rag.py --run eval_set.json --api http://localhost:8000
   ```
   ⚠️ 本課程預設 judge 與受測 pipeline **同一支模型**（都是 Flash），
   成本最低但自我評分偏誤較大。要提高結論強度就
   `export GEMINI_JUDGE_MODEL=<更強的模型>` 再重跑。這個取捨要對同學講明，
   並寫進 decision record——見 `references/method-validation.md` 誠實條款。
   這一步先確立「強 RAG 的每個元件不是白加的」——若強 RAG 沒贏 naive，
   後面都不用談，先回 Phase 4 找原因。

3. **SOTA 對齊迴圈**【進階選做——需要較強的 agent 判斷力。若目前執行
   代理能力有限或環境無 MCP，做完步驟 1、2、4 即可，這已構成
   「強 RAG 優於 naive baseline」的完整數據證明】：
   用 Langchain-docs MCP 查官方當前推薦的 retrieval 技術、用 web search
   查近期 RAG/GraphRAG 文獻 → 列出「文獻推薦但 pipeline 沒有」的候選
   （reranker、HyDE、hybrid BM25、社群偵測式 GraphRAG…）→ 一次實作
   一個候選 → 用同一評估集重跑步驟 2 → 勝則併入主線重新受挑戰、
   敗則寫入 decision record 否決欄 → 直到無候選勝出。
   迴圈紀律（單一變因、評估集定版、迭代上限）見 method-validation.md。

4. **產出結論**：eval_report.json + decision records + 誠實條款
   （「最佳」的適用邊界：此評估集、此影片、已測候選集合內）。

教學重點：這個 Phase 示範的是 **agent 的自我證成能力**——不是讓 LLM
說「我的方法很好」，而是讓它建立評估基礎設施、調研、實測、留紀錄。
「有邊界的強結論」比「無邊界的空話」有價值，這句話值得寫在白板上。

**MCP 驗證點**：本 Phase 的 MCP 用法與前面不同——前面是「驗證資料存對了」，
這裡是「取得判斷依據」。讓同學觀察 agent 怎麼把 MCP 查到的官方文件
轉譯成候選清單，這是 skill+MCP 協作最高階的形態。

**✅ 成功判準**：`--generate` 產出 `eval_set.json`（打開檢查題目合理）；
`--run` 結尾印出「===== 勝負 =====」JSON 並產出 `eval_report.json`，
其中 `wins.strong_rag > wins.baseline`。
**❌ 失敗時**：strong_rag 沒贏 → 不是錯誤，是重要發現。**依序查這三個原因**：

1. **語料太小（最常見，先查這個）**：跑
   `uv run python -c "import os;from langchain_chroma import Chroma;from langchain_google_genai import GoogleGenerativeAIEmbeddings;print(Chroma(collection_name='yt_rag',embedding_function=GoogleGenerativeAIEmbeddings(model=os.environ.get('GEMINI_EMBED_MODEL','gemini-embedding-001')),persist_directory='./chroma_db')._collection.count())"`
   看總 chunk 數。**低於 ~30 就別期待強 RAG 會贏**——naive 的 `k=5` 已經撈走
   語料的一大半，兩邊 context 幾乎重疊，檢索策略根本沒有發揮空間，
   分數還會一起觸頂（都 4.5 分以上就是這個徵兆）。
   實測：一支 6 分鐘影片只產出 8 個 chunk，naive 每題拿到 62% 全文，
   結果 8 題有 6 題兩邊評分**完全相同**。
   → 換一支 20 分鐘以上的影片，或多灌幾份文件，再重跑。
2. **圖譜空或全是孤島**：跑 Phase 3 的替代驗證指令看 Entity 數。
   圖譜撈不到東西時，強 RAG 只剩 Multi-Query 的增量。
3. **Multi-Query 改寫偏題**：改寫出來的 query 跟原問題無關。

三個都不是 → 如實回報「在此語料上強 RAG 無顯著增量」。
**這正是評估的價值：它會告訴你「加的東西沒用」，而這個結論跟「有用」一樣有價值。**

## Phase 6：前端圖譜視覺化

讀 `references/frontend-graph.md` 照做。兩段式教學：
1. **保底版**：純 React + react-force-graph-2d，完整程式碼在 reference 內
   （含該套件「links 被改寫成物件」的經典坑的處理）。先讓所有同學都能動。
2. **升級版**：CopilotKit（AG-UI）替換聊天欄，用 `useCopilotAction` 讓
   agent 主動高亮圖譜節點。**寫之前先用 CopilotKit MCP 查當前 API**——
   前端框架迭代快，照舊教學抄必踩版本坑。

課程高潮示範：問一個問題 → 答案出現、附影片時間戳連結、右側圖譜相關節點
同步變橘色 → 點任一節點 → 鄰居子圖瞬間展開。

**✅ 成功判準**：瀏覽器開 http://localhost:5173（vite 預設埠）看到左聊天
右圖譜；問一題後有節點變橘色；點節點後圖上節點數增加。
**❌ 失敗時**：圖是空白 → 先確認 Phase 4+5 成功判準第一條的節點數 > 0，
再開瀏覽器 DevTools Console 看是否 CORS 或連線錯誤（後端要在 8000 埠
運行中）；節點不會展開 → 看 Console 是否報 `l.source.id` 相關錯誤，
表示用了自己改寫的合併邏輯而非 reference 內建版本（硬規則第 4 條）。

## 教學收尾：本 skill 展示的模式

帶同學回顧這個 skill 本身的結構，這是課程真正要教的東西：

| 元素 | 在本 skill 中 | 通用原則 |
|---|---|---|
| 腳本 | 00~05 六支 .py（00 是多來源統一入口） | 確定性、可重跑、冪等的步驟寫成腳本 |
| MCP（驗證用） | Chroma/Neo4j | 建完每層立刻互動驗證，不要最後才 debug |
| MCP（判斷依據用） | Langchain-docs/CopilotKit + web search | 易過期的知識即時查，轉譯成決策依據 |
| 評估迴圈 | Phase 4.5 + eval 腳本 + decision record | 方法宣稱要有「文獻對齊 + 實測數據」雙證據 |
| SKILL.md | 本檔 | 流程編排、判斷邏輯、每步的「為什麼」 |
| references/ | mcp-setup / frontend-graph / method-validation | 深度內容按需載入，不塞爆主文件 |

出作業建議：讓同學把 Phase 3 的抽取 prompt 換成自己領域的 schema
（如財經影片抽「公司-持有-產品」），體會 schema 設計對圖譜品質的影響。

## 疑難排解速查

- `ModuleNotFoundError` → 指令沒加 `uv run`，或不在 skill 根目錄（`pyproject.toml` 那層）。
- Gemini 回 404 / model not found → 模型改名了。跑 `uv run python scripts/check_setup.py`
  看可用清單，`export GEMINI_MODEL=<清單裡的>` 後重跑。
- Gemini 429 / quota exceeded → 免費層每分鐘請求上限。等一分鐘重跑，腳本冪等不會重複寫。
- Chroma 報維度不符（dimension mismatch）→ 換過 `GEMINI_EMBED_MODEL` 但沒重建庫。
  刪掉 `./chroma_db` 重跑 Phase 2。嵌入模型換了，整個向量空間就得重建。
- 抓不到字幕 / 429 → 等幾分鐘重試，或課前預抓 source.json 發放。
- PDF 抽不到字 → 掃描版，改 `--engine llamaparse`（需 LLAMA_CLOUD_API_KEY）。
- 網頁抽不到正文 → JS 渲染頁，改 `--engine tavily`（需 TAVILY_API_KEY）。
- 文件來源被切成超大塊 → 檢查是否誤用 01 直出格式跳過 00（缺 source_type
  會被當成 youtube 做時間窗聚合）。
- Chroma MCP 查無資料 → 路徑或 collection 名不一致（mcp-setup.md）。
- 圖譜全是孤島節點 → 抽取 prompt 的實體正規化不足，同義詞未合併。
- 前端圖重複邊/抖動 → 沒處理 link.source 被改寫成物件（frontend-graph.md 坑 1）。
- LangChain import 錯誤 → 版本漂移，用 Langchain-docs MCP 查當前 import 路徑。
- 強 RAG 沒贏 naive baseline → **先查總 chunk 數**（< ~30 就是語料太小，
  naive 已撈走大半語料，兩邊沒差是必然），再查圖譜是否為空/孤島，
  最後查 Multi-Query 改寫是否偏題。詳見 Phase 4.5 的「❌ 失敗時」。
- 埠 8000 被佔用（`address already in use`）→ 換一個埠即可，
  `uv run uvicorn chatbot_server:app --port 8010`，
  之後 Phase 4.5 記得帶 `--api http://localhost:8010`。
- A/B 勝負反覆不穩定 → judge 噪音；差距 <0.3 分視為平手，或每題評 3 次取中位數。
