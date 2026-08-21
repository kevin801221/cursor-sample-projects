# Walkthrough：用 Cursor 把 Anchor 讀懂、跑起來、改造它

> 這份文件帶你做三件事：**跑起一個 local-first 的論文閱讀器**（在 PDF 上拖框直接問 AI）、**用 Cursor 讀懂一個 1400 行後端 + 5000 行前端的真實 codebase**、然後**動手改造它**。過程中你會親手驗證一件事：**region-first 的精準上下文，勝過把整份 PDF 糊成向量的 whole-PDF chat。**
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先做這五件事，動手當天才不會卡）

1. **確認雙棧環境**：`python3 --version` 要 3.13+（`pyproject.toml` 寫死 `requires-python = ">=3.13"`）、`uv --version`、`node --version` 要 18+。缺 uv 就 `curl -LsSf https://astral.sh/uv/install.sh | sh`。
2. **拿一把免費 Gemini 金鑰**（aistudio.google.com/apikey → Create API key），寫進 `Anchor_knowledge.ai/.env`：一行 `GEMINI_API_KEY=...`。注意這個 repo 的 `.env` **不會自動載入**，要用 `set -a; . ./.env; set +a`（下面 Step 0 會講為什麼）。
3. **提前跑一遍完整安裝**：`uv sync && npm install && npm run build`。第一次 npm install 拉 pdfjs-dist + React 可能要幾分鐘，別留到課堂上。
4. **準備一份論文 PDF**：找一篇你真的讀過、有公式有表格的論文（arXiv 隨便抓一篇都行）。拖框問公式是全課最「哇」的一幕，素材要選有料的。
5. **先看過 `docs/specs/2026-07-15-pdf-region-ask-design.md` 的前三節**——這是作者的架構設計定稿，讀懂它等於拿到整個 codebase 的地圖。

