# Walkthrough：把一個 production 級 MCP Server 掛進 Cursor，並拆解它為什麼會被 AI 自動調用

> 這份文件帶你做兩件事：第一，把 RAG Architect 這個 MCP server 掛進 Cursor，讓 AI 在你描述 RAG 需求時**自動**調用它、回一份點名元件與代價的架構藍圖。第二——也是更重要的——把它拆開，看懂一個「會被 agent 自己找到、自己正確使用」的工具是怎麼設計的。你會親手驗證一件事：**確定性路由 + 可稽核的推導，比讓 LLM 即興回答更值得信任。**
>
> 這是 Project 10（自建 MCP Server）的進階實戰版。Project 10 教你「工具怎麼寫」；這一課教你「工具怎麼設計，才會真的被用」。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先做這五件事，做的當天才不會卡）

1. **裝好 `uv`**：`uv --version` 有輸出（沒有就 `curl -LsSf https://astral.sh/uv/install.sh | sh`）。這個專案的前置需求只有 uv 與 Python 3.10+，**不需要任何 API key**。
2. **先跑一次 `uvx` 冷啟動**：`uvx` 第一次從 git 解析套件要下載、建環境，可能 1–3 分鐘；之後有快取秒開。課前先在自己機器跑一遍，上課時 Cursor 掛載才不會顯示連線逾時。
3. **本地 clone 一份 repo 並跑過測試**：`cd rag-architect-mcp && uv sync && uv run python test_rag_architect.py`，確認結尾是 `0 failure(s)`。demo.sh 的每一幕都在這個 repo 上放映。
4. **在 Cursor 裡試調用一次**：掛好 MCP 後，問一句「我們有數千頁的法律合約，條款跨頁引用多，資料絕對不能上雲，RAG 要怎麼設計」，確認 AI 會自動叫 `design_rag_architecture`。
5. **看過本文件的每個「✅ 預期看到」**——知道正常畫面長什麼樣，才判斷得出「這是正常的」還是「翻車了」。

