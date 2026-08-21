# CLI 工具與 Telegram Bot

> Cursor 課程 Project 12（第 33 章）：打造能發佈的 CLI，加一個會發圖的 Telegram Bot。
> 一句話：**CLI 核心體驗來自參數解析、互動提問、正確 exit code 三者缺一不可**；**Telegram Bot 的 run_polling 與 webhook 互斥，部署時只能啟用一種**。

## 專案規格

| | |
|---|---|
| **最終成果** | A：可用 `npx` 執行、發佈到 npm 的腳手架產生器；B：能產生指板圖片、支援按鈕互動的 Telegram Bot |
| **技術棧** | A：Node.js + commander + inquirer；B：Python + python-telegram-bot + Pillow |
| **預估時間** | A 約 4–5 小時，B 約 4–6 小時，合計 8–11 小時 |
| **前置需求** | Cursor Pro、Node 20+、Python 3.8+、Telegram BotFather 帳號（或用 polling 本地測試） |

## 這個 CLI 做什麼

- 用 `commander` 解析 `init` 子指令，支援 `--help` 顯示完整說明
- 用 `inquirer` 互動提問專案名稱與選擇模板（鍵盤上下鍵可操作）
- 生成完整的腳手架：複製模板、替換專案名稱、產生可跑的 package.json
- 用 `npm link` 本地測試成全域指令，最後 `npm publish --access public` 發佈到 npm registry
- **關鍵需求**：執行失敗時回傳正確的 `exit code 1`，讓 CI 腳本能判斷成功或失敗

## 這個 Bot 做什麼

- 使用者發送 `/note` 指令，Bot 呼叫 callback handler 回傳音名按鈕（用 `InlineKeyboardButton` 產生）
- 點擊任一按鈕，`CallbackQueryHandler` 接住事件並用 `pattern` 匹配
- handler 內先呼叫 `query.answer()` 清掉用戶端轉圈，再產生指板圖片回傳
- 用 `context.user_data` 記住每個使用者上一次選擇的音名（隱私隔離：各用戶各自獨立）
- 支援 polling 或 webhook 部署（但二選一，不能同時啟用）

## 架構

### Node CLI

```
使用者終端機
    ↓ 執行 npx create-project-scaffold init my-app
Node.js CLI 應用程式
    ├─ commander：解析指令參數與 --help
    ├─ inquirer：互動式提問（下拉選單、文字輸入）
    └─ fs/path：複製模板、生成新專案結構
    ↓
本機磁碟
    └─ ~/my-app/  (完整腳手架)
        ├─ package.json  (含正確的專案名稱)
        └─ 模板內容
    ↓ (使用者手動執行)
npm publish --access public  →  npm registry
    ↓
任何人都可 npx create-project-scaffold init xxx 直接執行
```

**Exit code 規則**：成功結束 → 0；使用者取消 → 0（不算錯誤）；失敗路徑 → 1。

### Python Telegram Bot

```
Telegram 用戶端  (發送 /note 指令，點按鈕)
    ↕ API 通訊
Python Bot 應用程式  (polling 或 webhook)
    ├─ CommandHandler：接住 /note 指令
    ├─ CallbackQueryHandler：接住按鈕點擊
    │   └─ query.answer() 先清圈 → 再產生圖片回傳
    ├─ context.user_data：記錄使用者選擇（各用戶隔離）
    └─ Pillow：產生指板圖片
    ↓ (部署)
polling：Bot 定期拉取更新（本地測試用）  或  webhook：Bot 監聽 HTTP 請求（生產環境用）
```

**互斥規則**：`run_polling()` 與 webhook 同時啟用會導致重複回應或訊息遺漏，只能二選一。

## 開發階段