## 🗺️ 學習地圖（建議 3 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 名詞卡 | 25 分 | 閱讀理解（這是全課靈魂，慢慢看） |
| Step 0 跑起來 | 20 分 | 動手做（uv + npm 雙棧、上傳 PDF 拖第一個框） |
| Step 1 用 Cursor 拿地圖 | 20 分 | 動手做（讀設計文件、讓 AI 畫資料流） |
| Step 2 雙通道抽取 | 25 分 | 動手做（region.py + prompts.py，三個實測坑） |
| Step 3 SSE 串流管線 | 25 分 | 動手做（main.py 的 /api/ask，curl 看 frame） |
| Step 4 記憶蒸餾與兩跳擴展 | 30 分 | 動手做（memory.py + 圖譜 explorer，跑測試） |
| Step 5 wiki agent 與 fallback | 15 分 | 動手做（生成一頁 wiki、讀 agent prompt） |
| Step 6 改造練習 | 30 分 | 動手做（加第五把 prompt、修埠不一致） |
| 收尾 + 思考題 | 10 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `../Anchor_knowledge.ai/`，遙控器是 `./demo.sh`（位於 `project-17-anchor-pdf-ai-reader/` 根目錄）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 六幕全部離線、唯讀、秒回——真正起 server 的 live demo 留在最後 15 分鐘。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd ../Anchor_knowledge.ai && uv sync && npm install && npm run build` | 同步 Python 依賴 + 前端 build；demo.sh 六幕不需要，但最後的 live demo 需要 |
| 2 | `.env` 填好金鑰，`set -a; . ./.env; set +a && uv run uvicorn main:app --port 8791` 起一次、拖一個框確認有答案 | 現場網路或金鑰額度出事時，你已經有一份跑通的 data/app.db 可以直接展示圖譜與 wiki |
| 3 | 跑一次 `./demo.sh`（無參數）與 `./demo.sh 3` | 確認遙控器路徑正確、每幕有輸出 |

### 放映時間軸

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:25 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §名詞卡 | 「隔著電話唸論文 vs 指著那行問」+ 卡片盒比喻 | whole-PDF chat 的盲點與 region-first 的產品洞察 |
| 0:25–0:35 | 第 1 幕：這是什麼 App | `./demo.sh 1` | `Anchor_knowledge.ai/README.md` | 產品自述 + 檔案結構 + 各檔行數 | 全端 side project 的骨架長什麼樣 |
| 0:35–0:55 | 第 2 幕：四把 system prompt | `./demo.sh 2` | `Anchor_knowledge.ai/prompts.py` | 27 行的雙通道原則：文字為準、圖補版面、[推測] 標記 | prompt 是產品規格，不是咒語 |
| 0:55–1:20 | 第 3 幕：region.py 雙通道抽取 ⭐ | `./demo.sh 3` | `Anchor_knowledge.ai/region.py` | 81 行全文：座標不翻 y、TEXTFLAGS_TEXT、dpi 夾取 | 每行註解都是一次實測換來的坑 |
| 1:20–1:50 | 第 4 幕：/api/ask SSE 管線 ⭐ | `./demo.sh 4` | `Anchor_knowledge.ai/main.py` | build_contents 穩定前綴 + gen() 四步管線 | 串流時代的錯誤處理：HTTP 已 200，例外只能轉 error frame |
| 1:50–2:20 | 第 5 幕：記憶蒸餾與兩跳擴展 ⭐ | `./demo.sh 5` | `Anchor_knowledge.ai/memory.py` | 蒸餾 prompt、「not evidence」條款、search() 兩跳 | 把模型輸出當不受信任的輸入 |
| 2:20–2:45 | 第 6 幕：wiki agent 與 fallback | `./demo.sh 6` | `Anchor_knowledge.ai/main.py` | WIKI_AGENT_PROMPT、get_concept/get_neighbors、確定性 fallback | agent 要配退路，失敗不能開天窗 |
| 2:45–3:00 | Live demo + 收尾 | — | localhost:8791 | 真的拖框、看串流、開圖譜、生成 wiki | 全部串起來的樣子 |

---

## 🎬 開場故事：隔著電話唸論文 vs 指著那行問

想像你讀論文卡在第 7 頁一條公式上，旁邊剛好坐著一位教授。

**傳統方法（whole-PDF chat）**像隔著電話問：你把整本論文寄給遠方的教授，然後問「那個 loss function 是什麼意思」。教授手上是整份文件的摘要索引，他會跟你講這篇論文「整體在做什麼」——但你卡住的是**第 7 頁那一條**，他常常答到隔壁去。工具越努力理解「整份文件」，越容易答非所問。

**Anchor 的方法（region-first）**是教授就坐在你旁邊：你用手指著那條公式說「這個」。而且 Anchor 一次給教授兩樣東西——**唸給他聽的精確文字**（PyMuPDF 從 PDF 內嵌文字層抽出來的，一個字都不會錯）加上**讓他親眼看一眼的截圖**（版面、上下標、表格線都在）。只唸不看會漏掉版面語意，只看不唸會把 $\sigma$ 認成 o。兩個都給，答案才又準又懂版面。

故事還有下半場。你問過的東西去哪了？

**傳統聊天**像貼滿螢幕的便利貼：問完就過去了，三週後你只記得「好像問過類似的」。

**Anchor** 像卡片盒筆記法（Zettelkasten）：每次問答結束，背景有一個安靜的圖書館員把對話**蒸餾**成一張張卡片——這是概念、這是發現、這是還沒解的疑問——再用帶類型的線把卡片連起來：支持、矛盾、延伸。你在第 5 篇論文框住一段話時，圖書館員會先翻卡片盒：「你三週前在第 1 篇問過相關的東西」，把那張卡片附在旁邊——但他很守規矩：**卡片只是提示，不是證據，你現在框住的內容永遠優先。** 卡片攢多了，還能替每張卡片寫一頁百科、互相連結成你自己的 wiki。

這個對照表會貫穿全課：

| 生活比喻 | Anchor 的機制 | 程式碼在哪 |
|---|---|---|
| 用手指著那行問 | 拖框 → fitz 座標 rect → 後端裁切同一塊 | `src/PdfPage.tsx` → `region.py` |
| 唸給教授聽 + 讓他看一眼 | `<region_text>` 精確文字 + 裁切圖雙通道 | `region.py`、`prompts.py` |
| 圖書館員事後整理卡片 | 答案存好後 best-effort 蒸餾成節點與邊 | `main.py extract_memory_candidates` |
| 翻卡片盒找相關卡片 | FTS5 找種子 → 圖上最多擴展兩跳 | `memory.py search()` |
| 卡片只是提示不是證據 | memory_context 的「not evidence」條款 | `memory.py format_memory_context` |
| 替卡片寫百科 | DeepAgents 拿兩個工具探索圖再寫頁 | `main.py _wiki_agentic` |

---

## 🔍 名詞卡（十四個術語的白話解釋）

### 1. Local-first（本機優先）

> 白話：資料的家在你的電腦，不在別人的雲端。Anchor 的 PDF、對話、圖譜、wiki 全部存在一顆本機 `data/app.db`，唯一出門的是「你框的那一塊」（送給 Gemini 答題）。
> 為什麼重要：論文可能是未發表的稿子、公司內部文件。「上傳整份文件到別人伺服器」和「只送出我指定的一小塊」是完全不同的隱私邊界。

### 2. Sidecar（隨行小工具）

> 白話：不是一個平台、不是一個服務，是跟在你身邊的個人小工具。作者在 `pyproject.toml` 的自述就是「本機個人 sidecar」。
> 為什麼重要：定位決定架構。因為是單人 sidecar，所以敢用一顆 SQLite、一條連線、零外部資料庫——簡單到看得完，是這個 repo 適合教學的原因。

### 3. Region-first（區塊優先）

> 白話：問答的單位不是「整份文件」，是「你框住的那個矩形」。一個框 = 一個對話串，追問都帶著同一塊上下文。
> 為什麼重要：這是整個產品的核心洞察。你卡住的從來不是「這篇論文」，是「這一段」。上下文的精度比份量值錢。

### 4. pdf.js 與 PyMuPDF

> 白話：同一份 PDF 的兩個門。前端用 pdf.js（Mozilla 出品）把 PDF 畫在瀏覽器 canvas 上給你看；後端用 PyMuPDF（Python 套件，repo 裡 `import pymupdf`；舊模組名叫 `fitz`，所以座標系慣稱 fitz 座標）從同一份檔案精確抽文字、偵測表格、裁切圖片。
> 為什麼重要：前端從不解析 PDF 的內容，只負責「把你的拖曳變成座標」；真正的抽取全在後端。職責切得乾淨，座標就是唯一的合約。

### 5. fitz 座標（永不翻 y）

> 白話：PyMuPDF 的座標系是左上原點、y 向下——跟瀏覽器 canvas 同向。「PDF 原點在左下所以要翻 y」對 PyMuPDF 是錯的，它已經幫你翻好了。
> 為什麼重要：這是整個 repo 用實測釘死的地基（`tests/test_backend.py` 有 4 條 assert 守著）。座標翻錯一次，框到的就是頁面另一頭。

### 6. SSE（Server-Sent Events）

> 白話：HTTP 的單向水管。伺服器把答案切成一個個 `data: {...}` frame 逐段推給瀏覽器，這就是「答案一個字一個字長出來」的原理。
> 為什麼重要：SSE 回應一開始就是 HTTP 200，後面出錯沒辦法改狀態碼——所以錯誤只能包成一個 error frame 塞進串流。這是串流時代錯誤處理的必修課。

### 7. SQLite WAL 模式

> 白話：SQLite 的 Write-Ahead Logging 模式，讀寫可以並行，不會讀一半被寫入卡住。`main.py` 的 DDL 第一行就是 `PRAGMA journal_mode=WAL`。
> 為什麼重要：一顆檔案型資料庫就撐起整個 app（文件、對話、筆跡、便條、剪貼、圖譜、wiki、簡報），零安裝、零維運。

### 8. FTS5 / BM25

> 白話：SQLite 內建的全文檢索引擎（FTS5）配經典的關鍵字排名演算法（BM25）。Anchor 用它找「跟這次問題相關的記憶卡片」，中文切成三字一組（trigram）來索引。
> 為什麼重要：注意這裡**沒有向量資料庫**——詞面檢索在個人規模夠用，還省掉一整套 embedding 基礎設施。技術選型要配規模。

### 9. 記憶圖譜（Memory Graph）

> 白話：節點是「概念、發現、疑問、明講的偏好、論文本身」，邊是帶類型的關係——支持、矛盾、延伸、提及。全部存在 SQLite 三張表裡（`memory_node` / `memory_edge` / `memory_source`）。
> 為什麼重要：每個節點都留著出處（哪篇論文、第幾頁、哪個對話），點卡片能跳回證據。沒有出處的知識庫是無法信任的。

### 10. 蒸餾（Memory Extraction）

> 白話：答案存好之後，再問模型一次：「這輪對話裡有什麼值得長期記住的？」用 JSON schema 逼它輸出結構化的節點與邊。日常翻譯這種沒營養的，明確要求回零個節點。
> 為什麼重要：蒸餾是**事後、非同步、best-effort**——失敗只記 log，絕不拖垮答題。加強元件不能讓系統變脆。

### 11. 兩跳擴展（Two-hop Expansion）

> 白話：FTS5 撈到種子卡片後，沿著圖上的邊最多再走兩步，把鄰居的鄰居也納入候選，按「種子排名 + 邊的信心 + 有沒有被釘選」計分取前幾名。
> 為什麼重要：這是圖譜存在的理由——詞面搜不到但概念相連的東西，靠邊走過去。跟 Project 14 的 GraphRAG 圖譜擴展是同一個思想，這裡是零依賴的 SQLite 版。

### 12. DeepAgents（agentic wiki）

> 白話：LangChain 的 agent 框架。Anchor 給 agent 兩個工具——`get_concept`（看一張卡片）和 `get_neighbors`（看它的鄰居）——讓它自己在圖上探索最多兩跳，看夠了才動筆寫 wiki 頁。
> 為什麼重要：對比「把所有資料塞進一個大 prompt」，agent 是「自己決定要看什麼」。而且它有退路：兩次回空就交給不用模型的確定性組頁。

### 13. 穩定前綴與 implicit cache

> 白話：`build_contents()` 把「裁切圖 + 原文」永遠放在對話最前面，追問只往後面加。Gemini 看到重複的前綴會自動命中快取，省錢省延遲。
> 為什麼重要：這是「知道模型怎麼計費」的工程。同一個框追問十次，那張圖只算一次全價。

### 14. 樂觀 UI（Optimistic UI）

> 白話：你一放開滑鼠，`crop.ts` 立刻從**已經渲染好的 canvas** 裁出縮圖塞進側欄——不等後端回覆。真正的高清裁切圖後端慢慢做。
> 為什麼重要：體感速度是設計出來的。零 round-trip 的縮圖讓「拖框 → 看到反應」之間沒有任何等待。

---

## Step 0：把 Anchor 跑起來

### 0-1 安裝雙棧

這個專案前後端各有一套依賴管理：Python 用 uv、前端用 npm。

```bash
cd Anchor_knowledge.ai
uv sync
npm install
npm run build
```

`npm run build` 會先跑 `tsc --noEmit`（型別檢查）再 `vite build` 產出 `dist/`。注意 `main.py` 最後一段：**靜態檔只在 `dist/` 存在時才掛載**——沒 build 過就開瀏覽器，你會看到 404，不是 bug。

✅ **預期看到**：`uv sync` 裝好 fastapi/pymupdf/google-genai/deepagents 等套件；`vite build` 結尾印出 `dist/index.html` 與若干 assets。

### 0-2 金鑰與 `.env` 的正確姿勢

在 `Anchor_knowledge.ai/` 建一個 `.env`，內容一行：

```
GEMINI_API_KEY=你的金鑰
```

然後——重點來了——這個專案**不自動載入 `.env`**（後端直接讀環境變數，`genai.Client()` 讀 `GEMINI_API_KEY`）。啟動前要手動灌進 shell：

```bash
set -a; . ./.env; set +a
```

`set -a` 的意思是「接下來 source 的變數全部自動 export」。漏掉這行，最常見的症狀是 server 起得來、拖框問下去才在 SSE 裡收到 error frame。

### 0-3 啟動與第一個框

```bash
uv run uvicorn main:app --port 8791
```

✅ **預期看到**：`Uvicorn running on http://127.0.0.1:8791`。