## 🗺️ 學習地圖（建議 2.5–3 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 名詞卡 | 30 分 | 閱讀理解（這是全課靈魂，慢慢看） |
| Step 0 環境 + 跑測試 | 15 分 | 動手做（uv sync、22 項檢查全過） |
| Step 1 掛進 Cursor | 15 分 | 動手做（.cursor/mcp.json、看到工具出現） |
| Step 2 三段使用者旅程 | 25 分 | 動手做（自動調用、缺一題問一題、反駁 = slot 判錯） |
| Step 3 讀懂確定性路由 | 25 分 | 在 Cursor 裡讀程式碼（router.py 決策矩陣） |
| Step 4 讀懂 slot 抽取 | 20 分 | 在 Cursor 裡讀程式碼（session.py fail-safe） |
| Step 5 自動調用的四道機制 | 20 分 | 閱讀理解 + 對照 server.py |
| Step 6 改一次、測一次 | 20 分 | 動手做（加詞表、跑測試、指到本地 checkout） |
| 收尾 + 思考題 | 10 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `../rag-architect-mcp/`（與 `project-15-rag-architect-mcp/` 同層），遙控器是 `./demo.sh`（位於 `project-15-rag-architect-mcp/` 根目錄）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 六幕全部離線、唯讀、秒出——不起 server、不連網，展示的都是 repo 真實檔案。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd rag-architect-mcp && uv sync && uv run python test_rag_architect.py` | 確認 22 項檢查全過，Step 0 現場示範不翻車 |
| 2 | 在自己的 Cursor 掛好 `.cursor/mcp.json`，問一次法律合約題 | uvx 冷啟動要下載，先觸發快取；並確認自動調用真的發生 |
| 3 | 跑一遍 `./demo.sh` 和每一幕 | 確認遙控器輸出正常，投影字夠大 |

### 放映時間軸

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:30 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §名詞卡 | 裝潢估價單比喻、六種架構決策矩陣 | 為什麼「憑記憶答 RAG」會給你 2023 年的答案 |
| 0:30–0:45 | 第 1 幕：一行掛進 Cursor | `./demo.sh 1` | `rag-architect-mcp/.cursor/mcp.json` | uvx 設定物件 + 各家 client 放哪的對照表 | MCP 掛載：同一個物件到處能用，免 key 免 clone |
| 0:45–1:15 | 第 2 幕：確定性路由 ⭐ | `./demo.sh 2` | `rag_architect/router.py` | `select_architecture` 的決策矩陣：型態→規模→結構 | 純函式路由 vs LLM 即興回答；可稽核 = 可信任 |
| 1:15–1:35 | 第 3 幕：fail-safe 抽取 ⭐ | `./demo.sh 3` | `rag_architect/session.py` | `_NEGATED_CLOUD` regex 與否定優先邏輯 | 「不可以上雲」包含「可以上雲」——隱私要錯在嚴格側 |
| 1:35–2:00 | 第 4 幕：tool schema 設計 | `./demo.sh 4` | `rag_architect/server.py` | 四段式 description、無狀態全選填的簽名 | 工具會不會被自動調用，是 description 和形狀決定的 |
| 2:00–2:20 | 第 5 幕：skill 與 /rag | `./demo.sh 5` | `skills/rag-architect/SKILL.md` | skill 的觸發條件 frontmatter + /rag 指令內容 | MCP 給工具，skill 教判斷力；兩者分工 |
| 2:20–2:40 | 第 6 幕：測試即 bug 清單 | `./demo.sh 6` | `test_rag_architect.py` | 22 個測試名——每個名字就是一個出過的 bug | 回歸測試的正確寫法：每項對應一次真實翻車 |

---

## 🎬 開場故事：網紅裝潢文 vs 設計師估價單

想像你要裝潢一間老公寓，有兩種找答案的方式。

**第一種：滑網紅裝潢文。**「2023 年最流行北歐風！全室木紋、開放式廚房、無主燈設計！」文章寫得漂亮，但它不知道你家是 30 年老公寓、管線要重拉、樑柱不能動。你照做，做到一半發現預算爆掉、廚房排煙根本不合法規。——這就是**問 LLM「RAG 怎麼做」憑記憶得到的答案**：語意切塊、pgvector、加 reranker——2023 年的流行款，不看你的語料長什麼樣。

**第二種：找一位老派設計師。**他不跟你聊風格，先問四件事：**幾坪？格局怎樣？預算上限？要不要住人？**四題答完，他給你一張估價單——上面不寫「北歐風」，寫的是：「這面牆打掉要補結構費 8 萬」「這種管線只能用明管，你要接受它露出來」「完工驗收看這三個檢測項目」。而且最關鍵的：**同樣的四個答案，他永遠開同一張估價單。**不會因為這週流行什麼、心情好不好就改。你不同意的時候，他不跟你吵結論，他問：「是不是坪數我記錯了？」

RAG Architect 就是那位老派設計師：

| 裝潢估價單 | RAG Architect |
|---|---|
| 四個問題：坪數、格局、預算、住人 | 四個 slots：data_volume、data_complexity、privacy_boundary、domain |
| 缺一題就問一題，不用猜的 | `NEEDS_INPUT` + 剛好一個 next_question |
| 點名建材，不是講風格 | 點名元件：Qdrant、bge-m3、LightRAG，不是「用個向量庫」 |
| 「打掉這面牆要補結構費」 | tradeoffs：「圖是一次 schema 承諾，ontology 一改就要重建索引」 |
| 驗收檢測項目 | evaluation_metrics：ragas_faithfulness、multi_hop_recall |
| 同樣四個答案 = 同一張估價單 | 確定性路由：同樣 slots 永遠同一個架構 |
| 不同意時查「哪一題記錯了」 | 反駁 = 某個 slot 判錯了，不是跟結論吵架 |

這個比喻會貫穿全課。記住一件事：**估價單值得信任，不是因為設計師聰明，是因為他的推導你查得到。**

---

## 🔍 名詞卡（十四個術語的白話解釋）

### 1. MCP（Model Context Protocol）

> 白話：讓 AI 能呼叫外部工具的開放協議。Cursor、Claude Code、Claude Desktop 都是 MCP client；你寫的 server 提供工具，client 裡的 AI 決定何時呼叫。
> 為什麼重要：這是「AI 只能講話」和「AI 能動手查、動手算」的分界線。本課的一切都建立在它上面。

### 2. MCP server / client

> 白話：server 是「提供工具的一方」（本課的 rag-architect-mcp），client 是「掛載工具、讓 AI 使用的一方」（Cursor）。一個 client 可以掛很多 server。
> 為什麼重要：分清楚誰是誰，才知道設定檔要放在哪一邊（答案：client 那邊，`.cursor/mcp.json`）。

### 3. stdio（標準輸入輸出傳輸）

> 白話：client 把 server 當子行程啟動，兩邊用 stdin/stdout 傳 JSON 訊息。沒有埠號、沒有網址。
> 為什麼重要：這就是為什麼設定檔裡只有 `command` 和 `args`——Cursor 負責把行程拉起來。

### 4. uvx

> 白話：uv 的「免安裝直接跑」指令。`uvx --from git+https://github.com/... rag-architect-mcp` 會從 git 解析套件、建好隔離環境、快取起來、直接執行。
> 為什麼重要：使用者不用 clone、不用填絕對路徑——`client-configs/README.md` 講了一個教訓：舊版每個 client 一個資料夾，每個都寫死作者機器上的絕對路徑，「在作者以外的每一台機器上都是錯的」。

### 5. FastMCP

> 白話：官方 `mcp` 套件裡的高階框架。`@mcp.tool(...)` 裝飾一個 Python 函式，它就變成 MCP 工具；型別注解自動變成 schema。
> 為什麼重要：本課 server 的兩個工具總共就是兩個函式。框架把協議細節收走，你的力氣花在 description 和工具形狀上。

### 6. Slot（欄位）

> 白話：決定架構的四個必填事實：語料規模、資料複雜度、隱私邊界、領域。像設計師的四個問題。
> 為什麼重要：整個 server 的輸入就這四件事 + 三個選填提示（precision / latency / entity_density）。輸入空間有限，輸出才可能確定。

### 7. 確定性路由（Deterministic Routing）

> 白話：`router.py` 是純函式——同樣的 slots 進去，永遠同一個架構出來。無 I/O、無網路、無隨機。
> 為什麼重要：這是與「讓 LLM 即興回答」的本質差異。LLM 的答案不可重現、不可稽核；純函式的答案你可以逐行指出「為什麼是這個」。

### 8. Fail-safe（失效安全）

