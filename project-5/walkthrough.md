# Walkthrough：在 Cursor 上把 ShortenURL 一步一步做出來

> 這份文件帶你從零做出 **ShortenURL**——一個短網址服務，並親手證明一件事：**分層架構能防止邏輯全塞進一個檔案，背景任務讓轉址快如閃電。**
> 你會學到三件事：怎麼把 routers/services/repositories 三層分開、怎麼用 BackgroundTask 不卡轉址效能、怎麼把分層紅線寫成 `.cursor/rules` 讓 Agent 替你擋住亂來的做法。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先做這六件事，動手不會卡）

1. **裝好 Python 3.11+ 和 uv**——檢查 `python --version` 與 `uv --version`；沒有的話用 Homebrew 裝。
2. **建立 PostgreSQL 資料庫**——本地或用 Render 免費層；測試 `psql -U user -d shortenurl -c "\dt"`；確認能連。
3. **先把整個專案骨架跑一次**——跑過 `uv sync`、migrations 套用、本地 server 啟動，確認 `/docs` 自動文件頁面開得起來。第一次跑會花點時間，先跑過一次之後改功能才不會卡。
4. **熟悉分層四層的職責邊界**——router 不碰 SQL、service 不碰 AsyncSession、repository 才寫 database 語句；這三條是整個教學的核心。
5. **設定測試環境變數**——確認 `.env.local` 能正確讀進來；缺少 `API_KEY_SALT` 時服務應該啟動失敗（這就是「缺失環境變數要拋出錯誤」的驗證）。
6. **動手過程中每跑完一個指令就對照文中的「✅ 預期看到」**——判斷得出「這是正常的」還是「翻車了」，除錯速度差十倍。

