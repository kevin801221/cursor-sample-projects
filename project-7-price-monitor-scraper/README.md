# PriceBot — Python 爬蟲與自動化腳本

> Cursor 課程 Project 7（第 28 章）：uv、httpx、BeautifulSoup、Playwright、pydantic v2。
> 一句話：**合法合規比技術難度更重要，動手前先查五件事**——爬蟲的難題不是「抓」，是「抓錯了怎麼辦」。

## 專案規格

| | |
|---|---|
| **最終成果** | 定期抓取商品價格寫入 SQLite，價格變動時發 Telegram 通知 |
| **技術棧** | uv、httpx、BeautifulSoup、Playwright、pydantic v2、SQLite、Telegram Bot API |
| **預估時間** | 6–8 小時，含環境安裝與排錯 |
| **前置需求** | Python 基礎、本機可執行 curl 與 uv |

## 這個機器人做什麼

- 排程任務每 6 小時自動執行一次
- 爬取 books.toscrape.com 的商品清單（PLP）與詳細資料（PDP）
- 用 pydantic 驗證每筆資料，拒絕髒資料進資料庫
- SQLite upsert：新商品寫入、既有商品比對新舊價格
- 價格下跌或上漲時，透過 Telegram Bot 發送通知
- 整個流程受 Cursor Rules 強制驗證、日誌與速率限制
- **沒有驗證的髒資料直接進資料庫，之後很難排查** ——資料進庫前，必須 pydantic 驗證通過

## 三層爬蟲架構

```
Scheduler (cron / APScheduler)
    每 6 小時觸發一次爬取流程
        ↓
Scraper 層（BeautifulSoup / Playwright）
    PLP：清單頁僅蒐集商品連結
    PDP：詳情頁才是資料真正的來源（價格、庫存、評分）
        ↓
Validation 層（pydantic）
    驗證每筆資料：價格是否合理、缺必填欄位立即拋例外
    髒資料直接 log 警告，不寫入資料庫
        ↓
Storage 層（SQLite）
    upsert：既有商品更新，新商品插入
    事務一致性保證，同時只有一個程序寫入
        ↓
Notification 層（Telegram Bot API）
    查舊值、寫新值、比較差異
    變動時立即通知，第一次執行不誤發
```

## 資料模型

```sql
products (
  sku text primary key,
  name text not null,
  price float not null,
  in_stock boolean not null,
  rating float,
  url text,
  last_scraped_at timestamp,
  price_history [(time, price, in_stock)]  -- 用單獨表儲存，便於查詢歷史
)

price_history (
  sku text foreign key,
  timestamp timestamp,
  price float,
  in_stock boolean
)
```

## 五階段開發流程

| 階段 | 做什麼 | 驗收 |
|---|---|---|
| 1. 環境建置 | uv init、uv add（httpx、BeautifulSoup、pydantic）、寫 .cursor/rules | pyproject.toml 與 uv.lock 出現 |
| 2. 結構分析 | 用瀏覽器工具讀 PLP/PDP selector、檢查 robots.txt | 取得 selector、確認允許爬取 |
| 3. 資料與爬取 | 寫 pydantic 模型、PLP/PDP 爬蟲函式、處理 Playwright 動態渲染 | Product 物件通過驗證 |
| 4. 儲存與通知 | SQLite upsert、價格變動判斷、Telegram 通知 | 變動時收到通知、第一次執行不誤發 |
| 5. 排程與部署 | cron 排程、環境變數管理、Docker 化 | 每 6 小時自動跑一輪 |

## 專案結構

```
priceboard/
├── .cursor/rules/
│   ├── 00-scraper.mdc          # 爬蟲工程規則，全專案唯一的 alwaysApply
│   └── compliance.mdc           # 合規五件事，碰到 scraper.py 才載入
├── src/
│   ├── models.py                # pydantic Product、PriceHistory 模型
│   ├── scraper.py               # BeautifulSoup PLP/PDP 爬蟲
│   ├── dynamic_scraper.py        # Playwright 爬蟲（動態渲染用）
│   ├── storage.py               # SQLite upsert、查詢歷史
│   ├── notification.py          # Telegram 通知邏輯
│   ├── validator.py             # 資料驗證與清理
│   └── main.py                  # 排程主程式
├── tests/
│   ├── test_models.py           # pydantic 驗證測試
│   ├── test_scraper.py          # 爬蟲實際測試
│   └── test_storage.py          # 資料庫隔離測試
├── .env.example                 # 環境變數模板
├── pyproject.toml               # uv dependencies
├── uv.lock                       # dependency lock file
├── requirements-dev.txt         # 開發工具
└── walkthrough.md               # 完整逐步教學
```

## 爬蟲工程規則（本課核心）

**四件事寫進 Always Apply 規則：**

1. **pydantic 驗證擋住格式錯誤的髒資料流進資料庫**
   - `Product(**data)` 驗證失敗立即拋例外
   - `field_validator` 擋下不合理的價格（例如 0 元、負數）
   - 抓不到元素先 log 警告再回傳 None，而非程式崩潰

2. **loguru 取代 print()，方便排查排程執行紀錄**
   - 新增商品、價格變動、驗證失敗都用 logger
   - 排程日誌到檔案，搜尋錯誤無需重跑

3. **動手前先查 robots.txt，把倫理檢查寫進流程而非事後補**
   - 爬取前自動讀 robots.txt 驗證許可
   - 違反 ToS 的網站在程式碼裡就要擋下

4. **速率限制與金鑰管理**
   - 預設 1 併發、間隔 1 秒，別把對方當壓力測試
   - API 金鑰從環境變數讀，絕不硬編碼

## 合規五件事（動手前必查）

技術本身中性，合不合規看爬什麼、怎麼爬、怎麼用。踩到任何一項，寫得再好都得下線。

| 項目 | 檢查項目 | 做法 |
|---|---|---|
| **robots.txt** | 業界最低限度禮儀 | 爬取前自動檢查、違反自動拒絕 |
| **服務條款** | 已有多起違反 ToS 的爬蟲業者被提告 | 讀官網 ToS、確認允許自動爬取 |
| **個人資料** | 即使公開可見，收集個資仍受個資法規範 | 不爬個人隱私資訊、不販售資料 |
| **合理速率** | 預設 1 併發間隔 1 秒 | Semaphore 限速、持尊重 |
| **登入內容** | 絕對不要繞過登入擷取資料 | 程式碼明確禁止爬需登入的頁面 |

## 快速開始

```bash
# 1. 初始化環境（uv 管理）
uv init
uv add httpx beautifulsoup4 pydantic[email] python-dotenv loguru tenacity
uv add -d pytest

# 2. 複製環境變數範本
cp .env.example .env
# 編輯 .env：設定 TELEGRAM_BOT_TOKEN、TELEGRAM_CHAT_ID

# 3. 建立資料庫與執行首次爬取
uv run src/main.py --init-db
uv run src/main.py --run-once

# 4. 檢查通知是否成功
# 打開 Telegram，應該收到第一次執行的訊息（或無訊息，因為沒有舊資料比較）

# 5. 設定排程（cron，每 6 小時）
# 編輯 crontab：0 */6 * * * /usr/local/bin/uv run /path/to/priceboard/src/main.py

# 6. 跑測試
uv run pytest tests/ -v
```

完整建置步驟、合規檢查、怎麼用 Cursor Agent 做出爬蟲，見 **[walkthrough.md](./walkthrough.md)**。
