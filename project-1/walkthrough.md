# Walkthrough：第 0 課 環境準備

> 目標：跑完第 4 節的健康檢查**全綠**、帳號總表全部打勾。
> 這一課不寫任何程式，但它決定之後 14 課的節奏——環境沒弄好，每一課的前 40 分鐘都會在救火。
> 這一課做的事叫「**把必然會發生的失敗提前到今天發生**」：Docker 要下載好幾 GB、驗證信會躺在垃圾郵件夾、公司電腦會擋安裝。這些事今天爆掉，你有充裕的時間修；等正式開工才爆，就要用寫程式的時間賠。

## 🗺️ 學習地圖（60–90 分）

| 段落 | 時間 | 備註 |
|---|---|---|
| 裝機五件套 | 30 分 | 下載等待時間長，建議提早開始 |
| 帳號申請總表 | 20 分 | 驗證信記得翻垃圾郵件夾 |
| 三個核心概念先修 | 15 分 | 閱讀理解 |
| 健康檢查全綠 | 15 分 | 動手做 |

---

## 🎬 課堂放映表（講師用）

> 診斷工具與遙控器為 `./demo.sh`（位於 `project-1/` 根目錄）。
> 指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕，或直接跑 `./doctor.py` 進行環境診斷。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | 跑一次 `./demo.sh 3` | 檢視講師電腦上的所有環境是否全綠 |
| 2 | 若 Docker 未啟動，先開啟 Docker Desktop | 避免示範本地 Supabase 或 Neo4j 時當場等待啟動 |
| 3 | 確認各平台免費帳號（GitHub、Supabase、AI Studio）已登入備用 | 現場切換示範時不用等收驗證信 |

### 放映時間軸

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:15 | 概念與理念說明 | — | `walkthrough.md` §1–§3 | 裝機五件套表格、帳號總表、三個核心名詞卡（Agent / Rules / MCP） | 把必然發生的失敗前移 |
| 0:15–0:30 | 第 1 幕：五件套快速檢驗 | `./demo.sh 1` | `walkthrough.md` §1 | 終端機依序印出 Node.js (v20+)、Git、uv、Docker 版本號 | 驗證指令比「我裝好了」更可信 |
| 0:30–0:45 | 第 2 幕：大檔下載與備援策略 | `./demo.sh 2` | `walkthrough.md` §1 備援提示 | 大檔預載指令與各專案的雲端免費備援方案 | 公司擋 Docker 時的優雅備援退路 |
| 0:45–1:00 | 第 3 幕：全自動健康診斷 ⭐ | `./demo.sh 3` | `project-1/doctor.py` | 全綠色的終端機診斷卡片，提示全數 core 工具就緒 | 課前診斷與地基健全 |

### 🧯 現場翻車備案

| 翻什麼 | 徵狀 | 30 秒內的救援 |
|---|---|---|
| Docker 在學生電腦無法啟動 | `docker: command not found` 或 daemon error | 告知學生不用慌，涉及 Docker 的 project-2 與 14 全程支援 Supabase 雲端專案與 Neo4j Aura 雲端免費版 |
| Python / uv 找不到指令 | `uv: command not found` | 執行 `curl -LsSf https://astral.sh/uv/install.sh \| sh` 並重新開啟終端機分頁 |

---

## 1. 裝機五件套

每裝完一個，跑右邊的驗證指令，看到版本號才算過：

