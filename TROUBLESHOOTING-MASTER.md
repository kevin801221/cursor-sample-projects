# 🧯 全課程 17 專案課前檢查與卡點救援總手冊（講師與學生必備）

> **這份手冊的目的**：把課堂上、自學時最常見的卡點與救援路徑集中在一處。
> 多數問題可以快速定位；帳號、網路、API 配額、Docker 與第三方服務故障仍需在課前實測，不能用文件保證一定可用。

---

## ⚡ 1. 課堂萬用三大黃金自救法

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ 1. 遇到資料被改亂、誤刪卡片、想重置：                                         │
│    👉 直接執行該專案的重置指令（例如 Project 2 執行 ./demo.sh 3），1 秒回血！   │
├────────────────────────────────────────────────────────────────────────────┤
│ 2. 遇到連不上網路、沒有 API Key：                                             │
│    👉 優先切離線 Mock／唯讀場景；必須連外的專案改用 walkthrough 備援畫面。     │
├────────────────────────────────────────────────────────────────────────────┤
│ 3. 老師不想切換終端機、不想 Live Coding：                                    │
│    👉 直接將各專案 walkthrough.md 頂部的「畫面與流程圖解」投影在螢幕上即可！     │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 2. 全 17 專案卡點與快速救援速查總表

| 專案 | 常見可能卡住的地方 | 畫面上會出現的徵狀 | 30 秒內快速救援招式 |
|---|---|---|---|
| **Project 1**<br>環境準備 | Docker Desktop 沒開或當掉 | 終端機報錯 `docker: daemon not running` | 1. 打開 Docker Desktop 等鯨魚圖示停止轉動<br>2. 若公司電腦完全不能裝 Docker，直接改用 Supabase / Neo4j 免費雲端版（見 `docker-services.md`） |
| **Subagent + Hooks**<br>安全護欄與分工 | 1. Hook 未執行或報錯<br>2. `jq` 未安裝<br>3. 迴圈觸發超時 | 1. 權限沒給或輸出非 JSON<br>2. 提示 `jq: command not found`<br>3. Agent 陷入無限重試 | 1. 執行 `chmod +x .cursor/hooks/*.sh`，確保腳本只輸出合法 JSON<br>2. 執行 `brew install jq`<br>3. 在 `hooks.json` 顯式設定 `loop_limit: 2` 與 `failClosed: true` |
| **Project 2**<br>TaskBoard | 1. 誤刪任務卡片或想重置<br>2. 登入不知道帳密<br>3. 埠 3000 被占用 | 1. 看板變空<br>2. 找不到測試帳號<br>3. Next.js 改開在 3001 | 1. 執行 `./demo.sh 3` 一秒重置所有測資<br>2. 登入填 `alice@taskboard.test` / `taskboard123`（**不用填團隊 ID**）<br>3. 依終端機印出的實際網址打開（例如 `localhost:3001`） |
| **Project 3**<br>React 元件庫 | 1. `check.mjs` 檢查報錯<br>2. 元件庫 Showcase 沒畫面 | 1. 提示發現寫死色碼（如 `#ffffff`）<br>2. 5173 埠被佔用 | 1. 將色碼替換為 `tokens.ts` 裡的 Token 變數<br>2. Vite 會自動切到 5174 埠，點擊終端機連結即可 |
| **Project 4**<br>習慣追蹤 App | 1. 連續天數（Streak）沒跳動<br>2. 瀏覽器 LocalStorage 髒掉 | 1. 打卡後天數未累加<br>2. 舊資料殘留 | 1. Streak 計算需為「今天」或「連續昨日」才累加<br>2. 在瀏覽器按 F12 → Application → Clear Storage 清除快取 |
| **Project 5**<br>FastAPI 短網址 | 1. 建立短網址報 422 錯誤<br>2. 埠 8000 被占用 | 1. Pydantic 提示 URL 格式錯誤<br>2. Uvicorn 啟動失敗 | 1. 網址開頭必須包含 `http://` 或 `https://`<br>2. 執行 `uv run uvicorn app.main:app --port 8001` |
| **Project 6**<br>Chrome 擴充 | 1. 學生電腦沒裝 Chrome 或無法載入擴充<br>2. 選取文字沒跳出氣泡 | 1. 擴充功能無法安裝<br>2. 滑鼠反白文字後無反應 | 1. **直接開啟內建模擬器**：`http://localhost:8086/simulator.html`（免裝擴充）<br>2. 選取的文字長度必須大於等於 3 個字元才會觸發 |
| **Project 7**<br>爬蟲 PriceBot | 1. 爬取真實網站被反爬蟲擋下<br>2. Streamlit 8501 埠衝突 | 1. 403 Forbidden 或驗證碼<br>2. 提示 Address in use | 1. **切換內建離線商城**：直接使用 `mock_server.py`，100% 穩定放映<br>2. Streamlit 會自動切換至 8502 埠 |
| **Project 8**<br>營運儀表板 | 產生瑕疵資料時每次數字不同 | 圖表與同學講義對不上 | 程式已固定隨機種子 `seed=42`，執行 `./demo.sh 1` 產出的數字保證全班一模一樣 |
| **Project 9**<br>RAG 知識庫 | 沒有 OpenAI API Key、示範 PDF 或網路斷線 | 索引只有 FAQ，婚假題失敗 | 課前先跑 `./project-9-rag-chatbot/demo.sh 1` 產生 PDF、再跑第 4 幕建索引；第 9 幕可 100% 離線跑 10 題，現行基準為 9/10 且小於等於 2 題失手即通過 |
| **Project 10**<br>MCP Server | 執行時提示找不到 `dist/index.js` | 模組載入失敗 | 執行 `npm run build`，TypeScript 會自動編譯輸出到 `dist/` |
| **Project 11**<br>Phaser 遊戲 | 角色掉出地圖或速度過快穿牆 | 物理碰撞失效 | 執行 `./project-11-rooftop-dash-game/demo.sh 1` 跑 `physics-check.mjs`，物理限速會自動鎖定在 400px/s 防穿牆 |
| **Project 12**<br>CLI 與 Bot | 1. 建立重複目錄報錯<br>2. 點擊 Telegram 按鈕一直轉圈 | 1. Exit Code 1<br>2. 提示響應超時 | 1. 加上 `--force` 參數強制覆蓋，或換一個資料夾名稱<br>2. 在 Handler 第一行務必加上 `query.answer()` 立即回調 |
| **Project 13**<br>AutoCV YOLO | 沒有 GPU 或 CUDA 記憶體不足 | PyTorch 拋出 OOM | 課堂先用 `demo.sh` 的模擬接力場景；要跑真訓練時降低 `batch`／`imgsz` 並縮小資料集，CPU 可跑但不要承諾秒級完成 |
| **Project 14**<br>GraphRAG | 缺 Gemini key、Neo4j 密碼或服務連不上 | `check_setup.py` 對外部條件標紅 | 課前跑第 1 幕；Neo4j 不可用時走 NetworkX 備援，Gemini 不可用時改投影 walkthrough 與第 2–5 幕唯讀程式場景 |
| **Project 15**<br>RAG Architect MCP | MCP client 沒自動調用或 `uvx` 首次下載失敗 | 工具未出現、server 未連線 | 先在 repo 跑 `uv sync` 與 `uv run python test_rag_architect.py`；確認本地 22 項全綠，再依 client 設定 MCP |
| **Project 16**<br>Lazy Superstack | 一次啟用所有 MCP，缺憑證造成紅燈 | Settings 顯示多個 server 連線失敗 | 課堂只啟用零憑證 A 級 MCP；需要帳密的 B 級維持範本狀態，絕不把憑證寫進教材 |
| **Project 17**<br>Anchor PDF Reader | 缺 Gemini key；Node 22+ 測試出現 `localStorage` 失敗 | 問答無法連模型；前端有 9 個測試失敗 | `.env` 設 `GEMINI_API_KEY`；測試使用 `NODE_OPTIONS="--localstorage-file=/tmp/vitest-ls.json" npm test`，無 key 時仍可先跑後端 87 與前端 81 項離線測試 |

---

## 🎯 3. 講師無代碼（Zero-Code）教學指南

如果您上課時**不希望切換到終端機打指令**，建議採用以下流程：

1. 打開該專案的 **`walkthrough.md`**（例如 [Project 2 Walkthrough](./project-2-taskboard-saas/walkthrough.md)）。
2. 直接將頂部的 **「🖥️ 網站功能與畫面圖解」** 與 **「🎬 開場故事」** 投影在大螢幕上。
3. 按照 ASCII 介面框、Mermaid 流程圖向同學講解：
   * **功能是什麼**（介面外觀、使用者操作）。
   * **痛點在哪裡**（為什麼傳統寫法會被駭客攻破）。
   * **架構怎麼解**（後端 RLS、分層架構、Pydantic 安檢門如何把關）。
4. 遇到同學提問程式細節時，直接指著文件中的 **`> 對 Agent 說：`** 與 **`✅ 預期看到`** 程式區塊解說即可！
