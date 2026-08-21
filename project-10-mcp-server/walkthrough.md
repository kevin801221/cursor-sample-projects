# Walkthrough：在 Cursor 上把 MCP Server 一步一步做出來

> 這份文件帶你從零做出**自己的 MCP Server**——讓 AI 不只能看你的資料，還能主動觸發你設計的「工具」，像多了個聰明的助手。你會學到三件事：怎麼用 Zod 驗證請求、怎麼設計不會污染協定的 stdout、怎麼用 AbortController 處理逾時。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式
>
> 預估 5–7 小時。核心理念：**先驗後接——用 MCP Inspector 逐工具測好再接進 Cursor，否則出問題時分不清是誰的錯。**

---

## 🚦 開始前檢查清單（先做這三件事，做的時候才不會卡）

1. **裝好 MCP Inspector 並跑一次示範工具**——Inspector 是本份教學最重要的除錯工具，第一次用可能要設定，先試過一次之後才知道正常畫面長什麼樣。
2. **在自己的 Cursor 註冊一份測試 MCP server**，看側欄能不能顯示「Connected」——這驗證環境全對，後面實作時直接連接只是重複一次。
3. **把本文件「✅ 預期看到」的三個關鍵畫面逐一瀏覽**（MCP Inspector 回傳 JSON、Zod 驗證失敗、console.log 污染 stdout），知道正常畫面長怎樣，出問題時才判斷得快。

## 🗺️ 學習地圖（建議 5–7 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 第 1 節概念 | 40 分 | 閱讀理解（這是全篇靈魂，顧問與助理的比喻要記起來） |
| 第 2–3 節初始化與寫 Tools | 60 分 | 動手做（程式碼邊寫邊理解意義） |
| 第 4 節寫 Resources | 20 分 | 動手做（快速帶過） |
| 第 5 節 Inspector 測試 | 40 分 | 動手做（**一定要親自試的一幕**：看工具被呼叫的實況） |
| 第 6–7 節接進 Cursor、情境練習 | 50 分 | 動手做（「你寫的工具」在 Cursor 裡被用上） |
| 第 8 節驗收與排錯 | 30 分 | 動手做 + 檢查排錯表 |
| 收尾三句話 | 10 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `./company-mcp-server/`，遙控器 `demo.sh` 就放在這份文件旁邊（`project-10-mcp-server/demo.sh`）。整堂課的指令只有一個：
> `./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕，`./demo.sh reset` 把工單資料還原成課前狀態。
> 11 幕全部離線可跑，除了第一次 `npm install` 之外不需要網路，也不需要任何 API key。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd company-mcp-server && npm install && npm run build`（或直接跑一次 `./demo.sh 1`） | 第一次跑會裝 50 MB 的 `node_modules` 且需要網路；裝完之後 11 幕全離線。當著學生的面等 npm install 是最尷尬的三分鐘 |
| 2 | `./demo.sh reset` | 第 5、6 幕會真的寫進 `data/tickets.json`。不還原的話，第 5 幕回傳的編號就不是講稿上的 TKT-0004，而是 TKT-0007、TKT-0012⋯ 一班比一班大 |
| 3 | 自己先跑一次 `./demo.sh 6` | 它的第一段會**靜止整整 8 秒**。先看過，上台才講得出「這 8 秒就是逾時保護在數秒」，而不是慌著按 Ctrl+C |
| 4 | 把終端機字體調到一頁能看約 40 行，確認滑鼠可以往回捲 | 第 2 幕的 `tools/list` 是完整 74 行（整幕 139 行）。這是為了讓 `create_ticket` 的 inputSchema 真的出現在畫面上，代價就是要捲 |
| 5 | 確認 `node -v` ≥ 20，且 `echo $LANG` 含 UTF-8 | 全篇畫面都是中文；終端機編碼不對會整片變問號，現場沒得救 |
| 6 | 把 `walkthrough.md` 開在第二個視窗，`company-mcp-server/` 用 Cursor 開好 | 每一幕都要配一個原始碼檔投影，臨時找檔案會斷節奏 |
| 7 | 要示範第 11 幕的 Connected 的話，先把 Cursor 完全結束（Cmd+Q）一次 | Cursor 只在啟動時讀 `mcp.json`；沒有完全重啟，側欄不會出現新的 server |

### 放映時間軸

時間軸切成 7 段，一段對上面學習地圖的一列（骨幹合計 250 分鐘），中間插兩次 10 分鐘休息，全長 **4 小時 30 分**。學習地圖寫「建議 5–7 小時」，多出來的就是學生卡關、Q&A 與練習題的緩衝。

**A. 開場故事 + 第 1 節概念（40 分 · 學習地圖第 1 列）**

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:14 | 無（純口述） | — | `walkthrough.md` §🎬 開場故事 | 那張「故事 ↔ 系統」8 列對照表：顧問=LLM、助理=MCP Server、紙條=JSON-RPC、房間裡大聲聊天=`console.log` 污染 stdout | 三個角色 + 一條紅線，全篇比喻的錨點 |
| 0:14–0:32 | 無（純口述） | — | `walkthrough.md` §1.2–§1.6 | Tools／Resources／Prompts 三欄對照表；四個反模式的 ✗／✓ 程式碼並排 | 三鐵律的由來：數量克制、回傳精簡、錯誤可讀 |
| 0:32–0:40 | 第 1 幕 專案骨架與編譯 | `./demo.sh 1` | `company-mcp-server/package.json`、`company-mcp-server/tsconfig.json` | `find` 列出 8 個檔案（含 `src/paths.ts`、`data/tickets.seed.json`）→ 一行 `> tsc` 零錯誤零警告 → `ls` 印出 `dist/index.js`、`dist/paths.js`、`dist/tools/search.js`、`dist/tools/tickets.js`、`dist/resources/tickets-resource.js` | MCP server 就是一支普通的 Node 程式；`"type": "module"` + NodeNext，所以每個 import 都要帶 `.js` |

