# Walkthrough：把一包 AI Agent 能力在 Cursor 裡長出來——Rules / Commands / Hooks / MCP 全對照

> 這份文件帶你做一件事：拿一個真實的 Claude Code plugin——`Lazy Superstack`（教材資料夾 `lazy-cloud-devops`）當素材，**把它捆的八大能力（PM、設計思考、馬尾哥極簡、資料庫、全端、AI、雲端部署、資安），在 Cursor 裡一步一步重新長出來**。你會親手驗證一件事：**AI agent 的能力不是「模型變聰明」，是幾種擴充機制的組合——機制是可攜的，打包方式才是平台的。**
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個動作做完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式
>
> 每個機制章節固定四段式：**(a) 這是什麼 → (b) 為什麼用它 → (c) 官方怎麼說（引官方文件，附連結）→ (d) 在 Cursor 一步一步做**。Cursor 行為只寫官方文件查得到的；查不到的一律標「以你安裝的版本實測為準」。

---

## 🚦 開始前檢查清單（先做這五件事，上課當天才不會卡）

1. **確認教材 repo 在同層**：`ls ../lazy-cloud-devops/.claude-plugin/plugin.json` 有東西。這堂課的素材全部來自這個 repo，不在什麼都做不了。
2. **把 `demo.sh` 六幕全部跑一遍**（`./demo.sh 1` 到 `./demo.sh 6`）。全部離線、唯讀、秒回——跑不動代表路徑壞了，先修。
3. **裝好 Cursor 並確認版本**：Help → About（或 Cursor → About Cursor）看版本號。Rules 與 `.cursor/mcp.json` 很早就有；自訂 slash commands 需 1.6+，原生 Skills 與 `/migrate-to-skills` 需 2.4+（見各章「官方怎麼說」）。
4. **親手跑一次 hook 腳本**：`cd ../lazy-cloud-devops && bash hooks/inject-ponytail.sh`，確認會印出馬尾哥守衛區塊。Step 3 要拿它當 Cursor hook 的素材。
5. **確認 `npx` 與 `uvx` 存在**：`which npx uvx`。這是 A 級 MCP（Context7、Docker MCP）的前置工具，Step 5 掛 MCP 需要。

## 🗺️ 學習地圖（建議 2.5–3 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 兩邊生態的機制對照 | 25 分 | 閱讀理解（這是全課靈魂，慢慢看） |
| Step 0–1 開箱 + 盤點 plugin.json（要搬什麼） | 20 分 | 動手做（ls、cat、列搬家清單） |
| Step 2 Skill → Cursor Rules（+ 2.4 原生 Skills） | 35 分 | 動手做（建 .mdc、寫 frontmatter、驗證咬人）⭐ |
| Step 3 Hook → `.cursor/hooks.json` 或 alwaysApply | 20 分 | 動手做（兩條路都走一次） |
| Step 4 Command → `.cursor/commands/` | 20 分 | 動手做（搬兩個指令、拆 frontmatter 差異） |
| Step 5 MCP → `.cursor/mcp.json` 兩級啟用 | 25 分 | 動手做（A 級直接掛、B 級補憑證）⭐ |
| Step 6 策展合規：授權與上游同步 | 15 分 | 閱讀理解（NOTICES + sync 腳本，平台無關） |
| Step 7 總驗收：讓 rule 咬人 + doctor 體檢 | 15 分 | 動手做（本課落地重點） |
| 附錄（Claude Code 原生安裝）+ 思考題 | 10 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 素材在 `../lazy-cloud-devops/`，遙控器是 `./demo.sh`（位於 `project-16-lazy-superstack-plugin/` 根目錄）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 六幕全部離線、唯讀、10 秒內完成——不碰網路、不起 server、不碰 Docker。
> 每一幕看的是 Claude Code plugin 的真實檔案；**每一幕的收尾都問同一個問題：「這在 Cursor 是什麼？」**——答案在 walkthrough 對應的 Step。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `./demo.sh` 列清單，六幕各跑一次 | 確認 repo 路徑正確、每幕都有輸出 |
| 2 | `cd ../lazy-cloud-devops && bash hooks/inject-ponytail.sh` | 第 3 幕的主角，先確認腳本能跑 |
| 3 | 開一個練習用專案，先把 Step 2 的 `.cursor/rules/ponytail-guard.mdc` 建好備用 | Step 7 現場驗收「rule 咬人」不能賭第一次就成功 |
| 4 | Cursor Settings 裡先確認 MCP 頁面能開 | Step 5 要投影「server 亮綠燈」的畫面 |

### 放映時間軸

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:25 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §名詞卡 | 米其林套餐 vs 吃到飽比喻、Claude Code ↔ Cursor 機制對照表 | agent 能力 = 機制組合；機制可攜、打包方式屬於平台 |
| 0:25–0:40 | 第 1 幕：plugin.json 盤點 | `./demo.sh 1` | `.claude-plugin/plugin.json` | 51 行 JSON：skills / commands / hooks / mcpServers 四欄位 | 這是搬家前的物品清單——四個欄位就是要搬進 Cursor 的四批貨 |
| 0:40–1:05 | 第 2 幕：Skill 層與策展表 ⭐ | `./demo.sh 2` | `skills/README.md`、`skills/pm-brainstorming/SKILL.md` | 5 個 skill 的來源對照表 + Vendored 合規註記 | 這批 Markdown 紀律在 Cursor 叫 Rules（.mdc）；2.4+ 連 SKILL.md 都直接吃 |
| 1:05–1:25 | 第 3 幕：Hook 現場注入 | `./demo.sh 3` | `hooks/inject-ponytail.sh` | hooks.json matcher + 守衛區塊當場印出來 | Cursor 也有 hooks：`.cursor/hooks.json` 的 `sessionStart` 可注入 context；更懶的等價物是 alwaysApply rule |
| 1:25–1:45 | 第 4 幕：Command 層 | `./demo.sh 4` | `commands/lazy-ship.md`、`commands/superstack-doctor.md` | frontmatter、六步 pipeline、doctor 鐵律 | Cursor 1.6+ 也有 `.cursor/commands/*.md`——但 `allowed-tools`、`$1/$2` 沒有官方等價物 |
| 1:45–2:10 | 第 5 幕：MCP 兩級啟用 ⭐ | `./demo.sh 5` | `plugin.json` mcpServers、`mcp-optional.example.json` | A 級 2 個預設開 vs B 級 6 個附 `_doc` 的範本 | MCP 是跨工具協議——同一段 JSON 搬進 `.cursor/mcp.json` 就能用；兩級啟用的精神照搬 |
| 2:10–2:30 | 第 6 幕：策展紀律與閘門 | `./demo.sh 6` | `THIRD_PARTY_NOTICES.md`、`scripts/deploy-gcp.sh` | Vendored 來源彙整 + footprint gate 程式碼 | 授權合規與極簡閘門是平台無關的——搬去 Cursor 一樣要做滿 |

---

## 🎬 開場故事：米其林套餐 vs 吃到飽

想像你要幫一個新來的工程師「補能力」。有兩家餐廳可以選。

**第一家是吃到飽**：三百道菜擺滿檯面。聽起來很划算，但你走近一看——三盤都叫「炒飯」但味道互相打架（撞名）、一半的菜不知道放多久了（沒人維護）、菜色標籤全都寫「本店特製」但你分明在別家看過（來源不明）。你吃了兩輪就膩了，還吃壞肚子。

