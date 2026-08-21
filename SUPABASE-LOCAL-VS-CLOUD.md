# ☁️ Supabase 地端 Docker vs 雲端 Cloud 完整對照與指令免跑註解指南

> **這份指南的目的**：
> 1. 解釋「本地 Docker」與「雲端 Supabase」的完全等價關係。
> 2. 明確標記哪些指令在**目前已安裝好的狀態下「完全不用再執行」**。
> 3. 提供無法使用 Docker 的同學「如何 3 分鐘切換至雲端 Supabase」的標準步驟與註冊指引。

---

## ⚖️ 1. 本地 Docker vs 雲端 Cloud 等價對照表

| 功能元件 | 🟢 本地 Docker 模式（目前專案狀態） | ☁️ 雲端 Supabase 模式（備援方案） |
|---|---|---|
| **費用與網路** | **100% 免費、100% 離線免連網** | 免費方案（需註冊、需連上網際網路） |
| **註冊網址** | **免註冊**（直接在本機 Docker 運行） | 前往 [https://supabase.com/](https://supabase.com/) 點擊 Sign Up |
| **建立專案** | 執行 `npx supabase start` 自動產生 | 登入後點擊「New Project」選擇免費區域（如 Tokyo） |
| **網頁管理後台 (Studio)** | [http://127.0.0.1:54323](http://127.0.0.1:54323)（本地直接開） | `https://supabase.com/dashboard/project/<your-ref>` |
| **API 進入點 (URL)** | `http://127.0.0.1:54321` | `https://<your-ref>.supabase.co` |
| **測試電子郵箱** | [http://127.0.0.1:54324](http://127.0.0.1:54324) (Mailpit 免寄真信) | 需到 Authentication 設定 SMTP 或查看 Logs |
| **PostgreSQL 資料庫** | `localhost:54322`（本機直接連） | 需設定 Database 密碼與連線字串 |
| **指令差異** | **免 login、免 link** | 需執行 `npx supabase login` 與 `link` |

---

## 🚦 2. 指令清單與「免跑註解」（目前環境狀態）

在目前的專案中，**所有環境與依賴都已經就緒**。以下是各指令在不同情境下的執行需求：

```bash
# ==============================================================================
# 1. 專案建立與套件安裝（⭐ 目前本機已全數安裝完畢，全部「免跑」！）
# ==============================================================================
# [免跑 - 已建置] npx create-next-app@latest taskboard --typescript --app --tailwind --no-src-dir
# [免跑 - 已建置] npx create-expo-app@latest habit-tracker
# [免跑 - 已安裝] cd taskboard && npm install
# [免跑 - 已安裝] npm install @supabase/supabase-js @supabase/ssr

# ==============================================================================
# 2. Supabase 初始化與啟動
# ==============================================================================
# [免跑 - 本地已初始化] npx supabase init
# [免跑 - 本地 Docker 免登入] npx supabase login
# [免跑 - 本地 Docker 免綁定] npx supabase link --project-ref <ref>
# [常駐執行中]          npx supabase start       # （Docker 容器已在背景運行）

# ==============================================================================
# 3. 課堂常用日常指令（⭐ 老師與同學「只需跑這幾行」即可！）
# ==============================================================================
npm run dev              # 啟動前端網頁伺服器（Project 2 開在 localhost:3000，Project 4 開在 5174）
./demo.sh <幕次>         # 課堂放映遙控器（例如 ./demo.sh 3 重置測資，./demo.sh 5 模擬攻擊）
```

---

## ☁️ 3. 如果想改用「雲端 Supabase」，該怎麼做？（3 分鐘切換教學）

如果學生的公司電腦被鎖死「不能開 Docker」，請引導學生按照以下 4 個步驟切換到雲端：

### 步驟 1：前往註冊帳號
1. 打開瀏覽器進入 👉 **[https://supabase.com/](https://supabase.com/)**。
2. 點擊右上角 **「Start your project」** 或 **「Sign Up」**（可用 GitHub 帳號一鍵授權登入）。

---

### 步驟 2：建立一個免費雲端專案
1. 進入 Dashboard 後，點擊綠色的 **「New Project」**。
2. 填寫專案設定：
   * **Name**：輸入 `taskboard`（或自訂名稱）。
   * **Database Password**：設定一組資料庫密碼（請牢記）。
   * **Region**：選擇距離台灣最近的 **Tokyo (ap-northeast-1)** 或 **Singapore**。
   * **Pricing Plan**：選擇 **Free Plan**。
3. 點擊 **「Create new project」**，等待約 1–2 分鐘等雲端資料庫建置完成。

---

### 步驟 3：找到雲端連線資訊（URL 與 Keys）
1. 在左側選單點擊齒輪圖示 **Project Settings** → 點擊 **API**。
2. 複製以下三樣資訊：
   * **Project URL**（網址形如 `https://abcdefghijklm.supabase.co`）
   * **Project API Keys (`anon` / `public`)**（前端用大廳鑰匙）
   * **Project API Keys (`service_role` / `secret`)**（後端用萬能鑰匙）
   * **Reference ID**（網址列或 General 設定裡的 Project Ref，例如 `abcdefghijklm`）

---

### 步驟 4：替換專案內的 `.env.local`
把 `taskboard/.env.local` 或 `habit-tracker/.env.local` 的內容改成雲端的資訊即可：

```bash
# 換成雲端 Supabase 連線資訊
NEXT_PUBLIC_SUPABASE_URL=https://abcdefghijklm.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

如果要用 CLI 把本地 SQL 推上雲端，才需要執行：
```bash
npx supabase login
npx supabase link --project-ref abcdefghijklm
npx supabase db push
```

---

### 💡 講師一句話總結：
> **「本機有 Docker = 100% 離線免註冊秒跑；沒 Docker = 3 分鐘免費註冊 Supabase 雲端版填入 `.env.local` 即可！」**