開 <http://localhost:8791>：

1. 點「上傳 PDF」丟進你準備的論文
2. 直接在頁面上**拖一個框**，框住一條公式
3. 浮動 toolbar 跳出來，按 `E`（解釋）
4. 側欄先出現你框的縮圖（樂觀 UI），接著答案逐字長出來，公式用 KaTeX 渲染

再試：按 `V` 切到文字模式反白一句話問問題、按 `⌘+Enter` 追問、按 `Esc` 中斷串流。

🧯 **卡住的話**：
- `uv sync` 報 Python 版本 → 這個專案要求 **Python 3.13+**（`requires-python = ">=3.13"`），`uv python install 3.13` 可以直接裝
- 開 8791 看到 404 或空白 → 沒跑 `npm run build`，`dist/` 不存在
- 拖框後側欄跳 `gemini ...` error frame → 金鑰沒灌進環境（回 0-2），或免費額度用完
- 想整個重來 → `rm -rf data/`（PDF、對話、圖譜全在裡面，砍掉就是全新狀態）

> ❓ **想一想**：為什麼上傳同一份 PDF 兩次，`data/pdf/` 裡只有一個檔案？
>
> **答案**：檔名是內容的 sha256 雜湊（`add_doc()`），同內容 → 同雜湊 → 同檔名，天然去重。`tests/test_backend.py` 的第一條 assert 就在守這件事。