**第二家是米其林套餐**：只有八道菜，一個領域一道。菜單上每道菜都寫著產地與供應商（授權與來源）；主廚的原則是——**能跟信任的供應商直送的食材，就不自己養一座農場**（能 wire 就不 vendor）；真的要自己收進廚房的，只收兩樣別處吃不到的，而且冷藏、標籤、進貨紀錄做好做滿（LICENSE + NOTICES + sync 腳本）。

`Lazy Superstack` 就是第二家。別的「集大成」plugin 塞 300 個 skill 互相撞名，這個 repo 反過來：**vendored 來源只有 2 個（共 3 個 skill）、自寫 2 個，DB / 全端 / AI / 雲端能力全靠輕量 MCP wiring（8 個 server）**。它的 README 有一句話值得抄在牆上：

> **plugin 本身也極簡，因為塞太多本身就是 slop。**

但這堂課還有第二層：這家米其林開在「Claude Code 商圈」。你的廚房在 Cursor。**這堂課就是把整份菜單搬進你家廚房重做一遍**——你會發現：食譜（Markdown 紀律）、供應商電話（MCP JSON）原封不動能用，只有「上菜的方式」要換成 Cursor 的講法。

| 米其林套餐 | Lazy Superstack（Claude Code） | 搬進 Cursor 之後 |
|---|---|---|
| 一個領域一道菜 | 八大領域各配一種機制 | 同一套精選，不塞好塞滿 |
| 菜單標產地與供應商 | LICENSE + THIRD_PARTY_NOTICES.md | 照搬——授權跟著檔案走 |
| 供應商直送不自己養農場 | `plugin.json` 的 `mcpServers` | `.cursor/mcp.json` 的 `mcpServers`（同一協議） |
| 只收 2 樣別處吃不到的 | vendored superpowers-PM 與 OWASP | 複製進 `.cursor/rules/` 或 `.cursor/skills/`，合規註記跟著走 |
| 開店前廚房自動點火 | SessionStart hook 注入馬尾哥 | `.cursor/hooks.json` 的 `sessionStart`，或更懶的 `alwaysApply` rule |

---

## 🔍 名詞卡（十六個術語的白話解釋）

### 1. Plugin（外掛 / 能力捆綁包）〔Claude Code 專屬〕

> 白話：一個資料夾 + 一張清單（`plugin.json`），把 skills、commands、hooks、MCP 設定捆成一包，讓別人「裝一次、全部到位」。
> 為什麼重要：**Cursor 沒有等價物**——沒有「裝一個包全部到位」的機制。這正是本課的張力：在 Cursor 你要自己把四批貨逐一搬進 `.cursor/`，也因此你會真正搞懂每一批貨是什麼。

### 2. Skill（SKILL.md）

> 白話：給 AI 看的「方法論手冊」，本體是一個 `SKILL.md`（純 Markdown）。agent 在對的時機把它載入 context，照裡面的規則做事。
> 為什麼重要：skill 給的是**知識與紀律**，不是工具。它改變 agent「怎麼想」。原生於 Claude Code plugin；**Cursor 2.4+ 也有原生 Skills，同樣認 SKILL.md**（見 Step 2 官方引文）。

### 3. Cursor Rules（`.cursor/rules/*.mdc`）

> 白話：Cursor 的規則檔——放在專案 `.cursor/rules/` 下的 `.mdc` 檔，內容會被放進 AI 的 context。
> 為什麼重要：這是本課把「skill 紀律」搬進 Cursor 的主要容器。它同時能扮演 skill（知識）和 hook（常駐注入）兩種角色，取決於 frontmatter 怎麼寫。

### 4. .mdc frontmatter（description / globs / alwaysApply）

> 白話：`.mdc` 檔最上面兩條 `---` 夾住的 metadata：`description`（讓 Agent 判斷何時相關）、`globs`（哪些檔案命中時自動附掛）、`alwaysApply`（每次對話都載入）。
> 為什麼重要：**三個欄位的組合決定 rule 的觸發方式**——frontmatter 寫錯，rule 永遠不會生效（最常見的翻車點）。

### 5. 四種觸發型態（Rules）

> 白話：官方文件把 rule 分四型——Always Apply（永遠載入）、Apply Intelligently（Agent 依 description 判斷）、Apply to Specific Files（glob 命中自動附掛）、Manual（只在你 `@` 它時載入）。
> 為什麼重要：對應 Claude Code 的心智模型——Always ≈ hook 注入、Intelligently ≈ skill 自動觸發、Manual ≈ 手動引用。

### 6. AGENTS.md

> 白話：放在專案根目錄的純 Markdown 指示檔，是 `.cursor/rules` 的「免 frontmatter 簡易版」；子目錄可以放巢狀 AGENTS.md，愈深層的優先。
> 為什麼重要：只想寫幾條全案規則時，一個 AGENTS.md 比一堆 .mdc 更馬尾哥。

### 7. Command（斜線指令）

> 白話：一個 Markdown prompt 檔，使用者打 `/指令名` 觸發。Claude Code 放在 plugin 的 `commands/`；Cursor 1.6+ 放在專案的 `.cursor/commands/`。
> 為什麼重要：command 是**使用者主動觸發的工作流**——rules/skills 是 agent 自己判斷時機，command 是你下令。

### 8. Hook（掛勾）

> 白話：在特定事件自動執行的腳本。Claude Code 用 plugin 的 `hooks/hooks.json`（事件叫 `SessionStart`）；Cursor 用專案的 `.cursor/hooks.json`（事件叫 `sessionStart`），雙向以 stdio 上的 JSON 溝通。
> 為什麼重要：hook 解決「時機」問題——馬尾哥規則若等 agent 自己想到才載入就太晚了，hook 讓它**從第一個 prompt 就生效**。

### 9. MCP（Model Context Protocol）

> 白話：讓 AI 能呼叫外部工具的協議。接上 MongoDB MCP，agent 就能自己查資料庫；接上 Context7，就能自己拉最新官方文件。
> 為什麼重要：skill/rule 給知識、MCP 給**手腳**。而且 MCP 是**跨工具協議**——同一段 server 設定，Claude Code 與 Cursor 都認得。

### 10. `.cursor/mcp.json`（專案層）vs `~/.cursor/mcp.json`（全域）

> 白話：Cursor 的 MCP 設定檔有兩層——放專案裡的只對這個專案生效（可進版控、全隊共用），放家目錄的對所有專案生效。
> 為什麼重要：兩級啟用策略靠它落地：團隊共用的 A 級放專案層，含個人憑證的 B 級放全域層或用環境變數插值。

### 11. Cursor 原生 Skills（`.cursor/skills/<name>/SKILL.md`）〔2.4+〕

> 白話：Cursor 較新版本的原生技能包，格式就是 SKILL.md，還相容 `.claude/skills/` 目錄。用 `/skill 名` 或 `@` 觸發。
> 為什麼重要：這是 Claude Code skill 的**最短搬家路徑**——連格式都不用改。也證明「機制可攜」不是口號，兩邊生態正在互相靠攏。

### 12. Agent / Ask / Plan 模式

> 白話：Cursor 聊天的三種模式——Agent（預設，能改檔跑指令）、Ask（唯讀問答）、Plan（先產出實作計畫給你審，再動工）。
> 為什麼重要：rules 與 MCP 工具都是餵給 Agent 用的；驗收 rule 有沒有咬人，要在 Agent 模式測。

### 13. 三種處置：Vendored / Wired / Inspired

> 白話：Vendored＝把別人的檔案**複製**進來（附原版 LICENSE）；Wired＝**零複製**，只在設定檔指向官方 server；Inspired＝只借概念、內容自己重寫並致謝。
> 為什麼重要：三種措辭嚴格區分——這是誠實，也是法律。搬進 Cursor 時這套紀律**原樣適用**：複製 .mdc 也要帶著 LICENSE 與註記。

