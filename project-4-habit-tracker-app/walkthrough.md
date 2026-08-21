# Walkthrough：在 Cursor 上把習慣追蹤 App 一步一步做出來

> 這份文件帶你從零做出**習慣追蹤 App**——一個能離線打卡、自動同步、深色模式不跑版的行動 App。
> 你會學到三件事：怎麼用規則明文約束 AI 的 UI 邊界、怎麼用 Checkpoint 和截圖快速修復排版、怎麼用強制開發順序避免「先做畫面後接資料」的返工。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先做這五件事，動手才不會卡）

1. **裝好 Expo CLI 並跑過一次整個流程**——本地 Supabase 啟動（`npx supabase start`）第一次會下載 Docker 映像（可能 5–10 分鐘），先跑過一次，之後啟動只要幾十秒。
2. **在手機或模擬器上安裝 Expo Go App**（iOS App Store / Google Play），這樣掃 QR code 就能直接看到你做好的 App。
3. **把本文件每個「✅ 預期看到」瀏覽一遍**，知道正常畫面長怎樣（模擬器啟動後 Metro 的 QR code、Expo Go 掃碼後的載入畫面），動手時才判斷得出「這是正常的」還是「翻車了」。
4. **準備 Cursor 的 Checkpoint 功能**：用快捷鍵存檔（Cmd+Shift+S），再點 Timeline 看能否復原——排版修復演示要靠這個。
5. 動手過程中，每跑完一個指令就對照文中的「✅ 預期看到」——判斷得出「這是正常的」還是「翻車了」，除錯速度差十倍。