**B. 第 2–3 節 初始化與寫 Tools（60 分 · 第 2 列）**

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:40–0:52 | 第 2 幕 協定長什麼樣 | `./demo.sh 2` | `src/index.ts` 第 22–70 行 | 青色 `──▶ 送出 REQUEST` 與綠色 `◀── 收到 RESPONSE (147 ms)` 成對出現；initialize 回 `"capabilities": {"tools":{},"resources":{},"prompts":{}}` 與 `"serverInfo": {"name":"company-knowledge-mcp","version":"1.0.0"}`；接著 `tools/list` 完整 74 行，`create_ticket` 的 `priority` enum `low/medium/high` 看得見 | MCP 不是魔法，就是 stdin／stdout 上的 JSON 紙條；Cursor 側欄的 Connected 就是 initialize 成功 |
| 0:52–1:06 | 第 3 幕 呼叫工具 + 分頁 | `./demo.sh 3` | `src/tools/search.ts` 第 49–75 行 | 四次 `tools/call`：`{query:"VPN",limit:3}` → KB-001＋KB-002、`"total": 2`、`"hasMore": false`；`{query:"密碼",tag:"security"}` → KB-003＋KB-002、`"total": 3`、`"hasMore": true`；`query:"工單"` offset 0 → KB-001／KB-004，offset 2 → KB-011／KB-013，兩頁都是 `"total": 5` 且零重複。每則下面都有灰字「── 解出來的內容（把上面那串跳脫字元還原）──」 | 鐵律 2 回傳精簡：只給 id／title／tag／excerpt，excerpt 最多 200 字（KB-001 剛好斷在「三、憑證」） |
| 1:06–1:16 | 第 4 幕 Zod 擋下壞紙條 | `./demo.sh 4` | `src/tools/search.ts` 第 12–21 行、`src/index.ts` 第 72–99 行 | 三個紅標頭 RESPONSE，全部 `"isError": true`，文字分別是「參數不合格，請修正後重試：<br>- query：搜尋字串不能空白」、「- limit：limit 最多 20」、「- description：description 必填，請描述問題與已經試過的做法<br>- priority：priority 只能是 low、medium 或 high」——全中文，一行 stack trace 都沒有 | 第一道防線：模型亂填參數時，工具要用人話退件 |
| 1:16–1:24 | 第 5 幕 建立工單（有副作用） | `./demo.sh 5` | `src/tools/tickets.ts` 第 74–95 行、`data/tickets.json` | 約 155 ms 回 `{"ticketId":"TKT-0004","message":"Ticket TKT-0004 created successfully"}`；當場切到 `data/tickets.json`，檔案從 3 筆變成 4 筆，最後一筆 status 是 `open` | Tools 會真的改變世界，所以 description 裡要寫「先查再開票」 |
| 1:24–1:40 | ⭐ 第 6 幕 外部 API 壞掉時 | `./demo.sh 6` | `src/tools/tickets.ts` 第 101–140 行 | 第一段畫面靜止 8 秒 → 綠標頭顯示 `(8004 ms)`（每次數字略有不同），內容 `{"error":"Ticket API 連線逾時（8 秒）。工單尚未建立，請稍候再試，或檢查 VPN／網路連線。"}`；第二段 154 ms 秒回 `{"error":"Ticket API 回傳 503，工單沒有建立。請確認標題是否重複，或稍後再試一次。"}`；`data/tickets.json` 仍是 4 筆，沒有殘缺工單 | AbortController 逾時保護 + 錯誤可讀：模型看得懂才會換策略，看到 stack trace 只會盲目重試 |

**☕ 休息 1:40–1:50（10 分）**

**C. 第 4 節 寫 Resources（20 分 · 第 3 列）**

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 1:50–2:00 | 第 7 幕 Resource `tickets://all` | `./demo.sh 7` | `src/resources/tickets-resource.ts`、`src/index.ts` 第 104–124 行 | `resources/list` 回一個資源：`"uri": "tickets://all"`、`"name": "公司工單清單"`、`"mimeType": "application/json"`；`resources/read` 解碼後列出 TKT-0001(closed)、TKT-0002(in_progress)、TKT-0003(open)、TKT-0004(open)，每筆**恰好** id／title／status／priority／created_at 五個欄位，沒有 description | Resources 是「給我看現在的狀態」，Tools 是「請做一件事」；清單只給 5 個欄位，不給全文 |
| 2:00–2:10 | 無（讀原始碼） | — | `src/paths.ts`、`src/index.ts` 第 115–124 行 | 把 `dataPath()` 跟 §4.1 講稿裡的 `fs.readFileSync("data/tickets.json")` 並排；示範 `cd / && node /Users/…/company-mcp-server/dist/index.js` 仍然讀得到資料 | 相對路徑是相對「行程的 cwd」，Cursor 啟動 server 時 cwd 不是你的專案 → ENOENT。這跟 `mcp.json` 要絕對路徑是同一條規則 |

**D. 第 5 節 用 Inspector 測試（40 分 · 第 4 列）**

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 2:10–2:22 | ⭐⭐ 第 9 幕 反面教材：污染 stdout | `./demo.sh 9` | `scripts/break-stdout.mjs`、`src/index.ts` 第 176–188 行 | 【壞掉的版本】stdout 第一行 `"[debug] server starting..."` → 紅字 `JSON.parse 失敗 ✗ Unexpected token 'd', "[debug] ser"... is not valid JSON`；【修好的版本】第一行 `{"result":{"protocolVersion":"2024-11-05",…"company-knowledge-mcp"…}}` → 綠字 `JSON.parse 成功 ✔`；兩次的灰字 stderr 都是 `company-knowledge-mcp running on stdio`。接著 `grep -rn 'console.log' src/` 命中 `src/index.ts:4` 與 `src/index.ts:178` 兩行，下面黃字說明「都是註解，沒有任何一行是真正的呼叫」 | 鐵律 3：stdout 唯一合法內容是 JSON-RPC 訊息，除錯訊息一律走 stderr |
| 2:22–2:32 | 第 10 幕 自我檢查 | `./demo.sh 10` | `scripts/check.mjs` | **11 行綠色 ✔**（search／tag 過濾／分頁／三種 Zod 退件／建票寫檔／Resource 5 欄位／逾時人話／503 說明沒建立／src 無 console.log），最後一行綠字「全部檢查通過。data/tickets.json 已還原成原始狀態。」，exit code 0 | 先驗後接（鐵律 1）：接進 Cursor 之前，每條路徑都要有跑得起來的驗證 |
| 2:32–2:50 | 學生動手（不放映） | `cd company-mcp-server && node scripts/inspect.mjs --list`，再自選步驟 | `scripts/inspect.mjs` | 學生自己的終端機印出 9 個可用步驟：`tools`／`search`／`page`／`zod`／`ticket`／`timeout`／`fail`／`resources`／`prompts`，每個都附一行中文說明 | 本課的 MCP Inspector 就是這支 `scripts/inspect.mjs`——全離線、不用 `npx`、不用連網下載 |

**☕ 休息 2:50–3:00（10 分）**