## 🗺️ 學習地圖（建議 3 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 第 1 節概念 | 30 分 | 閱讀理解（這是全篇靈魂，慢慢看） |
| 第 2 節規則設定 | 20 分 | 動手做（Agent 被規則擋下是最精彩的一幕） |
| 第 3 節骨架與 config | 15 分 | 動手做（uv init、依賴安裝、環境變數驗證） |
| 第 4 節資料庫與 ORM | 30 分 | 動手做 migration；Alembic autogenerate |
| 第 5 節分層實作（schemas → repositories → services → routers） | 45 分 | 動手做（邊做邊理解分層邊界） |
| 第 6 節 BackgroundTask 情境 | 25 分 | 動手做（測試轉址速度與後臺寫入） |
| 第 7–8 節 驗收與排錯 | 12 分 | 閱讀理解 + 動手做自動測試 |
| 收尾三句話 | 10 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `./shortenurl/`，遙控器是 `./demo.sh`（位於 `project-5/` 根目錄）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 全程離線、不需要外部雲端資料庫、內建 SQLite 即可完整運行。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd project-5/shortenurl && uv sync --extra dev` | 第一次同步 uv 虛擬環境與下載依賴。課前做完後，課堂上全離線秒開 |
| 2 | 跑一次 `./demo.sh 5`（測試全綠） | 執行 pytest 確認 4 passed（建立、自訂衝突、Pydantic 驗證、轉址分析）全綠 |
| 3 | 確認 8000 埠沒有殘留行程 | 第 6 幕 FastAPI 服務需要 8000 埠 |

### 放映時間軸

時間軸切成 6 段，對應上方學習地圖（合計 180 分鐘），全長 **3 小時**。

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:30 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §1 | 餐廳外場/廚房/倉庫三層對照表、四個反模式、分層邊界圖 | 分層架構概念與職責分離 |
| 0:30–0:50 | 第 1 幕：分層規則與結構 | `./demo.sh 1` | `shortenurl/.cursor/rules/architecture.mdc` | architecture.mdc 規則檔：router 不碰 SQL、service 不碰 session | 把分層紅線寫進規則，讓 AI 替你把關邊界 |
| 0:50–1:10 | 第 2 幕：Pydantic 門口安檢 ⭐ | `./demo.sh 2` | `shortenurl/app/schemas/url.py` | `validate_target_url` 檢查協定、格式與長度，非法請求 422 退回 | 壞資料在門口擋下，不浪費後端與資料庫資源 |
| 1:10–1:40 | 第 3 幕：短網址生成與資料層 | `./demo.sh 3` | `shortenurl/app/services/url_service.py` | Service 生成 6 碼短代碼並協同 Repository 存入資料庫 | 業務邏輯集中在 Service，資料庫隔離在 Repo |
| 1:40–2:15 | 第 4 幕：BackgroundTask 點擊分析 ⭐ | `./demo.sh 4` | `shortenurl/app/routers/url_router.py` | `BackgroundTasks.add_task` 非同步記錄點擊 IP 與 User-Agent | 轉址 307 毫秒秒回，點擊計數在背景非同步更新 |
| 2:15–2:30 | 第 5 幕：pytest 測試全綠 | `./demo.sh 5` | `shortenurl/tests/test_shortenurl.py` | 4 passed 全綠色通過 | 沒有測試證明的架構，等於不知道有沒有寫對 |
| 2:30–3:00 | 第 6 幕：啟動服務與管理介面 ⭐ | `./demo.sh 6` | `shortenurl/app/static/index.html` | 瀏覽器展示 Web 管理面板與 Swagger `/docs`，即時測試短網址生成與點擊跳轉 | 完整端到端成果展示 |

### ⭐ 全場最值得停下來的一幕

**第 4 幕的 BackgroundTask 與第 6 幕的 Web Dashboard。**
在第 4 幕展示轉址路由：FastAPI 是如何先回傳 307 重定向給使用者瀏覽器，同時把點擊統計任務丟到背景執行緒，保證轉址零延遲。在第 6 幕打開瀏覽器，現場建立短網址、複製短連結在新分頁打開，再回頭看 Dashboard，點擊次數即時跳轉，後台日誌精準捕捉訪問時間！

### 🧯 現場翻車備案

| 翻什麼 | 徵狀 | 30 秒內的救援 |
|---|---|---|
| 埠 8000 被占用 | Uvicorn 啟動失敗 | 改用 `uv run uvicorn app.main:app --port 8001` |
| 資料庫被測試測資污染 | 想重置資料庫 | 刪除 `shortenurl/shortenurl.db` 即可，下次啟動時會自動重建乾淨資料庫 |

---

## 🎬 開場故事：一間餐廳的外場、廚房、倉庫

想像我們今天不是要寫程式，是要管一間餐廳。客人來點餐——這是我們要做的事。但一間餐廳有三個完全不同的工作機能。

第一個：**外場**。客人對著外場點「我要一碗炒飯」。外場的工作就是記下點單、送菜到桌子。外場永遠不走進廚房自己炒飯，永遠不自己進冷藏庫拿食材。外場只做一件事：收點單、回復給客人。

第二個：**廚房**。主廚接到點單：「炒飯」。主廚的工作是「決定怎麼做」——先檢查食材夠不夠、決定炒多少、決定調味。但主廚也不自己進冷藏庫拿東西——那是倉管的工作。主廚只做一件事：決策與組織。

第三個：**倉庫**。只有倉管能進冷藏庫。他聽廚房喊「要蛋、要米、要醬油」，他就進冷藏庫拿出來。拿出來後，米呢？米得經過廚房的手才能變成炒飯。

好，現在想一個問題：如果我們允許外場直接進冷藏庫？或是倉管直接替客人炒飯？餐廳會亂成什麼樣子？會有人一邊點餐一邊搶食材、食物分不清誰點的、倉管可能炒糊……全亂套。

**這就是程式碼設計的第一節課：邊界。今天整個教學要學的就是怎麼在三層之間畫清邊界，讓每層只做該做的事，亂來的代碼被 AI 擋下來。**

把這個比喻記在心裡，會貫穿全課：

| 餐廳 | 程式碼 | 職責 |
|---|---|---|
| 外場 | routers（HTTP 層） | 收點單（request）、回復客人（response） |
| 廚房 | services（業務邏輯） | 決定怎麼做、驗證、重試邏輯 |
| 倉庫 | repositories（資料庫層） | 唯一能進冷藏庫（AsyncSession）的地方 |
| 安檢門 | Pydantic schemas | 點餐單長得奇怪（「我要 -3 碗飯」）直接在門口退回，不進餐廳 |
| 傳菜生 | BackgroundTask | 一邊端菜給客人一邊準備下一道，不用等完全準好 |

---

## 0. 課前準備

- Python 3.11+、uv（Python 套件管理工具）
- PostgreSQL 16（本地或用 Render 免費層）
- Render 帳號（部署用，https://render.com）
- GitHub 帳號（版控）

```bash
# 檢查環境
python --version          # Python 3.11+
uv --version             # 最新 uv
psql --version           # PostgreSQL 16
```

> 🔍 **名詞卡：uv**
> 白話：Python 的套件管理工具，像廚房的「食材管理員」——你告訴它你要什麼（fastapi、sqlalchemy），它自動下載安裝、解決版本衝突。比舊的 pip 快 10 倍。
>
> 🔍 **名詞卡：PostgreSQL**
> 白話：一個資料庫軟體，就是「超強的 Excel」——很多張表格、彼此有關聯、可以下指令查詢。短網址服務的所有資料（連結、點擊紀錄）都存這裡。
>
> 🔍 **名詞卡：FastAPI**
> 白話：一個 Python 框架，讓你快速蓋網路服務。你寫 `@app.post("/links")` 就自動變成一個 API 端點，客人可以透過網路呼叫。

---

## 1. 先懂概念：分層架構、Pydantic、BackgroundTask

### 1.1 分層架構——邏輯與資料庫不能混

常見錯誤：整個業務邏輯塞進 router 或 service，SQL 分散四處，改功能時找不到改哪裡。

回到餐廳的比喻。最常見的錯誤是什麼？外場兼廚師兼倉管——一個人做三件工作。初期沒問題，客人少。但客人多了之後：外場忙著點餐沒時間炒飯、廚師忙著倒冷藏庫裡沒人點菜、倉管一邊點餐一邊入庫……沒人知道誰該做什麼。找 bug 的時候，炒飯出問題了，你去哪裡改？沒人知道。

```
❌ 錯的：邏輯全塞進 router
@app.post("/links")
async def create(req: CreateLinkRequest, session: AsyncSession):
    # 驗證 slug
    existing = await session.execute(select(Link).filter(...))
    if existing: raise HTTPException(409)
    # 建立連結
    link = Link(...)
    session.add(link)
    await session.commit()  # ← 應該在哪層呢？
    return link