> 白話：不確定時，往安全的那一邊倒。隱私抽取拿不準就回 `local_only`（最嚴格），絕不把「不可以上雲」讀成「可以上雲」。
> 為什麼重要：隱私判反的代價不對稱——多嚴格一點只是多花點自架功夫，太寬鬆是資料外洩。

### 9. NEEDS_INPUT / COMPLETED / ERROR（三態回應）

> 白話：工具的回覆狀態。缺欄位回 `NEEDS_INPUT` + 剛好一個問題；齊了回 `COMPLETED` + 藍圖；真的壞了才回 `ERROR`。
> 為什麼重要：舊版 crash 時回 `IN_PROGRESS`，agent 讀起來是「繼續問使用者問題」，於是永遠迴圈。狀態語意設計錯，agent 的行為就錯。

### 10. Tool description（工具描述）

> 白話：寫給 AI 看的工具說明書。Anthropic 的指引：這是決定工具會不會被選中**最重要**的因素。
> 為什麼重要：本課的 description 是四段式範本——回傳什麼（講具體）、何時該用（用使用者真正會打的字）、怎麼呼叫、何時**不該**用。

### 11. Server instructions

> 白話：FastMCP 的 `instructions=` 參數，會進 MCP 的 `InitializeResult`，Claude Code 每個 session 注入成 system prompt 的一段。
> 為什麼重要：這是最便宜的自動調用槓桿——工具還沒被呼叫，觸發條件就已經在 context 裡。注意：Claude Desktop 會存這欄位但不讀它，所以重量還是在 tool description 上。

### 12. Skill

> 白話：教 AI「拿到工具結果之後該怎麼用」的文件。MCP 工具說「有一份藍圖可以拿」，skill 說「拿到後：跑 research queries、呈現取捨而不是倒 JSON、把反駁當 slot 判錯」。
> 為什麼重要：工具給能力，skill 給判斷力。而且 skill 的 description 刻意只寫觸發條件、不摘要流程——實測發現一旦摘要了流程，Claude 就照摘要做、跳過不讀本文。

### 13. Research plan（研究計畫）

> 白話：`COMPLETED` 回應裡附的一組搜尋查詢 + 一段指示，讓**呼叫端 agent 用自己的搜尋工具**去跑。Server 自己只有 arXiv 保底（免 key、最多 5 篇）。
> 為什麼重要：這是漂亮的職責分工——你的 coding agent 本來就有比 server 能內建的任何東西都好的搜尋工具。指示裡甚至明講：「如果現行證據支持，就去反駁這份藍圖」。

### 14. CAG（Prompt-Cached Long Context）

> 白話：語料夠小（100 頁以下，或幾百頁且不要求高精準）就**完全跳過檢索**——prompt caching 讓每次查詢重讀整份語料變便宜。決策矩陣六個分支之一。
> 為什麼重要：「你根本不需要 RAG」也是一種 RAG 架構建議——而且藍圖會同時警告你：在非字面比對的基準上，多數模型 32K token 就掉到短文脈分數的一半以下，1M context window 不是跳過檢索的許可證。

---

## Step 0：環境準備與 22 項檢查

### 0-1 取得程式碼、同步環境

```bash
cd rag-architect-mcp    # 課程 repo 同層已附；或 git clone https://github.com/kevin801221/rag-architect-mcp
uv sync
```

✅ **預期看到**：uv 建好 `.venv`，唯一的執行期依賴是 `mcp[cli]`。對照 `pyproject.toml`：`dependencies = ["mcp[cli]>=1.6.0"]`——只有這一行。session、router、research 全部只用標準函式庫（`re`、`urllib`、`xml.etree`）。

> ❓ **想一想**：一個做「架構諮詢」的 server，為什麼刻意只有一個依賴、不裝 LLM SDK？
>
> **答案**：因為路由是純函式，不需要 LLM。沒有 LLM 依賴 = 沒有 API key = 任何人 `uvx` 一行就能跑 = 沒有「金鑰過期」這種課堂翻車點。依賴越少，能壞的東西越少。

### 0-2 跑測試（不連網、不需要 pytest）

```bash
uv run python test_rag_architect.py
```

✅ **預期看到**：22 行 `  ok  test_...`，結尾一行：

```
0 failure(s)
```

注意測試檔開頭這行：`os.environ.setdefault("RAG_ARCHITECT_NO_NETWORK", "1")`——網路被關掉，路由在隔離中被驗證。**路由不需要網路就能測，正是「決策不依賴搜尋」的證明。**

🧯 **卡住的話**：
- `ModuleNotFoundError: No module named 'mcp'` → 沒跑 `uv sync`，或用了系統 Python（要用 `uv run`）
- Python 版本錯誤 → 需要 3.10+，`uv python install 3.12` 後重跑 `uv sync`

### 0-3 手動起一次 server（看它真的會動）

```bash
uv run rag-architect-mcp
```

✅ **預期看到**：游標停住、沒有輸出——**這是正常的**。stdio server 在等 client 從 stdin 送 JSON 訊息，它不是 HTTP server、沒有埠號。按 `Ctrl+C` 結束。之後都交給 Cursor 拉起行程，你不用自己跑這條。

---

## Step 1：掛進 Cursor

### 1-1 兩種掛法：專案層 vs 全域

MCP 是掛在 **client** 上的。Cursor 讀兩個位置：

| 位置 | 檔案 | 適合 |
|---|---|---|
| 專案層 | `<你的專案>/.cursor/mcp.json` | 這個工具只在某專案用；設定跟著 repo 進版控 |
| 全域 | `~/.cursor/mcp.json` | 到處都要用（架構諮詢工具很適合全域） |

