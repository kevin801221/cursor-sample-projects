# UI 元件庫：Figma / 截圖轉 React 元件

> Cursor 課程 Project 3（第 24 章）：設計轉程式碼。
> 一句話：**設計轉程式碼最容易生出一堆一次性樣式，難以維護**——先給設計系統規則，元件才不會各自估一套顏色與間距。

## 專案規格

| | |
|---|---|
| **最終成果** | Button、Input、Card、Modal 四個核心元件，各含多種變體與尺寸，含 Storybook 文件與無障礙檢查 |
| **技術棧** | Vite、React 18、Tailwind、Storybook 8、Figma MCP |
| **預估時間** | 4–5 小時，其中 design tokens 與規則約 1.5 小時、元件實作約 3 小時 |
| **前置需求** | Figma 帳號（或改用截圖）、Cursor Pro、MCP 基本設定 |

## 這個專案做什麼

- 從 Figma 設計稿或截圖出發，產出可維護的 React 元件庫
- 定義設計系統規則（design tokens、色票、間距），杜絕一次性樣式
- 四個元件（Button / Input / Card / Modal）各含多種變體與狀態
- 用 Storybook 自動產生文件、驗證所有變體
- 無障礙檢查：自動掃描對比度 + 手工鍵盤操作測試

## 三種設計轉程式碼路徑

截圖轉元件有三種方式，各有取捨，最後都歸結為同一套規則：

| 路徑 | 優點 | 缺點 |
|------|------|------|
| Figma MCP | 結構資訊精確、間距色碼都讀得到 | 需要 Figma 設計稿用 Auto Layout |
| 截圖貼給 Agent | 不需存取權限、快速出稿 | 顏色間距是估出來的 |
| Figma 外掛匯出 | 樣式數值精確 | 常需重構成專案慣例 |

**核心概念**：選哪條路都一樣，要先統一色票與間距規則，元件才不會各自估數值。

## 設計系統規則：防止一次性 class 的坑

```
問題 ✗                          → 解決方案 ✓
每個元件寫死 #3B82F6 之類色碼   →  色票定義在 tailwind.config.js
間距各自估 p-[13px] 任意值      →  間距沿用 Tailwind 預設刻度
改一個顏色要全專案逐一找       →  改一個 token 全站顏色一次更新
```

這些規則寫成 `.cursor/rules/design-system.mdc`（含 globs），Agent 就會在產元件時自動擋下色碼，改用 `bg-primary`、`text-foreground` 之類的語意化 token。

## 開發階段

| 階段 | 做什麼 | 預估時間 | 驗收 |
|------|--------|---------|------|
| 1. 規則與 tokens | 定義 design tokens（色票、間距、圓角）、寫成 `tailwind.config.js` 與 rules | 30 分 | `npm run build` 無色碼警告 |
| 2. 第一個元件 | 產 Button（主、次、幽靈變體 × 小中大尺寸）、寫 Storybook stories、加無障礙屬性 | 1 小時 | 3 × 3 變體矩陣都在 Storybook |
| 3. 其他元件 | 產 Input、Card、Modal，複用同一套 tokens 與樣式模式 | 1.5 小時 | 四元件都無色碼、視覺一致 |
| 4. 無障礙檢查 | 加 @storybook/addon-a11y 自動掃描、手工鍵盤測 Modal 焦點陷阱 | 30 分 | 對比度過 WCAG AA、鍵盤操作完整 |

## 專案結構

```
component-library/
├── .cursor/rules/
│   ├── design-system.mdc       # 色票、間距、禁用十六進位色碼規則（globs 作用在 src/components）
│   └── a11y.mdc                # 無障礙檢查規則
├── src/
│   ├── components/
│   │   ├── Button.tsx          # 變體: primary/secondary/ghost, 尺寸: sm/md/lg
│   │   ├── Input.tsx           # 預設/error/disabled 狀態
│   │   ├── Card.tsx            # 容器元件，內部間距用 token
│   │   ├── Modal.tsx           # 含焦點陷阱、Escape 關閉
│   │   └── index.ts            # 統一匯出
│   ├── config/
│   │   └── tokens.ts           # tokens 型別定義（可選，幫 TypeScript 檢查）
│   └── index.tsx               # 根入口
├── src/stories/
│   ├── Button.stories.tsx
│   ├── Input.stories.tsx
│   ├── Card.stories.tsx
│   └── Modal.stories.tsx
├── tailwind.config.js          # 擴展 Tailwind，定義所有 tokens
├── .storybook/
│   ├── main.ts
│   └── preview.tsx             # 引入 @storybook/addon-a11y
├── vite.config.ts              # Vite 設定
├── package.json
└── walkthrough.md              # 完整逐步教學
```

## 四條鐵律（本課核心）

1. **禁止寫死色碼，一律用語意化 token**——色票規則防止每個元件各自估一組顏色，十六進位色碼只能出現在 `tailwind.config.js` 一處。
2. **開發新元件前先搜尋 `src/components/`**——複用規則防止 Modal 重寫一份按鈕樣式，樣式一致性必須靠去重，不靠人工維護。
3. **無障礙檢查要自動掃描加手工測**——自動化掃描只能抓對比度，鍵盤操作（Tab、Shift+Tab、Enter、Escape）仍要人工驗。
4. **design tokens 要先集中管理，元件才不會各自估數值**——Auto Layout 是 Figma MCP 能否精確還原版面的關鍵；一次性 class 的代價要到第三個元件才顯現（七種藍色、五種間距）。

## 快速開始

```bash
npm install
npm run dev                    # Vite 開發伺服器
npx storybook dev             # Storybook 看所有元件
npx storybook build           # 產出靜態文件
npx storybook add @storybook/addon-a11y  # 加無障礙掃描插件
```

完整建置步驟、design tokens 概念、三種設計轉程式碼路徑的選擇指南，見 **[walkthrough.md](./walkthrough.md)**。