---

## Step 1：用 Cursor 拿到整個 codebase 的地圖

不要從 `main.py` 第一行開始讀。這個 repo 留了一份比程式碼更好讀的東西：**設計文件**。

### 1-1 先讀設計定稿

在 Cursor 裡打開 `docs/specs/2026-07-15-pdf-region-ask-design.md`。這是作者動工前寫的架構設計，狀態欄寫著「設計定稿，待施工。座標系與 PyMuPDF 行為皆經實跑程式碼驗證」。它的 §3 檔案樹連每個檔案的預估行數都寫好了，§4 把 pointerdown → chat 出字的完整資料流走了一遍。

`docs/plans/` 底下還有記憶圖譜與 card-to-ppt 兩個功能的 design + implementation 計畫——這個 repo 本身就是「先寫設計文件再動工」的示範。

### 1-2 讓 Cursor 替你畫資料流

在 Cursor 的 Chat 裡（用 `@` 把檔案帶進上下文）問：

> `@docs/specs/2026-07-15-pdf-region-ask-design.md` `@main.py` `@region.py`
> 我拖一個框、按下「解釋」之後，資料經過哪些函式？請按順序列出：前端哪個元件送出請求 → 後端哪些函式接手 → 什麼時候寫 DB → 什麼時候打 Gemini → 答案怎麼回到畫面。每一站附上檔名與函式名。

✅ **預期看到**：AI 列出大致這條鏈——`PdfPage.tsx`（拖框得 rect）→ `api.ts askStream`（POST /api/ask）→ `main.py resolve_ask()`（收斂新框/追問兩種請求）→ `region.py extract_region()`（抽文字+表格+圖）→ `memory_store.search()`（撈相關記憶）→ `insert_thread/insert_msg`（先寫 DB）→ `build_contents()` + `gemini_stream()`（打模型）→ SSE frame 回 `Chat.tsx`。

對照 `main.py` 的 `/api/ask`（搜 `async def ask`）驗證它沒唬你——`gen()` 函式體的註解就標著 1、2、3、4 四步。

### 1-3 建立「問程式碼」的習慣

再丟兩個問題感受一下 Cursor 讀 codebase 的姿勢：

> 這個專案的前端為什麼完全不解析 PDF 內容？框的座標從瀏覽器像素換算到 PDF 座標的公式在哪個檔案？

> `main.py` 的 `db = connect()` 是模組層級的單例，這對測試有什麼影響？測試怎麼避免污染真實的 data/？（提示：搜 `PDFASK_DATA`）

**講解重點**：問 AI 的訣竅是「要求它引用檔名與函式名」，逼它落地到真實程式碼，你才驗證得了。

---

## Step 2：雙通道抽取——region.py 的 81 行

`region.py` 是全 repo 密度最高的檔案：81 行，每個決定都附了實測依據。在 Cursor 裡打開它，配合 `./demo.sh 3` 投影。

✅ **預期看到**：`./demo.sh 3` 印出幕次 banner（📺／🎯 兩行）後，接著是 `region.py` 的 81 行全文——`extract_region()`、`_extract_tables()` 與那三段實測註解都在同一屏內讀得完。

### 2-1 一個函式、兩種模式

`extract_region(sha, page_no, rect, kind)`：

