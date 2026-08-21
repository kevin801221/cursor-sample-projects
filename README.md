# Cursor 實戰專案課（第 22–33 章）

書中 Part 05「12 個從零到部署的 Step-by-Step 專案」。每個資料夾都有 `README.md`（專案是什麼）與 `walkthrough.md`（在 Cursor 上一步一步做出來）。

> 🧯 **上課與自學必備**：若遇到任何環境問題、指令報錯或卡點，請直接查閱 **[TROUBLESHOOTING-MASTER.md](./TROUBLESHOOTING-MASTER.md)（17 專案課前檢查與快速救援總手冊）**。
> ☁️ **Supabase 地端 vs 雲端**：Docker 本地已安裝狀態與雲端切換免跑指令對照見 **[SUPABASE-LOCAL-VS-CLOUD.md](./SUPABASE-LOCAL-VS-CLOUD.md)**。
> 🤖 **跨 Agent 使用**：核心程式可以共用，但設定層要分平台轉接；邊界與驗收標準見 **[AGENT-PORTABILITY.md](./AGENT-PORTABILITY.md)**。
> ✅ **課前一鍵檢查**：開課前跑 `./preflight.sh`——17 個資料夾、5 個教材 repo、所有 demo.sh 與 md 連結一次驗完，全綠再開課。

## SQLite 視覺化檢視器

不用安裝資料庫 GUI；從 repo 根目錄執行後會自動開啟瀏覽器。工具只用唯讀連線，適合課堂查看資料表、欄位、筆數、分頁與搜尋：

```bash
# 自動掃描並讓你選擇 .db / .sqlite / .sqlite3
uv run tools/sqlite_viewer.py

# 或直接指定資料庫
uv run tools/sqlite_viewer.py project-5-fastapi-backend/shortenurl/shortenurl.db
uv run tools/sqlite_viewer.py project-7-price-monitor-scraper/pricebot/data/pricebot.db
uv run tools/sqlite_viewer.py Anchor_knowledge.ai/data/app.db
```

若不想自動開瀏覽器，加上 `--no-browser`；終端機按 `Ctrl+C` 即可關閉。

| 資料夾 | 章 | 專案 | 一句話 |
|---|---|---|---|
| [project-1-environment-setup](./project-1-environment-setup/) | — | 第 0 課：環境準備日 | 裝機五件套 + 帳號總表 + 健康檢查全綠——把必然會發生的失敗前移 |
| [project-subagent-hooks](./project-subagent-hooks/) | — | Subagent + Hooks 實戰 | Subagent 決定誰來做，Hook 決定什麼一定會發生、什麼絕對不准發生；雙軌協同為 API 加上防護網 |
| [project-2-taskboard-saas](./project-2-taskboard-saas/) | 22–23 | TaskBoard（Next.js + Supabase + 金流） | 多租戶隔離做在資料庫層 RLS；webhook 沒驗簽等於任何人都能偽造付費事件（課堂版用 [Mock 金流](./project-2-taskboard-saas/walkthrough-2-mock-payment.md)，進階版用 [Stripe](./project-2-taskboard-saas/walkthrough-2-stripe.md)） |
| [project-3-react-component-library](./project-3-react-component-library/) | 24 | Figma / 截圖轉 React 元件庫 | 設計轉程式碼最容易生出一次性樣式，design tokens + rules 先行 |
| [project-4-habit-tracker-app](./project-4-habit-tracker-app/) | 25 | React Native + Expo 習慣追蹤 App | 行動端 UI 一改就跑版，用規則和 Checkpoint 雙重把關 |
| [project-5-fastapi-backend](./project-5-fastapi-backend/) | 26 | FastAPI 後端 API 與雲端部署 | 分層架構加 Pydantic 驗證，讓 Agent 不把邏輯全塞一起 |
| [project-6-chrome-extension](./project-6-chrome-extension/) | 27 | Chrome 擴充功能（Manifest V3） | API key 放錯地方，等於把金鑰送給每個造訪過的網頁 |
| [project-7-price-monitor-scraper](./project-7-price-monitor-scraper/) | 28 | Python 爬蟲價格監控 PriceBot | 合法合規比技術難度更重要，動手前先查五件事 |
| [project-8-operations-dashboard](./project-8-operations-dashboard/) | 29 | pandas + Streamlit 營運儀表板 | 把髒資料清乾淨、算對指標，做成能互動的儀表板 |
| [project-9-rag-chatbot](./project-9-rag-chatbot/) | 30 | RAG 知識庫 Chatbot | 查完再答，公司文件秒回答案還附出處 |
| [project-10-mcp-server](./project-10-mcp-server/) | 31 | 自建 MCP Server | 自己寫工具讓 Agent 呼叫，而不是只靠內建能力 |
| [project-11-rooftop-dash-game](./project-11-rooftop-dash-game/) | 32 | Phaser 3 平台跳躍遊戲 Rooftop Dash | 從一頁 GDD 開始，疊代出一個能玩的遊戲 |
| [project-12-cli-telegram-bot](./project-12-cli-telegram-bot/) | 33 | CLI 工具與 Telegram Bot | 打造能發佈的 CLI，加一個會發圖的 Bot |
| [project-13-autocv-yolo-agents](./project-13-autocv-yolo-agents/) | — | AutoCV：5 個 AI agent 自動訓練 YOLO（[repo](./auto-cv-train-optimization-claude_code/)） | 打一句話讓 agents 接力訓練模型；再用優化階梯把成績「幾乎一定」推得更好 |
| [project-14-graphrag-chatbot](./project-14-graphrag-chatbot/) | — | GraphRAG 問答機器人（[repo](./agent-automatic-graphrag-chat-skill/)） | 丟一個 YouTube 連結，建出附時間戳引用、即時高亮知識圖譜的問答機器人 |
| [project-15-rag-architect-mcp](./project-15-rag-architect-mcp/) | — | RAG Architect：RAG 架構藍圖 MCP Server（[repo](./rag-architect-mcp/)） | MCP 工具會不會被 AI 自動調用是設計出來的；不准出錯的決策交給純函式路由——可稽核，才值得信任 |
| [project-16-lazy-superstack-plugin](./project-16-lazy-superstack-plugin/) | — | Lazy Superstack：一個 plugin 長出八大能力（[repo](./lazy-cloud-devops/)） | Skill／Command／Hook／MCP 是 agent 的四種器官，plugin 把它們捆成一包；策展的紀律是能 wire 就不 vendor |
| [project-17-anchor-pdf-ai-reader](./project-17-anchor-pdf-ai-reader/) | — | Anchor：框選 PDF 問 AI 的知識圖譜閱讀器（[repo](./Anchor_knowledge.ai/)） | 框住卡你的那一塊直接問——精確文字＋忠實截圖雙通道送模型；每次問答蒸餾成記憶圖譜，PDF 不出你的電腦 |