| 工具 | 做什麼用 | 安裝 | ✅ 驗證 |
|---|---|---|---|
| **Cursor** | 主角：AI 編輯器 | [cursor.com](https://cursor.com) 下載 | 開得起來、能登入 |
| **Node.js 20+** | 跑 JavaScript 專案（前端課全靠它） | [nodejs.org](https://nodejs.org) LTS 版 | `node -v` → v20 以上 |
| **Docker Desktop** | 本地跑 Supabase、Neo4j 用的「便當盒」（詳見 [docker-services.md](./docker-services.md)） | [docker.com](https://docker.com) | `docker run hello-world` |
| **uv** | Python 專案的套件管理（本課程 Python 一律用 uv，不用 pip） | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `uv --version` |
| **git** | 版本控制 | macOS 內建（`xcode-select --install`） | `git -v` |

🧯 **卡住的話**：Docker 在公司電腦被擋是最常見的坑——先記下來，含 Docker 的課（project-2 的本地 Supabase、project-14 的 Neo4j）改走雲端版即可（Supabase 雲端專案、Neo4j Aura 免費版）。

**預先下載大檔**（強烈建議今天就跑，各附所屬課程）：

```bash
docker pull neo4j:5          # project-14 GraphRAG 用
npx supabase start           # project-2 用；第一次會拉映像，跑完可 npx supabase stop
```

## 2. 帳號申請總表

全部**免費方案即可**。驗證信沒收到先看垃圾郵件夾。

| 帳號 | 哪幾課用 | 備註 |
|---|---|---|
| [GitHub](https://github.com) | 全程 | 沒有的先辦，下面兩個都靠它登入 |
| [Supabase](https://supabase.com) | project-2（TaskBoard） | 建一個空專案放著 |
| [Vercel](https://vercel.com) | project-2 部署 | 用 GitHub 帳號登入最快 |
| [Roboflow](https://roboflow.com) | project-13（AutoCV） | 拿 API key |
| [Google AI Studio](https://aistudio.google.com) | project-9（RAG）、project-14（GraphRAG） | 拿免費 Gemini 金鑰 |
| Telegram + [@BotFather](https://t.me/BotFather) | project-12（Bot） | 跟 BotFather 要一個 bot token |
| Expo Go（手機 App） | project-4（習慣追蹤 App） | 手機商店直接裝 |
| ~~Stripe~~ | ~~project-2 Part 2~~ | **不用辦**——課堂版改用 Mock 金流（零註冊），見 project-2 |

## 3. 三個核心概念先修

> 🔍 **名詞卡：Agent**
> 白話：Cursor 裡會「自己動手」的 AI——不只回答，還會讀檔、改程式、跑指令，像坐在旁邊的實習工程師。之後每一課都是「你講需求、它動手、你驗收」。
>
> 🔍 **名詞卡：`.cursor/rules`**
> 白話：貼在工地牆上的施工守則，寫給 AI 看。標了 `alwaysApply` 的守則它每次開工前都會先讀——所以它會在你自己都忘記的時候提醒你。第 1 課（project-2）就會寫第一份。
>
> 🔍 **名詞卡：MCP**
> 白話：讓 AI 接上外部工具的「標準插座」。插上資料庫的 MCP，AI 就能自己查表；插上你自己寫的 MCP（project-10 會自己做一個），AI 就多了你發明的能力。

> ❓ **想一想**：AI 這麼聰明，為什麼還需要我們寫規則給它？
>
> **答案**：聰明不等於知道**你的**紅線。規則是把「這個專案什麼不能做」寫成它每次都會讀到的白紙黑字——它的聰明才會用在對的方向。

## 4. 健康檢查：全綠才算完成

```bash
echo "— 裝機檢查 —" && \
node -v && docker --version && uv --version && git -v && \
docker run --rm hello-world >/dev/null 2>&1 && echo "docker: OK" && \
echo "— 全部通過 ✅ —"
```

✅ **預期看到**：四個版本號 + `docker: OK` + `— 全部通過 ✅ —`。
帳號部分逐項自我檢查：Supabase 能開 Dashboard、AI Studio 能看到 API key、BotFather 給了 token。

## 5. 帶走的三句話

1. **把必然會發生的失敗前移**——大下載、帳號審核、公司防火牆，都要在正課之前爆完。
2. **驗證指令比「我裝好了」可信**——每個工具都要親眼看到版本號，這個習慣之後每一課都在用。
3. **環境是所有課的地基**——之後任何一課卡住，先回來跑一次第 4 節的健康檢查。
