# Lazy Superstack：把一包 agent 能力搬進 Cursor

> Cursor 課程 Project 16：拿一個真實的 Claude Code plugin（`Lazy Superstack`）當素材，把它捆的八大能力——PM、設計思考、馬尾哥極簡、資料庫、全端、AI 應用、雲端部署、資安——**在 Cursor 裡用 Rules / Commands / Hooks / MCP 一步一步重新長出來**。

一句話：**Rules 給知識、Commands 給工作流、Hooks（或 alwaysApply）給時機、MCP 給手腳——能力是可攜的，打包方式才是平台的；而策展的紀律是：授權要清楚、能 wire 就不 vendor、塞太多本身就是 slop。**

## 專案規格

| | |
|---|---|
| **最終成果** | 在自己的專案建出完整的 `.cursor/` 能力層：`rules/*.mdc`（ponytail 紀律，alwaysApply + globs 兩種觸發）、`commands/`（/lazy-ship、/superstack-doctor）、`hooks.json`（sessionStart 注入）、`mcp.json`（A 級零憑證直掛、B 級 `${env:NAME}` 插值）；並能對照說出每個機制在 Claude Code plugin 端的原形 |
| **技術棧** | Cursor Rules（`.cursor/rules/*.mdc`，description / globs / alwaysApply）、Cursor 自訂 slash commands（`.cursor/commands/*.md`，1.6+）、Cursor Hooks（`.cursor/hooks.json` sessionStart，JSON stdio）、Cursor 原生 Skills（SKILL.md，2.4+）、`.cursor/mcp.json`（MCP servers：Context7 / Docker / MongoDB / Postgres / AWS / Terraform / GitHub / shadcn）、素材：Claude Code plugin 系統 |
| **預估時間** | 2.5–3 小時（素材唯讀研究 + 在自己專案動手建 `.cursor/` 設定） |
| **前置需求** | Cursor（Rules 與 mcp.json 很早就有；自訂 commands 需 1.6+、原生 Skills 需 2.4+）＋終端機；node/npx 與 uvx（A 級 MCP 前置工具）；選配：Claude Code CLI（文末附錄的原生安裝體驗用） |

## 這個專案做什麼

素材 `Lazy Superstack`（教材資料夾名 `lazy-cloud-devops`）是一個 **AI coding agent 能力捆綁包**：在 Claude Code 裝這一個 plugin，agent 就同時長出八大領域的能力。它不是程式，是一包「精選過的擴充機制」。本課把這包東西當成**搬家演習的貨物**，逐批搬進 Cursor：

1. **5 個 skills**（Markdown 紀律）→ Cursor **Rules**（`.mdc`：常駐摘要用 `alwaysApply`、前端細則用 `globs`、方法論用 description 觸發）；2.4+ 也可直接搬成原生 **Skills**（SKILL.md 格式相容，官方甚至讀 `.claude/skills/`）
2. **2 個 commands**（`/lazy-ship` 一鍵極簡部署、`/superstack-doctor` 能力體檢）→ `.cursor/commands/*.md`（1.6+；`allowed-tools`、`$1/$2` 沒有官方等價物——課程會誠實拆這個差異）
3. **1 個 SessionStart hook**（注入馬尾哥守衛）→ 兩條路：`.cursor/hooks.json` 的 `sessionStart`（`additional_context` 注入），或更馬尾哥的 `alwaysApply` rule
4. **兩級 MCP wiring** → `.cursor/mcp.json`：A 級零憑證直接掛（Context7、Docker），B 級補憑證再掛（MongoDB、Postgres、AWS、Terraform、GitHub、shadcn），憑證用 `${env:NAME}` 插值不落地

這堂課教的不是「怎麼用這個 plugin」，而是**「AI agent 的能力生態系怎麼組合」**——每種擴充機制的本質是什麼、在 Cursor 怎麼落地、以及哪些差異是真實存在的（每個機制都有「官方怎麼說」小節，引 Cursor 官方文件並附連結）。

## 架構圖

```
   素材：lazy-cloud-devops（Claude Code plugin）          你的專案（Cursor）
   ─────────────────────────────────────────            ──────────────────────────
   .claude-plugin/plugin.json（物品清單）
        │
        ├─ skills/  5 個 SKILL.md「知識與紀律」  ──搬──▶  .cursor/rules/*.mdc
        │   ponytail-guard / design-thinking              （alwaysApply / globs / description）
        │   pm-brainstorming / pm-writing-plans           或 .cursor/skills/（2.4+，SKILL.md 直搬）
        │   security-owasp
        │
        ├─ hooks/   SessionStart 注入「時機」   ──搬──▶  .cursor/hooks.json sessionStart
        │   inject-ponytail.sh                            （additional_context）或 alwaysApply rule
        │
        ├─ commands/ 2 個 prompt 檔「工作流」   ──搬──▶  .cursor/commands/*.md（1.6+）
        │   /lazy-ship  /superstack-doctor                （allowed-tools、$1/$2 無等價物）
        │
        └─ mcpServers「手腳」＋ mcp-optional    ──搬──▶  .cursor/mcp.json
            A 級：Context7、Docker（零憑證）              （同一協議、同一 JSON 形狀；
            B 級：MongoDB/Postgres/AWS/                     憑證用 ${env:NAME} 插值）
                  Terraform/GitHub/shadcn

   三種來源處置與合規（跟著檔案走，跨編輯器不豁免）：
   🖊️ 自有｜📥 Vendored（複製 + 附 LICENSE）｜🔌 Wired（只設定指向，零複製）
   THIRD_PARTY_NOTICES.md ＋ 各目錄 LICENSE ＋ scripts/sync-vendored.sh
```

