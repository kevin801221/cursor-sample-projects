# ShortenURL — FastAPI 後端 API 與雲端部署

> Cursor 課程 Project 5（第 26 章）：FastAPI + PostgreSQL。
> 一句話：**分層架構加 Pydantic 驗證，讓 Agent 不把邏輯全塞一起**——routers 不碰 SQL、services 不碰 AsyncSession、repositories 才能寫 database 語句。

## 專案規格

| | |
|---|---|
| **最終成果** | 建立短網址、302 轉址、點擊統計、API key 認證 |
| **技術棧** | FastAPI、Pydantic v2、SQLAlchemy 2 async、PostgreSQL 16 |
| **預估時間** | 6–9 小時，含測試與部署 |
| **前置需求** | Python 基礎、GitHub 帳號、Render 帳號 |

## 這個 API 做什麼

- 建立短網址：POST `/links`，指定目標 URL 與可選的自訂 slug
- 302 轉址：GET `/{slug}`，立即返回 Location header，快速跳轉
- 背景記錄點擊：不拖慢轉址回應，用 BackgroundTask 非同步寫入點擊紀錄
- 統計查詢：GET `/links/{slug}/stats`，回傳該短網址的點擊總數
- API Key 認證：每個請求用雜湊驗證 API key；依 API key 限流，不用 IP

## 分層架構四層

```
HTTP 請求（Client）   只帶 Authorization header 與 JSON body
  ↓ HTTP / JSON
routers 層           只處理 HTTP 解析與回應
  ↓ 呼叫
services 層          商業邏輯（重試、驗證、過期判斷）
  ↓ 呼叫
repositories 層      唯一能操作 AsyncSession 的層
  ↓ SQL
models/schemas 層    ORM model 與 Pydantic v2
  ↓ 資料庫
PostgreSQL           持久化資料
```

**絕對紅線**：
- routers **絕不直接寫 SQL**，一律呼叫 services
- services **絕不直接呼叫 AsyncSession**，一律呼叫 repositories
- repositories **唯一直接操作 AsyncSession 與執行 SQL**
- 每個 endpoint **都要宣告 response_model**，不回傳原始 dict

## 資料模型

```sql
links               短網址（slug、target_url、created_at、expires_at）
clicks              點擊紀錄（link_id、user_agent、referrer、recorded_at）
api_keys            認證金鑰（key_hash、owner_name、created_at、rate_limit）
```

外鍵串起表，但安全邊界在 **Pydantic schema 驗證** 與 **AsyncSession 層限制**。

## 四階段開發流程

| 階段 | 做什麼 | 驗收 |
|---|---|---|
| 1. 骨架與規範 | FastAPI 專案、寫 `.cursor/rules`、環境變數 | Agent 遵守分層架構 |
| 2. 資料庫與 ORM | 建表、Alembic migration、SQLAlchemy models | 三張表都建起來 |
| 3. 分層實作 | schemas、repositories、services、routers | 分層邊界清楚 |
| 4. 認證與部署 | API Key 驗證、BackgroundTask、Render 部署 | API 全 endpoint 通測 |

## 專案結構

```
shortenurl/
├── .cursor/rules/
│   ├── 00-layering.mdc          # 分層紅線，唯一的 alwaysApply
│   ├── fastapi.mdc              # FastAPI 慣例（globs 按需載入）
│   └── database.mdc             # SQLAlchemy async 慣例
├── migrations/
│   ├── versions/
│   │   └── 001_initial.py        # Alembic migration：建三張表
│   ├── env.py
│   └── alembic.ini
├── app/
│   ├── models/                   # SQLAlchemy ORM models（Link、Click、ApiKey）
│   │   ├── __init__.py
│   │   └── base.py               # declarative_base
│   ├── schemas/                  # Pydantic v2 input/output schemas
│   │   ├── link.py
│   │   ├── click.py
│   │   └── api_key.py
│   ├── repositories/             # 資料庫操作層
│   │   ├── __init__.py
│   │   ├── base.py               # BaseCRUD
│   │   ├── link_repo.py
│   │   └── click_repo.py
│   ├── services/                 # 商業邏輯層
│   │   ├── __init__.py
│   │   ├── link_service.py       # 轉址、過期判斷、記錄點擊
│   │   └── auth_service.py       # API key 驗證、限流
│   ├── routers/                  # HTTP endpoint 層
│   │   ├── __init__.py
│   │   ├── links.py              # POST/GET /links、GET /{slug}、GET /links/{slug}/stats
│   │   └── health.py             # GET /health
│   ├── database.py               # AsyncSession 工廠、連線池
│   ├── config.py                 # 環境變數、設定物件
│   ├── main.py                   # FastAPI app、middleware、exception handler
│   └── dependencies.py           # Depends()、認證、限流依賴
├── tests/
│   ├── conftest.py               # pytest fixtures（async session、測試用 API key）
│   ├── test_links.py             # 轉址、建立、統計測試
│   ├── test_auth.py              # API key 驗證、限流測試
│   └── test_rls.py               # 跨 API key 隔離測試
├── .env.local                    # 本地開發環境變數（不版控）
├── .env.example                  # 環境變數範本
├── pyproject.toml                # uv 管理的依賴清單
├── uv.lock
└── walkthrough.md                # 完整逐步教學
```

## 五條鐵律（本課核心）

1. **分層架構規則能防止商業邏輯與 SQL 全塞進單一檔案**——routers 只處理 HTTP 層，不寫業務邏輯；services 寫業務邏輯，不寫 SQL；repositories 唯一寫 SQL。
2. **每個 endpoint 都要宣告 response_model**——不回傳原始 dict；Pydantic v2 驗證確保 API 契約對稱。
3. **background task 必須自行開新 session**——不共用 request 的 AsyncSession，否則轉址回應後 session 就關了，background 會報「session 已關閉」。
4. **API key 要雜湊儲存，rate limit 要依 API key 而非 IP**——明文儲存與 IP 限流是最常見的安全地雷。
5. **機密設定值不給預設值**——缺少環境變數（如 `API_KEY_SALT`）要讓服務啟動失敗，而不是用預設值 `changeme`。

## 快速開始

```bash
# 安裝依賴（使用 uv）
uv sync

# 建立 .env.local（參考 .env.example）
cp .env.example .env.local
# 編輯 .env.local，設定：
# - DATABASE_URL=postgresql://...
# - API_KEY_SALT=<自訂隨機串>
# - RENDER_EXTERNAL_URL=http://localhost:8000

# 初始化資料庫
uv run alembic upgrade head

# 執行測試
uv run pytest

# 本地開發
uv run uvicorn app.main:app --reload
# http://localhost:8000/docs
```

完整建置步驟、分層概念、Pydantic 驗證、BackgroundTask、API Key 驗證，見 **[walkthrough.md](./walkthrough.md)**。