## 🗺️ 學習地圖（建議 3 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 第 1 節概念 | 25 分 | 閱讀理解（這是全課靈魂，慢慢看） |
| 第 2 節規則寫進規範 | 15 分 | 閱讀理解（規則內容很重要，仔細讀） |
| 第 3 節資料庫與服務層 | 30 分 | 動手做（可加速：先讀 migration 再一起跑） |
| 第 4 節 Hooks 與查詢 | 20 分 | 動手做（連接層，邊寫邊理解） |
| 第 5 節元件與排版 | 20 分 | 動手做（先做第一個元件，再看其他成品） |
| 第 6 節頁面與導航 | 15 分 | 動手做（用 Expo Go 掃 QR code，⭐ 一定要親自試的一幕） |
| 第 7 節情境演練（截圖修排版） | 15 分 | 動手做（Checkpoint + 截圖修復最有效） |
| 第 8–9 節驗收與小結 | 40 分 | 閱讀理解 + 反思 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `./habit-tracker/`，遙控器是 `./demo.sh`（位於 `project-4-habit-tracker-app/` 根目錄）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 支援瀏覽器 Mobile Frame 模擬器預覽，無需實體手機或模擬器即可全班放映。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd project-4-habit-tracker-app/habit-tracker && npm install` | 第一次安裝依賴（約 10–20 秒）。課前裝好，課堂上全離線秒開 |
| 2 | 跑一次 `./demo.sh 2` | 檢查型別與 Streak 連續天數邏輯 |
| 3 | 跑一次 `./demo.sh 5`（構建驗證） | 確認 `npm run build` 成功輸出 dist/ 目錄 |
| 4 | 確認 5174 埠沒有殘留行程 | 第 4 幕 App 展示會使用 Vite 埠 |

### 放映時間軸

時間軸切成 6 段，對應上方學習地圖（合計 180 分鐘），全長 **3 小時**。

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:25 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §1 | 制服廠比喻、多端跑版成因、強制開發順序（資料模型 → 服務層 → UI） | 邊界約束與防禦性排版 |
| 0:25–0:40 | 第 1 幕：Scope 規則檔 | `./demo.sh 1` | `habit-tracker/.cursor/rules/00-scope.mdc` | 00-scope.mdc 的嚴格規範：禁止未授權動畫與任意元件 | 把紅線寫進 Cursor Rules，約束 AI 不亂加功能 |
| 0:40–1:10 | 第 2 幕：資料模型與 Streak ⭐ | `./demo.sh 2` | `habit-tracker/src/types/habit.ts` | Habit 介面、calculateStreak 連續天數算法與種子資料 | 核心邏輯先行，先算對天數再畫畫面 |
| 1:10–1:30 | 第 3 幕：離線打卡持久化 | `./demo.sh 3` | `habit-tracker/src/services/habitStorage.ts` | loadHabits / saveHabits 離線打卡切換與 completedDates 陣列 | 離線優先架構設計 |
| 1:30–2:20 | 第 4 幕：啟動手機模擬器視圖 ⭐ | `./demo.sh 4` | `habit-tracker/src/components/MobileFrame.tsx` | 瀏覽器展示 iPhone 框架之習慣追蹤 App，即時打卡與切換主題 | 眼見為憑：點擊打卡、Streak 🔥 自動更新、即時新增習慣 |
| 2:20–3:00 | 第 5 幕：構建驗收與總結 | `./demo.sh 5` | `habit-tracker/vite.config.ts` | `tsc -b && vite build` 產出乾淨 Bundle | 跨平台構建與生產環境驗證 |

### ⭐ 全場最值得停下來的一幕

**第 4 幕的手機模擬器展示台。**
展示台內嵌 iPhone 實體機殼（含 Dynamic Island 與 Home Indicator），直接在投影螢幕上點擊打卡按鈕，卡片瞬間切換勾選狀態、Streak 火焰天數即時累加、上方「今日完成度」動態跳轉百分比！切換深色模式時，所有元件色彩平滑過渡且排版完全不跑版。

### 🧯 現場翻車備案

| 翻什麼 | 徵狀 | 30 秒內的救援 |
|---|---|---|
| 模擬器埠被占用 | 提示 port 5174 被占用 | 查看終端機印出的實際 URL (如 http://localhost:5175) |
| 本地打卡資料需重置 | 測試過後想還原初始 4 個示範習慣 | 在瀏覽器 DevTools Console 執行 `localStorage.clear(); location.reload();` 即可瞬間還原 |

---

## 🎬 開場故事：同一件制服要穿遍全班

想像今天要做一個「制服廠」，替全班同學量身訂做制服。但這家廠有個奇怪的規則：所有人穿的是**同一件制服**，不是各自一件。產品經理在褲子上加了一個口袋，滿分。Lily 用 iPhone 12 試穿時剛好貼身，完美。但 David 用 Pixel 7 一穿，寬度不夠，口袋位置整個皺掉——這叫「跑版」。

制服廠現在有三個選擇：

1. **各做一版**：每個人尺寸一件（native app：iOS、Android、Web 各一份）
2. **做一件 one-size-fits-all**（Responsive Web：同一份 HTML，CSS 自動換行）
3. **做一件智慧制服**（React Native：同一份 JS，跑在 iOS、Android、Web——用規則讓 UI 不亂加，用 Checkpoint 讓改壞能立刻復原）

這份教學做的是第三種。關鍵是：**改排版之前一定要 Checkpoint（遊戲存檔點），改壞了立刻讀檔重來。而且最重要的是不能一開始就亂加東西，要有規則約束 Agent。**

這個制服比喻會貫穿全份教學。對照表：

| 制服廠 | 系統 |
|---|---|
| 各個同學的身材 (iPhone 12、Pixel 7、平板、網頁...) | 各種螢幕尺寸 |
| 加一個口袋導致皺掉 | 新增一個 UI 元素導致跑版 |
| 改動前先拍照、改壞立刻看照片改回 | Checkpoint + 截圖修復 |
| 廠長的規則「不要亂加東西」| `.cursor/rules/00-scope.mdc` alwaysApply |
| 師傅的工作流：尺寸 → 布料 → 裁縫 → 試衣 → 調整 | 資料庫 → 服務層 → hooks → 元件 → 頁面 |

---

## 0. 課前準備

- 安裝 [Cursor](https://cursor.com)、Node.js 20+、Docker
- 註冊 [Supabase](https://supabase.com) 帳號，建一個空專案（免費方案即可）
- 安裝 Supabase CLI：`brew install supabase/tap/supabase`（或 `npx supabase` 直接用）
- 裝好 Expo Go App（iOS App Store / Google Play）或有可用的模擬器

> 🔍 **名詞卡：React Native**
> 白話：用 JavaScript / TypeScript 寫，同一份程式碼自動跑在 iPhone、Android、Web 上——「一份程式碼、三種平台」。對比：iOS 要用 Objective-C/Swift、Android 要用 Kotlin，每個平台都要重寫一遍，React Native 幫你省掉那個工作。
>
> 🔍 **名詞卡：Expo**
> 白話：React Native 的「傻瓜包裝」。不用自己配 Xcode / Android Studio 的複雜環境，Expo 幫你整理好；拿手機下個 Expo Go App，掃 QR code 就能看到你做好的 App——開發速度快十倍。
>
> 🔍 **名詞卡：原生 App vs 網頁**
> 白話：原生 App（Native App）= 裝在手機系統裡、有硬體通知、內存可以永續活著；網頁 = 瀏覽器跑、每次關掉重開都是新頁面。React Native 是「用網頁技術寫原生 App」——兼具兩者的好處。
>
> 🔍 **名詞卡：模擬器（Emulator）**
> 白話：在電腦上虛擬跑一台手機——不用真的買 iPhone 或 Android，就能測試 App。iOS 模擬器（Xcode）和 Android 模擬器（Android Studio）。

---

## 1. 先懂概念：行動端排版為什麼這麼容易跑版

### 1.1 行動端與網頁排版的核心差異

Web 開發時，大家習慣在寬螢幕上開發——螢幕寬，加一個 icon、改一個 padding，溢出去就 scrollbar 搞定。行動端完全不同。手機螢幕是「一屏就要漂亮」——加一個 icon、改一個 padding，就會文字換行、按鈕擠出螢幕、間距破裂、深色模式下文字看不見。這不是小事，是整個開發思維的翻轉。

Web 的限制是寬度，但它有 scrollbar；行動端是「一屏就要漂亮」。加一個 UI 元素，就會：

- 文字換行
- 按鈕擠出螢幕
- 間距破裂
- 深色模式下文字看不見

網頁時代習慣的「看起來 OK 就上」在行動端會付出代價。

### 1.2 連續天數是典型的「沉默故障」

> 🔍 **名詞卡：沉默故障（Silent Failure）**
> 白話：邏輯錯了不會報錯，畫面看起來還能用，但數字是錯的。這是最難察覺的 bug。「有時候會少算一天」、「昨天打卡了但今天連續天數卻歸零」——都是典型症狀。
>
> ❓ **想一想**：如果連續天數演算法寫錯了，編譯器會報錯嗎？
>
> **答案**：不會。程式跑得好好的，數字才是錯的。這比語法錯誤更可怕，因為你看不出來。

邏輯錯了不會報錯，是最難察覺的 bug。常見錯誤包括：

| ✗ 錯誤實作 | ✓ 正確實作 |
|---|---|
| 今天沒打卡就直接歸零 | 今天沒打卡但昨天有算，仍不中斷 |
| 忽略昨天有打卡的情況 | 缺一整天才真正中斷 |
| 沒有針對邊界情況寫測試 | 寫 6 個測試涵蓋空陣列與重複日期 |

正確邏輯：**只要前一天有打卡紀錄（不管今天有沒有），連續天數就繼續計算。缺一整天才重置。**

### 1.3 Checkpoint 和截圖：行動端排版修復的二次元武器

> 🔍 **名詞卡：Checkpoint**
> 白話：Cursor 內建的時間線功能，存檔可一鍵復原。像遊戲的「存檔點」——改排版改壞了，按一下回到改動前。
>
> ❓ **想一想**：改排版時，怎麼樣最安全？
>
> **答案**：改之前先 Checkpoint，萬一改壞立刻復原。

**Checkpoint**：Cursor 內建的時間線功能，存檔可一鍵復原。改排版時必開。

**截圖**：把模擬器截圖拖進對話框，Agent 直接看懂視覺問題，比文字描述快十倍，而且會順便掃出同類問題。

組合技：改動前 Checkpoint → 改排版 → 截圖 → 排版跑了立刻復原 → 換個思路重來。

### 1.4 環境變數的 EXPO_PUBLIC_ 前綴——什麼進 bundle，什麼不進

> 🔍 **名詞卡：EXPO_PUBLIC_ 前綴**
> 白話：Expo 與 Next.js 不同。只有 `EXPO_PUBLIC_` 前綴的變數會被打進 App bundle（打包到手機裡）；普通變數只在打包時可用。打進 bundle = 任何人都能從 App 逆向工程讀出來。機密絕對不能用前綴。

Expo 與 Next.js 不同：只有 `EXPO_PUBLIC_` 前綴的變數會被打進 bundle；普通變數只在打包時可用。

```bash
✓ EXPO_PUBLIC_SUPABASE_URL=<url>           # 進 bundle，客戶端使用
✓ EXPO_PUBLIC_SUPABASE_ANON_KEY=<key>      # 進 bundle，客戶端使用
✗ SUPABASE_ADMIN_KEY=<key>                 # 不進 bundle，不用在行動端
```

機密資料**絕不可用前綴**——一旦加上 EXPO_PUBLIC_，打包 App 的任何人都能解開。

---

## 2. 階段一：骨架與規範

### 2.1 建立 Expo 專案

第一步是鋪軌道。Expo 專案建好、Supabase 連上、環境變數設好，後續才能一步步堆功能。

```bash
# ------------------------------------------------------------------------------
# 專案建立與套件安裝（⭐ 目前本機已全數安裝建置完畢，此區指令「免重複執行」）
# ------------------------------------------------------------------------------
npx create-expo-app@latest habit-tracker
cd habit-tracker
npm install @supabase/supabase-js @supabase/ssr
npm install nativewind react-native-css-in-js
npm install @react-navigation/native expo-router
npm install @tanstack/react-query