- `kind="box"`（拖框）→ 回**文字 + 表格 markdown + 裁切圖**三樣
- `kind="text"`（反白）→ 只回文字，不做 pixmap——更快更省，因為反白時瀏覽器已經拿到精確文字了

### 2-2 三個用實測換來的坑

逐行讀這三處註解，每一個都值得抄進你自己的專案：

1. **`TEXTFLAGS_TEXT` 必加**——不加的話 `get_text("dict")` 會把區塊裡的圖片二進位一起塞進 payload，作者實測從 2.7KB 暴漲到 382KB。
2. **rotation 頁的雙空間**——`get_text` 的 clip 活在「未旋轉」空間要先乘 `derotation_matrix`；`get_pixmap` 的 clip 活在「已旋轉」空間用原 clip。同一個框、兩個 API、兩種座標空間。
3. **dpi 夾取**——`dpi = min(150, ...)` 鎖住長邊 ≤ 1568px，因為 Gemini 的 vision 內部就會縮到這個量級，「超過只是白付頻寬」。PNG 超過 400KB 就轉 JPEG。

還有一行安靜但關鍵的：`"is_scanned": len(text.strip()) < 3`——掃描檔抽不出文字**不丟例外**，標個旗標讓下游全靠圖回答。

### 2-3 prompts.py：雙通道的使用說明書

打開 `prompts.py`（27 行）。`_COMMON` 把雙通道的優先序寫成了給模型的規則：

- 文字以 `<region_text>` 為準；圖用來理解版面、表格、圖表、公式
- 文字殘缺（框到一半的字）才依圖補齊**並標 [推測]**
- 沒有 `<region_text>`（掃描檔）就直接讀圖
- 數學一律 LaTeX、用 `$` 包好——這就是側欄公式漂亮的原因

> ❓ **想一想**：為什麼不乾脆只送截圖給多模態模型就好？模型明明「看得懂」圖。
>
> **答案**：vision 模型會幻讀——把 $\sigma$ 認成 o、把下標讀錯位。PDF 內嵌文字層是零錯字的 ground truth。反過來只送文字也不行：表格線、公式的上下標結構、圖表本身都不在文字層裡。兩通道各補對方的盲區。

**在 Cursor 裡做**：問 AI——

> `@region.py` 如果我框了一個「太扁的框」（高度 30pt），表格偵測會發生什麼事？為什麼作者要加這個判斷？

（答案在 `_extract_tables` 開頭：`clip.height <= 60` 直接回空，省 100–500ms——不可能是表格的框連偵測都不跑。）

---

## Step 3：SSE 串流管線——main.py 的 /api/ask

這是全案最長的一條路，配合 `./demo.sh 4` 投影。

### 3-1 先看 build_contents 的穩定前綴

搜 `def build_contents`。注意排列順序：**裁切圖 + 原文永遠放在 contents 最前面**，然後補一句假的 model 回覆「我看到這個區塊了。」，之後的追問只往後 append。docstring 講明了動機：「穩定前綴 → implicit cache 命中點」。同一個框追問十次，那張圖的 token 只付一次全價。

### 3-2 gen() 的四步

搜 `async def gen`，函式體的註解自己就是教材：

1. **抽取**——`extract_region` 是同步阻塞的 PyMuPDF 呼叫，用 `anyio.to_thread.run_sync` 丟進 threadpool，不卡 event loop
2. **thread**——新框就 INSERT，追問就沿用；先把 thread 資訊 yield 給前端
3. **先寫 user 問題進 DB，開一個空的 assistant 泡泡**——先佔位再串流
4. **串流**——`async for` 逐 token yield；**中斷或例外都把已累積的部分寫回 DB**

第 4 步有一行值得放大投影的註解：

```
except Exception as e:  # HTTP 已 200，例外只能轉 error frame
```

SSE 回應一開始就送出 200 了，後面炸掉沒辦法改狀態碼——唯一的辦法是把錯誤包成一個 `{"error": ...}` frame 塞進串流，讓前端顯示。這是所有做串流 API 的人都要學的一課。

另外注意 `_sse()` 的註解：token 常含換行，裸換行會切斷 SSE frame，所以每個 payload 一律 JSON 包起來。

### 3-3 動手驗證

server 跑著（Step 0），另開終端機：

```bash
curl -s localhost:8791/api/docs | python3 -m json.tool
```

✅ **預期看到**：你上傳過的文件清單，每筆有 `sha256`、`filename`、`pages`。

把 sha256 抄下來，直接用 curl 看原始 SSE frame（`-N` 關掉緩衝）：

```bash
curl -N -X POST localhost:8791/api/ask -H "Content-Type: application/json" \
  -d '{"sha256":"貼你的sha","page":0,"rect":[50,50,500,300],"kind":"box","action":"summarize"}'
```

✅ **預期看到**：先來一個 `data: {"thread": ...}` frame（如果這次有撈到歷史記憶，緊接著一個 `data: {"used_memories": [...]}`），然後一串 `data: {"t": "..."}` 逐 token，最後 `data: {"done": true, "msg_id": ..., "usage": {...}}`——答完幾秒後如果這輪有料，還會多一個 `data: {"created_memories": [...]}`：你親眼看到蒸餾在答案之後才發生。