### 14. 策展（Curation）

> 白話：不是「收集」，是「篩選 + 把關 + 說明來源」。博物館策展人不會把倉庫全搬出來展。
> 為什麼重要：這個 repo 的設計規格裡有一整段「砍掉清單」——被砍的比被收的多。策展的價值在砍。你搬進 Cursor 時同樣要砍：不是五個 skill 全都值得 alwaysApply。

### 15. AI Slop 與馬尾哥（Ponytail）

> 白話：AI Slop＝LLM 預設傾向的過度生成（多餘程式碼、肥大依賴、投機抽象、過寬權限）；馬尾哥＝「正確地懶」的資深工程師人設，能不寫的絕不寫。
> 為什麼重要：這包能力的核心敵人與核心哲學。`ponytail-guard` 的 Slop Test 四問就是你要搬進 Cursor 的第一條 rule。

### 16. 兩級啟用（A 級 / B 級）

> 白話：A 級 MCP 零憑證即用，預設開；B 級需要憑證（連線字串、金鑰），只放範本，預設不開。
> 為什麼重要：全部預設開 = 沒憑證的使用者一裝就噴錯。這是「為新手的第一次啟動體驗」做的設計——搬進 Cursor 時照搬這個精神。

---

## Step 0：開箱——用 Cursor 打開素材 repo

一切從看清結構開始。**不要先讀內容，先看形狀**——形狀就會告訴你有哪四批貨要搬。

用 Cursor 直接打開 `lazy-cloud-devops` 資料夾（File → Open Folder），然後開內建終端機（Ctrl+`）：

```bash
ls -la
find skills -name "SKILL.md" | sort
```

✅ **預期看到**：

```
.claude-plugin/  commands/  docs/  hooks/  scripts/  skills/
LICENSE  README.md  THIRD_PARTY_NOTICES.md  mcp-optional.example.json

skills/design-thinking/SKILL.md
skills/pm-brainstorming/SKILL.md
skills/pm-writing-plans/SKILL.md
skills/ponytail-guard/SKILL.md
skills/security-owasp/SKILL.md
```

再讓 Cursor 的 Agent 幫你導覽（Agent 模式）：

> 「這是一個 Claude Code plugin。請掃一遍目錄結構，告訴我：skills、commands、hooks、MCP 設定各在哪個檔案？如果我要把這些能力搬到 Cursor（rules、commands、hooks、mcp.json），每一批各對應什麼？」

**講解重點**：四個目錄對四批貨——`skills/` 是知識、`commands/` 是工作流、`hooks/` 是時機、`plugin.json` 的 `mcpServers` 是手腳。整包用 `.claude-plugin/plugin.json` 捆起來的東西叫 plugin——那是 Claude Code 的打包格式，**Cursor 沒有等價物**，所以接下來我們逐批手搬。

🧯 **卡住的話**：
- 找不到資料夾 → 教材 repo 與教學資料夾同層：`cursor-sample-projects/lazy-cloud-devops/`。

---

## Step 1：盤點 plugin.json——搬家前的物品清單

```bash
cat .claude-plugin/plugin.json
```

✅ **預期看到**：51 行 JSON。重點看最後四個欄位：

```json
  "skills": "./skills",
  "commands": "./commands",
  "hooks": "./hooks/hooks.json",
  "mcpServers": {
    "context7": { "command": "npx", "args": ["-y", "@upstash/context7-mcp"], "env": {} },
    "docker":   { "command": "uvx", "args": ["mcp-server-docker"], "env": {} }
  }
```

**講解重點**（指著螢幕講三件事）：

1. 這四個欄位就是**四批要搬的貨**：`skills`（5 份 SKILL.md）→ Step 2、`hooks`（1 個 SessionStart 注入）→ Step 3、`commands`（2 個 prompt 檔）→ Step 4、`mcpServers`（A 級 2 個，另有 B 級 6 個在 `mcp-optional.example.json`）→ Step 5。
2. `skills` 和 `commands` 只是路徑——Claude Code 的 plugin 系統會去掃那個目錄。搬進 Cursor 後，掃描目錄變成 `.cursor/rules/`、`.cursor/commands/`，一樣是「目錄即約定」。
3. `mcpServers` 裡只有兩個——因為只有這兩個**零憑證即用**。這是 Step 5 的伏筆。

> ❓ **想一想**：`version` 是 `2.0.0`，而資料夾叫 `lazy-cloud-devops`、`name` 卻叫 `lazy-superstack`。為什麼會不一致？
>
> **答案**：`docs/superpowers/specs/2026-06-24-lazy-superstack-design.md` 記載了演進：這個 repo 的前身是 `lazy-cloud-devops` plugin（雲端部署導向），2.0 改名 `lazy-superstack` 並擴大為八領域能力捆綁包。plugin 的身分認 `plugin.json` 的 `name`，不認資料夾名。

---

## Step 2：Skill → Cursor Rules——把紀律變成 .mdc ⭐

### (a) 這是什麼

Claude Code 的 skill 是「agent 在對的時機載入的 Markdown 方法論」；Cursor 對應的主要容器叫 **Rules**——放在專案 `.cursor/rules/` 下的 `.mdc` 檔，內容進 AI 的 context。這一步我們把 `ponytail-guard` 這份 296 行的極簡鐵律，變成 Cursor rule。

### (b) 為什麼用它

不做這步會怎樣？你在 Cursor 裡請 AI 寫元件，它預設就是裝 react-modal、拉 axios、加一層「為以後留彈性」的抽象——AI Slop 全餐。skill 級的紀律必須進 context 才存在；在 Cursor，rule 就是讓紀律進 context 的正門。

### (c) 官方怎麼說

官方 Rules 文件（[cursor.com/docs/context/rules](https://cursor.com/docs/context/rules)）：

> "Project rules live in `.cursor/rules` as `.mdc` files and are version-controlled."
> （專案規則以 `.mdc` 檔存放在 `.cursor/rules`，並納入版本控制。）

frontmatter 有三個欄位：`description`、`globs`、`alwaysApply`，組合出四種觸發型態：

| 官方型態 | 觸發方式（官方描述） |
|---|---|
| Always Apply | 每次聊天都載入 |
| Apply Intelligently | "When Agent decides it's relevant based on description"（由 Agent 依 description 判斷相關才載入） |
| Apply to Specific Files | 檔案命中 `globs` 樣式時自動附掛 |
| Manual | "Included only when you @-mention the rule in chat"（只有你在聊天中 `@` 提到它才載入） |

官方同時建議：**"Keep rules under 500 lines"（規則保持在 500 行以內）**，大規則拆成可組合的小塊。建立方式除了手動建檔，官方也提供聊天內 `/create-rule` 或 Customize → Rules → Add Rule。另外，專案根目錄的 `AGENTS.md` 是免 frontmatter 的純 Markdown 替代品，子目錄可放巢狀 AGENTS.md，愈深層優先。

### (d) 在 Cursor 一步一步做

在**你自己的任一練習專案**（不是教材 repo）裡：

**第 1 步：建目錄**

```bash
mkdir -p .cursor/rules
```

✅ **預期看到**：專案根目錄出現 `.cursor/rules/`（Cursor 檔案總管裡可見）。

**第 2 步：建常駐摘要 rule（對應 hook 注入的那份精華）**

建 `.cursor/rules/ponytail-guard.mdc`，內容如下（Slop Test 四問抄自 `../lazy-cloud-devops/skills/ponytail-guard/SKILL.md` §0）：

```markdown
---
description: 馬尾哥極簡鐵律——生成任何程式碼前先過 Slop Test
alwaysApply: true
---