## 三個值得偷走的設計

**1. 能力分兩級啟用，別讓使用者一裝就噴錯。**
八個 MCP 全部預設開，沒憑證的人一啟動就滿屏紅字。素材 repo 把 MCP 分成 A 級（零憑證）和 B 級（需憑證，只放範本 `mcp-optional.example.json`）——搬進 `.cursor/mcp.json` 時照搬這個精神：A 級直接掛，B 級誰有憑證誰自己搬區塊，而且用 Cursor 官方的 `${env:NAME}` 插值讓設定檔裡永遠沒有明文憑證。`/superstack-doctor` 的鐵律跨平台成立：**絕不印出任何憑證的值，只報有 / 無**。

**2. 規則要挑對觸發型態，全部常駐就是吃到飽。**
Cursor Rules 官方給四種觸發：Always Apply、Apply Intelligently（依 description）、Apply to Specific Files（globs）、Manual（@ 提及）。本課的搬法：Slop Test 摘要用 `alwaysApply: true`（等價 SessionStart hook）、前端替換表用 `globs` 綁前端檔、完整方法論按需觸發。官方建議「規則保持在 500 行以內」——常駐 context 是稀缺資源，這正是策展。

**3. 極簡不是口號，是部署腳本裡的一道閘門。**
`scripts/deploy-gcp.sh` 在部署前稽核 Dockerfile（非 multi-stage 直接 die），建完 image 量大小超過 `MAX_IMAGE_MB`（預設 300）**直接拒絕部署**。規則的三種存在形態——rule 自律、常駐注入、會 fail 的硬檢查——強度遞增，而最強的那層是 bash，在哪個編輯器都能跑。

## 快速開始

```bash
# 教材 repo 與本資料夾（project-16-lazy-superstack-plugin/）同層；先看素材
cd ../lazy-cloud-devops
cat .claude-plugin/plugin.json          # 物品清單：四批要搬進 Cursor 的貨
bash hooks/inject-ponytail.sh           # 親手看 hook 注入什麼（離線、唯讀）

# 回到你自己的練習專案，開始搬（完整步驟見 walkthrough.md Step 2–5）
mkdir -p .cursor/rules .cursor/commands
# 1. 建 .cursor/rules/ponytail-guard.mdc（alwaysApply: true，Slop Test 四問）
# 2. 搬兩個指令
cp ../lazy-cloud-devops/commands/lazy-ship.md        .cursor/commands/
cp ../lazy-cloud-devops/commands/superstack-doctor.md .cursor/commands/
# 3. 建 .cursor/mcp.json 掛 A 級（context7 + docker），到 Settings → MCP 看綠燈
```

> Cursor 行為以官方文件為準（Rules / MCP / Hooks / Skills 各章附引文與連結）；官方沒寫的（如 command 的 `$1` 參數替換）課程明說「無官方等價物，以實測為準」。完整逐步教學見 [walkthrough.md](./walkthrough.md)。

## 核心教學重點

| 段落 | 重點 | 驗證方式 |
|---|---|---|
| Step 1 | `plugin.json` 是搬家物品清單：skills / commands / hooks / mcpServers 四批貨各對應 Cursor 的什麼 | 能說出四批貨的 Cursor 落點 |
| Step 2 | Skill → Rules：`.mdc` frontmatter（description / globs / alwaysApply）與四種觸發型態；2.4+ 原生 Skills 直搬 SKILL.md | Rules 設定頁列出兩條 rule，觸發型態正確 |
| Step 3 | Hook → 兩條路：`.cursor/hooks.json` sessionStart（JSON `additional_context`）或 alwaysApply rule | 新對話裡 agent 能複述三條 CORE LAWS |
| Step 4 | Command → `.cursor/commands/`：prompt 可搬；`allowed-tools`、`$1/$2` 無官方等價物要改寫 | `/` 下拉出現兩個自訂指令 |
| Step 5 | MCP → `.cursor/mcp.json`：兩級啟用照搬、`${env:NAME}` 插值、`_doc` 註解欄位要清掉 | Settings → MCP 兩個 A 級 server 亮綠燈 |
| Step 6 | 策展合規（平台無關）：LICENSE、NOTICES、sync-vendored.sh；複製進 `.cursor/` 不豁免 | 說得出 Vendored / Wired / Inspired 差在哪 |
| Step 7 | 總驗收：rule 咬人（react-modal → `<dialog>`）＋ `/superstack-doctor` 體檢 | Agent 模式實測通過 |
| 附錄 | Claude Code 原生安裝（`--plugin-dir`）：體驗 plugin「一包到位」的價值與 `allowed-tools` 的機制級保險 | 選配 |