🧯 **卡住的話**：
- `thread not found` / 400 → rect 或 page 超出該 PDF 範圍，換 `page:0` 和小一點的 rect
- 卡住沒輸出 → 金鑰沒載入，看 uvicorn 那個終端機的 log
- 回了 `{"error": "gemini ..."}` → 正常的錯誤路徑！這就是 3-2 講的 error frame

---

## Step 4：記憶蒸餾與兩跳擴展——memory.py

配合 `./demo.sh 5` 投影。這是全案思想密度最高的一段。

### 4-1 蒸餾的三道閘門

**閘門一：prompt 就在挑剔。** `main.py` 搜 `Extract only durable research memory`——蒸餾 prompt 開宗明義：只抽「長期有價值」的，日常翻譯回零個節點；`user_preference` 只有使用者**明講**偏好才准出現。

**閘門二：schema 約束。** 蒸餾請求帶 `response_json_schema=MEMORY_EXTRACTION_SCHEMA`，node 的 kind、edge 的 kind 都是 enum 白名單。

**閘門三：程式碼再驗一次。** `memory.py` 的 `parse_memory_extraction()` 把回來的 JSON 當**不受信任的輸入**重新逐欄檢查：節點截前 20、邊截前 30、title 截 200 字、confidence 夾 [0,1]、邊的兩端必須是這輪出現過的 key、`explicit_preference` 不是 `True` 的偏好直接丟棄。壞 JSON？log 一行，這輪不抽。

> ❓ **想一想**：schema 都約束了，為什麼還要 parse 再驗一次？
>
> **答案**：schema 擋不住「格式對但內容越界」——模型可以回 500 個節點、confidence 給 3.7、edge 指向不存在的 key。凡是模型產生的資料，入庫前都要當外部輸入驗證。這個原則跟「凡是使用者輸入都要驗證」一模一樣。

### 4-2 檢索：FTS5 種子 + 兩跳擴展

搜 `def search`。流程：

1. `_seed_rows()` 用 FTS5（BM25 排名）找詞面相關的種子節點——中文切 trigram，FTS 失敗還有 LIKE fallback
2. 從種子出發沿邊擴展，**最多兩跳**（`depth >= 2` 就停）
3. 計分：種子名次 + 節點 confidence + 釘選加 3 分，每走一跳扣 2 分再加邊的 confidence，低信心（< 0.45）的節點與邊直接不走
4. 每個候選還記著 `path`——「A → extends → B」這樣的推理路徑，前端可以顯示「為什麼撈到這張卡」

然後看 `format_memory_context()`：撈到的記憶包成 `<memory_context>`，開頭那句話值得抄——

> They may guide connections, but they are not evidence and must not override the current PDF region.

記憶可以引導，但不是證據，絕不覆蓋當下框住的內容。整個 context 還有 4000 字元的硬上限，逐張卡片塞、塞不下就截斷或跳過。

### 4-3 動手驗證

```bash
uv run python -m unittest tests.test_memory -v      # 只跑記憶圖譜的測試
uv run python -m unittest discover -s tests -t .    # 後端全部測試
```

✅ **預期看到**：`OK`。測試用 `PDFASK_DATA` 指到 temp 目錄，不碰你真實的 `data/`。

然後回到瀏覽器：多框幾個概念問一問，打開 toolbar 的「記憶」看卡片長出來（可以釘選、編輯、標不相關），再開「圖譜」看力導向圖——`graphLayout.ts` 是**零依賴、決定性**的 Fruchterman–Reingold 實作，種子擺在圓上不用亂數，同樣的圖永遠長同樣的形狀。也可以直接：

```bash
curl -s localhost:8791/api/graph | python3 -c "import json,sys; d=json.load(sys.stdin); print('節點:', len(d['nodes']), '邊:', len(d['edges']))"
```

**在 Cursor 裡做**：

> `@memory.py` search() 的計分公式裡，pinned 加 3 分、每跳扣 2 分，這兩個數字的相對大小意味著什麼？如果我想讓「同一篇論文的記憶」更容易被撈到，該改哪裡？

（後者的答案在 `main.py` 的 ask 流程與 `memory.py` search 尾段：`current_sha` 命中會加 1.5 分。）

---

## Step 5：wiki agent 與 fallback 階梯

配合 `./demo.sh 6` 投影。

### 5-1 給 agent 兩個工具，讓它自己逛圖

`main.py` 搜 `WIKI_AGENT_PROMPT`。生成一頁 wiki 時，Anchor 不是把整個圖塞進 prompt，而是用 DeepAgents 建一個 agent，只給兩個工具：

- `get_concept(id)`——看一張卡片的完整內容與來源
- `get_neighbors(id)`——看它的一跳鄰居

prompt 要求它「先看目標概念，再看鄰居，必要時對重要鄰居再看一次（最多兩跳），只根據工具回傳的內容撰寫，絕不杜撰」。寫出來的頁面帶 `[[wikilink]]`、相關概念清單、論文頁碼來源。

### 5-2 fallback 階梯

注意 `_wiki_agentic` 的防禦層次：

1. agent 偶發回空 → **重試一次**（`for attempt in range(2)`）
2. 還是空、或整個 agent 炸掉 → `_wiki_fallback()` 用純 Python 組一頁確定性的內容（內容 + 相關概念 + 來源），**不用任何模型**
3. `thinking_budget=0` 的註解也誠實：2.5-flash 開 thinking 在 agent loop 常回空——所以關掉