**E. 第 6–7 節 接進 Cursor + 情境練習（50 分 · 第 5 列）**

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 3:00–3:12 | 第 11 幕 接進 Cursor | `./demo.sh 11` | `company-mcp-server/.cursor/mcp.json` | 印出剛寫好的 mcp.json：`"args": ["/Users/…/project-10-mcp-server/company-mcp-server/dist/index.js"]`（這台機器的絕對路徑）、`env` 含 `KNOWLEDGE_API_URL` 與 `DEMO_OFFLINE: "1"`；接著綠字 `✔ JSON 語法合法`、`ls -l dist/index.js` 顯示 9447 bytes；最後是重啟 Cursor 的三步驟與沒 Connected 時的 a→d 排錯順序 | 相對路徑會因為 Cursor 啟動時的工作目錄而失效；絕對路徑才保證找得到 |
| 3:12–3:32 | 學生動手（不放映） | 用 Cursor 開 `company-mcp-server/`，Cmd+Q 完全結束再開 | Cursor → Settings → Features → MCP | 側欄出現 `company-knowledge  Connected`；問 Agent「這個 MCP Server 提供哪些工具和資源？」，它會答出 search_knowledge_base、create_ticket、`tickets://all`、triage_ticket | 全課唯一必須人工確認的一步——協定層前面 10 幕已經驗完了 |
| 3:32–3:42 | 第 8 幕 Prompt `triage_ticket` | `./demo.sh 8` | `src/index.ts` 第 129–171 行 | `prompts/list` 顯示 `triage_ticket` 與兩個參數（complaint `required: true`、priority `required: false`）；`prompts/get` 解碼區塊印出 4 步驟中文指引，第 3 步帶入 `priority "medium"`，最後一行是「鐵律：查得到答案就不要開票——開票是有副作用的動作。」 | Prompts 是「預設路線」：把人的決策流程寫死成一鍵套用，模型才不會一有抱怨就開票 |
| 3:42–3:50 | 情境對話（在 Cursor 裡） | 對 Agent 貼 §7 的那段 Prompt | Cursor Agent 面板 + 工具呼叫側欄 | 問「VPN 連線逾時怎麼辦？」→ 側欄先出現一次 `search_knowledge_base`，查到 KB-001 後 Agent 直接總結解法、**不開票**；換成知識庫沒有的題目，才會看到第二個工具呼叫 `create_ticket` | 你提供工具，Agent 自己決定何時用——這個決策過程就是 MCP 的價值 |

**F. 第 8 節 驗收與排錯（30 分 · 第 6 列）**

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 3:50–4:00 | 第 10 幕（重跑，當驗收表用） | `./demo.sh 10` | `walkthrough.md` §8 驗收清單 | 同樣的 11 行 ✔ 與 exit code 0，逐條對到 §8 的九個核取方塊（build／search／create_ticket／Resource／絕對路徑／Connected／列出工具／無 console.log／先搜後建） | 驗收不是打勾，是跑得出來的證據 |
| 4:00–4:15 | 無（排錯演練） | 學生故意改壞再修 | `walkthrough.md` §9 排錯速查表 | 在 `src/index.ts` 加一行真的 `console.log("hi")` → 重跑 `./demo.sh 9` 兩邊都變 ✗，`./demo.sh 10` 最後一條變 ✘ 且 exit code 非 0；把那行刪掉後恢復 11 行 ✔ | 九成的課後卡關都在 §9 那張表裡；先製造一次故障，學生才記得住徵狀 |
| 4:15–4:20 | 收尾動作 | `./demo.sh reset` | `data/tickets.json`、`data/tickets.seed.json` | 綠字「✔ data/tickets.json 已還原成課前的 3 筆工單（.cursor/mcp.json 保留，第 11 幕會覆寫）。」 | 有副作用的示範，散場前要收乾淨——下一班才跑得出 TKT-0004 |

**G. 收尾三句話（10 分 · 第 7 列）**

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 4:20–4:30 | 無（口述，可回放） | 需要時 `./demo.sh 3`／`9`／`10` | `walkthrough.md` §11 帶走的三句話 | 三句話各配一幕回放：第 1 句（精簡）↔ 第 3 幕的 200 字 excerpt；第 2 句（不准 console.log）↔ 第 9 幕的紅字 ✗；第 3 句（先驗後接）↔ 第 10 幕的 11 行 ✔ | 讓每句結論都掛在一個學生親眼看過的畫面上 |

### ⭐ 全場最值得停下來的一幕

**第 9 幕（`./demo.sh 9`）。** 它是整堂課唯一的「對照組實驗」：同一支 server、同一份 `dist/`、連跑兩次，唯一的差別只是 stdout 多了一行 `[debug] server starting...`，畫面就從紅色的 `JSON.parse 失敗 ✗` 變成綠色的 `JSON.parse 成功 ✔`。學生前面聽了兩小時「不要用 console.log」，這一幕才第一次**親眼看到後果**。

它只跑 2 秒，但請在這裡停 **8–10 分鐘**，而且停在紅字那一段先別往下捲。丟三個問題：

1. 「壞掉的那次，後面的 JSON 其實都正常送出來了——為什麼 client 還是判定這個 server 死了？」（答：協定是串流，第一次 parse 失敗就斷線，不會自己重新對齊。）
2. 「如果那行 `console.log` 是藏在你安裝的第三方套件裡呢？」（答：一樣會壞，而且 `grep -rn 'console.log' src/` 找不到——所以鐵律是「stdout 一律當成唯讀通道」，不是「我的程式碼別印就好」。）
3. 「那 stderr 為什麼安全？」（回頭指畫面：兩次的灰字 `[server stderr] company-knowledge-mcp running on stdio` 都在，兩次都沒事。）

### 🧯 現場翻車備案

| 翻什麼 | 徵狀 | 30 秒內的救援 |
|---|---|---|
| `npm install` 卡住（沒網路／registry 慢） | 第 1 幕停在灰字「第一次跑，先安裝依賴…」不動 | 這正是課前準備第 1 項的理由。現場只能拿預先裝好的 `node_modules`（隨身碟／備援機），或直接跳到第 2 幕開講——其餘 10 幕全離線，不需要網路 |
| 第 5 幕編號對不上講稿 | 回傳 `TKT-0009` 而不是 `TKT-0004` | `./demo.sh reset`（2 秒）再重跑 `./demo.sh 5`。順口補一句「編號會一直往上跳，就是『有副作用』最好的證據」 |
| 第 6 幕被當成當機 | 畫面靜止 8 秒，學生開始交頭接耳 | **別按 Ctrl+C**。橫幅前已有灰字提醒，照著念「這 8 秒就是 AbortController 在數秒」。真的等不了就 Ctrl+C，改跑 `DEMO_TICKET_FAIL=1 node scripts/inspect.mjs fail`，154 ms 秒回 503 那段 |
| 第 2 幕輸出看不完 | 74 行 JSON 一路捲過去，後排看不到 | 改跑不帶變數的 `node scripts/inspect.mjs tools`（回到 34 行截斷版），先講 `search_knowledge_base`；`create_ticket` 的 inputSchema 改投影 `src/index.ts` 第 51–68 行原始碼 |
| Cursor 側欄沒有 Connected | 第 11 幕做完，Settings → MCP 是空的或紅點 | 照第 11 幕畫面最後印出的 a→d 四步：檔案在不在 → 直接 `node dist/index.js` 會不會當場報錯 → 路徑是不是絕對 → 有沒有人偷加 `console.log`。真的救不回來就跑 `./demo.sh 2` 證明協定層是活的，問題在 Cursor 端設定，課後再處理 |
| 編譯錯誤／`dist/` 是舊的 | 任何一幕開頭跳出「TypeScript 編譯失敗」 | `demo.sh` 的 `ensure_build` 已經自動重編過了，所以只要看錯誤第一行：九成是 import 少了 `.js`（本專案是 ESM + NodeNext） |
| 中文變亂碼 | 畫面上的「逾時」變成問號或 `` | 終端機不是 UTF-8。`export LANG=zh_TW.UTF-8` 後重開終端機；來不及就換一個 iTerm2／內建 Terminal 視窗重跑那一幕 |
| 學生自己的機器跑不動 | Node 版本、權限、路徑各種 | 全班改看講師畫面，把 `./demo.sh N` 當錄影帶用，課後照 §9 排錯表補做。「一堂課只有一個遙控器」就是它存在的理由 |