內容是同一個物件（取自 `client-configs/mcp.json`，一字不差）：

```json
{
  "mcpServers": {
    "rag-architect": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/kevin801221/rag-architect-mcp", "rag-architect-mcp"]
    }
  }
}
```

**rag-architect-mcp 這個 repo 本身已內建 `.cursor/mcp.json`**——用 Cursor 直接打開這個 repo，工具開箱即用。要鎖版本就在 git URL 後面加 ref：`git+https://github.com/kevin801221/rag-architect-mcp@v0.2.1`。

### 1-2 確認掛載成功

打開 Cursor Settings → 找到 MCP 區塊。

✅ **預期看到**：`rag-architect` 出現、狀態是綠燈／enabled，展開後看到**兩個工具**：`design_rag_architecture` 和 `rag_consultant`。

🧯 **卡住的話**：
- 一直轉圈或紅燈 → uvx 第一次冷啟動要下載（1–3 分鐘）；先在終端機手動跑一次 `uvx --from git+https://github.com/kevin801221/rag-architect-mcp rag-architect-mcp` 觸發快取，跑到停住（等待 stdin）就是成功，`Ctrl+C` 後回 Cursor 重載 MCP
- `command not found: uvx` → uv 沒裝或不在 PATH；GUI 啟動的 Cursor 可能讀不到 shell 的 PATH，把 `command` 改成 uvx 的絕對路徑（`which uvx` 查）
- JSON 寫錯 → 少逗號、多逗號最常見，貼回 `client-configs/mcp.json` 的原文

### 1-3 其他 client 放哪（自學對照）

同一個物件到處能用——這正是 `client-configs/README.md` 的重點：舊版每個 client 一個資料夾、每個都寫死絕對路徑，「在作者以外的每一台機器上都是錯的」；現在一份 `mcp.json` 通吃：

| Client | 放在哪 |
|---|---|
| Cursor | `.cursor/mcp.json`（專案）或 `~/.cursor/mcp.json`（全域） |
| Claude Code | `.mcp.json`（專案）或 `claude mcp add-json` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Gemini CLI | `.gemini/settings.json` 或 `~/.gemini/settings.json` |
| Codex | `~/.codex/config.toml`（TOML 格式，見 repo README） |

---

## Step 2：三段使用者旅程（在 Cursor 裡實測）

沒有人會打「請使用 RAG 工具」。他們只會描述一個問題。以下三段照 `README_zh.md` 的真實輸出重演，你要在 Cursor 的對話框逐段實測。

### 2-1 旅程一：AI 已經知道夠多了

在 Cursor 對話框輸入（不要提任何工具名）：

> 我們有數千頁的法律合約，條款之間跨頁引用很多，資料絕對不能上雲。RAG 要怎麼設計？

✅ **預期看到**：AI **自動**呼叫 `design_rag_architecture`，把你的話原封不動當 `requirements` 傳進去。工具回 `COMPLETED`，collected_slots 是：

```jsonc
{
  "data_volume": "thousands_pages",
  "data_complexity": "cross_page_relations",
  "privacy_boundary": "local_only",     // ← 讀的是「絕對不能上雲」，不是「可以上雲」
  "domain": "legal"
}
```

推薦架構 **Graph-Augmented RAG**，AI 的回答裡有元件表（LightRAG／LazyGraphRAG、Kuzu 或自架 Neo4j、bge-reranker-v2-m3、vLLM 開源權重）和代價（「圖是一次 schema 承諾」）。

**注意 AI 沒有說的東西**：沒有 Cohere reranker、沒有任何託管向量服務。`privacy_boundary=local_only` 讓它們在藍圖裡**根本不可達**——所以它們從來沒有進入對話。這就是路由層做隱私（結構性保證）和 prompt 裡拜託 AI「請注意隱私」（軟性期望）的差別。

🧯 **卡住的話**：AI 憑記憶回答、沒調用工具 → 見排錯速查表「工具沒被自動調用」列。

### 2-2 旅程二：缺一題，就問一題

> 我們有五千頁的掃描財報 PDF，很多表格，只能地端。

✅ **預期看到**：工具回 `NEEDS_INPUT`，`missing_slots: ["domain"]`，AI 轉頭問你**一個**問題：「這是給誰用的——金融、製造、還是一般企業知識？」你答「金融」，AI 第二次（也是最後一次）呼叫，回 **Layout-Aware Hybrid Retrieval**：原生數位表格走 docling → hybrid index → cross-encoder，掃描件與圖表走 ColQwen2.5 視覺 late-interaction、**完全不做 OCR**。

> ❓ **想一想**：「財報」看起來明明就是金融，工具為什麼不自己猜？
>
> **答案**：製造業看供應商財報、銀行看申報文件，recall/precision 的取捨完全不同。而且 server 的 tool description 明講：「Do not guess slot values to avoid the question」——猜錯 `privacy_boundary` 的設計會外洩資料，猜錯 `data_volume` 的設計會貴 10 倍。**問一題的成本遠低於猜錯的成本。**

### 2-3 旅程三：反駁（全課最重要的一段）

接著上一段說：

> 等等，那些財報其實不是 PDF，是我們 Postgres 裡的結構化表。使用者要問的是「Q3 各區營收加總」。