同一個模式在 deck 也出現一次：AI storyboard 失敗 → 本地編譯器。**這個 repo 的每個 LLM 呼叫都有一條不靠 LLM 的退路。**

### 5-3 動手

瀏覽器開 toolbar 的「Wiki」，挑一個概念按生成，看 agent 寫的頁面；點 `[[wikilink]]` 跳到別的概念。想看 fallback 長什麼樣：在沒有金鑰的 shell 起 server 再生成一次（或看 `_wiki_fallback` 的程式碼想像輸出）。

✅ **預期看到**：一頁 Markdown 百科——`# 概念標題` 開頭、內文自然處帶 `[[wikilink]]`、結尾兩節「## 相關概念」（列 `[[標題]]` 與關係類型）與「## 來源」（論文與頁碼）。這個結構是 `WIKI_AGENT_PROMPT` 明文要求的，fallback 版也長一樣的骨架。

🧯 **卡住的話**：
- 生成的頁面很乾、只有一兩句 → 正常：prompt 要求「資訊不足就據實精簡」，多問幾輪讓卡片長多一點再生成
- 沒金鑰或 agent 兩次回空 → 自動走 `_wiki_fallback()` 確定性組頁（內容 + 相關概念 + 來源），不會開天窗

---

## Step 6：改造練習——這才是 Cursor 課的重點

跑得起來、讀得懂之後，改它。三個任務由易到難，全部用 Cursor 完成，改完都要跑測試。

### 任務 A（送分）：換模型一行

`main.py` 搜 `MODEL = "gemini-2.5-flash"`，註解寫著「升級改這一行」。問 Cursor：

> 這個 repo 有幾處寫死模型名？如果我想改用環境變數覆蓋預設模型，最小改動是什麼？

### 任務 B（真實 bug）：修 dev 埠不一致

repo README 的開發提示說「backend on 8791 + `npm run dev`」，但 `vite.config.ts` 的 proxy 寫死 `http://127.0.0.1:8000`，設計文件 spec §2 也是 8000。也就是說照著 README 開 dev 模式，前端打 `/api` 會全部 connection refused。對 Cursor 說：

> `@vite.config.ts` `@README.md` 這兩個檔案對 dev 模式的後端埠號說法不一致，找出所有相關位置，統一成 8000，並告訴我為什麼 dev 模式的 proxy 要關注 SSE buffering。

驗證：`uv run uvicorn main:app --reload --port 8000` + `npm run dev`，開 Vite 給的網址拖框，答案要能串流（hot-reload 開發從此不用每改一行就 rebuild）。

### 任務 C（完整功能）：加第五把 prompt「批判」

現在有翻譯/解釋/摘要/自訂問四個 action。加一個 `critique`：批判這個區塊的論證——假設是否成立、證據是否支撐結論。對 Cursor 說：

> 我要加一個新 action "critique"。請找出從前端按鈕到後端 prompt 的所有需要修改的位置，先列清單給我確認再動手。

✅ **預期看到**：清單至少涵蓋——`prompts.py` 的 `SYS` 加一把、`main.py` 的 `ACTION_LABEL` 加一句、前端 `src/types.ts` 的 `Action` 型別、`App.tsx` 的 `ACTION_LABEL`、`RegionToolbar.tsx` 的按鈕與快捷鍵。改完跑：

```bash
uv run python -m unittest discover -s tests -t .
npm test
npm run build
```

三個都綠、瀏覽器上新按鈕能出批判式答案，任務完成。（Node 22+ 跑 `npm test` 若有 9 個 localStorage 相關失敗，見下方排錯表的 `--localstorage-file` 解法。）

**講解重點**：任務 C 的價值在「先列清單再動手」——讓 AI 先做影響面分析，你來把關，這比讓它直接改快十倍也安全十倍。

---

## 驗收清單

- [ ] `uv sync`、`npm install`、`npm run build` 三連通過
- [ ] localhost:8791 上傳 PDF、拖框、答案串流、KaTeX 公式正常渲染
- [ ] 反白模式（`V`）問過一次、追問（`⌘+Enter`）過一次、`Esc` 中斷過一次
- [ ] 能不看筆記說出「拖框到答案」經過的五站（前端座標 → /api/ask → extract_region → build_contents → SSE）
- [ ] 講得出 region.py 三個實測坑各在防什麼
- [ ] curl 過 `/api/ask` 看過原始 SSE frame，包含結尾的 `created_memories`
- [ ] `uv run python -m unittest discover -s tests -t .` 與 `npm test` 全綠
- [ ] 記憶面板有卡片、圖譜 explorer 有節點、生成過至少一頁 wiki
- [ ] 完成改造任務 B（dev 埠）與 C（critique action），測試仍全綠

## 常見坑排錯速查