# ------------------------------------------------------------------------------
# Supabase 後端連線（依環境二選一）
# ------------------------------------------------------------------------------
# 【情境 A：本地 Docker 模式（目前專案狀態，推薦首選）】
#   ✓ Docker 已在背景運行本地 Supabase，直接跳過 login 與 link 指令！
#   ✓ 執行 npx supabase start 即可（若已在運行則自動跳過）
#   ✗ npx supabase login                  # （本地模式：免跑）
#   ✗ npx supabase link --project-ref ... # （本地模式：免跑，無需填寫 ref）

# 【情境 B：雲端 Supabase 模式（備援：電腦不能裝 Docker 時才使用）】
#   1. 去 https://supabase.com/ 免費註冊專案
#   2. 在 Project Settings -> API 找到 Project Ref（例如 abcdefghijklm）
#   3. 執行：npx supabase login && npx supabase link --project-ref abcdefghijklm
```

`.env.local`：

```bash
# 本地 Docker 模式填寫：
EXPO_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...

# 若改走雲端模式則填寫：
# EXPO_PUBLIC_SUPABASE_URL=https://abcdefghijklm.supabase.co
# EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...
```

> 💡 **重點提醒**：
> 1. **有 Docker 就不用註冊**：本地 Docker 已經自帶 Postgres 資料庫、Auth、Studio 網頁後台，完全免費且離線可用。
> 2. **`<你的 project ref>` 只有在連雲端時才需要**：本地開發時一律使用 `http://127.0.0.1:54321`，不需要 link 任何 project ref！

注意看這兩行都有 `EXPO_PUBLIC_` 前綴——這代表「本來就要打進 App 的」。Supabase URL 和 anon key 是「大廳門禁」，本來就公開，沒關係。**EXPO_PUBLIC_ 前綴必須有，否則客戶端讀不到。**

✅ **預期看到**：目前環境已全數建置完畢，直接在 `habit-tracker` 目錄執行 `npm run dev` 即可在瀏覽器開啟 iPhone 模擬器！

🧯 **卡住的話**：詳細地端 vs 雲端切換步驟與排除方式請參閱 **[SUPABASE-LOCAL-VS-CLOUD.md](../SUPABASE-LOCAL-VS-CLOUD.md)** 與 **[TROUBLESHOOTING-MASTER.md](../TROUBLESHOOTING-MASTER.md)**。