✅ **預期看到**：AI **不會捍衛**上一個答案。它修正 slot（`data_complexity: charts_tables → structured_records`），重新呼叫，架構整個換成 **Text-to-SQL Structured Retrieval**——因為沒有任何向量索引算得出「Q3 各區營收加總」，它只能檢索到**提到**營收的段落。並且 tradeoffs 裡有一條安全紅線：生成的 SQL 必須沙箱化——唯讀角色、statement timeout、row limit。

**四個 slot 有三個沒變，一個變了，架構整個換掉——而且換的理由你指得出來。**這就是確定性路由對「反駁」的意義：使用者的不同意，幾乎永遠是某個 slot 值判錯了，而不是結論錯了。查 slot，不吵結論。

---

## Step 3：讀懂確定性路由（router.py）

現在把黑盒子拆開。在 Cursor 裡打開 `rag_architect/router.py`，或直接問 AI：

> 「打開 rag_architect/router.py，解釋 select_architecture 的分支順序：為什麼 source_code 和 structured_records 排在最前面，語料大小排第二，cross_page_relations 排第三？」

### 3-1 決策矩陣：先看型態，再看規模，最後才看結構

`select_architecture()`（router.py 第 99 行起）的分支順序本身就是一堂課：

| 順位 | 條件 | 架構 | 為什麼在這個位置 |
|---|---|---|---|
| 1 | `source_code` | Code RAG (AST + Agentic Search) | 向量相似度對程式碼是**錯的檢索原語**——embedding 切塊會把 function 跟它的呼叫者切開。型態先於一切 |
| 2 | `structured_records` | Text-to-SQL | 沒有任何向量索引算得出「各季營收加總」。同上，型態先於一切 |
| 3 | 塞得進 context（`under_100_pages`，或 `hundreds_pages` 且不要求高精準） | Prompt-Cached Long Context (CAG) | 塞得進 cached context window 的語料，索引是純營運成本、零 recall 收益 |
| 4 | `charts_tables` | Layout-Aware Hybrid Retrieval | 表格的意義在幾何排版裡，線性文字抽取會摧毀它 |
| 5 | `cross_page_relations` | Graph-Augmented RAG | 跨頁證據常常沒有共同詞彙——單向量相似度剛好漏掉的 case |
| 6 | 其餘全部 | Contextual Retrieval + Reranking | 主力打法：contextual embeddings + contextual BM25 + cross-encoder |

> ❓ **想一想**：50 頁的醫療語料、跨頁關係很多——會被路由到 GraphRAG 嗎？
>
> **答案**：不會，是 CAG。因為「塞得進 context」的判斷在 `cross_page_relations` 之前——50 頁語料蓋知識圖譜是純燒錢。這正是 `test_small_corpus_skips_retrieval_infrastructure` 測試守著的行為：「A 50-page medical corpus must not build a knowledge graph.」——而這條測試對應一個真的出過的 bug。

### 3-2 元件由 privacy_boundary 決定（_stack 函式）

看 `_stack()`（router.py 第 47 行起）：`local_only` 回傳 bge-m3、Qdrant 自架、Kuzu、vLLM——**沒有任何託管服務**；`compliant_cloud_ok` 才有 voyage-3、Cohere Rerank 3.5、Neo4j AuraDB。這不是「建議你別用雲端」，是雲端選項**在資料結構層就不存在**。

### 3-3 Overlay：加強元件不能靜悄悄變貴

`precision_requirement=high` **且** `latency_requirement != low` 時，才追加自我反思的 retrieve → grade → retry 迴圈（LangGraph）。它每次查詢多花好幾秒——所以絕不會被靜悄悄加進對延遲敏感的設計。對應測試：`test_agentic_overlay_is_gated_on_precision_and_latency`。

### 3-4 研究只補引用，永遠不動決策

`build_blueprint()` 先路由、再抓 arXiv 引用；抓引用失敗時只會多一則 `research_note`，**架構完全不受影響**。對照 `research.py` 裡 fetch 例外分支上的註解：「research is decorative, never fatal」。這是「會變的」（文獻）和「不准變的」（決策）的分層。

---

## Step 4：讀懂 slot 抽取（session.py）

在 Cursor 裡問：

> 「打開 rag_architect/session.py，解釋 _NEGATED_CLOUD 這個 regex 在防什麼 bug？為什麼註解說『不可以上雲』包含『可以上雲』？」

### 4-1 Fail-safe 的否定偵測

`session.py` 第 78 行附近：

```python
# "不可以上雲" contains "可以上雲". A privacy router that reads the negated form
# as consent is worse than one that refuses to answer, so negation is detected
# first and resolves to the strict boundary.
_NEGATED_CLOUD = re.compile(...)
```

抽取順序是鐵律：**否定先偵測 → 任何地端訊號壓過同時出現的雲端字眼 → 不確定回 local_only。**「compliant cloud but data must stay local only」這種兩邊都提到的句子，一律判 `local_only`（對應測試 `test_local_wins_over_cloud_when_both_mentioned`）。

### 4-2 數字分桶與邊界

`_extract_data_volume` 把「250 pages」正確分到 `hundreds_pages`——舊版曾把它分到 `thousands_pages`（測試 `test_page_counts_bucket_on_the_right_boundaries` 就是那次翻車的紀念碑）。`_normalize` 還先把「1,000,000」的千分位逗號拆掉再解析。