| 症狀 | 最可能的原因 | 快速修法 |
|---|---|---|
| `uv sync` 抱怨 Python 版本 | 專案要求 >= 3.13 | `uv python install 3.13` 後重跑 |
| 開 8791 是 404 / 空白頁 | 沒 `npm run build`，`dist/` 不存在（main.py 只在 build 過才掛靜態檔） | `npm run build` 再重整 |
| 拖框後側欄跳 gemini error frame | `.env` 沒灌進環境變數 | `set -a; . ./.env; set +a` 後重啟 uvicorn |
| dev 模式 `/api` 全部 connection refused | vite proxy 指到 8000，你的後端跑在 8791 | 後端改 `--port 8000`，或改 `vite.config.ts`（見任務 B） |
| 掃描版 PDF 答案怪 | 沒有文字層，`is_scanned` 走純圖模式 | 正常行為；換有文字層的 PDF 對比差異 |
| 框公式回答把符號讀錯 | 只框到公式的一半，殘字靠圖補 | 框大一點；注意答案裡的 [推測] 標記 |
| `npm test` 直接炸 | 沒 `npm install`（vitest 在 devDependencies） | `npm install` 再跑 |
| `npm test` 有 9 個 App.test 失敗：`Cannot read properties of undefined (reading 'getItem')` | 新版 Node（22+，本機 26 實測）內建全域 `localStorage`，沒給 `--localstorage-file` 時是 `undefined`，蓋掉 jsdom 的實作 | `NODE_OPTIONS="--localstorage-file=/tmp/vitest-ls.json" npm test`（實測 81/81 全綠） |
| 記憶面板一直是空的 | 問的都是翻譯類，蒸餾 prompt 判定無長期價值 | 正常！問概念性問題（「這方法跟 X 差在哪」）才會長卡片 |
| 想砍掉重練 | — | `rm -rf Anchor_knowledge.ai/data/`（PDF、對話、圖譜全清） |
| 測試會不會弄髒我的 data/ | 不會 | 測試把 `PDFASK_DATA` 指到 temp 目錄 |

## 帶走的三句話

如果整份專案只能記住三件事，就這三句：

1. **上下文的精度比份量值錢**——region-first 把「你正在盯著的那一塊」原封不動送過去，勝過把整份 PDF 糊成向量再撈回來。做 AI 產品先問「使用者卡住的最小單位是什麼」，再決定送什麼上下文。

2. **雙通道：文字為準、圖補版面，而且要寫進 prompt 裡**——精確文字防幻讀、忠實截圖補版面語意，優先序（缺字才從圖補、要標 [推測]）明文寫在 system prompt 裡。模型的行為邊界是規格，不是玄學。

3. **凡是模型產生的，一律當不受信任的輸入；凡是加強用的，一律 best-effort**——蒸餾結果要 schema 約束加逐欄驗證才入庫；記憶、wiki agent、AI storyboard 全都有不靠 LLM 的退路。加強元件失敗，主路徑照常。

---

## ❓ 思考題（五題）

### ❓ 想一想 1：為什麼蒸餾放在「答案存好之後」，而不是跟答題同一個請求？

**答案**：三個理由。(1) 延遲——答題要搶首字時間，蒸餾多等幾秒沒人在乎；(2) 失敗隔離——蒸餾炸了只 log 一行，答案已經安全在 DB；(3) 關注點分離——答題 prompt 專心答題，蒸餾 prompt 專心挑「值得長期記的」，混在一起兩邊都做不好。

**延伸**：那為什麼不開一個背景排程批次蒸餾？→ 可以，但單人 sidecar 的規模「答完順手蒸餾」最簡單；批次是多用戶時代的優化。

### ❓ 想一想 2：memory_context 為什麼要明講「not evidence and must not override the current PDF region」？

**答案**：記憶可能過時、可能來自別篇論文的不同語境、甚至可能當初就蒸餾錯了。當下框住的區塊才是這次問答的證據。沒有這句話，模型會拿三週前的卡片蓋過你眼前的原文——那是最難 debug 的一種答錯，因為答案「看起來很有道理」。

### ❓ 想一想 3：`user_preference` 為什麼要 `explicit_preference=true` 才收，而且 prompt 和驗證程式碼各擋一次？

**答案**：從單一問題推斷偏好是很危險的歸納——你問了一次 RLHF 不代表你「對 RLHF 有長期興趣」。錯的偏好會在之後每次檢索裡累積偏差。prompt 擋一次是請模型自律，`parse_memory_extraction` 再擋一次是不信任它的自律——防禦要放在你能控制的那一側。

### ❓ 想一想 4：整個 app 為什麼敢只用一顆 SQLite，不上向量資料庫、不上圖資料庫？

**答案**：規模與需求決定選型。個人閱讀量的記憶卡片是百千級，FTS5 BM25 的詞面檢索 + 兩跳圖擴展（三張普通的表就存得下圖）已經夠準；WAL 模式撐得起單人讀寫。換來的是零外部依賴、`rm -rf data/` 就能重來、整個狀態一個檔案可備份。等語料大到詞面檢索明顯漏撈，再上 embedding 也不遲——而且儲存層已經隔離成 `LocalMemoryStore`，換後端不動 UI 合約。

### ❓ 想一想 5：build_contents 為什麼要偽造一句 model 的「我看到這個區塊了。」？

**答案**：Gemini 的多輪格式要求 user/model 交替。圖+原文是第一個 user turn，接著必須有一個 model turn 才能放使用者的問題。這句假回覆讓「區塊內容」與「問題」分屬不同回合——於是不管追問幾輪，最前面的「圖+原文+假回覆」前綴一個位元都不變，implicit cache 才有穩定的命中點。一句話同時解決格式合法性與快取經濟學。