| 階段 | 做什麼 | 驗收 |
|---|---|---|
| 1. 骨架與計畫 | npm init 設定 type module 與 bin；用 DO NOT CODE prompt 產出計畫 | Agent 先覆述需求、再產步驟清單，不立刻寫程式 |
| 2. CLI 參數解析與互動 | commander 定義 init 子指令、inquirer 提問；本機測試 `npm link` | 執行 `scaffold init my-app` 後產生資料夾、--help 顯示完整說明 |
| 3. 模板系統與複製 | 建立 templates/ 結構、複製模板、替換專案名稱 | 選中的模板能正確複製、npm install 後能啟動 |
| 4. Exit code 與發佈 | 失敗路徑設 `process.exitCode = 1`、npm publish | echo $? 驗證成功或失敗；npx 可直接執行 |
| 5. Bot 核心流程 | setup token、CommandHandler 與 CallbackQueryHandler | /note 指令有反應、按鈕點擊回傳圖片、query.answer() 清圈 |
| 6. Bot 圖片生成與部署 | Pillow 產生指板圖片、polling 或 webhook 二選一 | 圖片正確顯示、部署到 fly.io 或 Railway |

## 專案結構

```
project-12/
├── cli/
│   ├── package.json           # type: "module", bin: { scaffold: ... }
│   ├── index.js               # 主程式入口（commander 與 inquirer）
│   ├── templates/
│   │   ├── next-app/          # 模板 1：Next.js 骨架
│   │   │   ├── package.json
│   │   │   └── ...
│   │   └── express-api/       # 模板 2：Express 伺服器骨架
│   │       ├── package.json
│   │       └── ...
│   └── lib/utils.js           # 輔助函式（複製、替換）
├── bot/
│   ├── main.py                # Bot 主程式
│   ├── handlers/
│   │   ├── commands.py        # /note 等指令
│   │   └── callbacks.py       # 按鈕互動
│   ├── utils/
│   │   ├── image.py           # Pillow 指板圖片生成
│   │   └── data.py            # context.user_data 管理
│   ├── .env.example           # TOKEN=<your_token>
│   └── requirements.txt       # python-telegram-bot, Pillow 等
└── walkthrough.md             # 完整逐步教學
```

## 本課核心鐵律

1. **DO NOT CODE 逼它先問問題**——任務複雜時，先讓 Agent 產步驟清單而非直接寫程式；五個問題花 30 秒，省下一輪完整重做。
2. **Exit code 決定 CI 判斷**——漏了 `process.exitCode = 1` 或 `process.exit(1)` 會讓 CI 永遠成功，即使實際失敗；失敗路徑必須明確設定。
3. **npm link 是發佈前最後一關**——權限錯誤不要用 `sudo`，改用 nvm 管理 Node；這是驗證真實指令名稱的最後機會。
4. **Callback handler 一定要呼叫 query.answer()**——漏掉會讓按鈕一直轉圈逾時；先清圈再回傳圖片是 Bot 體感速度的關鍵。
5. **結構化反饋循環六步驟管理複雜任務**——覆述需求 → 產計畫 → 逐步實作（每步 commit） → 驗收，比直接埋頭寫省下返工。
6. **版本控制是生命線**——多檔案重構前先 commit；Checkpoints 不能取代 Git；至少每個邏輯步驟留一個 commit 訊息。

## 快速開始

### CLI 部分

```bash
cd cli
npm install

# 本地測試（npm link 註冊成全域指令）
npm link
scaffold init my-app
cd my-app && npm install && npm start

# 驗證 exit code
scaffold init my-app; echo $?     # 成功 → 0
scaffold init;                   # 取消 → 0
```

### Bot 部分

```bash
cd bot
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 建立 .env（從 BotFather 取得 TOKEN）
echo "TOKEN=<your_bot_token>" > .env

# 本地測試（polling）
python main.py
# 在 Telegram 搜尋你的 Bot 帳號、發送 /note、點按鈕

# 部署到 fly.io
fly deploy
```

完整建置步驟、核心概念、DO NOT CODE prompt、常見坑速查，見 **[walkthrough.md](./walkthrough.md)**。
