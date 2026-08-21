# Walkthrough：在 Cursor 上把 UI 元件庫一步一步做出來

> 這份文件帶你從零做出 **四個核心 UI 元件**（Button、Input、Card、Modal），並親手體驗一件事：**設計轉程式碼最容易生出一堆一次性樣式，難以維護**——但只要先定義設計系統規則，就能讓 AI 自動擋下違規、讓所有元件視覺統一。你會學到三件事：怎麼集中管理 design tokens、怎麼寫規則讓 Agent 替你把關、怎麼用 Storybook + 無障礙掃描驗證元件品質。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 簡易比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先做這五件事，動手時才不會卡）

1. **準備一張設計稿截圖或取得 Figma 帳號**——如果用截圖路徑（推薦），提前把四個元件（Button、Input、Card、Modal）的設計稿截圖存好；如果用 Figma MCP，確認帳號可以存取設計檔。
2. **本地跑一次 `npm create vite` + `npm install` + `npm run dev`**——第一次下載依賴通常慢，先跑過一次，之後啟動只要幾秒鐘。
3. **跑一次 `npx storybook dev`**——Storybook 啟動要等個 1–2 分鐘，預先開好確認能用。
4. **把 tailwind.config.js 準備好**——實作時會邊參考邊改，先確認編輯器好用。
5. **動手過程中，每跑完一個指令就對照文中的「✅ 預期看到」**——判斷得出「這是正常的」還是「翻車了」，除錯速度差十倍。