# Ponytail Guard（常駐摘要）

生成任何東西之前，依序問，第一個「否」就停：
1. 這需要存在嗎？（刪除、設定旗標、既有函式能不能解？）
2. 原生平台原語能做嗎？（<dialog>、fetch、Intl……先用平台）
3. 這是最小正確版本嗎？（「為以後留彈性」= 現在就是 slop）
4. 每一行、每個依賴、每個權限，經得起懷疑派資深工程師的 code review 嗎？

核心法則：少寫程式是終極整潔架構。刪除優先。存疑時，出貨較小的版本。
```

**第 3 步：建 glob 觸發的前端細則 rule（示範 Apply to Specific Files）**

建 `.cursor/rules/ponytail-frontend.mdc`，把 `SKILL.md` §1 的「原生優先替換表」搬進來（modal 套件→`<dialog>`、axios→`fetch`、moment→`Intl`、date-picker→`<input type="date">`……），frontmatter 寫：

```yaml
---
description: 前端原生優先替換表——碰前端檔案時自動附掛
globs: ["**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.html", "**/*.css"]
alwaysApply: false
---
```

**第 4 步：驗證 rule 有被引用**

打開 Cursor 的 Rules 設定頁（Customize / Settings → Rules），確認兩條 rule 都列在 Project Rules 清單、觸發型態分別顯示為 Always 與檔案限定。再開一個 Agent 對話實測（完整驗收在 Step 7）。

✅ **預期看到**：Rules 清單出現 `ponytail-guard`（Always Apply）與 `ponytail-frontend`（限定 glob）。

🧯 **卡住的話**：
- 清單沒出現 → 副檔名必須是 `.mdc`、目錄必須是 `.cursor/rules/`（不是 `.cursor/rule/`）；frontmatter 的兩條 `---` 要頂格。
- rule 出現但沒作用 → 檢查你是不是在 Ask 模式問（rules 餵給 Agent 對話用；用 Agent 模式測）。

### 2-1 延伸：Cursor 2.4+ 原生 Skills——SKILL.md 直接搬

Cursor 較新版本有原生 Skills，官方文件（[cursor.com/docs/context/skills](https://cursor.com/docs/context/skills)）：

> "A skill is a portable, version-controlled package that teaches agents how to perform domain-specific tasks."
> （skill 是可攜、可版控的能力包，教 agent 執行特定領域的任務。）
>
> "For compatibility, Cursor also loads skills from Claude and Codex directories: `.claude/skills/`, `.codex/skills/`, `~/.claude/skills/`, and `~/.codex/skills/`."
> （為了相容，Cursor 也會從 Claude 與 Codex 的目錄載入 skills。）
>
> "Skills load resources on demand, keeping context usage efficient."
> （skills 按需載入資源，讓 context 用量維持精省。）

也就是說：**教材 repo 的 SKILL.md 幾乎零改動可搬**——

```bash
mkdir -p .cursor/skills
cp -r ../lazy-cloud-devops/skills/ponytail-guard .cursor/skills/ponytail-guard
cp -r ../lazy-cloud-devops/skills/pm-brainstorming .cursor/skills/pm-brainstorming
```

frontmatter 的 `name` / `description` 兩邊通用（Cursor 另支援 `paths`、`disable-model-invocation` 等欄位）。之後在 Agent 輸入框打 `/ponytail-guard` 或 `@` 選取即可觸發。官方另提供 `/migrate-to-skills`（2.4+ 內建）把既有 rules/commands 轉成 skills；注意官方明說 **`alwaysApply: true` 或帶 `globs` 的 rule 不會被遷移**——因為它們的觸發條件與 skill 的行為不同。你的版本若還沒有 Skills，就用上面的 Rules 路徑，效果等價。

### 2-2 vendored 合規在 Cursor 一樣算數

搬 `pm-brainstorming` 這類 vendored skill 時，看它的檔頂（`sed -n '1,8p' ../lazy-cloud-devops/skills/pm-brainstorming/SKILL.md`）：「📥 Vendored skill」註記寫明來源（obra/superpowers）、作者（Jesse Vincent）、授權（MIT）、改了什麼。**複製到 `.cursor/` 時，同目錄的 `LICENSE` 與這段註記要跟著走**——MIT 的條件是保留版權與授權聲明，跨編輯器不會豁免。

> ❓ **想一想**：五個 skill 該全部設 `alwaysApply: true` 嗎？
>
> **答案**：不該——那就是把米其林變回吃到飽。`ponytail-guard` 的摘要值得常駐（它管「每一次生成」）；`pm-brainstorming`、`security-owasp` 這類是「特定時機的方法論」，用 description 讓 Agent 判斷（Apply Intelligently）或搬成 2.4+ 的 skill 按需觸發。**常駐的 context 是稀缺資源**——官方那句「500 行以內」就是在管這件事。

---

## Step 3：Hook → `.cursor/hooks.json`——時機問題的兩條路

### (a) 這是什麼

Claude Code 端：`hooks/hooks.json` 宣告「`SessionStart`（matcher：`startup|resume|clear`）時執行 `inject-ponytail.sh`」，腳本輸出被塞進 context。Cursor 端：**也有 hooks**——專案 `.cursor/hooks.json`（或全域 `~/.cursor/hooks.json`），其中 `sessionStart` 事件同樣能注入 context。

### (b) 為什麼用它

skill/rule 寫得再好，沒進 context 就等於不存在。馬尾哥的規則不能賭 agent「自己想到」，要在對話一開始就生效。先親手看 Claude Code 版注入了什麼：

```bash
cd ../lazy-cloud-devops
bash hooks/inject-ponytail.sh
```

✅ **預期看到**：一段 `<lazy-superstack active="true">` 包起來的文字——三條 CORE LAWS、一張「五個 skill 什麼時機用」的能力地圖、一句「When in doubt, ship the smaller version.」。這就是每個 session 開頭被餵進 agent 腦子的東西。

### (c) 官方怎麼說

官方 Hooks 文件（[cursor.com/docs/agent/hooks](https://cursor.com/docs/agent/hooks)）：

> "Hooks let you observe, control, and extend the agent loop using custom scripts."
> （Hooks 讓你用自訂腳本觀察、控制、擴充 agent 迴圈。）
>
> "Hooks are spawned processes that communicate over stdio using JSON in both directions."
> （Hook 是被啟動的行程，雙向都以 stdio 上的 JSON 溝通。）

設定檔位置：專案 `.cursor/hooks.json` 或使用者層 `~/.cursor/hooks.json`。`sessionStart` 在新對話建立時觸發，輸出 JSON 可包含 `additional_context`（注入對話的額外 context）與 `env`；官方註明它是 fire-and-forget——agent 不會等它回應。支援的事件遠不只這個（`beforeShellExecution`、`beforeMCPExecution`、`afterFileEdit`、`stop`……），完整清單見官方文件。

**跟 Claude Code 的差異要誠實講**：Claude Code 的 hook 腳本**直接印純文字**就會被當 context；Cursor 的 hook 要**輸出 JSON**（把文字放進 `additional_context` 欄位）。另外 Claude Code 的 matcher `startup|resume|clear` 語意（連 `/clear` 後都重新注入）在 Cursor 對應成「每個新對話都觸發 sessionStart」；細部行為以你安裝的版本實測為準。

### (d) 在 Cursor 一步一步做

**路線一（推薦，最馬尾哥）：alwaysApply rule 就是你的 SessionStart hook。**

Step 2 第 2 步建的 `ponytail-guard.mdc`（`alwaysApply: true`）已經達成「每次對話開頭規則就在 context 裡」的效果——零腳本、零行程、宣告式。內容固定的注入，用 rule 就好。

**路線二（內容需要動態產生時）：真的寫一個 Cursor hook。**

第 1 步：在練習專案建包裝腳本 `.cursor/hooks/inject-ponytail.sh`（把教材腳本的輸出包成 Cursor 要的 JSON）：

```bash
#!/usr/bin/env bash
# 把 lazy-superstack 的守衛文字包成 Cursor sessionStart 的 JSON 輸出
bash "$(dirname "$0")/../../../lazy-cloud-devops/hooks/inject-ponytail.sh" \
  | python3 -c 'import json,sys; print(json.dumps({"additional_context": sys.stdin.read()}))'