### 4-3 Domain 用加權，不用先到先得

`_extract_domain` 對每個領域算命中的關鍵字**數量**再取最高分——否則「healthcare records for our legal team」會照 dict 插入順序亂判。另外兩個真實教訓寫在詞表註解裡：`compliance` 單獨出現多半是 SOC2/GDPR 而不是法律領域；掃描發票是版面問題、Postgres 裡的發票是 SQL 問題，所以 `invoices` 刻意**不在** `structured_records` 的詞表裡。

> ❓ **想一想**：這套抽取只是關鍵字比對，講法不在詞表裡就抽不到。這算不算缺陷？
>
> **答案**：是限制，但有接手設計：抽不到就回 `NEEDS_INPUT` 問使用者，而不是亂猜。而且真正的 NLU 其實是**呼叫端的 LLM** 在做——agent 讀完對話後可以直接明確傳 slot 參數（明確傳入會覆蓋抽取結果）。詞表只是讓「使用者的原話直傳」也能動的保底。分層之後，每一層都可以簡單。

---

## Step 5：自動調用的四道機制（server.py + skill）

「使用者不應該需要說『用那個 RAG 工具』。」這一步讀懂四道互相獨立的機制，由便宜到昂貴——任何一道被拿掉，其他三道還是能運作。在 Cursor 裡問：

> 「打開 rag_architect/server.py，比較 DESIGN_DESCRIPTION 和 CONSULTANT_DESCRIPTION 的寫法。為什麼前者要寫『何時不該用』？為什麼後者要叫 agent 去用另一個工具？」

### 5-1 Server instructions（每個 session 都在 context 裡）

`server.py` 第 23 行起的 `SERVER_INSTRUCTIONS`：點名工具、列出**中英文**觸發語句（「設計 RAG 架構」「向量資料庫選哪個」「文件問答系統怎麼做」）、明講「Never invent a session id」。FastMCP 把它塞進 `InitializeResult`，Claude Code 每個 session 注入。這是槓桿最大的一根——而舊版把它留空。

### 5-2 Tool description（唯一每個 client 都會讀的東西）

`DESIGN_DESCRIPTION` 四段式，順序即優先級：

1. **回傳什麼**，講具體——「chunker, embedding model, vector or graph store, reranker, generator, tradeoffs, metrics」，不是「提供 RAG 諮詢」
2. **何時該用**，用使用者真正會打的字——「which vector database」「do I need GraphRAG」「why does my retrieval return garbage」
3. **怎麼呼叫**——包括「缺欄位回一個問題而不是報錯」
4. **何時不該用**——寫 RAG 程式碼、debug 現有 pipeline、解釋 embedding 是什麼

第 4 段跟前 3 段一樣重要：工具被**過度**調用，和不被調用一樣是失敗。

### 5-3 工具形狀（悄悄扼殺自動調用的地方）

對照兩個工具的簽名：

```python
design_rag_architecture(requirements="", data_volume="", data_complexity="", privacy_boundary="", domain="")
rag_consultant(session_id, user_message)
```

前者：無狀態、全選填、一次呼叫。後者：agent 得憑空捏一個 session_id、自己管理四輪狀態——**agent 會迴避這種工具**。`rag_consultant` 保留給真的需要逐題訪談的對話產品，而它的 description 直接叫 coding agent 去用另一個。名字也是形狀的一部分：動詞片語 `design_rag_architecture` 對應使用者會打的字，名詞 `rag_consultant` 對應不到。

### 5-4 Skill（教判斷力，不只是觸發條件）

`skills/rag-architect/SKILL.md` 教的是拿到藍圖**之後**的事：跑 research queries、呈現取捨而不是倒 JSON、把反駁當 slot 判錯。它的 frontmatter 只寫觸發條件、刻意不摘要流程——實測顯示描述裡一旦摘要了流程，Claude 就照摘要做、跳過不讀本文。

**Cursor 使用者注意**：skill 與 `/rag` 指令（`commands/rag.md`）是 Claude Code plugin 機制才有的。Cursor 掛 MCP 拿到的是兩個工具 + 它們的 description——已足夠觸發自動調用。想在 Cursor 得到等價的「判斷力」，可以把 SKILL.md 的 Procedure 段落改寫成**你自己專案**的 Cursor rule（`.cursor/rules/`），這是課後練習之一。

### 5-5 兩道選配（repo README 教的克制）

還有第五、第六道：`UserPromptSubmit` hook（確定性的推力）和 `CLAUDE.md` 加一行。hook **刻意不內建**在 plugin 裡——它會在每一個 prompt 都 spawn 一個 subprocess，只為了攔截其中一小部分。工具作者連「要不要多推一把」都算過成本。

---

## Step 6：改一次、測一次（動手擴充）

### 6-1 把 Cursor 指到你的本地 checkout

改程式碼前，先讓 Cursor 跑**你的**版本而不是 git 上的版本。照 `client-configs/README.md` 的「Working on the server itself」段落，把 mcp.json 換成：

```json
{
  "mcpServers": {
    "rag-architect": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/rag-architect-mcp", "rag-architect-mcp"]
    }
  }
}
```

（把路徑換成你機器上的絕對路徑。改完要在 Cursor 的 MCP 設定裡 reload。）

### 6-2 練習 A：加一個 domain 關鍵字

台灣團隊常說「金控」。在 Cursor 裡請 AI：