project-13～17 以開源 repo 為教材（project-13、14 為 Kevin 的兩個 repo），資料夾內是教學文件，程式碼在各自的 repo。其中 `rag-architect-mcp/`、`lazy-cloud-devops/`、`Anchor_knowledge.ai/` 是 git submodule——**剛 clone 完先跑 `git submodule update --init`**（或 clone 時加 `--recurse-submodules`），否則這三個資料夾會是空的。

## 🧭 建議授課順序

前半按上手難度爬坡（每堂都有一個「哇」時刻），後半是 AI 應用縱深一路疊上去；project-2 內容最重（多租戶 RLS + 金流），留到壓軸選講。

| 順位 | 專案 | 為什麼排這裡 |
|---|---|---|
| 0 | [project-1-environment-setup](./project-1-environment-setup/) | 第 0 課：環境健康檢查全綠再開課，把必然的失敗前移 |
| 1 | [project-subagent-hooks](./project-subagent-hooks/) | **核心心智模型先行**：學會 Subagent 分工與 Hooks 確定性護欄，為後續所有開發立下安全紀律 |
| 2 | [project-3-react-component-library](./project-3-react-component-library/) | 純前端、最快有成就感：截圖變元件，順便學 rules |
| 3 | [project-8-operations-dashboard](./project-8-operations-dashboard/) | Python 資料入門：清資料、算指標、互動儀表板 |
| 4 | [project-7-price-monitor-scraper](./project-7-price-monitor-scraper/) | Python 進階 + 合法合規思維（動手前先查五件事） |
| 5 | [project-5-fastapi-backend](./project-5-fastapi-backend/) | 後端分層、Pydantic 驗證、第一次雲端部署 |
| 6 | [project-6-chrome-extension](./project-6-chrome-extension/) | 前後端整合 + 金鑰安全（放錯地方等於送人） |
| 7 | [project-12-cli-telegram-bot](./project-12-cli-telegram-bot/) | 打包與發佈：CLI 工具 + Telegram Bot |
| 8 | [project-11-rooftop-dash-game](./project-11-rooftop-dash-game/) | 中場趣味：從一頁 GDD 疊代出能玩的遊戲 |
| 9 | [project-4-habit-tracker-app](./project-4-habit-tracker-app/) | 行動端（模擬器環境費時，放大家熟練之後） |
| 10 | [project-9-rag-chatbot](./project-9-rag-chatbot/) | AI 縱深起點：RAG——查完再答、答案附出處 |
| 11 | [project-10-mcp-server](./project-10-mcp-server/) | 自建 MCP Server：讓 agent 有自己的工具 |
| 12 | [project-14-graphrag-chatbot](./project-14-graphrag-chatbot/) | RAG 進階：GraphRAG + Neo4j 知識圖譜 |
| 13 | [project-13-autocv-yolo-agents](./project-13-autocv-yolo-agents/) | multi-agent：五個 agent 接力訓練 YOLO |
| 14 | [project-15-rag-architect-mcp](./project-15-rag-architect-mcp/) | MCP × RAG 集大成：確定性架構路由（RAG router） |
| 15 | [project-16-lazy-superstack-plugin](./project-16-lazy-superstack-plugin/) | agent 能力生態系：rules／MCP／commands 的策展 |
| 16 | [project-17-anchor-pdf-ai-reader](./project-17-anchor-pdf-ai-reader/) | 完整產品收官：local-first 全端 side project |
| 17 | [project-2-taskboard-saas](./project-2-taskboard-saas/) | 壓軸選講：多租戶 RLS + 金流——最難講，學生也要有前面全部的底子 |