---

## 🎬 開場故事：被鎖在房間裡的超聰明顧問

想像我們有一位超級聰明的顧問，但他被鎖在一間密閉房間裡——他看不到公司的資料庫、看不到 Slack、看不到郵件系統。他唯一能做的就是「講話」。

為了讓他幫公司解決問題，我們幫他請了一位助理。顧問想查知識庫，就在窗戶上貼一張紙條：「請幫我查 VPN 的常見問題」。助理去查檔案櫃，回來也貼一張紙條：「找到三篇文章，總結如下……」。如果助理不懂顧問的意思——例如紙條上沒寫查詢內容——助理會拒絕，貼回來「你的紙條不合格，請寫清楚查什麼」。

這裡有三個角色：顧問（LLM）、助理（MCP server）、紙條的格式規則（協定）。

但有一個大問題：假如我們在房間裡大聲聊天——「哎呀這個查詢有 bug 啦」，聲音會傳出去，混在紙條的內容裡。顧問和助理都會聽到，被打擾。這就是 `console.log` 會做的事——它在本應只有「紙條（JSON）」的通道裡大聲說話，把整個通訊弄壞。

這份教學要教的就是三件事：怎麼設計「紙條」的格式（MCP 協定）、怎麼寫助理的動作（Tools 和 Resources）、以及最重要的——千萬別讓房間裡有閒聊。

這個比喻會貫穿全文，先把對照表記在心裡（後面每個名詞卡都會回扣）：

| 故事 | 系統 |
|---|---|
| 超聰明但被鎖的顧問 | LLM / Cursor Agent |
| 幫他服務的助理 | MCP Server |
| 紙條（文字訊息） | JSON-RPC 協定的訊息 |
| 紙條格式規則 | MCP 協定定義 |
| 檢查紙條格式是否合法的人 | Zod schema 驗證 |
| 在房間裡大聲聊天 | `console.log` 污染 stdout |
| 助理知道他接下來要查哪些檔案櫃 | Tool schema 定義參數 |
| 告訴顧問「這個查詢錯誤」的訊息 | 錯誤回傳時的自然語言說明 |

---

## 0. 課前準備

- Cursor 3.11+、Node.js 20+、npm 或 pnpm
- 編輯器（VS Code / Cursor 內建終端機）
- 對 TypeScript 基本語法的理解

> 🔍 **名詞卡：MCP（Model Context Protocol）**
> 白話：讓 LLM（ChatGPT、Cursor 的 AI）和外部工具溝通的標準「插座」。就像你的手機有 USB-C 插座可以接各種配件，MCP 就是 AI 的 USB-C——接上後 AI 就多了一堆新能力。
> 比喻：便利商店的「叫號系統」。你（AI）點了咖啡，系統給你一張號碼牌；咖啡機（MCP server）根據號碼牌知道要做什麼；做好了再叫號交給你。

> 🔍 **名詞卡：TypeScript**
> 白話：JavaScript 加上「型別檢查」——變數先講好裝什麼（數字？文字？），裝錯編譯就報錯，很多 bug 在執行前就被抓到。

---

## 1. 先懂概念：MCP 協定與 Tool Schema

### 1.1 MCP 是什麼

MCP（Model Context Protocol）是 Anthropic 定義的開放協定，讓 LLM 客戶端（Cursor、Claude 桌面應用、自建應用）與外部 server 溝通。溝通方式有二：

1. **stdio**：server 作為子程序，JSON-RPC 訊息從 stdout/stdin 流動（本份教學重點）
2. **HTTP**：server 監聽 HTTP 埠，REST-like JSON-RPC 端點（進階，本文提到但不深入）

> 🔍 **名詞卡：stdio（標準輸入輸出）**
> 白話：程式的「嘴巴」（stdout 說話）和「耳朵」（stdin 聽話）。正常情況下程式只應該透過嘴巴和耳朵講話，其他聲音都是干擾。

> 🔍 **名詞卡：JSON-RPC**
> 白話：一套用 JSON 格式打包指令的方式，讓程式之間能明確互相呼叫——「請你執行 search_knowledge_base，參數是 {query: "VPN"}」。

### 1.2 MCP 三大能力再說一遍

| 能力 | 定義 | 觸發方式 | 範例 |
|---|---|---|---|
| **Tools** | 模型主動呼叫、會有副作用的動作 | Agent 根據使用者需求決定呼叫 | 建立工單、寄信、刪檔案 |
| **Resources** | 模型可讀取的靜態資料 | 側欄顯示、模型主動拉取 | 工單清單、設定檔、markdown 文件 |
| **Prompts** | 預先寫好的多步驟指引 | 使用者在指令選單選擇 | 「工單分類流程」一鍵套用 |

Tools 是「有副作用的動作」——呼叫後世界會改變（工單被建了、信被寄了）。Resources 是「只讀的資料」——Agent 拉來看就好，不會改動任何東西。Prompts 是「預設路線」——用戶按一個按鈕，一套流程自動跑起來。

本份教學實作重點是 **Tools** 和 **Resources**；**Prompts** 在情境練習時會用到。

### 1.3 Tool Schema — Zod 定義參數的「紙條格式」

Tool 的參數格式由 Zod schema 決定。模型呼叫時必須符合定義，否則 Zod 直接拒絕——這是第一道防線。

```typescript
import { z } from "zod";

const searchSchema = z.object({
  query: z.string().min(1, "搜尋字串不能空白"),
  limit: z.number().int().min(1).max(20).default(10),
  tag: z.enum(["security", "infrastructure", "process"]).optional(),
});
```

> 🔍 **名詞卡：Zod**
> 白話：一個檢查器。你告訴它「紙條上應該寫什麼」（query 是文字、limit 是 1 到 20 的數字），它會自動檢查進來的紙條有沒有符合規則。不符合就拒絕。
> 比喻：銀行的「提款申請表」。表格上寫著「帳號欄位必填、金額不超過一天提領上限」。客人交表時銀行先檢查格式對不對，格式不對直接打回。