> 「在 rag_architect/session.py 的 _DOMAIN_KEYWORDS 裡，幫 finance 加上『金控』這個關鍵字，然後在 test_rag_architect.py 加一個測試：extract_slots('我們是金控公司的內部文件') 的 domain 要是 finance。跑 uv run python test_rag_architect.py 確認全過。」

✅ **預期看到**：23 行 `ok`、`0 failure(s)`。然後在 Cursor 對話裡實測：「我們金控有數千頁純文字內規文件，可上合規雲端」→ domain 抽到 `finance`。

### 6-3 練習 B：體驗確定性（同輸入同輸出）

不改程式碼，直接驗證核心性質：

```bash
uv run python -c "
import os; os.environ['RAG_ARCHITECT_NO_NETWORK']='1'
from rag_architect import router
slots = {'data_volume':'thousands_pages','data_complexity':'cross_page_relations','privacy_boundary':'local_only','domain':'legal'}
for i in range(3):
    bp, plan = router.build_blueprint(slots)
    print(i, bp['recommended_architecture'])
"
```

✅ **預期看到**：三行一模一樣的 `Graph-Augmented RAG`。跑一百次也是。**這就是可以寫進合規文件、可以在會議上被質詢的性質**——換成「每次問 LLM」，你給不出這個保證。

### 6-4 練習 C（進階）：問 AI 一個設計問題

> 「如果我想加第五個必填 slot『update_frequency』（語料多久更新一次），要動 session.py、router.py、server.py 的哪些地方？加了之後，test_every_architecture_is_reachable_and_offline_safe 這個測試為什麼特別重要？」

好的回答會指出：`REQUIRED_SLOT_ORDER`、`SLOT_VALUES`、`SLOT_INTERVIEW_QUESTIONS`、抽取器、以及——最關鍵的——那個窮舉測試會自動掃過新 slot 的所有組合，確保沒有任何組合讓 server 崩潰或漏掉 reasoning/tradeoffs。**先有這種測試，才敢放心擴充。**

---

## 驗收清單

- [ ] `uv run python test_rag_architect.py` 結尾 `0 failure(s)`（22 項全過）
- [ ] Cursor MCP 設定裡看到 `rag-architect` 綠燈、兩個工具
- [ ] 旅程一：法律合約題**不點名工具**也會自動調用，回 Graph-Augmented RAG，且藍圖中沒有任何託管服務
- [ ] 旅程二：掃描財報題觸發 `NEEDS_INPUT`，AI 只問一個問題（domain）
- [ ] 旅程三：改口「其實是 Postgres 結構化表」後，架構換成 Text-to-SQL，且能說出是哪個 slot 變了
- [ ] 能複述決策矩陣的順序：型態 → 規模 → 結構，並解釋為什麼 50 頁語料不蓋知識圖譜
- [ ] 能解釋 `_NEGATED_CLOUD` 防的是什麼 bug、為什麼 fail-safe 要倒向 `local_only`
- [ ] 能說出 tool description 四段式的內容與順序
- [ ] 完成練習 A（加詞表 + 加測試 + 全過）

## 常見坑排錯速查