## 誠實的限制

- **Cursor 沒有 plugin 等價物**——沒有「裝一個包全部到位」的機制，要逐批把設定搬進 `.cursor/`。這是限制，也是本課的教學價值：逐批搬一次，你就真正懂每個機制。
- **`allowed-tools` 與 `$1/$2` 在 Cursor 沒有官方等價物**——doctor 的「不寫檔」保險在 Cursor 只剩 prompt 自律層；課程直說，不粉飾。
- **Cursor 功能隨版本演進快**——自訂 commands 需 1.6+、原生 Skills 與 `/migrate-to-skills` 需 2.4+、hooks 的欄位細節以你安裝的版本實測為準；官方文件連結都附在 walkthrough 各章。
- **`/lazy-ship` 與 deploy 腳本需要真實雲端帳號**（gcloud / aws CLI + 憑證 + Docker）才能真的部署；課堂上只讀腳本、講設計，不現場燒錢。
- **B 級 MCP 沒憑證就是不能用**——這正是兩級設計存在的原因，不是課程的缺陷。
- 素材 repo 的設計規格（docs/superpowers/specs/）誠實記著一條教訓：調研 agent 回報的 GitHub 星數「部分明顯偏高（疑似幻覺）」，實作前要用 GitHub API 核實——連選材本身都要先測後信。

## 檔案結構

```
project-16-lazy-superstack-plugin/ # 本教學資料夾（只有教學文件）
├── README.md                      # 這份（規格卡）
├── walkthrough.md                 # 完整逐步教學（Cursor 主軸）
└── demo.sh                        # 課堂遙控器（6 幕，全部離線唯讀）

../lazy-cloud-devops/              # 素材 repo（Claude Code plugin，本課不改動它）
├── .claude-plugin/plugin.json     # 物品清單：skills + commands + hooks + A 級 MCP
├── skills/                        # → 搬去 .cursor/rules/ 或 .cursor/skills/
│   ├── ponytail-guard/            # 🖊️ 自有：極簡鐵律（Slop Test + 前端/DB/容器/雲端規則）
│   ├── design-thinking/           # 🖊️ 自有：d.school 五階段
│   ├── pm-brainstorming/          # 📥 vendored from obra/superpowers（MIT）
│   ├── pm-writing-plans/          # 📥 vendored from obra/superpowers（MIT）
│   ├── security-owasp/            # 📥 vendored from agamm/claude-code-owasp（MIT）
│   └── README.md                  # skill 來源與命名空間對照表
├── commands/                      # → 搬去 .cursor/commands/
│   ├── lazy-ship.md               # /lazy-ship 一鍵極簡部署
│   └── superstack-doctor.md       # /superstack-doctor 能力體檢
├── hooks/                         # → 對應 .cursor/hooks.json sessionStart 或 alwaysApply rule
│   ├── hooks.json                 # SessionStart matcher（Claude Code 語法）
│   └── inject-ponytail.sh         # 注入馬尾哥守衛 + 能力地圖
├── scripts/
│   ├── deploy-gcp.sh              # Cloud Run 部署（含 footprint gate）
│   ├── deploy-aws.sh              # ECS Fargate 部署（含 footprint gate）
│   └── sync-vendored.sh           # 從上游重新同步 2 個 vendored 來源
├── mcp-optional.example.json      # B 級 MCP 範本（6 個 server）→ 搬去 .cursor/mcp.json
├── docs/superpowers/specs/        # 設計規格（決策紀錄）
├── THIRD_PARTY_NOTICES.md         # Vendored / Wired / Inspired 三類來源彙整
└── LICENSE                        # MIT
```

## 帶走的三句話

1. **能力是可攜的，打包方式是平台的**——Markdown 紀律、prompt 工作流、MCP JSON 走到哪都能用；學會拆解機制，換平台只是換打包。
2. **規則要挑對觸發型態**——常駐摘要 alwaysApply、領域細則 globs、方法論按需觸發；全部常駐就是把米其林變回吃到飽。
3. **搬家不豁免合規與策展**——LICENSE 與註記跟著複本走、沒憑證的 MCP 不掛、真正重要的規則寫成會 fail 的檢查。

## 官方文件（本課引用）

- Rules：https://cursor.com/docs/context/rules
- MCP：https://cursor.com/docs/context/mcp
- Hooks：https://cursor.com/docs/agent/hooks
- Skills：https://cursor.com/docs/context/skills
- Agent/Plan 模式：https://cursor.com/docs/agent/modes
- 自訂 commands（1.6 changelog）：https://cursor.com/changelog/1-6

## 授權

教材 repo（lazy-cloud-devops / Lazy Superstack）本體為 MIT；vendored 第三方內容各依其原始授權（皆 MIT，附於各 skill 目錄 LICENSE），完整彙整見 repo 的 `THIRD_PARTY_NOTICES.md`。
