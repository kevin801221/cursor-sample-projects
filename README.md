# Cursor 實戰專案課（第 22–33 章）

書中 Part 05「12 個從零到部署的 Step-by-Step 專案」。每個資料夾都有 `README.md`（專案是什麼）與 `walkthrough.md`（在 Cursor 上一步一步做出來）。

> 🧯 **上課與自學必備**：若遇到任何環境問題、指令報錯或卡點，請直接查閱 **[TROUBLESHOOTING-MASTER.md](./TROUBLESHOOTING-MASTER.md)（14 專案防翻車與 30 秒救援總手冊）**。
> ☁️ **Supabase 地端 vs 雲端**：Docker 本地已安裝狀態與雲端切換免跑指令對照見 **[SUPABASE-LOCAL-VS-CLOUD.md](./SUPABASE-LOCAL-VS-CLOUD.md)**。

| 資料夾 | 章 | 專案 | 一句話 |
|---|---|---|---|
| [project-1](./project-1/) | — | 第 0 課：環境準備日 | 裝機五件套 + 帳號總表 + 健康檢查全綠——把必然會發生的失敗前移 |
| [project-2](./project-2/) | 22–23 | TaskBoard（Next.js + Supabase + 金流） | 多租戶隔離做在資料庫層 RLS；webhook 沒驗簽等於任何人都能偽造付費事件（課堂版用 [Mock 金流](./project-2/walkthrough-2-mock-payment.md)，進階版用 [Stripe](./project-2/walkthrough-2-stripe.md)） |
| [project-3](./project-3/) | 24 | Figma / 截圖轉 React 元件庫 | 設計轉程式碼最容易生出一次性樣式，design tokens + rules 先行 |
| [project-4](./project-4/) | 25 | React Native + Expo 習慣追蹤 App | 行動端 UI 一改就跑版，用規則和 Checkpoint 雙重把關 |
| [project-5](./project-5/) | 26 | FastAPI 後端 API 與雲端部署 | 分層架構加 Pydantic 驗證，讓 Agent 不把邏輯全塞一起 |
| [project-6](./project-6/) | 27 | Chrome 擴充功能（Manifest V3） | API key 放錯地方，等於把金鑰送給每個造訪過的網頁 |
| [project-7](./project-7/) | 28 | Python 爬蟲價格監控 PriceBot | 合法合規比技術難度更重要，動手前先查五件事 |
| [project-8](./project-8/) | 29 | pandas + Streamlit 營運儀表板 | 把髒資料清乾淨、算對指標，做成能互動的儀表板 |
| [project-9](./project-9/) | 30 | RAG 知識庫 Chatbot | 查完再答，公司文件秒回答案還附出處 |
| [project-10](./project-10/) | 31 | 自建 MCP Server | 自己寫工具讓 Agent 呼叫，而不是只靠內建能力 |
| [project-11](./project-11/) | 32 | Phaser 3 平台跳躍遊戲 Rooftop Dash | 從一頁 GDD 開始，疊代出一個能玩的遊戲 |
| [project-12](./project-12/) | 33 | CLI 工具與 Telegram Bot | 打造能發佈的 CLI，加一個會發圖的 Bot |
| [project-13](./project-13/) | — | AutoCV：5 個 AI agent 自動訓練 YOLO（[repo](./auto-cv-train-optimization-claude_code/)） | 打一句話讓 agents 接力訓練模型；再用優化階梯把成績「幾乎一定」推得更好 |
| [project-14](./project-14/) | — | GraphRAG 問答機器人（[repo](./agent-automatic-graphrag-chat-skill/)） | 丟一個 YouTube 連結，建出附時間戳引用、即時高亮知識圖譜的問答機器人 |

project-13、14 以 Kevin 的兩個開源 repo 為教材，資料夾內是教學文件，程式碼在各自的 repo。
