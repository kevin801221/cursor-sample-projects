# Anchor：框選論文任一區塊直接問 AI 的 local-first 閱讀器

> Cursor 課程 Project 17：一個完整的全端 side project——React 19 + FastAPI + PyMuPDF + Gemini。在 PDF 上拖一個框（段落、公式、表格、圖都行）直接問 AI，答案逐字串流進側欄；每次問答自動蒸餾成個人記憶圖譜，還能長成一本可瀏覽的 AI wiki。

一句話：**Region-first 而不是 whole-PDF chat；精確文字 + 忠實截圖雙通道送模型；問完的東西不丟掉，蒸餾成圖譜；PDF 永遠不離開你的電腦。**

## 專案規格

| | |
|---|---|
| **最終成果** | 在本機跑起 Anchor：上傳論文 → 拖框問 AI → 答案串流附 LaTeX 公式 → 記憶面板長出概念節點 → 圖譜 explorer 看到跨論文連結 → 生成 wiki 頁互相 `[[wikilink]]`。然後在 Cursor 裡改造它：加一把新的 system prompt、修一個真實存在的埠號不一致 |
| **技術棧** | 前端 React 19 + TypeScript + Vite 6 + pdf.js；後端 FastAPI + SQLite（WAL + FTS5）+ PyMuPDF；模型 Gemini 2.5 Flash（google-genai）+ LangChain DeepAgents |
| **預估時間** | 跑起來 30 分鐘；讀懂四條主線 90 分鐘；改造練習 60 分鐘 |
| **前置需求** | Python 3.13+、uv、Node.js 18+、免費 Gemini API 金鑰（aistudio.google.com/apikey） |
| **程式碼位置** | `../Anchor_knowledge.ai/`（本資料夾只放教學三件套） |

## 這個 App 做什麼

讀論文卡住的那一刻，你以前的動作是：截圖 → 貼到聊天視窗 → 打問題。Anchor 把這三步壓成一步：

1. **拖框就問**——在 PDF 上框住卡住你的那一塊，按 `T`/`E`/`S`/`Q`（翻譯/解釋/摘要/自訂問），答案逐 token 串流進側欄。一個框 = 一個對話串，可以無限追問。
2. **反白也能問**——切到文字模式選一句話直接問（純文字、更快更省）。
3. **問過的不會蒸發**——每次完整答完，背景把對話蒸餾成「概念、發現、疑問」節點與帶類型的關係邊，存進跨論文的記憶圖譜。第 5 篇論文的問題，可以用到第 1 篇學到的概念。
4. **圖譜長成百科**——DeepAgents agent 拿兩個工具在圖上探索兩跳，替每個概念寫一頁有 `[[wikilink]]`、有來源頁碼的 wiki；整張圖還有力導向 explorer 可以拖、縮放、按文件過濾。
5. **標註與輸出**——螢光筆、便條、剪貼簿筆記本（匯出 Markdown）、記憶卡片選一選匯出帶引用的 `.pptx`。

一切存在本機一顆 `data/app.db`。送出去的只有你框的那一塊。

## 架構圖

```
瀏覽器（React 19 + pdf.js 連續捲動）
  拖一個框 ──► rect（fitz 座標：左上原點、y 向下、永不翻 y）
  │   cropThumb() 先把樂觀縮圖塞進側欄（零 round-trip）
  ▼
POST /api/ask（FastAPI，SSE 串流）
  ├─ region.py extract_region()：PyMuPDF 抽「精確文字 + 表格 markdown + 裁切圖」
  ├─ memory.py search()：FTS5 找種子節點 → 圖上最多擴展兩跳 → 有界 memory_context
  ▼
Gemini 2.5 Flash（google-genai，thinking_budget=0 壓低首字延遲）
  │   逐 token SSE 回側欄；使用者中斷也把已生成的部分寫回 DB
  ▼
答案安全存好「之後」（best-effort，失敗絕不擋答題主路徑）
  ├─ extract_memory_candidates()：蒸餾成節點 + 關係（JSON schema 約束輸出）
  ├─ parse_memory_extraction()：把不受信任的模型 JSON 逐欄驗證再入庫
  ▼
SQLite data/app.db（WAL + FTS5，全 app 唯一資料庫）
  ├─ /api/graph  → 力導向圖譜 explorer（graphLayout.ts，零依賴、決定性佈局）
  └─ /api/wiki/{id}/generate → DeepAgents 兩跳探索寫頁（失敗退確定性組頁）
```