### 2.2 核心規則檔：`.cursor/rules/00-scope.mdc`（alwaysApply）

工地都有牆上貼的安全守則。現在把安全守則貼在 AI 的「工地」裡——之後不管你叫它做什麼，它每次開工前都會先讀一遍這六條。最強的是：**它會在你自己都忘記的時候提醒你**。我們特意把重點放在檔案結尾，善用「新近效應」——最後讀到的東西最難忘。

這是整個專案唯一的 alwaysApply。**把最強的提醒放在檔案結尾，善用 recency 效應加強效果。**

> 🔍 **名詞卡：`.cursor/rules`**
> 白話：放在專案裡、專門寫給 AI 看的「行為守則」檔案。標了 `alwaysApply: true` 的守則，AI **每一次**對話都會自動先讀——像每天早會都要唸一次的工安條文。

```markdown
---
alwaysApply: true
---

# 習慣追蹤 App 範圍邊界

## 禁止（違反視為錯誤）

1. 禁止新增使用者沒有明確要求的 UI 元素
2. 禁止修改與當前任務無關的檔案或區域
3. 禁止「順手重構」未被要求整理的程式碼

## 必須（每次都要檢查）

4. 改動前先手動存一次 Checkpoint
5. 排版問題把截圖貼給我，不要用文字描述
6. 依強制開發順序做：資料庫 → 服務層 → hooks → 元件 → 頁面，一步都不能跳

## 補充規則

- 元件不得直接 import supabase，所有資料呼叫走 services/ 與 hooks/
- query key 必須含 userId，切換登入者時快取才會正確區隔
- 深色模式用 `dark:` 前綴，不要用條件渲染

## 重點提醒

**不確定該不該加，先問，不要先做。行動端 UI 對排版特別敏感，多一個 icon 就可能跑版。**
```

`alwaysApply: true` 代表四種 Agent 模式全程套用這條規則，每一次對話自動載入，不用你提醒。

✅ **預期看到**：重啟 Cursor 後，Settings → Rules 看得到 00-scope.mdc 標註 `alwaysApply`。

### 2.3 其餘規則用 globs

> 🔍 **名詞卡：context／globs**
> 白話：context 是 AI 的「工作記憶桌面」，桌面就那麼大，堆太多紙它反而找不到重點；globs 是「檔案路徑的萬用字元」（`app/**` = app 資料夾底下全部），讓某份守則**只在碰到相關檔案時**才被放上桌面。

**只有一條 always，其餘規則用 globs** —— 規則檔全部 alwaysApply 會把 context 塞爆，Agent 反而記不住重點。

再建兩份按需載入的：

`.cursor/rules/expo.mdc`（碰到 `app/**` 才載入）：

```markdown
---
description: Expo 架構慣例
globs: ["app/**/*.tsx", "app/**/*.ts"]
---

- 頁面用 expo-router，不用 React Navigation 原生 API
- 狀態管理用 React Query，不用 Redux/Zustand
- 所有資料呼叫走 hooks/useHabits.ts、useHogs.ts，元件用 const data = useHabits()
- 排版用 NativeWind（Tailwind 的行動端版），不要用行內 style
```

`.cursor/rules/supabase.mdc`（碰到 `services/**` 才載入）：

```markdown
---
description: Supabase 服務層慣例
globs: ["services/**/*.ts"]
---

- 所有 Supabase 呼叫集中在 services/
- 服務層函式暴露給 hooks/，不直接給元件
- habits 查詢加 `order by created_at desc`
- logs 查詢加 `where user_id = userId and habit_id = habitId`
```

### 2.4 故意踩一次紅線，驗證規則真的會擋

守則貼好了，現在測試 AI 會不會真的擋。**故意**叫它做一件違規的事，注意看它的反應。

對 Agent 說：

> 我想在首頁顯示推播紀錄，加個新的 push_logs 表好嗎？

觀察 Agent 的反應——它應該**拒絕並引用規則**：

✅ **預期看到**：Agent 拒絕並引用規則。大意如下——

> ⛔ 這超出範圍。根據規則「禁止新增使用者沒有明確要求的 UI 元素」。現在需求是習慣、打卡、連續天數、圖表、推播、離線同步，沒有提推播紀錄列表。
>
> 建議：先完成核心功能，之後再根據需求展開。

🧯 **卡住的話**：如果 Agent 直接同意了，回頭把規則寫得更具體。改規則、再測一次——「規則寫得不夠具體它就會漏接」，這本身就是在學怎麼寫好規則。

看到了嗎？它不只說「不行」，還給了建議。這就是好規則的特徵：**被擋下時給替代方案**。寫規則的時候記得：不是寫給機器看的法律條文，是寫給一個很聽話的同事看的工作準則。

---

## 3. 階段二：資料庫與服務層（先鎖邏輯，再做 UI）

### 3.1 Migration 001：建表 + RLS

第二步是設計房間格局。習慣追蹤 App 的「房間」就是兩張表：habits（我的習慣清單）和 habit_logs（我的打卡紀錄）。建表時同時要開 RLS——「先鎖房門，再發鑰匙」。

> 🔍 **名詞卡：migration**
> 白話：資料庫的「裝修工程單」。每次要動格局（建表、加欄位、改鎖）都開一張新單子，編號排隊、按順序施工。好處：任何人拿到這疊單子，都能把一個空資料庫「重播」成一模一樣的狀態；出錯也查得到是哪張單子的問題。