## 🗺️ 學習地圖（建議 4–5 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 第 1 節概念 | 45 分 | 閱讀理解（靈魂所在，先理解再動手） |
| 第 2 節設定 Figma MCP 或截圖路徑選擇 | 15 分 | 閱讀理解 + 選擇（決定路徑） |
| 第 3 節 Design Tokens 與規則 | 45 分 | 動手做（建專案、寫 tailwind.config.js、建規則） |
| 規則驗收（故意踩紅線）⭐ | 20 分 | 動手做（一定要親自試的一幕） |
| 第 4 節第一個元件 Button | 50 分 | 動手做（截圖貼進去、要求用 token、Storybook） |
| 第 5 節其他三個元件 + Storybook | 90 分 | 動手做 |
| 第 6 節無障礙檢查 | 30 分 | 動手做（a11y addon + 手工測 Modal 鍵盤） |
| 帶走三句話 + 驗收 | 15 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `./component-library/`，遙控器是 `./demo.sh`（位於 `project-3-react-component-library/` 根目錄）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 全程離線、不需要 Figma 付費帳號、不耗網路。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd project-3-react-component-library/component-library && npm install` | 第一次安裝依賴（約 10–20 秒）。課前裝好，課堂上全離線秒開 |
| 2 | 跑一次 `./demo.sh 2` | 執行 `check.mjs` 確認 tokens 與 A11y 檢查全數通過 |
| 3 | 跑一次 `./demo.sh 5`（構建驗證） | 確認 `npm run build` 成功輸出 dist/ 目錄 |
| 4 | 確認 5173 埠沒有殘留行程 | 第 4 幕展示台會使用 Vite 預設埠 |

### 放映時間軸

時間軸切成 6 段，對應上方學習地圖（合計 240 分鐘），全長 **4 小時**。

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:45 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §1 | 學校色票對照表、一次性樣式反模式、Design Tokens 定義 | 規範先行、集中管理 |
| 0:45–1:00 | 第 1 幕：Design Tokens 結構 | `./demo.sh 1` | `component-library/src/tokens/tokens.ts` | 色彩、間距（xs/sm/md/lg/xl）、圓角（sm/md/lg/full）集中定義 | 所有樣式只能從色票挑，禁止任意數值 |
| 1:00–1:30 | 第 2 幕：規則稽核與踩紅線 ⭐ | `./demo.sh 2` | `component-library/.cursor/rules/design-system.mdc` | `check.mjs` 掃描所有元件，輸出「0 處寫死十六進位色碼、A11y 標籤全過」 | 規則防線：讓 AI 在生成程式碼時主動阻擋一次性樣式 |
| 1:30–2:30 | 第 3 幕：四大核心元件與 A11y | `./demo.sh 3` | `component-library/src/components/Input.tsx` | Input 的 `aria-invalid`、`aria-describedby` 與 Modal 的 `Escape` 鍵監聽 | 無障礙不是最後才加的功能，必須做進元件基礎層 |
| 2:30–3:45 | 第 4 幕：啟動互動展示台 ⭐ | `./demo.sh 4` | `component-library/src/components/Showcase.tsx` | 瀏覽器開啟現代元件庫展示台，即時切換 Dark/Light 主題與 Props | 眼見為憑：Button / Input / Card / Modal 完整互動與 Props 即時變更 |
| 3:45–4:00 | 第 5 幕：打包構建驗證 | `./demo.sh 5` | `component-library/vite.config.ts` | `tsc -b && vite build` 產出乾淨 dist/ | 發佈前的生產環境打包驗證 |

### ⭐ 全場最值得停下來的一幕

**第 2 幕與第 4 幕的 Props 控制台。**
在第 2 幕現場故意在 `Button.tsx` 加入一行寫死的 `color: '#ff0000'`，重跑 `./demo.sh 2` 立刻紅字報錯退件！讓學生親身體會「由規則把關比由工程師肉眼 Code Review 效率高出十倍」。在第 4 幕展示台切換 Dark Mode 與 Props 控制台，所有元件瞬間無縫響應色票切換。

### 🧯 現場翻車備案

| 翻什麼 | 徵狀 | 30 秒內的救援 |
|---|---|---|
| 靜態檢查報錯 | 發現寫死十六進位色碼 | 檢查程式碼，將色碼替換為 `var(--color-*)` 或 `tokens.colors` |
| Vite 埠被占用 | 提示 port 5173 已被使用 | Vite 會自動遞增使用 5174，查看終端機印出的網址即可 |

---

## 🎬 開場故事：學校的色票與規格表

想像一所學校，全校有 50 間教室。一開始校長說「每間教室自己想辦法裝潢」。

第一間教室的老師去建材行買了一罐「藍色」油漆，刷了牆。第二間也想要藍色，隨便挑了一罐看起來差不多的油漆。第三間……又挑了一罐。結果呢？全校出現了七種「差不多的藍色」，走廊上看起來亂七八糟。

課桌也是。第一間教室的老師訂了一套 85 公分高的桌子。第二間訂了 87 公分。第三間訂了 83 公分。看起來都行，但學生坐著各教室高度不一樣，聯考來臨了要輪流去別間教室監考——坐著都不舒服。

這份教學要學的就是一件事：**在代碼裡做一套「色票與規格表」，就像學校統一發給每間教室一份「油漆色票」和「課桌規格單」**。以後所有設計只能從這份清單挑，顏色永遠一致、間距永遠規則、新元件出現時自動長得像一家人。這個清單，就叫 design tokens。

這個故事會貫穿全文，先把對照表記在心裡（後面每個名詞卡都會回扣）：

| 學校 | 系統 |
|---|---|
| 校長發下來的色票與規格表 | design tokens（tailwind.config.js） |
| 某間教室 | React 元件 |
| 自己另去買油漆與丈量尺寸 | 寫死十六進位色碼與任意 padding 值（一次性樣式） |
| 改色票，全校教室自動更新 | 改 token，全站元件自動同步 |
| 規則：「只能從色票挑、間距只能用規格單」 | `.cursor/rules/design-system.mdc` |
| 查水錶的人來檢查有沒有違規 | Agent 依規則擋住寫死的色碼 |

---

## 0. 課前準備

- 安裝 [Cursor](https://cursor.com)、Node.js 20+
- 註冊 [Figma](https://figma.com) 帳號（可選，截圖路徑不需要）；或準備好四個元件的設計稿截圖
- 如使用 Figma MCP，參考 Figma 官方文檔取得 Personal Access Token（可選，入門推薦用截圖）

> 🔍 **名詞卡：Figma**
> 白話：一個線上設計工具，設計師在裡面畫網頁版面、按鈕、表單之類的，後來每個設計檔的 URL 都是可分享的。工程師拿著設計稿截圖或直接讀 Figma 的資訊，把它變成 React 元件。
>
> 🔍 **名詞卡：MCP（Model Context Protocol）**
> 白話：讓 AI 接上外部工具的「標準插座」。裝了 Figma 的 MCP 後，Agent 可以自己去開 Figma 檔案、讀出色碼與間距的精確數值，不用手工估。
>
> 🔍 **名詞卡：設計稿截圖**
> 白話：從 Figma 或 Sketch 或 Adobe XD 截圖下來的一張圖——不需要權限，不需要登入，直接貼進 Cursor 對話框，Agent 就能根據這張圖產程式碼。

---

## 1. 先懂概念：一次性 class 的坑

### 1.1 什麼是一次性 class

常見場景：設計稿裡有四種不同的藍色（主按鈕、次按鈕、連結、警告提示），三種不同的間距（8px、12px、16px）。

沒有規則的做法：每個元件各自估一套。

```tsx
// ✗ 坑爹的寫法
export function Button({ variant }) {
  if (variant === 'primary') {
    return <button style={{ background: '#3B82F6', padding: '12px 16px' }}>...</button>
  }
  if (variant === 'secondary') {
    return <button style={{ background: '#6B7280', padding: '12px 16px' }}>...</button>
  }
}