重點：
- `.min()`, `.max()` 等驗證器自動擋掉超長或超短的值
- `.default()` 降低模型漏填的機率（不用特別提示才會填）
- `.optional()` 是選填，呼叫方不帶時不報錯
- 驗證失敗時 Zod 丟 ZodError，server 轉換成可讀訊息回傳給模型

### 1.4 重要 — console.log 與協定污染（反模式 1）

stdio server 唯一合法的輸出是 stdout 上的 JSON-RPC 訊息。任何雜訊（包括 `console.log` 的輸出）混進去會直接弄壞協定：

```typescript
// ✗ 錯誤
console.log("server starting...");   // 寫進 stdout，污染協定

// ✓ 正確
console.error("server starting...");  // 寫進 stderr，只有你看得到
```

還記得剛才房間裡大聲聊天的比喻嗎？`console.log` 就是在做那件事。stdout 是「紙條傳遞的窗口」，你在這裡大聲說「啊 bug 來了」，聲音就會混進紙條裡。Cursor 端收到的不再是「純淨的 JSON」，而是「JSON 加上你的碎碎唸」——解析直接爆炸。

**絕對紅線**：建完 server 必須全域搜尋 `console.log`（包括套件裡的），通通改 `console.error`。

### 1.5 回傳精簡與錯誤可讀（反模式 2、3）

常見的差工具設計：

```typescript
// ✗ 差設計：回傳整包外部 API 的原始 JSON（可能 240KB）
return {
  status: "success",
  data: rawApiResponse,  // 整堆欄位模型看不懂
};

// ✓ 好設計：只回傳模型接下來真正需要的欄位
return {
  articles: response.data.map(a => ({
    title: a.title,
    url: a.url,
    category: a.tags[0],
  })),
  total: response.meta.total,
};
```

**錯誤訊息也一樣**：

```typescript
// ✗ 差設計
return {
  error: Error("TypeError: Cannot read property 'items' of undefined..."),
};

// ✓ 好設計
return {
  error: "知識庫 API 連線逾時，請稍候再試。如果持續失敗，請檢查 VPN 連線。",
};
```

> 🔍 **名詞卡：逾時（timeout）**
> 白話：「我要求你 8 秒內回答，超過 8 秒我就放棄」——防止 Agent 傻傻等待一個永遠不會完成的工作。
> 比喻：餐廳點餐說「如果 10 分鐘還沒上菜我就離開」。

模型看不懂 stack trace，只會盲目重試。自然語言說明才能引導模型改變策略。

### 1.6 數量克制（反模式 4）

每個 CRUD 端點都變成一個工具是陷阱。模型會困在「我該呼叫哪一個？」的決策癱瘓。

```typescript
// ✗ 差設計：六個工具
- create_ticket
- read_ticket
- update_ticket
- delete_ticket
- list_all_tickets
- search_tickets

// ✓ 好設計：三個核心動作
- search_knowledge_base（搜尋知識庫）
- create_ticket（建立工單）
- list_tickets（查詢工單清單，改成 Resource 會更精簡）
```

數量越少，模型越能精準判斷何時該用。一個好工具的特徵：單一職責、回傳精簡、錯誤可讀。

> ❓ **想一想**：如果 Tool 回傳了 240KB 的原始 JSON，模型會怎樣？
>
> **答案**：被淹沒在資訊裡，反而找不到重點；或者因為訊息太長被截斷。所以好的 Tool 應該像貼心的書店店員——不是給你整本書庫，而是幫你先挑好最相關的三本。

---

## 2. 階段一：初始化

### 2.1 建立專案骨架

```bash
# 初始化專案
mkdir company-mcp-server && cd company-mcp-server
npm init -y

# 安裝依賴
npm install @modelcontextprotocol/sdk zod
npm install --save-dev typescript @types/node ts-node

# 建立資料夾
mkdir -p src/{tools,resources} data

# 初始化 TypeScript 設定
npx tsc --init
```

編輯 `tsconfig.json`（最少設定）：

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "resolveJsonModule": true
  }
}
```

### 2.2 配置 package.json 腳本

```json
{
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node src/index.js"
  }
}
```

完成後資料夾結構如下：

```
company-mcp-server/
├── src/
│   ├── index.ts
│   ├── tools/
│   ├── resources/
│   └── ...
├── data/
├── dist/                   (build 後產生)
├── package.json
├── tsconfig.json
└── node_modules/
```

寫 MCP server 就像蓋房子。先打樑柱（初始化）、接水電瓦斯（裝依賴），再裝櫃子和家具（寫工具）。順序不能亂。

✅ **預期看到**：`npm init`、安裝完依賴後可以 `npm run build`，終端機印 `tsc` 的執行過程，`dist/` 資料夾產生。

🧯 **卡住的話**：TypeScript 版本不相容時改用 `npx ts-node` 跳過編譯階段直接跑；如果 Node.js 版本太舊會報警告，可以升級或先跳過。

---

## 3. 階段二：寫 Tools（搜尋知識庫 & 建立工單）

### 3.1 Step 1：定義 search_knowledge_base 工具

對 Cursor Agent 說：

> 建立 `src/tools/search.ts`，實作 `search_knowledge_base` 工具。用 Zod 定義參數：query（必填字串，最少 1 字）、limit（選填數字，預設 10，最多 20）、tag（選填，可選 security / infrastructure / process）。邏輯：讀取 `data/knowledge.json`（每筆 {id, title, content, tag, created_at}），依 query 模糊搜尋 title 與 content，若指定 tag 則進一步過濾，依相關度排序後回傳 limit 筆。回傳結果只包含 {id, title, tag, excerpt（content 前 200 字）}。

預期產出代碼重點：

```typescript
// src/tools/search.ts
import { z } from "zod";
import * as fs from "fs";

const searchParamsSchema = z.object({
  query: z.string().min(1, "搜尋字串不能空白"),
  limit: z.number().int().min(1).max(20).default(10),
  tag: z.enum(["security", "infrastructure", "process"]).optional(),
});

type SearchParams = z.infer<typeof searchParamsSchema>;