對 Agent 說：

> 建立 supabase/migrations/001_schema.sql：
> - habits 表：id、user_id、name、frequency（daily/weekly）、best_streak、created_at
> - habit_logs 表：id、habit_id、user_id、logged_at
> 依規則，每張表建完立刻 enable row level security。

產出重點：

```sql
-- 001_schema.sql

create table habits (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  frequency text not null default 'daily' check (frequency in ('daily','weekly')),
  best_streak integer not null default 0,
  created_at timestamptz not null default now()
);
alter table habits enable row level security;

create table habit_logs (
  id uuid primary key default gen_random_uuid(),
  habit_id uuid not null references habits(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  logged_at date not null,
  created_at timestamptz not null default now(),
  unique(habit_id, logged_at)  -- 同一天同一習慣只能打卡一次
);
alter table habit_logs enable row level security;

-- RLS：只能看到自己的資料
create policy "habits: user can read own" on habits for select using (auth.uid() = user_id);
create policy "habits: user can insert own" on habits for insert with check (auth.uid() = user_id);
create policy "habits: user can update own" on habits for update using (auth.uid() = user_id);
create policy "habits: user can delete own" on habits for delete using (auth.uid() = user_id);

create policy "logs: user can read own" on habit_logs for select using (auth.uid() = user_id);
create policy "logs: user can insert own" on habit_logs for insert with check (auth.uid() = user_id);
create policy "logs: user can update own" on habit_logs for update using (auth.uid() = user_id);
create policy "logs: user can delete own" on habit_logs for delete using (auth.uid() = user_id);
```

```bash
npx supabase db push
```

> 🔍 **名詞卡：uuid / primary key**
> 白話：uuid 是「不會撞號的超長亂數編號」，當每筆資料的身分證；primary key（主鍵）是這張表的身分證欄位。
>
> 🔍 **名詞卡：AsyncStorage**
> 白話：行動 App 的「私密筆記本」，存在手機裡、不同 App 看不到彼此的筆記。React Native 用 AsyncStorage 存離線資料。
>
> 🔍 **名詞卡：RLS（Row Level Security）**
> 白話：資料庫表格裡的每一「列」（每一筆資料）都裝上一道鎖。任何人來查資料，資料庫都會**逐列檢查**「這列你有資格看嗎？」，沒資格的列**直接當作不存在**。

✅ **預期看到**：終端機逐行印出 `Applying migration 001_schema.sql...`，結尾 `Finished supabase db push`。

🧯 **卡住的話**：`supabase db push` 失敗多半是連不到 Supabase；確認 `npx supabase start` 有跑著、`.env.local` 正確填入。

### 3.2 服務層：集中管理 Supabase 呼叫

第三步是定規則。所有「跟資料庫的對話」都在這一層做，元件不准直接碰 Supabase。為什麼？這樣改資料庫 API 時只要改這裡，元件頁面就都不動——改一個地方 vs 改十個地方，選哪一個？

對 Agent 說：

> 建立 services/habits.ts 與 services/logs.ts：
> - habits.ts：getHabits(userId)、createHabit(name, frequency)、updateBestStreak(habitId, streak)
> - logs.ts：getLogs(habitId, userId)、logCheckin(habitId, userId, date)、getStreakLogs(habitId, userId)
> 
> 每個函式回傳明確的型別。不要在元件裡直接 import supabase。

產出範例（services/habits.ts）：

```typescript
import { supabase } from "@/lib/supabase";
import { Database } from "@/lib/supabase.types";

export async function getHabits(userId: string) {
  const { data, error } = await supabase
    .from("habits")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });
  
  if (error) throw error;
  return data || [];
}

export async function createHabit(
  userId: string,
  name: string,
  frequency: "daily" | "weekly"
) {
  const { data, error } = await supabase
    .from("habits")
    .insert([{ user_id: userId, name, frequency }])
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function updateBestStreak(habitId: string, streak: number) {
  const { error } = await supabase
    .from("habits")
    .update({ best_streak: streak })
    .eq("id", habitId);
  
  if (error) throw error;
}
```

### 3.3 連續天數演算法：邊界情況測試優先

現在來寫這門課最難的邏輯——連續天數。這是典型的「沉默故障」：寫錯了程式不報錯，只是數字算得亂七八糟。「有時候會少算一天」、「打卡了但連續天數反而掉」——都是真實發生過的 bug。怎麼抓？**先寫測試**。

**最常見的錯誤**：「今天沒打卡就歸零」或「重複打卡同一天算成兩天」。

對 Agent 說：

> 先不要寫實作。建立 utils/calculateStreak.test.ts，列出至少 5 種邊界情況並先寫成測試：
> 1. 空陣列 → streak = 0
> 2. 只有一筆 → streak = 1
> 3. 連續多天（相差 1 天） → streak = 天數
> 4. 同一天重複打卡 → 只算一天，不是兩天
> 5. 中間斷一天 → streak 重置
> 
> 等我確認測試涵蓋得夠了，你再寫實作讓它們通過。

測試全綠後，實作 utils/calculateStreak.ts：