```

```
✓ 對的：四層各司其職
routers/links.py：HTTP 層
  create_link(req: CreateLinkRequest, service: LinkService)
    → service.create_link(req.target_url, req.custom_slug)

services/link_service.py：業務邏輯層
  async def create_link(self, target_url, custom_slug):
    if not self.validate_slug(custom_slug): raise ValueError()
    return await self.link_repo.create_link(target_url, custom_slug)

repositories/link_repo.py：資料庫層
  async def create_link(self, target_url, custom_slug):
    link = Link(target_url=target_url, slug=custom_slug)
    self.session.add(link)
    await self.session.flush()  # ← 只有這層碰 AsyncSession
    return link
```

重點：
- **routers**：HTTP 解析、狀態碼、error handler。零 SQL。
- **services**：業務規則（驗證、重試、過期判斷）。零 AsyncSession。
- **repositories**：資料庫操作。唯一直接碰 AsyncSession。
- **schemas**：Pydantic models。request/response 型別驗證。

> 🔍 **名詞卡：HTTP 層**
> 白話：客人跟餐廳溝通的介面。客人說「給我炒飯」，這個「給」就是 HTTP 請求；餐廳說「好的，炒飯做好了」就是 HTTP 回應。外場只負責這個溝通，不負責真的做飯。
>
> 🔍 **名詞卡：業務邏輯層（services）**
> 白話：廚房的決策層。客人點『炒飯』，廚房要決定：米夠不夠、要炒多久、要加什麼調味。這些決定不應該在客人面前做（那是 HTTP 的事），也不應該到冷藏庫層決定（那是倉庫的事）。
>
> 🔍 **名詞卡：資料庫層（repositories）**
> 白話：倉庫的實際操作。「需要米」→ 倉管進冷藏庫拿米 → 回傳米。簡單明快。

> ❓ **想一想**：我們為什麼不讓外場直接進冷藏庫拿食材？
>
> **答案**：因為這樣外場就變成了廚房又變成了倉庫——他們會互相搶食材、改菜單、整間餐廳亂套。同理，router 不碰 AsyncSession 就是為了防止邏輯全混在一起。

### 1.2 Pydantic v2——request 進來先過 schema，不合法直接擋下

餐廳有安檢門。某個客人點「我要 -3 碗飯」，負責安檢的人怎麼想？「-3 碗？你是要退 3 碗嗎？」直接在安檢門擋下。根本不進餐廳。我們的 Pydantic schema 就是這個安檢門。

```python
# schemas/link.py
from pydantic import BaseModel, Field, HttpUrl

class CreateLinkRequest(BaseModel):
    target_url: HttpUrl                              # ← 自動驗證合法 URL
    custom_slug: str | None = Field(
        default=None,
        pattern=r"^[a-zA-Z0-9-]{3,30}$"             # ← regex 限定，-3 之類的直接擋
    )

class LinkResponse(BaseModel):
    slug: str
    target_url: str
    created_at: datetime
    expires_at: datetime | None
```

好處：
- request 進來自動驗證型別、欄位合法性
- 不合法的請求在 HTTP 層直接被擋，services 永遠收到合法資料
- response 自動序列化，OpenAPI 文件自動產出

> 🔍 **名詞卡：Pydantic**
> 白話：資料驗證工具。你定義「短網址 slug 要 3–30 個英文數字和連字號」，Pydantic 就自動檢查、不合格的請求當場退回。
>
> 🔍 **名詞卡：驗證（validation）**
> 白話：查證「這個東西符不符合規則」。「我要 -3 碗飯」不符合「數量要是正數」的規則，所以被擋。驗證最好做在最外層（安檢門），而不是做到廚房才發現。

### 1.3 BackgroundTask——轉址要立即回應，記錄點擊不能拖慢

現在想另一個場景：客人點了炒飯，廚房要先炒完才能端給客人。客人坐著等。但理想狀態是什麼？「你的炒飯準備中，先吃個水果吧」——廚房一邊炒一邊準備水果、準備下一道菜。客人不用坐著等全部做完。這就是背景任務。

情境：
- 使用者點短網址 → GET `/{slug}`
- 伺服器應該立刻 302 redirect（10ms 以內）
- 記錄「這個 IP / user-agent 點了這個連結」應該走背景，不能等 DB 寫完才回應

```python
# ❌ 錯的：等待點擊記錄才回應
@app.get("/{slug}")
async def redirect(slug: str, request: Request, service: LinkService):
    link = await service.get_link_and_record_click(slug, request)  # 可能 200ms
    return RedirectResponse(url=link.target_url, status_code=302)

# ✓ 對的：立即回應，背景記錄
@app.get("/{slug}")
async def redirect(
    slug: str,
    request: Request,
    service: LinkService,
    background_tasks: BackgroundTasks
):
    link = await service.get_link(slug)  # ~10ms
    background_tasks.add_task(
        service.record_click,  # 這個函式會自行開新 session
        slug, request.client.host, request.headers.get("user-agent")
    )
    return RedirectResponse(url=link.target_url, status_code=302)