## 三個值得偷走的設計

**1. 雙通道送模型：精確文字為準，忠實截圖補版面。**
只送截圖，模型會幻讀文字；只送文字，公式、表格、圖表的版面語意全丟了。Anchor 兩個都送：PyMuPDF 從 PDF 抽出的 `<region_text>` 是 ground truth，同一塊的裁切圖負責版面。`prompts.py` 的共同原則寫得很清楚：文字以 `<region_text>` 為準，殘缺才從圖補齊並標 `[推測]`，掃描檔沒有文字就全靠圖。答案「看得到又讀得準」。

**2. 加強元件一律 best-effort，主路徑永不被拖垮。**
記憶抽取放在「答案存好之後」才跑，抽取失敗只記 log；檢索記憶失敗，照樣用純 region 回答；wiki agent 兩次回空，退到確定性組頁 `_wiki_fallback`；AI storyboard 失敗，退本地編譯器。而且 `format_memory_context` 在 prompt 裡明講：記憶「may guide connections, but they are not evidence and must not override the current PDF region」——當下框住的證據永遠贏過歷史記憶。

**3. 把模型輸出當不受信任的輸入。**
蒸餾記憶時先用 JSON schema 約束 Gemini 輸出，拿回來還要過 `parse_memory_extraction()`：節點上限 20、邊上限 30、kind 白名單、confidence 夾到 [0,1]、edge 兩端必須是這一輪出現過的 key，`user_preference` 更要模型明確標 `explicit_preference=true` 才收——「從單一問題推斷你的偏好」被制度性禁止。壞 JSON？這輪不抽，下輪再來。

## 快速開始（完整步驟見 walkthrough.md）

```bash
cd Anchor_knowledge.ai
uv sync && npm install
npm run build

# .env 放一行：GEMINI_API_KEY=你的金鑰（aistudio.google.com/apikey 免費申請）
set -a; . ./.env; set +a
uv run uvicorn main:app --port 8791
```

開 <http://localhost:8791>，上傳一份 PDF，拖框開問。

跑測試（後端 unittest + 前端 vitest）：

```bash
uv run python -m unittest discover -s tests -t .   # 後端（實測 87 個測試全綠）
npm test                                           # 前端（實測 81 個測試全綠）
```

> Node 22+ 跑 `npm test` 若有 9 個 `localStorage` 相關失敗：新版 Node 內建的全域 `localStorage` 沒開 `--localstorage-file` 時是 `undefined`，會蓋掉 jsdom 的實作。用 `NODE_OPTIONS="--localstorage-file=/tmp/vitest-ls.json" npm test` 即可全綠（詳見 walkthrough 排錯表）。

## 核心教學重點

| 階段 | 重點 | 驗證方式 |
|---|---|---|
| Step 0 | 跑起來：uv + npm 雙棧、`.env` 載入的正確姿勢 | localhost:8791 拖框有串流答案 |
| Step 1 | 用 Cursor 讀懂 codebase：`docs/specs/` 設計文件是最好的地圖 | 能說出一個框從拖到答案經過哪五站 |
| Step 2 | 雙通道抽取：`region.py` 81 行裡的三個實測坑 | 講得出 TEXTFLAGS_TEXT / rotation / dpi 夾取各在防什麼 |
| Step 3 | SSE 串流管線：穩定前綴、中斷寫回、錯誤只能轉 error frame | curl 看得到 SSE frame |
| Step 4 | 記憶蒸餾與兩跳擴展：schema 約束 + 逐欄驗證 + FTS5 | `tests.test_memory` 全綠、圖譜 explorer 有節點 |
| Step 5 | wiki agent 與 fallback 階梯 | 生成一頁 wiki、拔掉金鑰也能出確定性頁 |
| Step 6 | 在 Cursor 裡改造：加第五把 prompt、修 dev 埠不一致 | 前後端測試全綠 |

## 誠實的限制