export function Badge({ color }) {
  if (color === 'blue') {
    return <span style={{ background: '#3B82F6' }}>...</span>  // 同一個藍色，不同檔案不同寫法
  }
}

export function Input({ size }) {
  if (size === 'md') {
    return <input style={{ padding: '12px 14px' }}>  // 間距寫死，和 Button 對不上
  }
}
```

**代價**：
- 改一個顏色要全專案找。第二個檔案你可能寫 `#2563EB`，以為不一樣其實是同一個色系。
- 第三個元件出現時，你發現 Button 用 `12px`、Input 用 `14px`、Badge 用 `10px`，視覺開始分裂。
- Figma 改色了，前端要改七個地方。

### 1.2 Design tokens——集中管理的真相

> 🔍 **名詞卡：Design tokens**
> 白話：代碼裡的「規格表」——不存顏色本身（`#3B82F6`），存「什麼時候用哪個顏色」（`primary`）。改色時只改一處，全站自動同步。

Design token 是一個寶寶命名標準：不存顏色本身，存「什麼時候用哪個顏色」。

```javascript
// ✓ 正確的做法：tailwind.config.js 一份真理
export default {
  theme: {
    colors: {
      primary: '#3B82F6',     // 主色
      secondary: '#6B7280',   // 次色
      foreground: '#000000',  // 文字
      background: '#FFFFFF',  // 背景
    },
    spacing: {
      2: '8px',
      3: '12px',
      4: '16px',
    },
  },
}
```

然後所有元件一律用語意化名稱：

```tsx
// ✓ 好的做法
export function Button({ variant }) {
  const colors = {
    primary: 'bg-primary text-white',
    secondary: 'bg-secondary text-foreground',
  }
  return <button className={colors[variant]}>...</button>
}

export function Input({ size }) {
  const paddings = {
    sm: 'px-2 py-2',
    md: 'px-3 py-3',
    lg: 'px-4 py-4',
  }
  return <input className={`border ${paddings[size]}`} />
}

export function Card() {
  return <div className="bg-background text-foreground p-4">...</div>
}
```

**改色只需改一行**：色票改了，全站自動同步。

> ❓ **想一想**：假設設計師突然說「我們的主色改成更深的藍色」，沒有 design tokens 要改幾個檔案？有 tokens 呢？

**答案**：沒有 tokens → 改 7 個地方；有 tokens → 改 tailwind.config.js 的一行。

### 1.3 色票規則的威力：`.cursor/rules`

> 🔍 **名詞卡：`.cursor/rules`**
> 白話：放在專案裡、專門寫給 AI 看的「行為守則」檔案。用 `globs` 限制作用範圍（例如只在 components 資料夾生效），Agent 在涉及相關檔案時自動載入、自動遵守——像每個員工的工作手冊。

即使你文件寫了「禁用十六進位色碼」，下一個同事還是會偷懶直接貼 `#3B82F6`。解決方案：**規則檔裡明寫禁止**。

```markdown
---
globs: src/components/**/*.tsx
alwaysApply: false
---

## 色票（Color Tokens）

- 禁止直接寫十六進位色碼（如 #3B82F6）
- 一律使用 bg-primary 、 text-foreground 等語意化 token
  
## 元件複用

- 開發新元件前先搜尋 src/components/ 是否已有相似元件
```

Cursor Agent 載入規則後，會在以下情況自動提醒你：

- 你問它「做一個藍色按鈕」→ 它產出時自動用 `bg-primary` 而非 `bg-[#3B82F6]`
- 你不小心貼了十六進位色碼 → 它會指出違規並改正

### 1.4 Auto Layout 是 Figma MCP 的基礎（選擇性）

若選擇 Figma MCP 路徑（比截圖路徑更精確），**Figma 的 Auto Layout 決定一切**。

不用 Auto Layout 的問題：
- 盒子的位置是座標 (x, y)，導出時根本看不出間距邏輯
- RWD 根本產不出來

用 Auto Layout 的優勢：
- MCP 能讀出 padding、gap 這些設計意圖，不是盲目的像素位置
- Agent 能推導出 Tailwind 的 `gap-3 px-4` 這樣的語意化間距

**規則**：若用 Figma MCP，設計稿所有容器都要開 Auto Layout。

### 1.5 三種設計轉程式碼路徑怎麼選