```

**關鍵**：background task 內部自行開新 AsyncSession（見 1.4）。如果共用 request 的 session，轉址回應後 session 就 commit/close 了，background 裡再用會炸掉「session 已關閉」。

> 🔍 **名詞卡：BackgroundTask**
> 白話：傳菜生。客人點炒飯，傳菜生一邊把炒飯端給客人一邊準備下一道菜——不用等全部做完才開始送。程式裡也是：立即回應 302 轉址，後臺另開一條線記錄點擊。
>
> 🔍 **名詞卡：async / await**
> 白話：「邊做邊等」的程式寫法。廚房炒飯時（等待），同時可以準備下一道菜；不是傻傻坐著等米煮好。在程式裡，`await` 就是「在這邊稍等」，等的時候 CPU 可以做別的。

### 1.4 背景任務必須自行開新 session

```python
# services/link_service.py
class LinkService:
    def __init__(self, repo: LinkRepository, session_factory):
        self.repo = repo
        self.session_factory = session_factory
    
    async def record_click(self, slug: str, ip: str, user_agent: str | None):
        # ✓ 自行開新 session，不共用 request 的
        async with self.session_factory() as session:
            async with session.begin():
                await self.repo.record_click(session, slug, ip, user_agent)
                # session.commit() 自動發生在 async with 結束
```

重點：background task 是獨立執行的協程，原本的 request session 對它沒用。必須自己創建連線。

> 🔍 **名詞卡：AsyncSession**
> 白話：非同步資料庫連線。想像你要寄信：同步版本是「我去郵局、寄信、等郵局確認才回家」；非同步版本是「我去郵局交信、郵局說『收到了』就走」，郵局在背景把信寄出去。BackgroundTask 需要自己的 AsyncSession，因為原本的 session 已經關閉了。

### 1.5 API Key 認證與限流

不能靠 IP 限流（VPN、代理會亂套），要依 API key。

```python
# ✗ 危險寫法
api_key_plain = "my-secret-key"
if request.headers.get("Authorization") == f"Bearer {api_key_plain}": ✓
    # 明文儲存與比對

# ✓ 正確寫法
import hashlib
api_key_hash = hashlib.sha256(b"my-secret-key" + salt).hexdigest()
provided_key_hash = hashlib.sha256(
    request.headers.get("Authorization", "").split()[-1].encode() + salt
).hexdigest()
if api_key_hash == provided_key_hash: ✓
    # 雜湊後再比對
```

> 🔍 **名詞卡：API Key**
> 白話：一張通行證。你要建短網址，得給出「我是誰」的證明——API key。就像去銀行要出示身分證。
>
> 🔍 **名詞卡：雜湊（hash）**
> 白話：把文字打碎，無法還原。「123456」經過雜湊變成「e10adc3949ba59abbe56e057f20f883e」。資料庫不存明文密碼，只存雜湊值。駭客拿到也沒用。

---

## 2. 階段一：骨架與規範

### 2.1 建立 FastAPI 專案骨架

從零開始。我們先建立一個餐廳的「組織圖」——外場在哪、廚房在哪、倉庫在哪。程式碼也是，先立好架子，再一層一層填東西。

```bash
# 初始化 uv 專案
uv init shortenurl --python 3.11

cd shortenurl

# 新增依賴（使用 uv）
uv add fastapi uvicorn sqlalchemy pydantic python-dotenv psycopg alembic slowapi pytest pytest-asyncio httpx
```

建立目錄結構：

```bash
mkdir -p app/{models,schemas,repositories,routers,services}
mkdir -p migrations/versions tests
touch app/__init__.py app/main.py app/config.py app/database.py app/dependencies.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/repositories/__init__.py
touch app/routers/__init__.py
touch app/services/__init__.py
touch .env.local .env.example
```

✅ **預期看到**：目錄結構像這樣
```
shortenurl/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── routers/
│   └── services/
├── migrations/
├── tests/
├── .env.local
├── .env.example
└── pyproject.toml
```

### 2.2 寫分層紅線：`.cursor/rules/00-layering.mdc`

工地都有牆上貼的安全守則。現在我們把安全守則貼在 AI 的「工地」裡——之後不管你叫它做什麼，它每次開工前都會先讀一遍這十一條。最強的是：它會在你自己都忘記的時候提醒你。

這是整個專案最重要的規則。**這十一條是整個專案唯一的 alwaysApply。**

建立 `.cursor/rules/00-layering.mdc`：

```markdown
---
alwaysApply: true
---

# ShortenURL 分層架構紅線

## 絕對禁止
1. routers 不得直接執行 SQL、不得直接操作 AsyncSession
2. services 不得直接操作 AsyncSession，一律呼叫 repositories
3. repositories 直接操作 AsyncSession 之外的地方出現 AsyncSession
4. 任何 endpoint 回傳 dict 而非 response_model 定義的 Pydantic model
5. BackgroundTask 內重複使用 request 的 AsyncSession（會在回應後報 "session is closed"）