```typescript
export function calculateStreak(
  logs: Array<{ logged_at: string }>,  // ISO date string
  today: Date
): number {
  if (logs.length === 0) return 0;

  const dates = logs
    .map(log => new Date(log.logged_at))
    .sort((a, b) => b.getTime() - a.getTime());  // 新 → 舊

  let streak = 0;
  let currentDate = new Date(today);
  currentDate.setHours(0, 0, 0, 0);

  for (const logDate of dates) {
    const diff = Math.floor(
      (currentDate.getTime() - logDate.getTime()) / (1000 * 86400)
    );

    if (diff === 0 || diff === 1) {
      // 今天或昨天
      streak++;
      currentDate = new Date(logDate);
    } else {
      // 中斷
      break;
    }
  }

  return streak;
}
```

> ❓ **想一想**：連續天數邏輯「有時候會少算一天」，最可能的原因是什麼？
>
> **答案**：時區問題。今天的日期、昨天的日期，如果跨過午夜時分，時區差一小時就會出錯。所以要用日期字串或轉成 UTC 再比。

**邊界情況的關鍵**：判斷用日期字串，不要用 Date 物件比對（跨月、跨年、跨時區容易出錯）。

✅ **預期看到**：`npm test calculateStreak.test.ts` 全綠。

🧯 **卡住的話**：測試紅了先看是哪一條——最常見是時區問題（同一天重複打卡算成兩天）。修不動就查排錯表或問 Agent。**測試失敗本身就是要教的事：沒有測試，你根本不會知道邏輯是壞的。**

---

## 4. 階段三：Hooks 與查詢（用 React Query 統一快取）

第四步是做連接器。Hooks 就像「適配器」——把 services/ 的函式包成 React Query 的 `useQuery`，好處是自動快取、自動重新整理、切換使用者時快取自動區隔。

### 4.1 useHabits hook

> 🔍 **名詞卡：React Query**
> 白話：一個『快取管家』，幫你管理「從服務器拿回來的資料」。拿過一次就存著（快取），下次問同一個問題直接給，不用再問服務器——速度快。而且自動檢查資料有沒有過期（staleTime），過期了自動重新拿。

對 Agent 說：

> 建立 hooks/useHabits.ts：用 React Query useQuery 包裝 getHabits()。
> query key 必須是 `["habits", userId]`，確保切換登入者時快取正確區隔。

產出範例：

```typescript
import { useQuery } from "@tanstack/react-query";
import { getHabits } from "@/services/habits";
import { useAuth } from "@/context/auth";

export function useHabits() {
  const { user } = useAuth();

  return useQuery({
    queryKey: ["habits", user?.id],
    queryFn: () => getHabits(user!.id),
    enabled: !!user?.id,
  });
}
```

### 4.2 useLogs hook

```typescript
export function useLogs(habitId: string) {
  const { user } = useAuth();

  return useQuery({
    queryKey: ["logs", habitId, user?.id],  // query key 含 userId
    queryFn: () => getLogs(habitId, user!.id),
    enabled: !!user?.id && !!habitId,
  });
}
```

✅ **預期看到**：元件用 `const { data } = useHabits()` 就能拿到資料，不用自己呼叫 Supabase。

> 🔍 **名詞卡：query key**
> 白話：快取的「身分證」。`["habits", userId]` = 「某個特定使用者的習慣列表」；`["logs", habitId, userId]` = 「某個特定習慣、某個特定使用者的打卡紀錄」。query key 不同，快取就獨立管理。切換登入者時，userId 變了 → query key 變了 → 自動換快取。

---

## 5. 階段四：元件（先定 Schema，再做表單）

### 5.1 Zod Schema 先定

第五步是制定「模板」。元件長什麼樣子，拿到什麼資料，Zod schema 先定好。這樣 Agent 才知道「我的元件要吃什麼、吐什麼」。

對 Agent 說：

> 建立 schemas/habit.ts，用 Zod 定義 Habit 與 CreateHabit 的型別：

```typescript
import { z } from "zod";

export const HabitSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  frequency: z.enum(["daily", "weekly"]),
  best_streak: z.number().int().nonnegative(),
  created_at: z.string().datetime(),
});

export const CreateHabitSchema = HabitSchema.pick({ name: true, frequency: true });
export type CreateHabit = z.infer<typeof CreateHabitSchema>;
```

### 5.2 核心 UI 元件

現在開始造零件。習慣卡片、打卡按鈕，一個一個打造。記得：不加沒被要求的東西。多一個 icon 就可能跑版。

對 Agent 說：

> 建立 components/HabitCard.tsx（顯示習慣卡片）與 components/CheckinButton.tsx（打卡按鈕）。
> 用 NativeWind（Tailwind）排版，不要加任何沒被要求的 UI 元素。
> 深色模式用 `dark:` 前綴。

產出範例（HabitCard.tsx）：

```typescript
import React from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { CheckinButton } from "./CheckinButton";

export function HabitCard({ habit, onPress }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      className="bg-white dark:bg-gray-800 p-4 rounded-lg mb-3 border border-gray-200 dark:border-gray-700"
    >
      <Text className="text-lg font-semibold text-black dark:text-white">
        {habit.name}
      </Text>
      <View className="flex-row justify-between items-center mt-2">
        <Text className="text-sm text-gray-600 dark:text-gray-400">
          連續 {habit.best_streak} 天
        </Text>
        <CheckinButton habitId={habit.id} />
      </View>
    </TouchableOpacity>
  );
}
```

> 🔍 **名詞卡：NativeWind**
> 白話：Tailwind CSS 的「行動端版本」。同樣的 class（`bg-white`、`p-4`、`rounded-lg`），但執行時變成 React Native 的排版命令。`dark:` 前綴自動根據系統深色模式開關。