export async function searchKnowledgeBase(
  params: unknown
): Promise<{ articles: Array<{ id: string; title: string; tag: string; excerpt: string }> }> {
  // 1. Zod 驗證參數
  const validated = searchParamsSchema.parse(params);

  // 2. 讀知識庫
  const knowledgeFile = JSON.parse(
    fs.readFileSync("data/knowledge.json", "utf-8")
  );

  // 3. 搜尋 & 過濾
  let results = knowledgeFile.filter(
    (article: any) =>
      article.title.includes(validated.query) ||
      article.content.includes(validated.query)
  );

  if (validated.tag) {
    results = results.filter((a: any) => a.tag === validated.tag);
  }

  // 4. 回傳精簡版
  return {
    articles: results.slice(0, validated.limit).map((a: any) => ({
      id: a.id,
      title: a.title,
      tag: a.tag,
      excerpt: a.content.slice(0, 200),
    })),
  };
}
```

看第 1 步——Zod 檢查紙條。如果模型傳來的 query 是空字串或 limit 是 100，Zod 會直接拒絕，訊息說「limit 最多 20，你傳 100」。這就是「助理檢查紙條」的工作。

### 3.2 Step 2：定義 create_ticket 工具（加逾時控制）

對 Agent 說：

> 建立 `src/tools/tickets.ts`，實作 `create_ticket` 工具。用 Zod 定義參數：title（必填，1-200 字）、description（必填，1-2000 字）、priority（必填，可選 low / medium / high）。邏輯：呼叫外部 Ticket API（模擬為 POST 到 https://api.tickets.local/create），設定 8 秒 AbortController 逾時。成功時回傳 {ticketId: "TKT-XXXX", message: "Ticket TKT-XXXX created"}；逾時時回傳 {error: "Ticket API timed out after 8 seconds"}；API 錯誤時回傳自然語言說明。

預期產出代碼重點：

```typescript
// src/tools/tickets.ts
import { z } from "zod";

const createTicketSchema = z.object({
  title: z.string().min(1).max(200, "標題最多 200 字"),
  description: z.string().min(1).max(2000, "描述最多 2000 字"),
  priority: z.enum(["low", "medium", "high"]),
});

type CreateTicketParams = z.infer<typeof createTicketSchema>;

export async function createTicket(
  params: unknown
): Promise<any> {
  // 1. Zod 驗證
  const validated = createTicketSchema.parse(params);

  // 2. AbortController 8 秒逾時
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);

  try {
    const response = await fetch("https://api.tickets.local/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(validated),
      signal: controller.signal,
    });

    if (!response.ok) {
      return {
        error: `Ticket API 返回 ${response.status}，請檢查標題是否重複或內容是否有問題。`,
      };
    }

    const data = await response.json();
    return {
      ticketId: data.id,
      message: `Ticket ${data.id} created successfully`,
    };
  } catch (e: any) {
    if (e.name === "AbortError") {
      return {
        error: "Ticket API 連線逾時（8 秒）。請稍候再試，或檢查網路連線。",
      };
    }
    return {
      error: `系統錯誤：${e.message}。請聯繫管理員。`,
    };
  } finally {
    clearTimeout(timeout);
  }
}
```

AbortController 就是「我給你 8 秒鐘回答」的機制。超過 8 秒 fetch 自動中止。為什麼要這樣做？因為如果 API 故障或網路掛掉，Agent 會傻傻等著永遠不會來的答案。有逾時，Agent 反而知道「喔不行，換個辦法」。

### 3.3 Step 3：在 index.ts 註冊 Tools

對 Agent 說：

> 建立 `src/index.ts`，用 @modelcontextprotocol/sdk 初始化 stdio server。註冊上面兩個 tools，Tool 定義要包含 name、description、inputSchema。確保完全沒有任何 console.log。

預期產出代碼重點：

```typescript
// src/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  StdioServerTransport,
} from "@modelcontextprotocol/sdk/server/stdio.js";
import { Tool, TextContent } from "@modelcontextprotocol/sdk/types.js";
import { searchKnowledgeBase } from "./tools/search.js";
import { createTicket } from "./tools/tickets.js";
import { z } from "zod";

const server = new Server({
  name: "company-knowledge-mcp",
  version: "1.0.0",
});

// 註冊 search_knowledge_base
server.setRequestHandler(ListToolsRequestHandler, async () => {
  return {
    tools: [
      {
        name: "search_knowledge_base",
        description:
          "搜尋公司知識庫。可用 tag 過濾：security / infrastructure / process",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "搜尋字串",
            },
            limit: {
              type: "number",
              description: "回傳筆數，預設 10，最多 20",
              default: 10,
            },
            tag: {
              type: "string",
              enum: ["security", "infrastructure", "process"],
              description: "分類篩選（選填）",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "create_ticket",
        description: "建立支援工單",
        inputSchema: {
          type: "object",
          properties: {
            title: { type: "string", description: "工單標題" },
            description: { type: "string", description: "問題描述" },
            priority: {
              type: "string",
              enum: ["low", "medium", "high"],
              description: "優先級",
            },
          },
          required: ["title", "description", "priority"],
        },
      },
    ],
  };
});