| 症狀 | 最可能的原因 | 快速修法 |
|---|---|---|
| Cursor MCP 紅燈／轉圈不停 | uvx 冷啟動下載中，或 uv 不在 Cursor 的 PATH | 終端機手動跑一次 uvx 指令觸發快取；或把 `command` 改成 `which uvx` 查到的絕對路徑 |
| `command not found: uvx` | uv 沒裝 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` 後重開 Cursor |
| 工具沒被自動調用，AI 憑記憶回答 | 問句太抽象（沒提語料／檢索），或 MCP 沒掛成功 | 先確認綠燈；問句帶上具體語料描述（規模、型態、隱私）；還是不行就點名一次「用 design_rag_architecture 分析」，之後同 session 通常就會自動用 |
| 工具回 `NEEDS_INPUT` 但 AI 自己猜答案往下走 | agent 沒遵守「不要猜 slot」 | 提醒它「照工具回的 next_question 問我，不要猜」；這正是 skill / rules 存在的理由 |
| 工具回 `ERROR: ... is not one of ...` | 明確傳入的 slot 值不在詞彙表（例如 `data_volume="a_few_pages"`） | 對照 README 的 Slots 表用合法值；這是刻意設計——未知值直接報錯，不靜悄悄亂路由 |
| `latest_tech_references` 是空的 | 離線、arXiv 沒回應、或設了 `RAG_ARCHITECT_NO_NETWORK=1` | 正常——架構完全不受影響（決策從不依賴搜尋）；照 `research_plan.queries` 用 agent 自己的搜尋補 |
| 測試跑不動：`No module named 'mcp'` | 沒 `uv sync` 或沒用 `uv run` | `cd rag-architect-mcp && uv sync && uv run python test_rag_architect.py` |
| 改了程式碼但 Cursor 行為沒變 | Cursor 還在跑 uvx 快取的 git 版本 | 換成 Step 6-1 的 `uv run --directory` 本地設定並 reload MCP |
| 手動跑 `uv run rag-architect-mcp` 停住沒輸出 | 正常——stdio server 在等 client 的 stdin | 不用自己跑；交給 Cursor 拉起行程 |

## 帶走的三句話

如果整份專案只能記住三件事，就這三句：

1. **確定性是信任的來源**——`router.py` 無 I/O、同輸入同輸出，推導可稽核。使用者反駁時你查「哪個 slot 判錯了」，不是跟結論吵架。一個會因為今天某篇部落格排名變動而改變的架構建議，本來就不叫建議。

2. **建議 = 元件 + 代價 + 驗證指標，缺一不可**——「用 GraphRAG」是關鍵字；「LightRAG 起步、圖是一次 schema 承諾、用 multi_hop_recall 驗證、local_only 時 data_egress_events 必須為零」才是建議。

3. **自動調用是設計出來的，不是求來的**——server instructions 進 context、description 寫使用者會打的字、形狀做成無狀態一次呼叫、缺欄位回一個問題。四道機制互相獨立，而且每一道都便宜。你下次寫 MCP 工具，先寫 description 再寫程式碼。

---

## ❓ 思考題（四題，先想再看答案）

### ❓ 想一想 1：確定性 vs 智慧

**題目**：把 `router.py` 的決策矩陣換成「把 slots 丟給 GPT/Claude，請它挑架構」，會更聰明嗎？列出你會失去的三樣東西。

<details>
<summary>看答案</summary>

會失去：(1) **可重現性**——同樣輸入可能得到不同答案，無法寫進合規文件、無法回歸測試；(2) **可稽核性**——你無法指出「為什麼是這個架構」的那一行；使用者反駁時只能重新擲骰子；(3) **零成本零依賴**——多了 API key、延遲、費用，還有「模型改版後建議悄悄變了」的風險。而「聰明」的部分其實沒有失去——自由文字理解本來就是**呼叫端 LLM** 在做（讀對話、填 slot），路由只負責不准出錯的那一段。這就是全課的分層：LLM 做模糊理解，純函式做關鍵決策。
</details>

### ❓ 想一想 2：fail-safe 的代價

**題目**：隱私抽取「不確定時一律回 `local_only`」。這會不會讓可以上雲的使用者拿到過度保守（自架、較貴人力）的建議？為什麼作者還是這樣設計？

<details>
<summary>看答案</summary>

會。但兩種錯的代價不對稱：多判 `local_only` 的代價是「多花自架功夫、也許多一次追問」，可修正、可發現；把「不可以上雲」判成「可以上雲」的代價是**照著建議把資料送出去**——等發現時已經外洩。錯誤代價不對稱時，預設值要放在代價低的那一邊。這跟 Project 13 的「訓練前停下來等你按 GO」是同一個工程紀律：不可逆的事，寧可多問一次。
</details>

### ❓ 想一想 3：為什麼保留 rag_consultant？

**題目**：`design_rag_architecture` 各方面都比 `rag_consultant` 適合 coding agent，為什麼不直接刪掉舊工具？

<details>
<summary>看答案</summary>

因為它們服務不同的呼叫者：`rag_consultant` 給「一輪只想答一題的人類」用——例如建在這個 server 上的引導式表單或聊天產品，逐題訪談是 feature 不是 bug。刪掉它會砍掉一種正當用途；留著它的風險（agent 誤用）則用兩道閘門控制：它的 description 直接叫 coding agent 去用另一個工具，server instructions 又補一句「Never invent a session id」。**與其刪工具，不如把『何時不該用』寫進描述**——這也是 tool description 第四段存在的理由。
</details>

### ❓ 想一想 4：測試哲學

**題目**：`test_rag_architect.py` 的 22 項測試「每一項都對應一個真的出過的 bug」。這種寫法和「追求覆蓋率」的測試有什麼不同？哪一項測試你認為防的 bug 最貴？

<details>
<summary>看答案</summary>

覆蓋率導向的測試證明「程式碼被執行過」；bug 紀念碑導向的測試證明「翻過的車不會再翻」——每一條都有真實故事，所以沒有一條是湊數的，改壞任何一條都代表舊 bug 復活。最貴的候選：`test_negated_cloud_is_local_only`（把隱私邊界判反 = 資料外洩，是資安事故不是功能 bug）；其次是 `test_every_architecture_is_reachable_and_offline_safe`（窮舉所有 slot 組合，保證沒有任何輸入讓 server 回不出藍圖——這是對「確定性路由」性質本身的測試）。附帶一課：這 22 項不連網、不需要 pytest、一個指令跑完——**測試越便宜，越會被跑**。
</details>

---

## 課外讀物：進階路線

- **四道自動調用機制的完整論證**：`README_zh.md` §怎麼讓 coding agent 自己找到它——含兩道選配（hook、CLAUDE.md）與各自的成本分析
- **決策矩陣的演進史**：`README_zh.md` §跟舊的五個分支差在哪——為什麼語意切塊全面退場、為什麼 GraphRAG 預設不再指微軟那套
- **skill 的判斷力設計**：`skills/rag-architect/SKILL.md`——「呈現決策，不是倒 JSON」「反駁 = slot 判錯」
- **Claude Code plugin 化**：`.claude-plugin/plugin.json` + `marketplace.json`——一個 repo 同時是 pip 套件、MCP server、Claude Code plugin 的檔案佈局

## 最後一句話

這份教學的目標不是教你「怎麼掛一個 MCP server」——掛起來只要 10 分鐘。真正的目標是你下次自己寫工具時，會先問四個問題：**description 寫的是使用者會打的字嗎？形狀是 agent 願意呼叫的嗎？不准出錯的邏輯是純函式嗎？每個測試對應一個真的翻過的車嗎？**這四個問題，比任何一個框架都值錢。