## 一定要做
6. 所有 router 的 async def 函式簽名都要有 response_model
7. 所有 Pydantic schema（request/response）都要標註 example 或 description
8. API key 驗證一律用雜湊比對，不能明文儲存
9. rate limiting 一律依 API key，不能依 IP address
10. background task 內部必須自行開新 AsyncSession，用 session_factory 而非共用 request 的 session
11. 機密設定值（如 API_KEY_SALT）絕不給預設值，缺少環境變數時應拋出 ValueError 讓服務啟動失敗
```

> 🔍 **名詞卡：`.cursor/rules` 與 alwaysApply**
> 白話：放在專案裡、專門寫給 AI 看的「行為守則」檔案。標了 `alwaysApply: true` 的守則，AI **每一次**對話都會自動先讀——像每天早會都要唸一次的工安條文。

### 2.3 驗證規則真的會擋：故意踩一次紅線 ⭐ 一定要親自試的一幕

守則貼好了，現在來測試 AI 會不會真的擋。**故意**叫它做一件違規的事，注意看它的反應。

對 Agent 說：

> 在 routers 裡直接寫 SQL：`select * from links where slug = ...`

✅ **預期看到**：Agent **拒絕並引用規則**，大意如下——

> ⛔ 這違反規則第 1 條。routers 層禁止直接執行 SQL。
>
> 我改用正確做法：
> 1. 在 repository 加 `get_link_by_slug()` 方法
> 2. 在 service 呼叫這個方法
> 3. 在 router 呼叫 service 的結果

看到了嗎？它不只說「不行」，還給了替代方案。這就是好規則的第二個特徵：**被擋下時給替代方案**。寫規則的時候記得：不是寫給機器看的法律條文，是寫給一個很聽話的同事看的工作準則。

🧯 **卡住的話**：如果 Agent 沒擋、直接照做了——代表規則寫得不夠具體，它漏接了。把規則第 1 條改得更具體（點名檔案路徑、變數全名），再測一次。規則的具體程度，決定它擋不擋得住。

### 2.4 環境變數與 config

`.env.example`：

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/shortenurl

# API Security
API_KEY_SALT=please-set-a-random-string-in-.env.local

# Render
RENDER_EXTERNAL_URL=http://localhost:8000
```

`app/config.py`：

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(...)  # 必填
    api_key_salt: str = Field(...)  # 必填，缺少就啟動失敗
    render_external_url: str = Field(default="http://localhost:8000")
    
    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"

settings = Settings()
```

測試環境變數是否正確讀取：

```bash
uv run python -c "from app.config import settings; print(settings.database_url)"
```

✅ **預期看到**：打出你的 DATABASE_URL；若 API_KEY_SALT 沒設定，應該報 `ValueError`。

---

## 3. 階段二：資料庫與 ORM

### 3.1 初始化 Alembic

> 🔍 **名詞卡：Alembic**
> 白話：資料庫的「版本管理系統」。每次改表結構（建表、加欄位），開一張工程單（migration）。好處：任何人拿到這疊單子，都能把一個空資料庫「重播」成一模一樣的狀態。

```bash
uv run alembic init migrations
```

編輯 `migrations/env.py`，設定 SQLAlchemy 異步引擎：

```python
from sqlalchemy.ext.asyncio import create_async_engine

def get_sqlalchemy_url():
    from app.config import settings
    return settings.database_url

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_sqlalchemy_url()
    
    connectable = create_async_engine(
        configuration["sqlalchemy.url"],
        echo=False
    )
    
    async def do_run_migrations(connection):
        await connection.run_sync(alembic_context.configure, connection=connection)
        await connection.run_sync(alembic_context.run_migrations)
    
    asyncio.run(run_migrations(connectable))