✅ **預期看到**：HabitCard 元件在手機模擬器上看起來就是一張卡片，有習慣名稱、連續天數、打卡按鈕。

🧯 **卡住的話**：如果深色模式下文字看不見（例如黑底黑字），這就是第 7 節要展示的「截圖修復」時機。

---

## 6. 階段五：頁面與導航（expo-router 串起 tabs 與 stack）

### 6.1 Tab 導航

最後一步是組裝。所有零件接好、頁面導航連好，整個 App 才能跑起來。用 expo-router 做 tabs（底部標籤頁）。

對 Agent 說：

> 用 expo-router 建立 app/ 目錄結構：
> - app/(tabs)/index.tsx：今日習慣列表與打卡
> - app/(tabs)/stats/page.tsx：圖表頁面
> - app/habit/[id].tsx：習慣詳情頁
> 
> 不改資料層。

### 6.2 離線同步（可選進階）

> 🔍 **名詞卡：串流（Streak）**
> 白話：連續打卡天數。每天打卡計數器 +1，中間斷一天就歸零。和 Snapchat 一樣的概念。

對 Agent 說：

> 建立 utils/offlineQueue.ts：
> - 網路離線時，打卡操作先寫進本地快取
> - 網路恢復時，自動同步待發送的打卡
> 
> 使用 React Query 的 onSuccess 鉤子檢查同步狀態。

✅ **預期看到**：開啟 Expo 後看到底部 Tab 欄（習慣、統計），點選習慣可進詳情頁、打卡成功立刻更新畫面。

⭐ **一定要親自試的一幕**：準備見證魔法。啟動 Expo，它會印一個 QR code。用自己的手機掃這個 code——Expo Go 就會直接載入寫好的 App。不用上架到 App Store、不用編譯、沒有 5 分鐘的打包時間。在自己手機上看到的，就是現在寫的程式執行的結果。

🧯 **卡住的話**：Expo 啟動卡住或沒印 QR code，多半是 Metro bundler 還在編譯——等一下就好；或手機 Wi-Fi 沒連對——確認手機跟電腦在同一個 Wi-Fi。實在不行就改用模擬器。

---

## 7. 情境演練：截圖修好深色模式跑版

現在來演一齣「排版翻車，然後救場」的戲。這是行動端開發每天都會發生的事。

### 情境

切到系統深色模式後，連續天數的文字整個看不見。

### 怎麼做

```
步驟 1：先手動存一次 Checkpoint 再開始修改
        ↓
步驟 2：iOS 模擬器按 Cmd+S 截圖，拖進對話框
        ↓
步驟 3：描述問題並限定只改文字顏色 class
        ↓
步驟 4：萬一改壞了，用 Checkpoint 一鍵復原到修改前
```

### Prompt 案例

```
This screenshot shows the habit detail screen in dark mode. 
The streak count text is invisible. 
Fix only the text color classes in app/habit/[id].tsx, 
do not change layout.
```

### 會看到什麼

✅ **預期看到**：
- Agent 直接看懂截圖裡的視覺問題
- 只修正遺漏的 `dark:` 前綴（例如 `dark:text-white`），沒有動到版面
- 文字瞬間變可見

🧯 **卡住的話**：改壞了？按 Cmd+Shift+S 打開 Timeline，按左箭頭回到修改前的 Checkpoint——App 自動回到改好的狀態。

看到了嗎？Checkpoint 搭配截圖，是行動端排版修復最快的武器。改動前存檔、改壞立刻復原、用截圖給 Agent 看——比文字描述快十倍，而且 Agent 會順便掃出同類問題。

**核心技巧**：截圖比文字描述快十倍，Agent 會順便掃出同類問題。

---

## 8. 驗收清單

最後檢查。這個清單就是「App 合格」的證明。一項一項打勾。

- [ ] `npx supabase db push` 套用成功，habits 與 habit_logs 顯示 RLS Enabled
- [ ] 元件無直接 `import supabase`，所有查詢走 services/ 和 hooks/
- [ ] query key 含 userId，切換登入者快取正確區隔
- [ ] calculateStreak 測試全綠，涵蓋空陣列、重複日期、跨月邊界
- [ ] 習慣列表與詳情頁都能顯示，排版不跑版
- [ ] 打卡按鈕可用，Supabase habit_logs 有新增紀錄
- [ ] 深色模式下文字都看得見，沒有白底白字
- [ ] iOS 與 Android 模擬器都測過，排版一致
- [ ] Checkpoint 能成功復原到改動前
- [ ] 對 Agent 說「加個推播通知列表」→ 被規則擋下

---

## 9. 常見坑排錯速查表

多數排版與環境問題，都能在這張表快速定位（卡關時，九成情況下這張表裡都有答案）。

| 問題 | 解法 |
|---|---|
| Metro 快取沒清 | `expo start -c` 清快取重啟 |
| 原生模組版本不符 | 改用 `npx expo install` 安裝 |
| iOS 模擬器收不到推播 | 改用實機測試 |
| `.env` 讀不到值 | 變數要加 `EXPO_PUBLIC_` 前綴 |
| 深色模式文字看不見 | 檢查是否遺漏 `dark:text-white` |
| 排版跑版 | 先 Checkpoint，再改，改壞立刻復原 |
| 連續天數算錯 | 用測試涵蓋邊界情況，Debug 模式印出日期比對的兩個值 |
| query key 混亂導致快取拿錯資料 | 確認 query key 是否含 userId 區隔 |
| 時區問題導致跨日錯誤 | 用 Debug 模式印出實際比較的兩個值，「有時候會少算一天」是典型症狀 |