- **沒有 LICENSE 檔**：repo 未附授權條款（`package.json` 標 `private: true`）。課堂研讀、本機改造沒問題；要再散布或商用，先取得作者授權。
- **dev 埠不一致**：repo README 的開發提示叫你把後端跑在 8791，但 `vite.config.ts` 的 proxy 寫死 `127.0.0.1:8000`。dev 模式後端要跑 8000（或改 proxy）。這是真實的坑，也是 walkthrough 的改造練習之一。
- **每答完一題就多打一次 LLM**：記憶蒸餾是額外一次 structured output 呼叫。Flash 便宜，但不是零成本。
- **檢索是詞面不是語意**：FTS5 BM25（中文切 trigram，失敗退 LIKE），沒有向量檢索。個人規模夠用，語料大了會想念 embedding。
- **單人單機**：一顆 SQLite、一條 `check_same_thread=False` 連線。設計文件明說儲存層已隔離、可換雲端後端，但現況就是個人 sidecar。
- **模型名寫死**：`MODEL = "gemini-2.5-flash"` 一行常數，模型改名要自己換。

> 知道自己的邊界在哪，比看起來什麼都能做更值錢。

---

## 檔案結構

```
project-17-anchor-pdf-ai-reader/   # 本資料夾：教學三件套
├── README.md                      # 這份（規格卡）
├── walkthrough.md                 # 完整逐步教學
└── demo.sh                        # 課堂遙控器（6 幕，全離線唯讀）

../Anchor_knowledge.ai/            # 程式碼在這裡（開源 repo）
├── main.py                        # 全部 /api 路由 + SQLite DDL + SSE 串流（1410 行）
├── region.py                      # extract_region()：文字/表格/裁切圖雙通道（81 行）
├── prompts.py                     # 四把 system prompt：translate/explain/summarize/ask（27 行）
├── memory.py                      # LocalMemoryStore：蒸餾驗證、FTS5、兩跳擴展、wiki 存取（735 行）
├── deck.py                        # 記憶卡片 → storyboard → .pptx 匯出（943 行）
├── src/                           # React 19 + TS 前端（~5100 行，含 vitest 測試）
│   ├── App.tsx / PdfScroll.tsx / PdfPage.tsx   # 三欄佈局、連續捲動、拖框 overlay
│   ├── Chat.tsx / api.ts          # SSE 消費、marked + KaTeX + DOMPurify 渲染
│   ├── MemoryPanel.tsx / GraphExplorer.tsx / WikiView.tsx / WikiGraph.tsx
│   ├── graphLayout.ts             # 零依賴 Fruchterman–Reingold 力導向佈局（決定性）
│   ├── crop.ts                    # 樂觀縮圖：從已渲染 canvas 裁 region
│   └── StrokeLayer.tsx / NoteLayer.tsx / NotebookPanel.tsx / DeckBuilder.tsx
├── scripts/export_deck.mjs        # Node 匯出 .pptx
├── tests/                         # 後端 unittest（10 個檔，含座標地基 4 條 assert）
├── docs/specs/2026-07-15-pdf-region-ask-design.md   # 架構設計定稿（讀懂全案最快入口）
├── docs/plans/                    # 記憶圖譜、card-to-ppt 的 design + implementation 計畫
├── pyproject.toml                 # uv 管理，Python >=3.13
└── package.json / vite.config.ts  # Vite 6 + vitest；/api proxy → 127.0.0.1:8000
```

## 帶走的三句話

1. **Region-first 勝過 whole-PDF chat**——把「你正在盯著的那一塊」原封不動送過去，比把整份文件糊成向量再撈回來，更能回答你卡住的那一句。上下文的精度，比上下文的份量值錢。
2. **雙通道：文字為準、圖補版面**——PDF 內嵌文字是 ground truth，截圖負責公式、表格、版面的語意；缺字才從圖補並標 [推測]。單通道要嘛幻讀、要嘛失明。
3. **加強元件永遠 best-effort**——記憶、wiki agent、AI storyboard 全都有失敗退路，答題主路徑永不被拖垮；而且記憶「可以引導、不是證據」，當下框住的內容永遠優先。

## 授權

repo 未附授權條款（`private: true`，無 LICENSE 檔）。本教學資料夾僅供課程研讀使用；散布或商用前請先取得原作者授權。
