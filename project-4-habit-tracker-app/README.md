# 習慣追蹤 App — 行動端 UI 一改就跑版，要用規則和 Checkpoint 雙重把關

> Cursor 課程 Project 4（第 25 章）：React Native + Expo。
> 一句話：**行動端排版特別敏感，多一個 icon 就可能跑版——要用規則明文約束 Agent 邊界，改動前先存 Checkpoint，排版跑掉立刻復原。**

## 專案規格

| | |
|---|---|
| **最終成果** | 新增習慣、打卡、連續天數、圖表、推播提醒、關閉網路仍可打卡、恢復連線後自動同步 |
| **技術棧** | Expo SDK 52、NativeWind 4、React Query 5、Supabase |
| **預估時間** | 8–12 小時，建議分 2–3 天進行較不容易疲勞 |
| **前置需求** | iOS/Android 實機或模擬器、Supabase 帳號 |

## 這個 App 做什麼

- 使用者用 Email 註冊登入（Supabase Auth）
- 建立習慣（名稱、頻率、推播時間）
- 每日打卡：點擊按鈕記錄、連續天數自動計算
- 連續天數展示：不中斷才算、缺一整天才真正重置
- 圖表視覺化：近 30 天打卡率、連續天數歷史
- **關鍵需求**：關閉手機網路仍可打卡，恢復連線後自動同步；深色模式不跑版

## 強制開發順序五步（順序顛倒最容易讓 Agent 先做出接不上資料的畫面）

```
1. 資料庫 schema       → 設計 habits、habit_logs 兩張表（含 RLS 政策）
                        ↓
2. 服務層              → Supabase 呼叫集中在 services/（元件不得直接 import supabase）
                        ↓
3. hooks               → 包裝成 React Query useQuery（query key 含 userId 區隔快取）
                        ↓
4. 元件                → 先定 Zod schema 再做表單（不加沒被要求的 UI 元素）
                        ↓
5. 頁面                → expo-router 串起 tabs 與 stack（App 可操作，不改資料層）
```

## 五階段開發流程

| 階段 | 做什麼 | 驗收 |
|---|---|---|
| 1. 骨架與規範 | 建 Expo 專案、寫 `.cursor/rules` | Agent 自動遵守五步驟與範圍邊界 |
| 2. 資料庫與服務 | 建 habits、habit_logs 表（含 RLS）與 Supabase 服務層 | 表顯示 RLS Enabled，元件無直接 supabase import |
| 3. hooks 與查詢 | React Query useQuery 包裝 Supabase 呼叫 | 快取不混亂，切換使用者快取正確區隔 |
| 4. 核心 UI 元件 | 習慣列表、詳情頁、打卡按鈕、圖表 | 原型能操作、沒有跑版問題 |
| 5. 離線同步與推播 | 本地快取、背景同步、推播提醒 | 關閉網路能打卡，恢復連線自動同步 |

## 專案結構

```
habit-tracker/
├── .cursor/rules/
│   ├── 00-scope.mdc           # 範圍邊界（禁止亂加 UI），alwaysApply
│   ├── expo.mdc               # Expo 架構慣例（globs 按需載入）
│   └── supabase.mdc           # Supabase 慣例（globs 按需載入）
├── supabase/migrations/
│   ├── 001_schema.sql         # habits、habit_logs 表 + RLS
│   └── 002_offline_queue.sql  # 離線快取表
├── app/
│   ├── (tabs)/
│   │   ├── index.tsx          # 今日習慣與打卡列表
│   │   └── stats/             # 圖表頁
│   ├── habit/[id].tsx         # 習慣詳情頁
│   └── _layout.tsx            # Tabs 與 Stack 導航
├── services/
│   ├── habits.ts              # 習慣 CRUD
│   └── logs.ts                # 打卡記錄 CRUD
├── hooks/
│   ├── useHabits.ts           # habits 列表與快取
│   └── useLogs.ts             # logs 列表與快取
├── components/
│   ├── HabitCard.tsx          # 習慣卡片
│   └── CheckinButton.tsx      # 打卡按鈕
├── utils/
│   ├── calculateStreak.ts     # 連續天數演算法
│   └── offline.ts             # 離線隊列管理
└── walkthrough.md             # 完整逐步教學
```

## 六條鐵律（本課核心）

### 範圍邊界（重要，違反視為錯誤）

1. **禁止新增使用者沒有明確要求的 UI 元素** —— 行動端 UI 對排版特別敏感，多一個 icon 就可能跑版
2. **禁止修改與當前任務無關的檔案或區域** —— 不確定該不該改，先問，不要先做
3. **禁止「順手重構」未被要求整理的程式碼** —— 排版出問題時最難排除的變因就是多餘改動

### 操作規則（重要，必須執行）

4. **改動前先手動存一次 Checkpoint** —— Cursor 的 Checkpoint 功能可一鍵復原，排版跑掉立刻按回上一版
5. **排版問題把截圖貼給 Agent** —— 比文字描述快十倍，Agent 會順便掃出同類問題
6. **新增或修改功能要依強制開發順序** —— 資料庫 → 服務層 → hooks → 元件 → 頁面，一步都不能跳

*關鍵提醒放在檔案結尾，善用 recency 效應加強效果。不確定該不該加，先問，不要先做。*

## 快速開始

```bash
npm install
npx supabase start          # 本地 Supabase（需 Docker）
npx supabase db push        # 套用 migrations
npm start                   # Expo 開發服務器
```

開啟 iOS 模擬器或 Android 模擬器，掃 QR code 進入 App。

完整建置步驟、離線同步實作、連續天數邏輯、Checkpoint 排版修復流程，見 **[walkthrough.md](./walkthrough.md)**。

---

**本專案最常見的問題**：排版跑版時，務必先 Checkpoint，再改，改壞了立刻復原。截圖是排查排版最有效率的方式，把模擬器的截圖拖進對話框，Agent 直接看懂視覺問題。