| 情境 | 選這條路 | 原因 |
|------|---------|------|
| 有 Figma 帳號、設計稿用了 Auto Layout | Figma MCP | 結構資訊精確，顏色間距直接讀 |
| 只有設計稿截圖、或 Figma 沒 Auto Layout | 截圖貼給 Agent | 快速、不需權限；缺點是色碼是估出來的 |
| Figma 有外掛匯出資料 | Figma 外掛匯出 | 最精確，但常需重構成專案慣例 |

**三條路最後都同歸於盡**：定義 design tokens、寫規則、產元件、驗無障礙。選哪條都一樣。

本教學推薦用**截圖路徑**最快上手：十五分鐘內就能從一張圖生出四個元件，你能看著 Agent 怎麼問、怎麼把設計意圖翻成程式邏輯。學會了截圖路徑，回家升級用 Figma MCP 也輕鬆。

---

## 2. 設定 Figma MCP（可選；推薦課程用截圖路徑）

### 2.1 為什麼要 MCP

沒有 MCP 時，Agent 對 Figma 設計稿是「瞎的」——只能從截圖猜顏色、猜間距。裝了 Figma MCP 後，Agent 自己就能：

- `get_file`：讀出設計稿的 component 清單、各元件的 layer 結構與 Auto Layout 設定
- `get_component_metadata`：查單個元件的色碼、字型、圓角、間距
- 生成 React 元件時能參考精確的設計資訊

### 2.2 如何設定（快速版）

前往 Figma 帳號設定 → Tokens 或 Developer 頁面，建一個 Personal Access Token；或改用截圖路徑（推薦新手）。

### 2.3 優先推薦：截圖路徑

推薦**先用截圖**：
- 不需權限
- 教會了 Agent 怎樣問好設計問題
- 後面想升級用 Figma MCP 也不難

如果你帳號有 Figma，可以課後試試 MCP 版本；現在為了快速見效，直接用截圖。兩條路最後都能產一樣的元件庫。

---

## 3. 階段一：定義 Design Tokens 與規則（50 分）

### 3.1 建立專案骨架

```bash
npm create vite@latest component-library -- --template react-ts
cd component-library
npm install -D tailwindcss postcss autoprefixer @storybook/react @storybook/addon-essentials @storybook/addon-a11y
npm install classnames
npx tailwindcss init -p
npx storybook@latest init
```

> 🔍 **名詞卡：Vite**
> 白話：超快的前端打包工具。比 Webpack 快十倍，開發時改個檔案立刻生效——寫 React 元件時會飛快地看到自己改的東西。
>
> 🔍 **名詞卡：Tailwind**
> 白話：樣式積木庫。不是寫 CSS 檔案，而是直接在 HTML 上疊 class——`<button className="bg-primary px-4 py-2">`。定義一次 token，所有 class 自動用 token 值。
>
> 🔍 **名詞卡：Storybook**
> 白話：元件博物館。把所有元件和它們的變體（大中小、成功失敗、加載中……）都展示在一個網頁上，便於檢查視覺是否一致、無障礙有沒有問題。

✅ **預期看到**：終端機逐行列出 `npm create vite` 的檔案生成、`npm install` 的套件下載、最後打開 Storybook 頁面看到「Welcome」範例。

🧯 **卡住的話**：`npm install` 卡住通常是網路問題，試試 `npm install --prefer-offline` 或切換網路；Storybook 啟動慢是正常的，等個 2 分鐘。

### 3.2 定義 Tailwind Tokens

對 Agent 說：