```

（路徑依你的專案與教材 repo 的相對位置調整；`chmod +x` 加執行權限。）

第 2 步：建 `.cursor/hooks.json`：

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      { "command": "./.cursor/hooks/inject-ponytail.sh" }
    ]
  }
}
```

第 3 步：重啟 Cursor（讓 hooks 設定被讀到），開一個新 Agent 對話，問它：

> 「你的 context 裡有沒有 lazy-superstack 的守衛區塊？裡面的三條 CORE LAWS 是什麼？」

✅ **預期看到**：agent 能複述 CORE LAWS（少寫程式是終極整潔架構／原生 API 優先與最小權限雲端／零魔法字串零死依賴零投機抽象）。

🧯 **卡住的話**：
- agent 說沒看到 → 先在終端機直接跑 `./.cursor/hooks/inject-ponytail.sh`，確認輸出是**一行合法 JSON**（`{"additional_context": "..."}`）；再確認腳本有執行權限、`hooks.json` 放在 `.cursor/` 下、重啟過 Cursor。hooks 的欄位與載入時機隨版本演進，以你安裝的版本實測為準。
- 覺得太麻煩 → 就對了。**內容固定時路線一是正解**；路線二留給「需要跑指令才知道要注入什麼」的場景（例如注入當下的 git 狀態）。

> ❓ **想一想**：Claude Code 的 matcher 特地包含 `clear`（`/clear` 清空 context 後重新注入）。這個防禦性設計在 Cursor 的世界對應什麼？
>
> **答案**：`alwaysApply` rule 天生免疫這個問題——它不是「注入一次」，是**每次對話組 context 時都在**。這是宣告式（rule）勝過命令式（hook）的典型案例：不用防「狀態被清掉」，因為根本沒有狀態。

---

## Step 4：Command → `.cursor/commands/`——搬兩個斜線指令

### (a) 這是什麼

Claude Code 端：`commands/*.md` 是帶 frontmatter 的 prompt 檔（`/lazy-ship`、`/superstack-doctor`）。Cursor 端：1.6 起也有自訂 slash commands——專案 `.cursor/commands/` 下的 Markdown 檔，在 Agent 輸入框打 `/` 選取。

### (b) 為什麼用它

`/superstack-doctor` 那種「固定步驟、固定輸出格式、固定鐵律」的工作流，每次用嘴巴重講一遍 prompt 是浪費；存成指令檔，團隊每個人打 `/` 就能複用同一套紀律。

### (c) 官方怎麼說