// 呼叫工具時的實作
server.setRequestHandler(CallToolRequestHandler, async (request) => {
  try {
    let result;
    if (request.params.name === "search_knowledge_base") {
      result = await searchKnowledgeBase(request.params.arguments);
    } else if (request.params.name === "create_ticket") {
      result = await createTicket(request.params.arguments);
    } else {
      return { content: [{ type: "text", text: "Unknown tool" }], isError: true };
    }

    return {
      content: [
        { type: "text", text: JSON.stringify(result) },
      ],
    };
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `工具執行失敗：${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// 除錯訊息必須用 stderr，不能用 console.log
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("company-knowledge-mcp running on stdio");
}

main().catch(console.error);
```

> 🔍 **名詞卡：server（伺服器）、client（客戶端）**
> 白話：server 是「幫忙做事的人」，client 是「要求的人」。你的 MCP server 是助理，Cursor 是老闆。
> 比喻：計程車駕駛（server）和乘客（client）——乘客下指令「去火車站」，駕駛執行。

✅ **預期看到**：`npm run build` 完成，`dist/index.js` 產生，裡面應該沒有任何 `console.log`。

🧯 **卡住的話**：編譯失敗通常是 import 路徑或 TypeScript 型別問題。先檢查 `src/tools/search.ts` 和 `src/tools/tickets.ts` 是否確實存在，再重新編譯。

---

## 4. 階段三：寫 Resources（工單清單）

### 4.1 實作 tickets://all 資源

對 Agent 說：

> 建立 `src/resources/tickets-resource.ts`，實作 Resource 提供者。Resource URI 為 `tickets://all`，type 為 `text/plain`（或 `application/json`）。讀取 `data/tickets.json`，回傳所有工單清單（只包含 id、title、status、priority、created_at）。

預期產出代碼重點：

```typescript
// src/resources/tickets-resource.ts
import * as fs from "fs";

export async function getTicketsResource(): Promise<string> {
  const ticketsFile = JSON.parse(
    fs.readFileSync("data/tickets.json", "utf-8")
  );
  
  const simplified = ticketsFile.map((t: any) => ({
    id: t.id,
    title: t.title,
    status: t.status,
    priority: t.priority,
    created_at: t.created_at,
  }));

  return JSON.stringify(simplified, null, 2);
}
```

> 🔍 **名詞卡：Resources**
> 白話：「靜態擺在那裡的資訊」，模型可以隨時拉來看。Tools 是「請做一件事」，Resources 是「給我看現在的狀態」。
> 比喻：菜單（Resources）vs 點菜（Tools）。

### 4.2 在 index.ts 註冊 Resource

在 index.ts 新增 ListResourcesRequestHandler：

```typescript
server.setRequestHandler(ListResourcesRequestHandler, async () => {
  return {
    resources: [
      {
        uri: "tickets://all",
        name: "公司工單清單",
        description: "所有已建立的工單",
        mimeType: "application/json",
      },
    ],
  };
});

server.setRequestHandler(ReadResourceRequestHandler, async (request) => {
  if (request.params.uri === "tickets://all") {
    const content = await getTicketsResource();
    return {
      contents: [
        {
          uri: "tickets://all",
          mimeType: "application/json",
          text: content,
        },
      ],
    };
  }
  return { contents: [] };
});
```

重新編譯：

```bash
npm run build
```

---

## 5. 階段四：用 MCP Inspector 測試所有工具

現在輪到最重要的步驟——「先驗後接」。我們用 MCP Inspector 獨立測試每個工具，確認它們真的能工作、Zod 驗證真的擋得住、JSON 輸出沒被污染。之後才接進 Cursor。否則出問題時分不清是工具的錯、還是 Cursor 連接的錯。

### 5.1 用 Inspector 測試

```bash
npm run build
npx mcp-inspector
```

Inspector 開啟後：
- 左側選 `company-knowledge-mcp`（或按「+」新增你的 server）
- 測試 `search_knowledge_base`：輸入 `{ "query": "VPN" }`，應回傳相關文章
- 測試 `create_ticket`：輸入 `{ "title": "Test", "description": "Desc", "priority": "medium" }`，應成功或清楚地說出失敗原因

✅ **預期看到**：

1. **search_knowledge_base 成功呼叫**：Inspector 顯示回傳的 JSON，包含 articles 陣列，每篇文章有 id、title、tag、excerpt（前 200 字）。

2. **參數驗證失敗時的清晰訊息**：輸入 `{ "query": "" }` —— Zod 直接拒絕，訊息說「搜尋字串不能空白」。

3. **逾時或 API 錯誤時的自然語言**：模擬 API 故障時回傳「Ticket API 連線逾時（8 秒）」而不是 stack trace。

4. **tickets://all Resource 可讀取**：側欄顯示 `tickets://all` 可點擊，點擊後看到 JSON 工單清單。

🧯 **卡住的話**：
- **JSON 解析失敗**：表示 stdout 被污染了。第一時間 grep 全專案 `console.log`：
  ```bash
  grep -r "console.log" src/
  ```
  任何地方都改成 `console.error`。
  
- **工具呼叫但沒回傳**：檢查 `data/knowledge.json` 或 `data/tickets.json` 是否存在。

- **回傳格式不符 inputSchema**：檢查 Tool 的 name、description 與呼叫方的名稱完全一致。

> ❓ **想一想**：如果你在工具裡加了一行 `console.log("searching...")`，Inspector 會怎樣？
>
> **答案**：JSON 解析失敗、Inspector 端看到 error。因為「searching...」會混進 stdout，變成「searching...{json}」這種垃圾。

---

## 6. 階段五：接進 Cursor

### 6.1 編譯 TypeScript

```bash
npm run build
# dist/index.js 與所有依賴都已準備好
```

### 6.2 配置 .cursor/mcp.json（重點：絕對路徑）

編輯 `~/.cursor/mcp.json`（macOS/Linux）或 `%APPDATA%\cursor\mcp.json`（Windows）：

```json
{
  "mcpServers": {
    "company-knowledge": {
      "command": "node",
      "args": ["/absolute/path/to/project-10-mcp-server/company-mcp-server/dist/index.js"],
      "env": {
        "KNOWLEDGE_API_URL": "https://api.tickets.local",
        "KNOWLEDGE_API_KEY": "<your-key>"
      }
    }
  }
}
```

**路徑必須是絕對路徑**。查詢方式：

```bash
cd /path/to/project-10-mcp-server/company-mcp-server
pwd
# 把輸出複製到 args 中，例如 /Users/kevin/cursor-class-2/project-10-mcp-server/company-mcp-server
```

路徑一定要絕對。相對路徑會因為「現在在哪個資料夾」而改變，Cursor 啟動時可能在別的位置，結果找不到檔案。絕對路徑就像「從根目錄開始數」，無論在哪都找得到。

### 6.3 重啟 Cursor 並驗證連線

重啟 Cursor 後，側欄應顯示「company-knowledge Connected」。問 Agent：

> 這個 MCP Server 提供哪些工具和資源？

Agent 應列出：
- Tools：search_knowledge_base、create_ticket
- Resources：tickets://all

✅ **預期看到**：側欄顯示 server 名稱與綠色的 Connected 狀態；Agent 能準確列出三個能力。

🧯 **卡住的話**：
1. 檢查路徑是否真的存在：`ls /path/to/dist/index.js`
2. 檢查 JSON 語法：用線上 JSON 驗證器或 `jq` 檢查
3. 試試 `node /path/to/dist/index.js` 看有沒有錯誤
4. 重啟 Cursor
5. 檢查全局搜尋是否有 `console.log` 污染 stdout

---

## 7. 情境：建立工單時處理逾時 ⭐ 一定要親自試的一幕

現在來看你寫的工具在真實使用中怎麼被呼叫。你要問 Agent 一件事——它會主動決定用哪個工具。注意看側欄，工具呼叫會出現在那裡。

**你說**：「VPN 連線逾時怎麼辦？」

**Agent 應**：
1. 自動呼叫 `search_knowledge_base` 查知識庫
2. 若找到答案（如 VPN 連線故障排查指南），回傳答案給你
3. 若找不到，主動呼叫 `create_ticket`，title 自動帶「VPN 連線逾時」

**帶著 Agent 走完流程的 Prompt**：

> 請代我搜尋「VPN 連線逾時」相關的知識庫文章。如果找到答案就用自然語言總結；如果找不到答案，用 create_ticket 建一個 medium 優先級的工單。

**預期產出**：
- 首次呼叫 `search_knowledge_base`
- 若回傳空陣列或內容不符，呼叫 `create_ticket`
- 最後用自然語言告知你

看到了沒？Agent 沒有盲目執行你講的每個指令，而是「思考」：先問知識庫有沒有答案，才決定要不要建新工單。這個決策過程——正是 MCP 的價值。你提供工具，Agent 聰明地選擇何時用。

---

## 8. 驗收清單

- [ ] 建成 TypeScript 專案，`npm run build` 無錯誤
- [ ] 用 MCP Inspector 測試 `search_knowledge_base`：帶 query 與 tag 各測一次
- [ ] 用 MCP Inspector 測試 `create_ticket`：正常與逾時兩種情況
- [ ] `tickets://all` Resource 在 Inspector 能讀取
- [ ] 配置 `.cursor/mcp.json` 用絕對路徑
- [ ] 重啟 Cursor，側欄顯示「Connected」
- [ ] 問 Agent 「列出這個 MCP Server 的工具」，能正確回應
- [ ] 全專案 grep `console.log`，只出現在註釋或已改成 `console.error`
- [ ] 測試情境：「搜尋知識庫，找不到時建工單」，Agent 確實先搜後建

---

## 9. 常見坑排錯速查

多數問題都能從這張對照表快速定位（學生課後卡關，九成在這張表裡）：

| 問題 | 常見原因 | 解法 |
|---|---|---|
| Cursor 看不到 server | `.cursor/mcp.json` 路徑是相對路徑或語法錯誤 | 改成絕對路徑，驗證 JSON 語法 |
| stdout 被污染，JSON 解析失敗 | 用 `console.log` 印除錯訊息 | `grep -r "console.log" src/` 全改 `console.error` |
| Zod schema 不符合 | 模型傳入參數型別不對（如字串傳進 number） | Tool description 更清楚，加 `.coerce` 或 `.default()` 降低漏填 |
| 環境變數沒吃到 | 圖形介面 Cursor 不繼承 shell 環境 | 改在 `.cursor/mcp.json` 的 `env` 欄位指定 |
| `create_ticket` 總是逾時 | 外部 API URL 錯誤或網路問題 | 檢查 `KNOWLEDGE_API_URL`，試試 curl 測試連線 |
| Inspector 連不上 server | TypeScript 編譯失敗或 dist/ 舊版本 | `npm run build` 重新編譯，檢查錯誤日誌 |
| 參數驗證失敗但訊息看不懂 | Zod error 訊息太長或格式不清 | 用 `try-catch` 捕捉 ZodError，轉換成人類語言 |

> ❓ **想一想**：如果 `.cursor/mcp.json` 的路徑寫成相對路徑如 `./dist/index.js`，會怎樣？
>
> **答案**：Cursor 啟動時可能在主資料夾或別的位置，相對路徑會指向錯誤的位置，server 找不到。絕對路徑才能保證不管在哪都找得到。

---

## 10. 動手練習

### 練習 1：幫 search_knowledge_base 加選填 tag 參數（入門，約 25 分）

**目標**：練習 Zod optional 參數與不破壞既有呼叫。

**怎麼做**：
1. 在 Zod schema 加 `tag` 為 `.optional()`
2. 搜尋邏輯依 tag 過濾（有帶 tag 才過濾）
3. 更新 Tool description，說明 tag 可用值
4. 在 MCP Inspector 各測一次帶與不帶

**完成標準**：
- [ ] 不帶 tag 行為不變（回傳所有分類結果）
- [ ] 帶 `tag: "security"` 時只回傳 security 分類
- [ ] 工具說明提到 tag 參數用途

**常見卡點**：
- 忘記在 Zod schema 用 `.optional()`，舊呼叫全失敗（破壞性改動）
- 工具說明沒更新，模型永遠不會主動帶
- tag 大小寫不一致，過濾失敗

---

### 練習 2：幫 create_ticket 加 60 秒防重複機制（中級，約 30 分）

**目標**：練習處理副作用與重試防護。

**怎麼做**：
1. 記錄最近建立的工單標題與時間戳（全域變數可以，示範用）
2. 建立前檢查 60 秒內是否有相同標題（不區分大小寫，trim）
3. 若找到重複，回傳 `isError: true` 與可讀說明
4. 測試：連續呼叫兩次相同標題，第二次應被擋

**完成標準**：
- [ ] 第二次建立相同標題時回傳 isError
- [ ] 錯誤訊息可讀（告訴模型是重複，不是隨機失敗）
- [ ] 超過 60 秒後可再建

---

### 練習 3：用 Inspector 驗證 triage_ticket Prompt 的決策流程（進階，約 25 分）

**目標**：練習測試 Prompt 有沒有真的引導 Agent 做對決策。

**怎麼做**：
1. 定義 `triage_ticket` Prompt：要求 Agent 先呼叫 `search_knowledge_base`，若有結果則回傳答案；若無結果才呼叫 `create_ticket`
2. 準備兩種測資：
   - 情境 A：搜尋到答案的使用者抱怨（應只呼叫 search）
   - 情境 B：找不到答案的使用者抱怨（應先 search 再 create）
3. 在 MCP Inspector 分別套用這個 Prompt，記錄 Agent 實際呼叫的工具順序
4. 驗證兩種路徑都正確

**完成標準**：
- [ ] 有記錄工具呼叫順序
- [ ] 查得到答案時只呼叫 search，不開票
- [ ] 查不到答案時先 search 再 create

---

## 11. 帶走的三句話

> 🎬 **回顧一下畫面**：這三句話各自對應一幕，想再看一次現場證據就回到 [🎬 課堂放映表（講師用）](#-課堂放映表講師用)——
> 第 1 句（回傳精簡）↔ 第 3 幕 `./demo.sh 3` 的 200 字 excerpt；
> 第 2 句（絕不 console.log）↔ 第 9 幕 `./demo.sh 9` 的紅字 `JSON.parse 失敗 ✗`；
> 第 3 句（先驗後接）↔ 第 10 幕 `./demo.sh 10` 的 11 行 ✔。

如果整份教學只能記住三件事，就這三句。

1. **Tools 做事、Resources 查資料、Prompts 教模型組合用法——數量克制、回傳精簡、錯誤可讀**
   - 一個工具只負責一件事，不要六個 CRUD 工具搞得模型暈頭轉向
   - 回傳 240KB 的原始 JSON 不如精簡成 8KB 的重點欄位
   - 錯誤訊息用自然語言（「API 逾時了」），不是 stack trace（「TypeError: undefined is not a function」）

2. **stdio server 絕不能用 console.log，一律改 console.error——stdout 唯一合法輸出是 JSON-RPC 訊息**
   - 任何雜訊混進去會讓 Cursor 端 JSON 解析失敗、server 直接斷線
   - 建完一定要 `grep -r "console.log"` 檢查一遍，第三方套件也要看
   - 這就像那個房間裡大聲聊天的比喻——你的碎碎唸會毀掉紙條傳遞

3. **先驗後接：用 MCP Inspector 逐工具測好再接進 Cursor——否則出問題時分不清是誰的錯**
   - Inspector 是開發階段最有效率的除錯工具
   - 接進 Cursor 前每個工具都要獨立驗證過
   - Zod 驗證、逾時控制、回傳格式全部要測

---

## 參考資料

- MCP 官方文件：https://modelcontextprotocol.io/
- Zod 文件：https://zod.dev/
- Node.js AbortController：https://nodejs.org/api/globals.html#class-abortcontroller