> 擴展 tailwind.config.js：定義以下 design tokens：
> - 色票：primary (#3B82F6)、secondary (#6B7280)、success (#10B981)、error (#EF4444)、warning (#F59E0B)、foreground (#000000)、background (#FFFFFF)、border (#E5E7EB)
> - 間距：沿用 Tailwind 預設（2=8px, 3=12px, 4=16px）
> - 圓角：sm (4px)、md (8px)、lg (12px)
> - 不要寫十六進位色碼，一律用 colors object

產出重點：

```javascript
// tailwind.config.js
export default {
  content: ["./src/**/*.{tsx,ts}"],
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        secondary: '#6B7280',
        success: '#10B981',
        error: '#EF4444',
        warning: '#F59E0B',
        foreground: '#000000',
        background: '#FFFFFF',
        border: '#E5E7EB',
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
      },
    },
  },
  plugins: [],
}
```

看這個檔案——它就是「校長的規格表」。以後所有按鈕要藍色，就寫 `bg-primary`；輸入框要圓角，就寫 `rounded-md`。改色時只改這裡一行，全站自動同步。

✅ **預期看到**：`tailwind.config.js` 最後長成上面這樣，nine 種色票、三種圓角、五種間距。

🧯 **卡住的話**：Tailwind 配置報錯通常是縮排或括號漏掉，看終端機的紅色訊息對著檔案查。改完存檔、重啟開發伺服器就行。

### 3.3 寫設計系統規則

> 🔍 **名詞卡：globs**
> 白話：萬用字元路徑。`src/components/**/*.tsx` 代表「src/components 資料夾底下、任何子資料夾、所有 .tsx 檔案」。用 globs 限制規則的作用範圍，避免 Agent 看所有檔案都套規則、導致 context 爆掉。

建 `.cursor/rules/design-system.mdc`：

```markdown
---
globs: ["src/components/**/*.tsx", "src/stories/**/*.tsx"]
alwaysApply: false
---

# Design System Rules

## 色票（Color Tokens）

- 禁止直接寫十六進位色碼（如 #3B82F6）
- 一律使用語意化 token：bg-primary、text-foreground、border-border 等
- 色票定義只在 tailwind.config.js 一處

## 間距規則

- 間距沿用 Tailwind 預設刻度（p-2, p-3, p-4 = 8px, 12px, 16px）
- 禁止任意值（如 p-[13px]）
- 一致的間距保證視覺和諧

## 元件複用

- 開發新元件前先搜尋 src/components/ 是否已有相似元件
- Button、Input 等基礎元件多次複用時，變化用 className prop，不要複製張貼

## 無障礙屬性

- 純圖示按鈕必須有 aria-label
- 互動元件要支援鍵盤操作
- Modal 開啟時焦點鎖在內部，關閉時歸還
```

規則檔就像「校長親筆簽名的行政命令」。以後誰想寫程式，AI 會先讀這份規則再動手。寫死色碼？直接被擋下來，Agent 會說「不行，改成 token」。

✅ **預期看到**：`.cursor/rules/design-system.mdc` 這個檔案出現在專案裡。

🧯 **卡住的話**：`.cursor/` 資料夾是隱藏的，檔案樹看不到也正常；用終端機 `ls -la` 驗證存在即可。或者在 Cursor 側邊欄找「Cursor Settings」點進去看 Rules 是否出現。

### 3.4 驗證規則真的會擋：故意踩一次紅線 ⭐ 一定要親自試的一幕

規則寫好了，現在來測試 AI 會不會真的擋。換你來**故意**叫它做一件違規的事——注意看它的反應。

對 Agent 說：

> 在 src/components/Test.tsx 裡，我寫了一個 Button 變體：`<button className="bg-[#3B82F6]">...</button>`。
> 請依照 design-system rules 檢查這個檔案，指出違規的那一行、對應規則的哪一條，然後改回 bg-primary。

✅ **預期看到**：Agent **拒絕並引用規則**，大意如下——

> ⛔ 發現違規：第 X 行 `bg-[#3B82F6]` 違反「色票規則 — 禁止直接寫十六進位色碼」。
>
> 改正：改成 `bg-primary`

這是實作的第一個里程碑。

看到了嗎？它不只說「不行」，還指出了哪一條規則、怎麼改。這就是好規則的特徵：**被擋下時有替代方案**。寫規則的時候要記得——它是給同事看的工作手冊，不是給機器看的法律條文。

🧯 **卡住的話**：如果 Agent 沒擋、直接照做了——代表規則寫得不夠具體它就會漏接。把規則改得更明確（例如在 globs 點名檔案路徑、在條文裡加上 Tailwind class 的例子），再測一次。

---

## 4. 階段二：第一個元件 Button（50 分）

### 4.1 情境：截圖生出 Button

最常見的開發場景：**只有一張設計稿截圖，沒有 Figma 帳號存取權限**。

對 Agent 說（**務必貼上截圖**）：

> Build a Button component based on this screenshot: variants primary/secondary/ghost, sizes sm/md/lg, disabled and loading states. Use only design tokens from tailwind.config.js, never hardcoded hex colors.

> 🔍 **名詞卡：variant（變體）**
> 白話：同一個元件的不同版本。Button 有 primary 版（藍色）、secondary 版（灰色）、ghost 版（透明無邊框），都是按鈕，但長得不一樣。變體越多，越能證明「design tokens 的威力」——所有版本用的顏色都來自同一份色票。

✅ **預期看到**：
- 產出的 Button.tsx 包含三種變體（primary、secondary、ghost）與三種尺寸（sm、md、lg）
- 樣式全部引用 token（bg-primary、px-3、rounded-md 之類），沒有出現十六進位色碼
- 若仍出現色碼，回覆要求改用 token 重寫

看截圖就能產元件，這是 Agent 的絕活。它看到「這個按鈕是藍色、邊距 12px、圓角 8px」，自動轉譯成「bg-primary、px-3、rounded-md」——因為你提前告訴它「色票在 tailwind.config.js」。

🧯 **卡住的話**：截圖太小看不清細節 → 貼高清大圖；Agent 產出了色碼 → 補充提示「一律改成 token、不要有硬編碼色值」；按鈕尺寸估不準 → 傷害不大，反正 Storybook 秀出來後一眼看出不對、再調。

### 4.2 寫 Button Storybook Stories

> 🔍 **名詞卡：Story（故事）**
> 白話：Storybook 裡展示某個元件的一個場景。「Button primary 32px 載入中」就是一個 story；「Button secondary 24px 禁用」是另一個 story。一個元件有多個 story，就像菜單上列了「烤雞、清湯、涼拌」三種吃法。

對 Agent 說：

> 為 Button.tsx 寫 Storybook stories（src/stories/Button.stories.tsx），展示：
> - 三種 variant（primary、secondary、ghost）
> - 三種 size（sm、md、lg）
> - disabled 與 loading 狀態
> - 各組合都要有 story（共至少 9 個組合）
> 用 Storybook 8 的 meta 物件格式，加上 argTypes 讓人在 Storybook UI 上能調整 variant 與 size。

產出重點：

```tsx
// src/stories/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '../components/Button';

const meta = {
  component: Button,
  title: 'Button',
  argTypes: {
    variant: { control: 'radio', options: ['primary', 'secondary', 'ghost'] },
    size: { control: 'radio', options: ['sm', 'md', 'lg'] },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = { args: { variant: 'primary', size: 'md', children: 'Primary Button' } };
export const Secondary: Story = { args: { variant: 'secondary', size: 'md', children: 'Secondary Button' } };
export const Ghost: Story = { args: { variant: 'ghost', size: 'md', children: 'Ghost Button' } };
export const Disabled: Story = { args: { disabled: true, children: 'Disabled' } };
export const Loading: Story = { args: { loading: true, children: 'Loading...' } };
```

Storybook 是元件庫的「展示廳」。進去逛一圈，能看到按鈕所有可能的樣子。這樣做有兩個好處：第一，視覺設計師進來一眼看出有沒有違規；第二，新人入職時，用 Storybook 就能把專案的「按鈕文化」學個清楚。

✅ **預期看到**：`npm run storybook dev` → 打開 http://localhost:6006 → 左邊清單有 Button stories → 點進去看到 9 個變體、可以用右上角的 control panel 切換 variant 與 size → 每個變體都應該用不同的色碼（primary 是藍色、secondary 是灰色……）、但色碼都來自 tailwind.config.js。

🧯 **卡住的話**：Storybook 啟動慢 → 等等；stories 檔名不對或格式錯誤 → 看終端機紅色訊息修改；看不到新增的 story → 試試 F5 重新整理頁面。

### 4.3 加無障礙屬性

> 🔍 **名詞卡：無障礙／ARIA（Accessible Rich Internet Applications）**
> 白話：讓「視障者的螢幕閱讀器」或「只用鍵盤的使用者」也能操作網站的技術。純圖示按鈕加 `aria-label`，Modal 加焦點陷阱，讓所有人都能用。

對 Agent 說：

> 補上 Button 的無障礙屬性：
> - aria-label（給 icon-only 按鈕用，例如 `<button aria-label="close">✕</button>`）
> - disabled 時自動加 aria-disabled
> - loading 時加 aria-busy

---

## 5. 階段三：其他三個元件（90 分）

### 5.1 Input 元件

對 Agent 說：

> 寫 Input.tsx：
> - 預設 / error / disabled 三種狀態
> - size 支援 sm / md / lg
> - 必須沿用 Button 同一套 design tokens（顏色、圓角、間距都一樣）
> - 加 aria-invalid 與 aria-describedby 方便錯誤訊息連結
> - 同時補上 Storybook stories

> 🔍 **名詞卡：props（元件的參數）**
> 白話：傳進元件的「設定值」。`<Button variant="primary" size="lg">` 裡的 `variant` 和 `size` 就是 props——決定按鈕長什麼樣。

❓ **想一想**：Input 和 Button 應該用同一套 tokens 還是各自一套？為什麼？

**答案**：同一套。因為這樣整個頁面視覺才一致，顏色和間距都對得上。用各自一套就會出現七種藍色的局面。

### 5.2 Card 元件

對 Agent 說：

> 寫 Card.tsx 容器元件：
> - 背景、邊框、圓角一律用 design tokens
> - 內部間距預設 p-4
> - 支援 header、footer slots
> - Storybook stories 展示 Card 搭配 Button、Input 的組合樣子

### 5.3 Modal 元件

> 🔍 **名詞卡：Modal（模態對話框）**
> 白話：騎著一匹馬跑出來的視窗，把背景變暗、擋住使用者，強制他先處理這個視窗的事（例如確認刪除）才能回到主頁面。

對 Agent 說：

> 寫 Modal.tsx：
> - 打開／關閉由 isOpen prop 控制
> - 半透明背景可點關閉
> - Escape 鍵也能關閉
> - **重點：焦點陷阱** → Tab / Shift+Tab 只在 Modal 內循環、關閉時焦點回到觸發按鈕
> - 加 aria-modal、aria-labelledby、role="dialog"
> - Storybook stories 展示各狀態

> 🔍 **名詞卡：焦點陷阱（Focus Trap）**
> 白話：只用鍵盤的人（Tab 跳焦點）打開 Modal，焦點應該被「困」在 Modal 裡循環，不會跳到背景。關閉 Modal 時，焦點要回到那個打開 Modal 的按鈕，不能掉到頁面最上面讓人迷路。

### 5.4 檢查色碼一致性

對 Agent 說：

> 列出 Button、Input、Card、Modal 四個元件用到的所有 design tokens。它們應該用的是同一套色票與間距，確保視覺一致。

✅ **預期看到**：四個元件都用 `bg-primary`、`text-foreground`、`border-border`、`rounded-md` 之類，沒有四個元件各自一套。

🧯 **卡住的話**：某個元件創造了新的顏色（例如 Modal 背景用了 `bg-black/50`）→ 標記為「應該改成 bg-background 加透明度 token」，後續再調整。重點是看到「元件視覺不一致的源頭」。

---

## 6. 階段四：無障礙檢查（30 分）

一個元件庫品質好不好，無障礙是最後的及格線。Storybook 裡內建了自動掃描工具，能抓出「對比度不夠」「缺 aria 屬性」這種問題；鍵盤操作只能靠人工測，也只有人工測才學得會。

### 6.1 加 Storybook 無障礙掃描插件

```bash
npx storybook add @storybook/addon-a11y
npm run storybook dev
```

進入 Storybook，每個 story 旁邊會出現「a11y」標籤，自動掃描：
- 色彩對比度（WCAG AA 4.5:1）
- 缺少的 ARIA 屬性
- semantic HTML 問題

> 🔍 **名詞卡：WCAG（Web Content Accessibility Guidelines）**
> 白話：網站無障礙的國際標準。AA 級是最常見的門檻：文字對比度至少 4.5:1（深色文字配淺色背景才看得清）。

**自動化掃描只能抓這些**；鍵盤操作仍要手測。

✅ **預期看到**：開啟 Storybook → 某個 Button story → 右邊 panel 點「a11y」標籤 → 掃描結果秀出「✓ 無違規」或「⚠ 對比度不足」。

🧯 **卡住的話**：掃描報對比度不足 → 這代表你選的色碼在 tailwind.config.js 裡對比度不夠，需要改顏色（例如 `primary` 從 `#3B82F6` 改成更深的藍）；這是設計決策，修不了就記下來「後續調色」。

### 6.2 手工鍵盤測 Modal

對 Agent 說：

> 幫 Modal 補上完整的鍵盤無障礙行為：開啟時焦點移入 Modal、Tab 與 Shift+Tab 只在 Modal 內循環、Escape 可關閉、關閉後焦點回到開啟它的那個按鈕。改完後請列出我應該怎麼用鍵盤逐步驗證這四件事。

預期產出：

```
驗證步驟：
1. 開啟 Storybook → Modal stories
2. 只用鍵盤（不碰滑鼠）
3. Tab 到「開啟 Modal」按鈕，按 Enter
4. 焦點應該進到 Modal 內的第一個可互動元素（e.g., 按鈕或輸入框）
5. 連按 Tab 好幾次，焦點應該在 Modal 內循環，不會掉到外面
6. 按 Escape，Modal 關閉
7. 焦點應該回到「開啟 Modal」按鈕
```

✅ **預期看到**：照著步驟走一遍，每個動作都符合預期。這是課後自己測、最容易被遺漏的一環。

🧯 **卡住的話**：焦點跑到背景 → 代表沒做焦點陷阱，或邏輯有漏洞；Escape 沒反應 → 事件監聽掛在錯誤的元素上。改不了就看文件秀「這是正確的行為」。

---

## 7. 情境演練

### 情境 1：Figma 改色，前端怎麼跟進

假設設計師把「主色」從 `#3B82F6` 改成 `#2563EB`（深一點的藍）。

**有 tokens 時**：只要改 `tailwind.config.js` 一行。
```javascript
colors: {
  primary: '#2563EB',  // 改這一行，全站自動同步
}
```

**沒有 tokens 時**：要找七個地方。

這就是一開始那個學校的故事的解脫。規格表改一行，五十間教室全部同步。沒有規格表，五十間教室全部要改一遍。

### 情境 2：某個按鈕偷偷寫死色碼

你在 code review 時發現誰寫的 Button variant 裡混了 `bg-[#FF6B6B]`（紅色）。

通常這是因為：
1. globs 沒涵蓋那個檔案 → 規則根本沒載入
2. Agent 忘了檢查 tailwind.config.js 有沒有這個顏色 → 要求它「改用 design tokens」
3. 真的是一個新需求色 → 先把新色加進 tailwind.config.js，再改用 token

### 情境 3：Input 和 Button 的邊框色對不上

見的最多的一個坑：Button 用 `border-gray-300`、Input 用 `border-gray-400`，看起來幾乎一樣但不完全一致。

**解決**：統一用 `border-border` token，所有邊框都用同一個色。改色時只改一個 token。

❓ **想一想**：如果 Button 和 Input 各自用一個邊框色，改邊框色時要改幾個檔案？如果都用 `border-border` token 呢？

**答案**：各自一個 → 改 2 個檔案（甚至更多，如果有 Card、Modal 等）；都用 token → 改 tailwind.config.js 一行。

---

## 8. 驗收清單

- [ ] `npm run dev` + `npm run storybook dev` 都能跑
- [ ] Button、Input、Card、Modal 四個元件都有 stories
- [ ] Storybook 查看 Button stories → 9 個變體都看得見（3 variant × 3 size）
- [ ] 全專案 grep `#[0-9A-F]` → 只出現在 tailwind.config.js，元件檔案零十六進位色碼
- [ ] Storybook 的 a11y 標籤掃描 → 沒有對比度或 ARIA 警告（或標記為「課後調整」）
- [ ] 用鍵盤測 Modal（Tab、Shift+Tab、Escape）→ 焦點陷阱正常、Escape 能關閉
- [ ] Input 與 Button 的 disabled 樣式一致
- [ ] 打開四個元件 story 並排比較 → 邊框、圓角、間距看起來同一家
- [ ] 每個元件都加上無障礙屬性（aria-label、aria-modal 等）

---

## 9. 常見坑排錯速查

多數視覺不一致的問題，能在這張表快速定位。

| 問題 | 排錯方式 |
|---|---|
| 元件出現十六進位色碼 | 檢查 globs 是否涵蓋該檔案；檢查 Cursor rules 是否真的載入 |
| 新元件功能重疊 | 先搜尋 src/components 既有元件，複用而非複製 |
| Button 和 Input 顏色不一樣 | 確認都用了 `bg-primary` / `border-border`，不是各自估 token 名稱 |
| Storybook 看不到新 story | 檢查檔名是否 `*.stories.tsx`、是否匯出 `default meta` 與至少一個 `Story` |
| Modal 按 Escape 沒反應 | 檢查事件監聽是否掛在 `document`；焦點陷阱邏輯是否在 useEffect 裡 |
| 焦點跑到背景 | Modal 没有焦點陷阱，或 focusable elements 清單不完整 |
| Storybook a11y 掃描顯示對比度警告 | token 色彩對比度不夠（應符合 WCAG AA 4.5:1），檢查 tailwind.config.js 的色碼選擇 |
| 規則檔改了但 Agent 還是寫色碼 | Cursor 需要重啟；或規則寫得不夠明確（加 glob 點名檔案路徑） |

---

## 10. 帶走的三句話

如果整份教學只能記住三件事，就這三句：

1. **設計轉程式碼最容易生出一堆一次性樣式**——七種藍色、五種間距的代價要到第三個元件才顯現；**design tokens 要先集中管理在 tailwind.config.js**，元件才不會各自估數值。改色只改一行，全站同步。

2. **Design-system rules 寫得夠具體，Agent 會替你擋**——禁止十六進位色碼、複用規則、無障礙規則三條寫進 `.cursor/rules`（用 globs 限制檔案範圍），Cursor 就會在你自己都忘記的時候提醒你；**被擋下時給替代方案，不是只說『不行』**。MCP 給眼睛，rules 給原則。

3. **無障礙檢查要自動掃描加手工測**——Storybook a11y 插件能抓對比度與 ARIA 缺陷，但鍵盤操作（焦點陷阱、Tab 循環、Escape 關閉、焦點歸位）只有手測才學得會；**這四件事每個互動元件都要驗**——不測就不知道有沒有鎖好。

回家試試 Figma MCP 版本，或者用 design tokens 升級既有專案——用 tailwind 的專案最快一小時就能整碗推翻重建。別再寫死色碼了，規格表一次搞定，一輩子省力。