Cursor 1.6 changelog（[cursor.com/changelog/1-6](https://cursor.com/changelog/1-6)）：

> "Commands are stored in `.cursor/commands/[command].md`."
> （指令存放在 `.cursor/commands/[指令名].md`。）
>
> "Run them by typing `/` in the Agent input and selecting the command from the dropdown menu."
> （在 Agent 輸入框打 `/`，從下拉選單選取執行。）
>
> "You can now create reusable prompts and quickly share them with your team."
> （你現在可以建立可複用的 prompt，快速分享給團隊。）

注意：目前官方文件站已把 commands 頁導向 **Skills**（[cursor.com/docs/context/skills](https://cursor.com/docs/context/skills)），並提供 2.4+ 內建的 `/migrate-to-skills` 把既有 commands 轉成 skills——官方沒有宣告 commands 廢棄，兩者並存，但風向是往 Skills 收斂。

### (d) 在 Cursor 一步一步做

**第 1 步：建目錄並複製兩個指令檔**（在你的練習專案）：

```bash
mkdir -p .cursor/commands
cp ../lazy-cloud-devops/commands/lazy-ship.md        .cursor/commands/lazy-ship.md
cp ../lazy-cloud-devops/commands/superstack-doctor.md .cursor/commands/superstack-doctor.md
```

**第 2 步：拆 frontmatter 差異——這是兩邊生態的真實分歧點。**

打開 `lazy-ship.md` 的 frontmatter，逐欄位對照：

| Claude Code 欄位 | 作用 | Cursor 有等價物嗎 |
|---|---|---|
| `description` | 給人和選單看的說明 | 官方只說 command 是 Markdown 檔，未文件化 frontmatter 欄位——留著無害，以實測為準 |
| `argument-hint: "[gcp\|aws] [service-name]"` | 提示參數格式 | **沒有官方等價物** |
| `allowed-tools: Read, Write, Edit, Bash, ...` | 這個 command 執行時被允許用的工具（權限最小化做到 command 層級） | **沒有官方等價物**——Cursor 的工具權限走全域的 Agent 設定與逐次確認，不綁在單一指令上 |
| 正文的 `$1` / `$2` 佔位符 | 參數替換（`/lazy-ship aws my-api` → `$1`=aws） | **沒有官方文件背書的替換機制**——你在 `/lazy-ship` 後面打的字會跟著進 prompt，但不會替換 `$1`，以實測為準 |

**第 3 步：把 `$1/$2` 改寫成 Cursor 能懂的講法。**編輯 `.cursor/commands/lazy-ship.md`，把 Arguments 一節改成：

```markdown
## Arguments

使用者會在指令後面接著打：目標雲（gcp 或 aws，預設 gcp）與服務名
（預設當前目錄名）。從使用者輸入中解析這兩個值再開始。
```

**第 4 步：驗證。**在 Agent 輸入框打 `/`。

✅ **預期看到**：下拉選單出現 `lazy-ship` 與 `superstack-doctor` 兩個自訂指令。

🧯 **卡住的話**：
- 下拉選單沒有 → 確認 Cursor 版本 ≥ 1.6、檔案在專案根的 `.cursor/commands/`（副檔名 `.md`）、重開對話再打 `/`。

**講解重點（兩個指令搬過去後依然成立的設計）**：

- `/lazy-ship` 的第一步是 **Invoke the `ponytail-guard` skill**——搬進 Cursor 後，這句話會讓 Agent 去找同名的 rule/skill（你在 Step 2 建好的）。機制互相組合的精神不變：command 編排工作流、rule 提供紀律、script 執行部署。
- `/superstack-doctor` 的兩條鐵律——**絕不印出任何憑證的值（只報有／無）**、**不替使用者寫入設定檔（只給指引）**——是寫在 prompt 正文裡的，跟平台無關，原封不動生效。但 Claude Code 端用 `allowed-tools: Bash, Read` 在機制層面禁止它寫檔的那道保險，Cursor 沒有等價物——**同一條規則，在 Cursor 只剩 prompt 自律這一層**。這是兩邊生態的真實差異，不用粉飾。

> ❓ **想一想**：為什麼「不替使用者寫入設定檔」也是一條鐵律？自動幫忙設定不是更貼心嗎？
>
> **答案**：憑證設定檔是使用者的信任邊界。一個第三方 prompt 自動改它，等於「裝了外掛就默默改你家鑰匙」。給指引讓使用者自己動手，是把最後的控制權留在人手上。

---

## Step 5：MCP → `.cursor/mcp.json`——兩級啟用照搬 ⭐

### (a) 這是什麼

MCP（Model Context Protocol）是讓 AI 呼叫外部工具的**跨工具協議**。教材 repo 把 8 個 MCP server 分成兩級：A 級（零憑證，`plugin.json` 預設開：Context7、Docker MCP）、B 級（需憑證，只放範本 `mcp-optional.example.json`，預設不開：MongoDB、Postgres、AWS、Terraform、GitHub、shadcn）。這一步把同一套分級搬進 Cursor。

### (b) 為什麼用它

rule 給知識，MCP 給手腳——沒有 MCP，agent 查不了資料庫、拉不了最新文件。而「兩級啟用」防的是：八個全部預設開，沒憑證的人一啟動就滿屏紅字。體貼是設計出來的。

### (c) 官方怎麼說

官方 MCP 文件（[cursor.com/docs/context/mcp](https://cursor.com/docs/context/mcp)）：

- **兩層設定檔**：專案層 `.cursor/mcp.json`（只對該專案生效）與全域 `~/.cursor/mcp.json`（所有專案生效）。
- **三種 transport**：stdio（本機、Cursor 代管行程）、SSE 與 Streamable HTTP（本機或遠端、自行部署的 server 用 `url` + `headers` 設定）。
- **環境變數插值**：設定值支援 `${env:NAME}`（環境變數）、`${workspaceFolder}`（專案根）、`${userHome}`（家目錄）。
- **啟用/停用**：

> "Toggle servers on/off without removing them: Open Customize in the sidebar, find the MCP server you want to change, use the toggle to enable or disable it."
> （不必刪除設定就能開關 server：打開側欄的 Customize，找到要改的 MCP server，用開關切換啟用/停用。）

- **認證**："MCP servers use environment variables for authentication. Pass API keys and tokens through the config."（MCP server 用環境變數做認證，API 金鑰與 token 透過設定傳入。）需要 OAuth 的 server 官方也支援。
- **工具數量**：現行官方文件**沒有**載明 Agent 可用工具數的固定上限（社群論壇歷史上有「40 個工具」上限的回報，屬版本相關的非官方資訊）。實務原則不變：**一次只開會用到的 server**——工具太多會稀釋 agent 選工具的準確度，以你安裝的版本實測為準。

### (d) 在 Cursor 一步一步做

**第 1 步：掛 A 級（零憑證，直接開）。**在練習專案建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "docker": {
      "command": "uvx",
      "args": ["mcp-server-docker"]
    }
  }
}
```

對照教材 `plugin.json` 的 `mcpServers`——**JSON 形狀一模一樣**，因為 MCP 是跨工具協議。這就是 Wired（零複製）的威力：搬家成本趨近於零。

**第 2 步：驗證 server 亮綠燈。**打開 Cursor 設定的 MCP 頁（側欄 Customize → MCP，或 Settings 搜 MCP）。

✅ **預期看到**：`context7` 與 `docker` 兩列，狀態為啟用（綠燈），展開能看到各自提供的工具清單（例如 context7 的文件查詢工具）。

**第 3 步：實測手腳。**開 Agent 對話問：

> 「用 context7 查一下 Next.js App Router 的最新官方文件，告訴我 layout.tsx 的檔案約定。」

✅ **預期看到**：Agent 呼叫 context7 的 MCP 工具（對話中會顯示工具呼叫），回答引用拉回來的文件內容。

**第 4 步：掛 B 級（需憑證，按需開）。**以 Postgres 為例，從 `../lazy-cloud-devops/mcp-optional.example.json` 複製 `postgres` 區塊到 `.cursor/mcp.json` 的 `mcpServers` 下，做兩個修整：

1. **拿掉 `_doc` / `_README` 底線欄位**——那是「JSON 沒有註解語法」的土辦法註解，給人看的；搬進正式設定檔前先清掉，避免不同版本解析差異。
2. **憑證用官方插值，別寫死**：

```json
    "postgres": {
      "command": "uvx",
      "args": ["postgres-mcp", "--access-mode=restricted"],
      "env": {
        "DATABASE_URI": "${env:DATABASE_URI}"
      }
    }
```

然後在 shell 環境設好 `DATABASE_URI`，重啟 Cursor，回 MCP 設定頁看它亮綠燈。**沒有憑證的 server 就不要加進來**——這就是兩級啟用的精神：範本躺在 example 檔裡，誰有憑證誰自己搬。

🧯 **卡住的話**：
- context7 紅燈 → 沒有 node/npx，或首次 `npx -y` 正在拉套件（等首次下載完成再看）。
- docker 紅燈 → 沒有 `uvx`（`curl -LsSf https://astral.sh/uv/install.sh | sh` 裝 uv）。
- B 級一開就噴錯 → 憑證環境變數沒設就複製了區塊——這正是它預設不開的原因。
- 想全域共用 → 把區塊搬到 `~/.cursor/mcp.json`；**含個人憑證的設定不要放專案層進版控**。

**講解重點（策展最實戰的一課）**：範本裡 Postgres 用的是 Postgres MCP Pro 而不是官方 `server-postgres`——`_doc` 寫得明白：官方那個「已 archived 且有 SQLi 漏洞」。選材不只看名氣，要看維護狀態與安全公告。這條紀律跟編輯器無關。

> ❓ **想一想**：shadcn MCP 不需要金鑰，為什麼還是被分在 B 級？
>
> **答案**：它的前置條件是「當前專案目錄有 `components.json`」——不是每個專案都是 shadcn 專案。B 級的定義不是「要錢」，是「有環境前置條件，預設開會在不滿足的環境噴錯」。

---

## Step 6：策展合規——授權不是附錄，是骨架（平台無關）

這一步沒有 Cursor 專屬動作——因為**授權合規跟編輯器無關**。但你在 Step 2 複製了 vendored 內容進 `.cursor/`，所以這步是你的責任清單。

```bash
cd ../lazy-cloud-devops
cat THIRD_PARTY_NOTICES.md
```

✅ **預期看到**：檔案開頭就給三種處置的**嚴格定義**（Vendored＝複製附 LICENSE／Wired＝設定指向未複製／Inspired＝概念致謝未複製），然後 A、B、C 三區分別列 vendored skills、wired MCP、inspired 來源——每一條都有來源 URL、作者、授權、**修改了什麼**。

再看上游同步腳本：

```bash
sed -n '1,15p' scripts/sync-vendored.sh
```

**講解重點**：vendored 內容會過時，所以要留一條回上游的路。`sync-vendored.sh` 從上游重抓兩個來源覆蓋進 `skills/`，然後**提醒你**：上游覆蓋會洗掉前綴與合規註記，要用 `git diff` 檢查重套。你搬進 `.cursor/` 的那些複本也一樣——上游更新時，你要自己同步。

> ❓ **想一想**：為什麼腳本「只更新內容、不自動重打前綴」？寫個 sed 自動改 frontmatter 不難吧？
>
> **答案**：馬尾哥式取捨。上游的檔案佈局隨時會變（腳本裡兩處 `die "... layout changed?"` 就是證據），自動改寫邏輯會跟著上游腐爛，變成「維護同步腳本的維護債」。同步是低頻動作，`git diff` 一眼可查——**人工檢查 + 明確提醒**比脆弱的自動化更便宜。

最後看部署腳本的 footprint gate（極簡的可執行版本）：

```bash
grep -n -A 5 "footprint gate" scripts/deploy-gcp.sh
```

✅ **預期看到**：建完 image 量大小，`SIZE_MB` 超過 `MAX_IMAGE_MB`（預設 300）直接 `die`——「strip slop and retry」。前面還有一段 Dockerfile 稽核：非 multi-stage 直接拒絕、非 Alpine/slim 警告、沒有 `USER` 警告、`:latest` 警告。

**講解重點**：規則有三種存在形態——寫在 rule/skill 裡（靠 agent 自律）、常駐注入 context（靠 alwaysApply/hook 提醒）、**寫成會 fail 的檢查**（靠腳本強制）。同一套馬尾哥哲學三種形態都有，強度遞增。真正重要的規則，最後都該走到第三種——而第三種（bash 腳本）在哪個編輯器都能跑。

---

## Step 7：總驗收——讓 rule 咬人、讓 doctor 跑起來

前面六步把四批貨都搬完了。現在驗收整包能力在 Cursor 裡是不是真的活著。

### 7-1 讓 rule 咬人

在練習專案開 **Agent 模式**對話，說：

> 「幫我寫一個 React 的 Modal 元件，用 react-modal 套件。」

✅ **預期看到**：AI 引用 ponytail 規則反問或直接改用原生 `<dialog>` + `.showModal()`——因為 rule 的替換表明寫「modal 套件是 slop，用 `<dialog>`」。如果 AI 乖乖裝了 react-modal，代表 rule 沒生效。

🧯 **卡住的話**：檢查 `.cursor/rules/*.mdc` 的副檔名與 frontmatter（`alwaysApply: true` 那條有沒有生效）、是否在 Agent 模式（Ask 是唯讀問答模式——官方 CLI 文件描述為 "Toggle Ask mode for read-only questions"，[cursor.com/docs/cli/reference/slash-commands](https://cursor.com/docs/cli/reference/slash-commands)）。

### 7-2 跑 `/superstack-doctor`

在 Agent 輸入框打 `/superstack-doctor`（Step 4 搬好的指令）。

✅ **預期看到**：Agent 照 prompt 檔用 Bash 逐項偵測，以三段清單回報——A 級前置工具（node/npx、uvx、docker daemon）、B 級憑證偵測（只報有／無）、skills 就緒狀態，最後一句總結「已就緒 N 項；想再開 M 項，看 `mcp-optional.example.json`」。**全程沒有任何一個憑證的值被印出來。**

🧯 **卡住的話**：Agent 執行 Bash 前可能逐次要你確認——這是 Cursor 的工具確認機制，正常；也再次提醒你：這裡沒有 `allowed-tools` 那道機制級保險，盯著它只用 Bash 和 Read。

### 7-3 （選配）試 Plan 模式

用 Plan 模式跑一次「幫這個專案加一個健康檢查 endpoint」。官方文件（[cursor.com/docs/agent/modes](https://cursor.com/docs/agent/modes)）：

> "Plan Mode creates detailed implementation plans before writing any code."
> （Plan 模式在寫任何程式碼之前，先產出詳細的實作計畫。）

✅ **預期看到**：計畫本身就被 ponytail rule 管到——不會出現「為以後留彈性」的投機項目。官方也說 "For quick changes or tasks you've done many times before, jumping straight to Agent mode is fine."（快速修改或做過很多次的任務，直接用 Agent 模式就好。）

**走完這步你就懂了**——**「能力」是可攜的，「打包方式」是平台的**。同一份 Markdown 紀律 + 同一段 MCP JSON，在 Claude Code 叫 plugin，在 Cursor 叫 rules + commands + hooks + mcp.json。學會拆解機制，換平台只是換打包。

---

## 附錄（延伸）：在 Claude Code 原生安裝這個 plugin

如果你也裝了 Claude Code CLI，可以體驗「一包到位」的原生安裝——對照出 plugin 機制的價值。

```bash
# 在 cursor-sample-projects/ 這層執行——用 --plugin-dir 載入本地 plugin（只作用於該次 session）
claude --plugin-dir ./lazy-cloud-devops
```

> repo README 寫的 `claude plugin add --path` 是舊版語法（2026-08 實測現行 CLI 已無此子指令）；要長期安裝，用 session 內的 `/plugin` 互動選單或 marketplace 流程（`claude plugin marketplace add` + `claude plugin install`）。CLI 語法隨版本演進，`claude plugin --help` 對照當前版本。

載入後：SessionStart hook 自動觸發（session 一開始 context 就有馬尾哥守衛——就是你 Step 3 親手印出來的那段；matcher `startup|resume|clear` 連 `/clear` 後都重新注入）；五個 skill 由 agent 依 frontmatter `description` 自動觸發；`/lazy-ship`、`/superstack-doctor` 直接可用（含 `allowed-tools` 與 `$1/$2` 參數）；A 級 MCP 直接就緒。

🧯 **卡住的話**：`--plugin-dir` 要指向**含 `.claude-plugin/plugin.json` 的那層**，不是它的上層或子目錄。

**一句話總結兩邊差異**：Claude Code 用 plugin 一次裝一包、`allowed-tools` 把權限收斂到指令層級；Cursor 用 `.cursor/` 目錄逐批宣告、換來的是 rules 的四種觸發型態與跨生態相容（連 `.claude/skills/` 都讀）。沒有誰全面贏——所以這堂課教的是機制，不是品牌。

---

## 驗收清單

- [ ] 能指著 `plugin.json` 說出 `skills` / `commands` / `hooks` / `mcpServers` 四批貨在 Cursor 各對應什麼（rules/skills、commands、hooks.json、mcp.json）
- [ ] 在自己的專案建好 `.cursor/rules/ponytail-guard.mdc`（alwaysApply）與 `ponytail-frontend.mdc`（globs），並能說出 Rules 的四種觸發型態
- [ ] 能說出 Cursor hook 與 Claude Code hook 的兩個差異（輸出要包 JSON 的 `additional_context`；內容固定時 alwaysApply rule 是更簡單的等價物）
- [ ] 把 `/lazy-ship`、`/superstack-doctor` 搬進 `.cursor/commands/` 並在 `/` 下拉選單看到；能說出 `allowed-tools`、`$1/$2` 在 Cursor 沒有官方等價物
- [ ] 建好 `.cursor/mcp.json` 掛上 A 級兩個 server 且亮綠燈；能解釋 A/B 級分級標準與 `${env:NAME}` 插值的用途
- [ ] 能說出 Vendored / Wired / Inspired 三種處置的定義，以及複製 .mdc 時 LICENSE 與註記為什麼要跟著走
- [ ] rule 咬人測試通過：要求用 react-modal 時，Agent 引規則改用 `<dialog>`
- [ ] 能說出 Postgres 為什麼不用官方 server-postgres（archived + SQLi）

## 常見坑排錯速查

| 症狀 | 最可能的原因 | 快速修法 |
|---|---|---|
| `demo.sh` 每幕都空白 | REPO_DIR 指不到教材 repo | 確認 `lazy-cloud-devops/` 與 `project-16-lazy-superstack-plugin/` 同層 |
| Cursor rule 沒生效 | 副檔名不是 `.mdc`、不在 `.cursor/rules/`、frontmatter 格式錯 | 檢查檔名/目錄/frontmatter 三件套；到 Rules 設定頁確認有列出 |
| rule 有列出但 AI 不理 | 在 Ask 模式測、或 description 太模糊讓 Agent 判斷不相關 | 換 Agent 模式；常駐紀律用 `alwaysApply: true` |
| `/` 下拉沒有自訂指令 | Cursor 版本 < 1.6、或檔案不在 `.cursor/commands/` | 升級 Cursor；確認路徑與 `.md` 副檔名 |
| hook 沒注入 | 腳本輸出不是 JSON、沒執行權限、沒重啟 Cursor | 終端機直接跑腳本驗證輸出是 `{"additional_context": ...}`；`chmod +x`；重啟 |
| context7 MCP 紅燈 | 沒有 node/npx，或首次 `npx -y` 在拉套件 | 裝 Node.js 18+；等首次下載完成再看 |
| Docker MCP 紅燈 | 沒有 `uvx`（uv 沒裝） | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| B 級 MCP 一開就噴錯 | 憑證環境變數沒設就複製了區塊 | 這正是它預設不開的原因；設好 `${env:NAME}` 對應的變數再開 |
| MCP JSON 解析錯 | 把 `_doc` / `_README` 底線欄位一起搬了 | 搬進 `.cursor/mcp.json` 前刪掉註解欄位 |
| MCP 工具很多但 Agent 亂選 | 一次開了太多 server | 用 Customize 的開關關掉沒在用的；一次只開需要的 |
| `sync-vendored.sh` 跑完 git diff 一片紅 | 上游覆蓋洗掉了前綴與 Vendored 註記 | 預期行為——照腳本結尾提醒，用 git diff 重套前綴與註記 |
| 想跑 `/lazy-ship` 真部署 | 需要 gcloud/aws CLI + 憑證 + Docker + 有 Dockerfile 的專案 | 課堂不部署；自己練習時先讀 `scripts/deploy-gcp.sh` 的 env 說明 |

## 帶走的三句話

如果整份專案只能記住三件事，就這三句：

1. **能力是可攜的，打包方式是平台的**——Markdown 紀律、prompt 工作流、MCP JSON 走到哪都能用；Claude Code 叫 plugin/skill/hook，Cursor 叫 rules/commands/hooks.json/mcp.json。學機制，不學品牌。

2. **規則要挑對觸發型態**——常駐紀律用 `alwaysApply`（等價 SessionStart hook）、領域細則用 `globs`、方法論用 description 讓 Agent 判斷、罕用的手動 `@`。全部 alwaysApply 就是把米其林變回吃到飽：常駐 context 是稀缺資源。

3. **搬家不豁免合規，也不豁免策展**——複製 vendored 內容進 `.cursor/` 時 LICENSE 與註記要跟著走；MCP 沒憑證就別掛（兩級啟用）；真正重要的規則最終要寫成會 fail 的檢查（footprint gate），那一層跟編輯器無關。

---

## ❓ 思考題（四題，先想再看答案）

### ❓ 想一想 1：策展的安全課

**題目**：這個 repo 為什麼堅持用 Postgres MCP Pro，而不是名氣更大的官方 `@modelcontextprotocol/server-postgres`？這給「選 MCP / 選套件」什麼一般性教訓？

<details><summary>看答案</summary>

`mcp-optional.example.json` 的 `_doc` 與設計規格都寫明：官方 server-postgres **已 archived（2025-07）且有 SQL injection 漏洞**。教訓：選材不能只看「官方」「星星多」，要查三件事——還在維護嗎、有沒有安全公告、有沒有更健康的替代品。名氣是滯後指標，維護狀態才是領先指標。這條跟你用哪個編輯器無關——掛進 `.cursor/mcp.json` 的每個 server 都該過這關。（順帶一提：設計規格還記載調研 agent 回報的星數「疑似幻覺」，要用 GitHub API 核實——AI 給的選材情報也要驗證。）

</details>

### ❓ 想一想 2：alwaysApply 的存在理由

**題目**：ponytail 的完整規則已經有 296 行的 SKILL.md 了，為什麼 Step 2 還要另外做一條精簡的 `alwaysApply` 摘要 rule？兩者不是重複了嗎？

<details><summary>看答案</summary>

不重複，是分工——而且這個分工在兩邊生態長得一樣。完整規則書（296 行，含前端/DB/容器/雲端細則）适合按需載入：Claude Code 靠 skill 的 description 觸發，Cursor 靠 Apply Intelligently rule 或 2.4+ skill（官方原話："Skills load resources on demand, keeping context usage efficient."）。常駐的只放**精簡摘要**（Slop Test 四問 + 核心法則）：Claude Code 靠 SessionStart hook，Cursor 靠 `alwaysApply: true`。如果把 296 行全部常駐，每個對話都浪費大量 context；如果全部按需，頭幾輪 agent 可能還沒想到要載入就生出 slop。摘要常駐 + 全文按需，是 context 預算的正確花法——官方那句「規則保持在 500 行以內」管的正是這件事。

</details>

### ❓ 想一想 3：第九個領域怎麼加

**題目**：假設你要幫這包能力加第九個領域「資料工程」（dbt、Airflow 之類），而且要同時服務用 Claude Code 和用 Cursor 的同事。照這個 repo 的策展紀律，你的決策流程是什麼？

<details><summary>看答案</summary>

依序問：(1) **有官方 / 健康維護的 MCP server 嗎？**有就 wire——這是最划算的選項，因為 MCP 設定兩邊通用：加進 `mcp-optional.example.json`（大概率需憑證，屬 B 級），Cursor 同事複製區塊進 `.cursor/mcp.json`、Claude Code 同事複製進 `.mcp.json`，並在 THIRD_PARTY_NOTICES.md B 區補一列。(2) **沒有 server、但社群有無可替代的方法論 skill 且授權允許重分發？**才 vendor——附 LICENSE、檔頂註記、前綴防撞名；Cursor 側放 `.cursor/rules/` 或 `.cursor/skills/`。(3) **兩者都沒有？**評估自寫（Inspired，致謝方法論來源），或——最馬尾哥的選項——**先不加**：需求還不明確就加能力，本身就是 slop。

</details>

### ❓ 想一想 4：doctor 的鐵律與消失的保險

**題目**：`/superstack-doctor` 的鐵律是「絕不印出憑證的值」。在 Claude Code 它還有 `allowed-tools: Bash, Read` 這道機制級保險；搬到 Cursor 後這道保險不存在了。憑證如果被印出，具體會發生什麼壞事？你在 Cursor 端能補上什麼防線？

<details><summary>看答案</summary>

憑證一旦被印出，就進了對話 context——接著可能被寫進對話紀錄、被後續工具呼叫夾帶、出現在你分享給同事的截圖或轉錄裡。**agent 的輸出就是一種 log**（OWASP 的「No sensitive data in logs」在 agent 時代的版本）。Cursor 端的防線：(1) prompt 鐵律照搬（第一層，自律）；(2) 憑證只放環境變數並用 `${env:NAME}` 插值，設定檔裡永遠沒有明文（第二層，讓「印出設定檔」也印不到值）；(3) Cursor 的 hooks 支援 `beforeShellExecution` 等事件，可以做指令級的把關（第三層，機制），細節見官方 hooks 文件。安全邊界要往「就算模型忘了也擋得住」的層級推。

</details>

---

## 最後一句話

這份教學的目標不是教你「用 Lazy Superstack」，也不是教你「Cursor 設定大全」。它是一次完整的搬家演習——把一包策展好的 agent 能力，從一個生態搬進另一個生態，途中你被迫搞懂每一種機制的本質：什麼是知識（rules/skills）、什麼是時機（hooks/alwaysApply）、什麼是工作流（commands）、什麼是手腳（MCP）、什麼是打包（plugin）。機制搞懂了，之後再出現第三個、第四個 agent 編輯器，你都搬得動。記住那句話——**把雜訊綁起來，只留下訊號。**