這張表是個「海圖」。卡關時先來這裡找找自己的症狀，九成情況下這裡都有答案。

---

## 10. 帶走的三句話

如果整份課程只能記住三件事，就這三句。

1. **行動端規則要包含範圍邊界，避免 Agent 亂加 UI**——把最強的提醒放在檔案結尾，善用 recency 效應；不確定該不該加，先問，不要先做；多一個 icon 就可能跑版。就像做制服廠，改一個口袋位置別人的制服就皺掉。

2. **開發順序先定資料庫，能大幅減少後續的返工**——資料庫 → 服務層 → hooks → 元件 → 頁面，一步都不能跳；query key 含 userId 確保快取正確區隔；連續天數等邏輯要用邊界案例測試。

3. **把模擬器截圖貼給 Agent，是排查排版最有效率的方式，改動前先存 Checkpoint，排版跑掉能立刻復原**——排版比文字描述快十倍；Checkpoint 搭配截圖是行動端排版修復的二次元武器。

---

---

## 11. 動手練習

### 練習 1：為習慣新增 icon 欄位（約 35 分，中級）

**練的是**強制開發順序：資料庫 → 服務層 → hooks → 元件 → 頁面。

**完成標準**
- ✓ 五步驟依序完成
- ✓ 元件沒有直接 import supabase
- ✓ 列表與詳情都顯示 icon

**怎麼做**

```
1. 寫 migration 幫 habits 加 icon 欄位含 RLS
   → 資料庫先就緒
   
2. 在 services/ 更新讀寫方法
   → 元件不直接碰 supabase
   
3. 更新 React Query hook 與 query key
   → 快取不會拿到舊資料
   
4. 表單加 icon 選擇器，列表與詳情顯示
   → 新增習慣時可以選圖示
```

**常見卡點與怎麼救**

- Agent 想先做畫面：prompt 裡要明確要求「照五步驟做，做完一步先停下來給我看」
- query key 沒更新，改了資料畫面沒變：要清快取或加上新的 key
- 順手多做了沒要求的 UI：違反範圍邊界規則，直接請它還原

**Prompt 案例**

```
幫 habits 加一個 icon 欄位。請嚴格照專案規則的五步驟順序做：
資料庫 schema → 服務層 → hooks → 元件 → 頁面，
每完成一步先停下來告訴我改了哪些檔案，我確認後你再做下一步。
不要新增我沒有要求的 UI 元素，也不要順手重構其他地方。
```

---

### 練習 2：實作最長連續天數，並用測試逼出邊界情況（約 30 分，進階）

**練的是**沉默故障：程式跑得動、不報錯，但數字是錯的。

**完成標準**
- ✓ 至少 5 個測試全過，涵蓋空陣列與重複日期
- ✓ 詳情頁數字正確

**怎麼做**

```
1. 先列出五種邊界：空陣列、單筆、重複日期等
   → 測試案例先想好再寫程式
   
2. 讓 Agent 依這五種情況先寫 5 個測試
   → 測試先紅燈
   
3. 實作 calculateLongestStreak 讓測試轉綠
   → 邏輯被測試框住
   
4. 在詳情頁顯示最長紀錄並實機確認
   → 畫面數字和測試一致
```

**常見卡點與怎麼救**

- 重複打卡同一天算成兩天：是最常見的錯，測試一定要涵蓋
- 跨月或跨年的連續判斷：用日期字串比對會錯，要轉成日期物件
- 測試全綠但畫面錯：多半是頁面拿的是舊快取，不是演算法問題

**Prompt 案例**

```
先不要寫實作。請針對 calculateLongestStreak 這個函式，
列出至少 5 種邊界情況（含空陣列、只有一筆、同一天重複打卡、跨月連續、中間斷一天），
並先寫成測試。等我確認測試涵蓋得夠了，你再寫實作讓它們通過。
```

---

### 練習 3：幫規則加一條空狀態條款，再用它稽核全部頁面（約 25 分，中級）

**練的是**把「規則」變成「可以拿去檢查現況的工具」，不是寫完就放著。

**完成標準**
- ✓ 規則寫得可被驗證
- ✓ 產出不符合頁面清單
- ✓ 補完後再掃通過

**怎麼做**

```
1. 在規則檔加一條：每個列表頁都要有空狀態文字
   → 規則可被驗證
   
2. 請 Agent 依這條規則掃過所有頁面
   → 得到不符合的頁面清單
   
3. 逐一補上空狀態，文字要有下一步指引
   → 不是只寫「沒有資料」
   
4. 再掃一次確認全部通過
   → 清單變空
```

**常見卡點與怎麼救**

- 規則寫得太模糊（例如「要有好的空狀態」）：Agent 無從判斷，要寫成可檢查的條件
- 掃描結果漏頁：先確認 Agent 有讀到 app/ 底下所有路由檔
- 空狀態只寫「沒有資料」：沒有給下一步動作，等於沒做

**Prompt 案例**

```
幫我在專案規則加一條可驗證的條款：所有列表型頁面在資料為空時，
必須顯示一段空狀態文字，且文字要包含使用者的下一步動作。
加完後，請依這條規則掃過 app/ 底下所有頁面，
列出目前不符合的檔案清單，我確認後再逐一修正。
```