```

### 3.2 建立 ORM Models

對 Agent 說：

> 建立 app/models/base.py：SQLAlchemy declarative_base；建立 app/models 底下的三個 model：
> 1. Link（id、slug unique、target_url、created_at、expires_at、created_by_api_key_id）
> 2. Click（id、link_id foreign key、user_agent、referrer、recorded_at）
> 3. ApiKey（id、key_hash、owner_name、created_at、rate_limit_per_minute）

#### 📊 資料庫表格關聯視覺化圖解（投影給同學看）

```mermaid
erDiagram
    API_KEYS ||--o{ LINKS : "1:N (由 API Key 建立短網址)"
    LINKS ||--o{ CLICKS : "1:N (短網址被點擊多次，CASCADE 刪除)"

    API_KEYS {
        uuid id PK "金鑰唯一識別碼"
        string key_hash "SHA-256 雜湊後的金鑰"
        string owner_name "擁有者名稱"
        int rate_limit_per_minute "每分鐘請求上限"
    }

    LINKS {
        uuid id PK "短網址唯一 ID"
        string slug UK "6 碼唯一短代碼 (如 aB3xY9)"
        text target_url "目標原始長網址"
        datetime expires_at "過期失效時間"
        uuid created_by_api_key_id FK "關聯到 API_KEYS(id)"
    }

    CLICKS {
        uuid id PK "點擊事件 ID"
        uuid link_id FK "關聯到 LINKS(id)"
        string ip_address "訪客 IP"
        text user_agent "訪客瀏覽器資訊"
        datetime recorded_at "點擊時間戳"
    }
```

> 💡 **向同學解說技巧**：
> 請同學注意 `LINKS` 與 `CLICKS` 是一對多（1:N）關聯。當訪客點擊短網址時，FastAPI 的 **BackgroundTask** 會在背景非同步寫入一筆 `CLICKS` 紀錄，既能收集數據，又完全不拖慢使用者的 307 轉址速度！

預期產出 ORM 重點：

```python
# app/models/link.py
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import Base

class Link(Base):
    __tablename__ = "links"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(30), unique=True, nullable=False, index=True)
    target_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_by_api_key_id = Column(
        UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False
    )

class Click(Base):
    __tablename__ = "clicks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    link_id = Column(UUID(as_uuid=True), ForeignKey("links.id", ondelete="CASCADE"))
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    owner_name = Column(String(255), nullable=False)
    rate_limit_per_minute = Column(Integer, default=100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

> 🔍 **名詞卡：ORM（Object-Relational Mapping）**
> 白話：用程式物件代表資料庫表格。比如 `Link` 物件代表 links 表的一筆資料——字段有 slug、target_url，方法有存檔、刪除。不用寫原生 SQL，更安全更方便。

### 3.3 建立 migration：001_initial

```bash
uv run alembic revision --autogenerate -m "initial schema"
```

檢查產生的 `migrations/versions/001_initial.py`，確認三張表都在，然後套用：

```bash
uv run alembic upgrade head
```

✅ **預期看到**：終端機逐行印出 `Applying...`，最後 `Running stamp_revision`。接著可以驗證：

```bash
psql $DATABASE_URL -c "\dt"
```

確認 links、clicks、api_keys 三張表都建好了。

---

## 4. 階段三：分層實作

### 4.1 建立 Pydantic Schemas

對 Agent 說：

> 建立以下 Pydantic schemas（app/schemas/）：
> - LinkCreateRequest：target_url（HttpUrl）、custom_slug（optional，regex ^[a-zA-Z0-9-]{3,30}$）、expires_at（optional datetime）
> - LinkResponse：slug、target_url、created_at、expires_at
> - LinkStatsResponse：slug、total_clicks（integer）
> - ClickResponse：id、recorded_at
>
> 所有 schema 都要標註 example 或 description。

預期產出重點：

```python
# app/schemas/link.py
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional

class LinkCreateRequest(BaseModel):
    target_url: HttpUrl
    custom_slug: Optional[str] = Field(
        None,
        pattern=r"^[a-zA-Z0-9-]{3,30}$",
        description="Custom slug: 3-30 chars, alphanumeric and hyphen only"
    )
    expires_at: Optional[datetime] = Field(None, description="Optional expiration datetime (UTC)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "target_url": "https://example.com/very/long/url",
                "custom_slug": "my-link",
                "expires_at": None
            }
        }
    }

class LinkResponse(BaseModel):
    slug: str
    target_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}  # ← SQLAlchemy orm_mode
```

### 4.2 建立 Repositories

對 Agent 說：

> 建立 repositories 層，唯一直接操作 AsyncSession 的層：
> - LinkRepository：create_link、get_link_by_slug、get_stats
> - ClickRepository：record_click、count_clicks_for_link
> - ApiKeyRepository：get_api_key_by_hash

預期產出重點：

```python
# app/repositories/link_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Link, Click
from datetime import datetime
from typing import Optional

class LinkRepository:
    async def create_link(
        self,
        session: AsyncSession,
        slug: str,
        target_url: str,
        api_key_id: str,
        expires_at: Optional[datetime] = None
    ) -> Link:
        link = Link(
            slug=slug,
            target_url=target_url,
            created_by_api_key_id=api_key_id,
            expires_at=expires_at
        )
        session.add(link)
        await session.flush()  # ← 非同步寫入
        return link
    
    async def get_link_by_slug(
        self,
        session: AsyncSession,
        slug: str
    ) -> Optional[Link]:
        result = await session.execute(
            select(Link).where(Link.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def get_stats(
        self,
        session: AsyncSession,
        link_id: str
    ) -> int:
        result = await session.execute(
            select(func.count(Click.id)).where(Click.link_id == link_id)
        )
        return result.scalar() or 0
```

注意這一行：`await session.flush()`。這是非同步的「把資料寫進資料庫」。為什麼用 flush 不用 commit？因為 session 的生命週期是 router 管的，repository 只負責放進去，router 負責說「確認送出去」。倉庫把米放進鍋子，廚房負責決定什麼時候起鍋。

### 4.3 建立 Services

對 Agent 說：

> 建立 services 層，零 AsyncSession 但有商業邏輯：
> - LinkService：create_link（驗證 slug 合法性、自動產生 slug）、get_link、record_click、get_stats
> - AuthService：verify_api_key、check_rate_limit

預期產出重點：

```python
# app/services/link_service.py
import random
import string
from typing import Optional
from datetime import datetime
from app.repositories import LinkRepository
from app.schemas import LinkCreateRequest, LinkResponse, LinkStatsResponse
from sqlalchemy.ext.asyncio import AsyncSession

class LinkService:
    def __init__(self, repo: LinkRepository, session_factory):
        self.repo = repo
        self.session_factory = session_factory
    
    def _generate_slug(self) -> str:
        """Generate a random 8-char slug."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    async def create_link(
        self,
        session: AsyncSession,
        req: LinkCreateRequest,
        api_key_id: str
    ) -> LinkResponse:
        # 驗證 slug 合法性
        slug = req.custom_slug or self._generate_slug()
        if not self._validate_slug(slug):
            raise ValueError(f"Invalid slug: {slug}")
        
        # 呼叫 repository 做資料庫操作
        link = await self.repo.create_link(
            session,
            slug=slug,
            target_url=str(req.target_url),
            api_key_id=api_key_id,
            expires_at=req.expires_at
        )
        return LinkResponse.model_validate(link)
    
    async def record_click(
        self,
        slug: str,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ):
        """Background task：自行開新 session，不共用 request 的 session"""
        async with self.session_factory() as session:
            async with session.begin():
                link = await self.repo.get_link_by_slug(session, slug)
                if link:
                    await self.repo.record_click(session, link.id, ip_address, user_agent)
```

service 層是廚房的決策層。「要建短網址」，service 來決定：slug 格式對不對、要自動產 slug 還是用客人的。這些都是廚房的工作。但實際的「把資料寫進資料庫」，交給 repository 去做。不要在廚房自己寫 SQL。

### 4.4 建立 Routers

對 Agent 說：

> 建立 routers 層，HTTP 層、Depends() 注入、響應模型明確：
> - POST /links：建立短網址，需要 API key 認證
> - GET /{slug}：302 轉址，背景記錄點擊（用 BackgroundTask）
> - GET /links/{slug}/stats：查點擊統計，需要 API key 認證

預期產出重點：

```python
# app/routers/links.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import LinkCreateRequest, LinkResponse, LinkStatsResponse
from app.services import LinkService
from app.dependencies import get_db, get_current_api_key

router = APIRouter(prefix="/links", tags=["links"])

@router.post(
    "",
    response_model=LinkResponse,
    description="Create a new short link",
    status_code=201
)
async def create_link(
    req: LinkCreateRequest,
    session: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_current_api_key),
    service: LinkService = Depends(get_link_service)
):
    """Create a new short link. Returns the slug and target URL."""
    try:
        return await service.create_link(session, req, api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/{slug}",
    description="Redirect to the target URL",
    status_code=302
)
async def redirect(
    slug: str,
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    service: LinkService = Depends(get_link_service)
):
    """Redirect to the target URL. Records click in background."""
    link = await service.get_link(session, slug)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    # 立即回應 302，背景記錄點擊
    background_tasks.add_task(
        service.record_click,
        slug,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return RedirectResponse(url=link.target_url, status_code=302)
```

這就是外場。收點單：request。詢問廚房「怎麼做」：呼叫 service。把菜端給客人：response。沒有 SQL、沒有複雜邏輯，就是協調而已。

---

## 5. 階段四：認證、限流、部署

### 5.1 API Key 認證與限流

對 Agent 說：

> 建立 dependencies.py 與 services/auth_service.py：
> - get_current_api_key()：從 Authorization header 提取 API key，雜湊後驗證（鹽值從 settings 讀）
> - check_rate_limit()：查詢 api_keys 表裡的 rate_limit_per_minute，用內存計數器簡化
> - get_link_service()：工廠函式，Depends() 注入

核心概念—— **API key 驗證只做雜湊比對，不能明文儲存**：

```python
# dependencies.py
import hashlib
from fastapi import Depends, HTTPException, Request
from app.config import settings
from app.services import AuthService

async def get_current_api_key(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    provided_key = auth_header.split()[-1]
    
    # 雜湊驗證（假設資料庫裡存的是雜湊值）
    # service = AuthService(...)
    # is_valid = await service.verify_api_key(provided_key)
    # if not is_valid:
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    
    return provided_key
```

✅ **預期看到**：無效 API key 回傳 401 Unauthorized；超過速率限制回傳 429 Too Many Requests。

🧯 **卡住的話**：API key 驗證失敗通常是鹽值設定不一致——確認 `.env.local` 裡的 `API_KEY_SALT` 跟資料庫裡的一樣。

---

## 6. 情境演練：背景任務記錄點擊 ⭐ 一定要親自試的一幕

現在來看最精彩的一幕。轉址要極快，記錄點擊不能卡。換你來測測看。

**需求**：轉址要立即回應，記錄點擊不能拖慢這個過程。

**怎麼做**：

1. **GET /{slug} 查到連結後立即回傳 302**
   - 查詢時間：~10–20ms
   - 回傳 302：<50ms

2. **用 FastAPI BackgroundTask 背景寫入 clicks 表**
   - 記錄任務被加進隊列，不等待
   - 1–2 秒後 DB 寫入完成

3. **background task 內自行開一個新的 async session**
   - request 的 session 已 commit/close
   - background 用獨立 session，自己控制生命週期

**會看到什麼**：

```bash
# 請求轉址
$ time curl -i http://localhost:8000/my-link
HTTP/1.1 302 Found
Location: https://example.com
real    0m0.045s   # ← 45ms，不會慢

# 立刻查統計（還沒寫入）
$ curl http://localhost:8000/links/my-link/stats
{"slug":"my-link","total_clicks":0}

# 稍等 2 秒再查
$ sleep 2
$ curl http://localhost:8000/links/my-link/stats
{"slug":"my-link","total_clicks":1}  # ← 背景任務寫入完成
```

✅ **預期看到**：轉址立刻回應（<100ms），後臺異步寫入；查詢統計時 total_clicks 逐漸遞增。

🧯 **卡住的話**：如果轉址很慢（>500ms），表示背景任務沒正確寫進去，改用同步寫入了。確認 `BackgroundTask` 有加進 `background_tasks` 隊列。

---

## 7. FastAPI 主程式與 Swagger 文件

> 🔍 **名詞卡：Swagger／OpenAPI**
> 白話：API 的「操作說明書」。打開 `/docs`，你會看到所有 API 端點、參數、範例——全自動產生。不用手寫文件。

對 Agent 說：

> 建立 app/main.py，FastAPI 應用：
> - 引入三個 router：links.py、health.py
> - 全局 exception handler，統一 HTTPException 與 ValueError 的錯誤格式
> - 讀取 settings 驗證環境變數（缺少就拋出 ValueError 讓服務啟動失敗）

預期產出重點：

```python
# app/main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from app.routers import links, health
from app.config import settings

app = FastAPI(
    title="ShortenURL API",
    description="Fast URL shortener with click tracking",
    version="1.0.0"
)

# 驗證機密環境變數（缺少就啟動失敗）
if not settings.api_key_salt:
    raise ValueError("API_KEY_SALT environment variable is required")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(links.router)
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

本地測試：

```bash
# 啟動開發伺服器
uv run uvicorn app.main:app --reload

# 在另一個終端測試
# 建立短網址
curl -X POST http://localhost:8000/links \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key-123" \
  -d '{"target_url": "https://example.com", "custom_slug": "test"}'

# 轉址
curl -i http://localhost:8000/test

# 查統計
curl http://localhost:8000/links/test/stats \
  -H "Authorization: Bearer test-key-123"

# OpenAPI 文件
open http://localhost:8000/docs
```

✅ **預期看到**：打開 `http://localhost:8000/docs`，看到一個互動式的 API 文件頁面。上面列出所有 endpoint、request/response 範例。可以直接在頁面上試打 API。

🧯 **卡住的話**：如果 `/docs` 打不開，確認 fastapi 和 uvicorn 都裝了；如果有 endpoint 沒出現，確認 router 有 include。

---

## 8. 驗收清單

> ❓ **想一想**：什麼時候一個服務才算「完成」？不是代碼寫完，而是能經過測試。
>
> **答案**：通過自動化測試、各層職責清楚、文件完整。

- [ ] `uv sync` 安裝成功，無版本衝突
- [ ] `uv run alembic upgrade head` 三張表全部建立
- [ ] `uv run pytest` 全綠（測試涵蓋：create link、redirect、stats、auth）
- [ ] 對 Agent 說「在 router 裡直接寫 SQL」→ 被規則擋下並給出替代方案
- [ ] POST /links 新增連結成功，回傳 LinkResponse
- [ ] GET /{slug} 立即回傳 302，<100ms
- [ ] 稍等 2 秒後查 /links/{slug}/stats，點擊數 +1
- [ ] 無效 API key 回傳 401
- [ ] 超過速率限制回傳 429
- [ ] 過期短網址回傳 404
- [ ] OpenAPI 文件（/docs）全部 endpoint 都列出來
- [ ] 開兩個瀏覽器分別用不同 API key 登入，互相看不到對方的連結 ⭐ 必做

---

## 9. 常見坑排錯速查

多數分層與非同步的問題都能在這張表快速定位：

| 問題 | 原因 | 解法 |
|---|---|---|
| `"session is closed"` 錯誤 | background task 重複使用 request 的 session | background task 內自行開新 session，用 `session_factory()` |
| 後臺任務沒寫入資料 | 沒有 `async with session.begin()` 或沒 commit | 改用 `async with session.begin(): ...`，會自動 commit |
| API key 校驗永遠失敗 | 明文比對或鹽值不一致 | 改用雜湊比對，鹽值從 `settings.api_key_salt` 讀 |
| rate limit 無效 | 用 IP 位址限流（VPN 會同一個 IP） | 改用 API key 限流，`key_func=get_api_key` |
| 轉址很慢（1s+） | 在轉址 endpoint 同步寫入 DB | 改用 BackgroundTask，轉址立即回應 |
| migration "multiple heads" | 多人開 migration 導致分支 | `uv run alembic merge heads` 合併 |
| Render 啟動失敗 | 埠號寫死（如 8000），Render 指派其他埠 | 改讀 `$PORT` 環境變數：`--port $PORT` |
| PostgreSQL 連線超時 | connection pool 用盡或連線逾時 | 增加 pool_size 或檢查 DATABASE_URL |
| Pydantic 驗證不夠嚴格 | schema 沒有 pattern 或 example | 補上 Field(pattern=...)、model_config |
| 轉址後無法看到點擊統計 | 查詢用了不同的 session 或事務隔離 | 確認 BackgroundTask 有 commit，或加 1-2 秒延遲再查 |
| 服務啟動時崩潰 | 缺少機密環境變數（如 API_KEY_SALT） | 檢查 `.env.local`，確認所有 Field(...) 都有值 |

---

## 10. 帶走的三句話

如果整份教學只能記住三件事，就這三句。

1. **分層架構規則能防止商業邏輯與 SQL 全塞進單一檔案**——routers 不碰 AsyncSession、services 不碰 SQL、repositories 才寫 database 語句；邊界清楚，改功能不會全專案尋寶。就像分工明確的餐廳，外場、廚房、倉庫各司其職。

2. **background task 必須自行開新 session，不共用 request session**——request 的 session 在回應後就關了，background 裡再用會炸掉；自行 `async with session_factory() as session:` 才不漏資料。就像傳菜生要背著自己的餐盤，不能拿客人吃剩的盤子再裝菜。

3. **API key 要雜湊儲存，rate limit 要依 API key 而非 IP**——明文儲存與 IP 限流是最常見的安全地雷；用 hashlib 雜湊、每個 key 獨立計數，就不會被 VPN 繞過。機密設定值也不給預設值，缺少環境變數要讓服務拒絕啟動。
