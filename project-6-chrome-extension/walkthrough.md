# Walkthrough：在 Cursor 上把選字標註擴充一步一步做出來

> 這份文件帶你從零做出 **Chrome 選字標註擴充**——一個真正安全的方式來存放 API 金鑰，即使有人竄改前端程式碼也拿不到。你會學到三件事：MV3 的三個執行環境怎麼各司其職、如何用訊息傳遞讓 content script 永遠看不到機密、怎麼把安全紅線寫成 `.cursor/rules` 讓 Agent 在你自己都忘記的時候替你擋。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先做這五件事，才不會卡）

1. **申請好一組 LLM API key**（OpenAI、Claude API、Gemini 都行）——跟著實作時要用。先測一次確認 key 有效。
2. **Chrome 開發者模式跑過一次擴充載入流程**——按 `npm run dev` 看 Vite 編譯成功、Chrome 開發者模式載入、選字工具列出現。第一次編譯可能要 1–2 分鐘，先跑過一次，之後重編只要幾十秒。
3. **把本文件每個「✅ 預期看到」瀏覽一遍**，知道正常畫面長怎樣，動手時才判斷得出「這是正常的」還是「翻車了」，除錯速度差十倍。
4. **準備測試網頁**（任何文字多的頁面，例如 Wikipedia、Medium 或新聞網站）——實作時展示選字標註要用。
5. 動手過程中，每跑完一個指令就對照文中的「✅ 預期看到」——判斷得出「這是正常的」還是「翻車了」，除錯速度差十倍。

## 🗺️ 學習地圖（建議 3 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 第 1 節概念 | 30 分 | 閱讀理解（這是全篇靈魂，慢慢看） |
| 第 2 節安全規則 | 20 分 | 動手做（測試規則擋 Agent；規則擋得住是最精彩的一幕） |
| 第 3 節骨架與訊息型別 | 25 分 | 動手做（先建立專案、跑 npm install；定義共用型別） |
| 第 4 節 Storage 與同步 | 20 分 | 動手做（初始化、設置 chrome.alarms、測試儲存） |
| 第 5 節 API 代理 | 25 分 | 動手做（真實 API 呼叫、選字當場看摘要） ⭐ 一定要親自試的一幕 |
| 第 6 節 UI 與設定 | 30 分 | 動手做（options 頁設定 key、popup 清單） |
| 第 7 節驗收 | 10 分 | 動手做（跑檢查清單；開兩個標籤頁示範跨環境同步） |
| 收尾三句話 | 10 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `./chrome-extension/`，遙控器是 `./demo.sh`（位於 `project-6-chrome-extension/` 根目錄）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 支援內建 Web 放映模擬器（`simulator.html`），課堂上無需開啟 Chrome 擴充管理介面即可現場演示選字與 AI 摘要。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | 跑一次 `./demo.sh 2`（安全稽核） | 執行 `check_security.mjs` 確保 Manifest V3 與 Content Script 金鑰隔離驗證全數通過 |
| 2 | 跑一次 `./demo.sh 4`，確認瀏覽器能打開 `http://localhost:8086/simulator.html` | 確認課堂模擬器埠未被占用，能正常進行文字選取與氣泡視窗彈出 |
| 3 | （選配）若有 OpenAI Key 可於 options.html 填入，或直接使用預設 Mock 模式 | 預設 Mock 模式 100% 離線秒回，免費用、無風險 |

### 放映時間軸

時間軸切成 6 段，對應上方學習地圖（合計 180 分鐘），全長 **3 小時**。

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:30 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §1 | 實習生/總管/對講機三人團隊比喻、MV3 架構圖、金鑰洩露風險 | 擴充功能安全防護原則 |
| 0:30–0:50 | 第 1 幕：安全規則檔 | `./demo.sh 1` | `chrome-extension/.cursor/rules/chrome-extension-security.mdc` | 規則檔三大條款：嚴禁 content.js 碰 API key、最小權限宣告 | 用 Cursor Rules 讓 AI 絕不把金鑰寫在實習生身上 |
| 0:50–1:15 | 第 2 幕：金鑰安全稽核 ⭐ | `./demo.sh 2` | `chrome-extension/check_security.mjs` | `check_security.mjs` 掃描輸出「100% 乾淨：0% 金鑰洩露、MV3 格式合規」 | 課堂現場證明安全邊界 |
| 1:15–1:40 | 第 3 幕：訊息傳遞機制 | `./demo.sh 3` | `chrome-extension/content.js`、`background.js` | `sendMessage` 與 `onMessage` 跨環境結構化通訊 | 實習生只傳話、總管才拿鑰匙辦事 |
| 1:40–2:30 | 第 4 幕：啟動課堂放映模擬器 ⭐ | `./demo.sh 4` | `chrome-extension/simulator.html` | 瀏覽器展示文章頁面，現場滑鼠反白選字，浮動選單即時彈出並顯示 AI 摘要筆記 | 眼見為憑：免裝擴充功能即時體驗選字、AI 摘要與筆記儲存 |
| 2:30–3:00 | 第 5 幕：規格與發佈驗收 | `./demo.sh 5` | `chrome-extension/manifest.json` | `manifest.json` 完整結構與 Chrome Web Store 發佈標準 | Manifest V3 規範與打包驗收 |

### ⭐ 全場最值得停下來的一幕

**第 4 幕的 Web 放映模擬器。**
在模擬器頁面中用滑鼠選取文章段落「Manifest V3 的核心精神...」，畫面上方瞬間平滑彈出黑底藍邊的浮動按鈕（✨ AI 摘要 / 🌐 翻譯）；點擊「AI 摘要」，右側通訊面板即時印出 Service Worker 收到訊息的通訊日誌，並在選字下方彈出毛玻璃氣泡顯示摘要與「💾 儲存筆記」按鈕，點擊後即時同步至擴充儲存庫！

### 🧯 現場翻車備案

| 翻什麼 | 徵狀 | 30 秒內的救援 |
|---|---|---|
| 模擬器埠 8086 被占用 | 提示 Address already in use | 改跑 `python3 -m http.server 8087` 並在瀏覽器打開 8087 埠 |
| 選字沒反應 | 滑鼠選取太短 | 選取文字長度需大於等於 3 個字元才會觸發浮動工具列 |

---

## 🎬 開場故事：你派出去的三個人

想像一下，今天做的擴充功能就像你派出去工作的三個人。

第一個人是**實習生** content script，你派他到別人家去工作。他的工作是「在客廳裡監聽有沒有人選字，然後叫人來處理」。問題是：他在別人家，客人（網頁 JS）可以看到他身上的所有東西。所以—— **絕對不能給他任何保險箱鑰匙**（API key）。

第二個人是**總管** service worker，坐在你自己家裡的辦公室。他的工作是「聽實習生的來電，拿著保險箱裡的金鑰（API key），去銀行（LLM API）辦事，然後把結果傳回給實習生」。只有他能接觸鑰匙，因為他在自己家裡，別人看不到。

第三個人是 popup，是你口袋裡的**對講機面板**，只有在你打開時才存在。他可以跟總管通話，也可以跟實習生通話，用來查看進度、改變設定。

整個專案的安全核心就一件事：**金鑰怎麼藏才真的藏得住，最後還是靠總管這個人的位置**——他在信任的環境裡，別人偷不到。

這個三人團隊比喻會貫穿全篇，先把對照表記在心裡（後面每個名詞卡都會回扣）：

| 三人團隊 | 系統 |
|---|---|
| 實習生（派到別人家） | content script（在頁面 JS 可見的環境） |
| 總管（自己家辦公室） | service worker（只有擴充可見） |
| 對講機面板 | popup / options（使用者介面） |
| 金鑰 | API key |
| 保險箱 | chrome.storage.local |

---

## 0. 準備

- 安裝 [Cursor](https://cursor.com)、Node.js 20+
- 裝 Chrome 開發者版本（Chrome Canary），或用現有 Chrome 開啟開發者模式
- 申請一個 API key：任何 LLM API 都可（例如 OpenAI、Claude API、Gemini API）
- Chrome Web Store 開發者帳號（上架用，這份教程先不上架，但要知道怎麼做）

> 🔍 **名詞卡：Chrome 開發者模式**
> 白話：Chrome 瀏覽器的「修理工模式」——開啟後可以手動載入未上架的擴充功能，不用等 Chrome Web Store 審查，開發時很方便。
>
> 🔍 **名詞卡：LLM API**
> 白話：「租借一個大型語言模型」的方式——你送文字給 OpenAI／Claude／Google，它們用自己的 AI 模型處理，回傳結果給你；根據用量付費，不用自己買 GPU。
>
> 🔍 **名詞卡：Chrome Web Store**
> 白話：Chrome 瀏覽器的「應用商店」——擴充功能上架後，全世界的 Chrome 使用者都能裝。上架前要通過 Google 的安全審查。

---

## 1. 先懂概念：MV3 三個執行環境與金鑰安全

### 1.1 MV3 與 MV2 的關鍵差異

Manifest V3（MV3）是 Google 在 2023 年強制推行的新標準。最大改變：

| 方面 | MV2 | MV3 |
|---|---|---|
| 背景腳本 | background page（常駐記憶體） | service worker（5 分鐘無事件就卸載） |
| 儲存 | localStorage | chrome.storage（同步或本地） |
| 排程 | setInterval | chrome.alarms（服務型 API） |
| 內容腳本通訊 | 同步或非同步回應 | 一律非同步（`return true` 才能延遲回應） |

**核心轉變**：再也不能靠「全域變數」存狀態。service worker 隨時會被終止，所以一切狀態都要落地 storage。

MV2 時代，背景腳本像一個「長期工」，整天坐在那邊待命，你可以跟他說「把 key 暫時存在記憶體裡」，他就一直記著。MV3 時代，service worker 是「按鐘點算薪水的臨時工」——閒著超過 5 分鐘就下班回家，下班時忘得乾乾淨淨。只能在紙條（storage）上寫下來，他下次回來時才能看到。

### 1.2 三個執行環境各自的能力與限制

```
┌─────────────────────────────────────┐
│   頁面 JS（不受信任的環境）          │
│  Content Script                     │
│  • 能力：操作頁面 DOM、監聽事件      │
│  • 限制：頁面 JS 可以觀察它的程式碼  │
│  • 絕對禁止：任何機密（API key）    │
└─────────────────────────────────────┘
         ↕ 訊息傳遞（明文不加密）
┌─────────────────────────────────────┐
│   Service Worker（受信任的環境）    │
│  • 能力：讀 chrome.storage.local     │
│        呼叫外部 API，保管 key       │
│  • 限制：5 分鐘無事件就被卸載        │
│  • 必須：狀態一律存 storage         │
└─────────────────────────────────────┘
         ↕ chrome.runtime.sendMessage
┌─────────────────────────────────────┐
│   Popup / Options                   │
│  • 能力：使用者介面，讀寫 storage   │
│  • 限制：只有打開時才存在            │
└─────────────────────────────────────┘
```

> 🔍 **名詞卡：Content Script**
> 白話：「派進別人家工作的實習生」——在網頁環境裡執行，能操作頁面的 DOM（改改配置、抓些文字），但頁面的 JavaScript 也能看到它做了什麼。最不安全的環境。
>
> 🔍 **名詞卡：Service Worker**
> 白話：「坐在自己辦公室的總管」——執行在只有擴充程式能看得到的環境，外面的頁面 JS 根本不知道它在幹嘛。所以只有它能保管秘密（API key）。代價是記憶體有限制，5 分鐘沒事做就被關了。
>
> 🔍 **名詞卡：Popup / Options**
> 白話：使用者介面的兩種方式——popup 是點擴充圖示彈出的小面板（短暫存在），options 是設定頁（使用者主動開）。都能讀寫 storage，但只有在開啟時才執行。
>
> ❓ **想一想**：為什麼不能把 API key 放在 content script 裡？
>
> **答案**：因為 content script 在網頁環境執行，頁面 JS 可以看到它的程式碼和變數。用 DevTools（按 F12）就能把 key 抄走。

**會看到什麼**：content script 選字時發出 `REQUEST_SUMMARY` 訊息 → service worker 收到 → 從 storage 讀 API key → 呼叫 LLM API → 把摘要寫回 storage 並傳回 → content script 顯示結果。全程 content script 永遠看不到那把 key。

### 1.3 為什麼 API key 絕不能進 content script

Content script 在「不受信任的環境」裡執行：

1. 頁面的 JavaScript 可以用 `Object.getOwnPropertyNames(window)` 列舉它注入的全域變數
2. DevTools → Console 按 F12 就能讀到硬碼的字串或變數
3. 頁面 JS 可以劫持你的 `fetch` / `XMLHttpRequest`，監聽每一條網路請求

拿著 API key 的 content script 等於把金鑰暴露給**每個用過這個瀏覽器的網頁**——包括惡意網站。

**正確做法**：
- API key 只存 `chrome.storage.local`（本機加密存儲，不走雲端）
- 只由 service worker 讀
- content script 送訊息請求摘要，service worker 代為調用

### 1.4 訊息傳遞的三個 API

| API | 用途 | 特點 |
|---|---|---|
| `chrome.runtime.sendMessage()` | content script → service worker | 非同步；service worker 要 `return true` 才能延遲回應 |
| `chrome.runtime.onMessage.addListener()` | service worker 接收訊息 | 監聽函式簽名：`(request, sender, sendResponse) => {...}` |
| `chrome.storage.onChanged.addListener()` | 任何環境監聽 storage 變化 | 有人改了 storage，所有監聽者都被通知 |

**經典坑**：sendResponse 沒回應 → 都是因為監聽函式忘記 `return true`；Promise 裡的 `sendResponse` 得不到任何回應，因為在返回 undefined 之後才執行。

> 🔍 **名詞卡：Discriminated Union**
> 白話：「有標籤的房間」——每個房間(資料結構)都貼著 type 標籤（例如 `type: "REQUEST_SUMMARY"`），TypeScript 就知道房間裡該有什麼家具(欄位)。打錯標籤 TypeScript 就會紅線提醒，不用等到執行才出錯。

> ❓ **想一想**：監聽函式忘記 `return true` 會發生什麼事？
>
> **答案**：service worker 會立刻回傳 undefined，不會等異步操作完成。content script 就收不到摘要了。

### 1.5 5 分鐘閒置卸載與 chrome.alarms

Service worker 沒有常駐記憶體。「5 分鐘無事件」的計時器開始於：

- 上一次處理的 message / alarm / 其他事件結束
- 之後 5 分鐘內都沒有新事件 → service worker 被卸載
- 再來一個事件 → 重新啟動，但**全域變數全丟了**

所以：

```js
// ✗ 危險：狀態存在全域變數
let apiKey = "sk-...";   // 重啟後消失

// ✓ 正確：狀態存 storage
chrome.storage.local.get("apiKey", (data) => {
  const apiKey = data.apiKey;  // 重啟也能讀到
});
```

**排程也是**：`setInterval` 在 service worker 卸載時被取消，重啟後不再執行。要用 `chrome.alarms`：

```js
// ✗ 危險：5 分鐘後 setInterval 被取消
setInterval(() => { cleanup(); }, 60 * 1000);

// ✓ 正確：chrome.alarms 穿過卸載邊界
chrome.alarms.create("cleanup", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "cleanup") { /* 清過期標註 */ }
});
```

> 🔍 **名詞卡：Chrome.alarms**
> 白話：「鬧鐘」——即使 service worker 被卸載下班了，下次到點時還是會叫醒它，觸發你要求的動作。`setInterval` 是「經理叫你反覆做某件事」，經理下班 service worker 就停了；chrome.alarms 是「鬧鐘在固定時間響」，再怎麼忙都躲不過。

> ❓ **想一想**：為什麼 MV3 要 5 分鐘就卸載 service worker？
>
> **答案**：省電池、省記憶體。不卸載的話，手機和筆電都會很耗電。Google 賭你大部分時間用不到擴充功能，閒著的話就關了。

---

## 2. 設定開發環境與安全規則

### 2.1 建立 Vite + MV3 專案

```bash
npm create vite@latest highlights-extension -- --template vanilla-ts
cd highlights-extension
npm install
npm install --save-dev @crxjs/vite-plugin sass
```

`vite.config.ts`：

```ts
import { defineConfig } from "vite";
import { crx } from "@crxjs/vite-plugin";
import manifest from "./src/manifest.json";

export default defineConfig({
  plugins: [crx({ manifest })],
  build: { outDir: "dist" },
});
```

`src/manifest.json`（MV3 格式，一開始最小化）：

```json
{
  "manifest_version": 3,
  "name": "選字標註",
  "version": "0.0.1",
  "description": "選字即標註，AI 摘要同時儲",
  "permissions": ["storage", "scripting", "activeTab"],
  "host_permissions": ["<all_urls>"],
  "background": {
    "service_worker": "src/background/index.ts"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["src/content/index.ts"],
      "run_at": "document_end"
    }
  ],
  "action": {
    "default_title": "標註",
    "default_popup": "src/popup/index.html"
  },
  "options_page": "src/options/index.html"
}
```

✅ **預期看到**：`npm create vite` 跑完會要求確認幾個選項（都按 Enter 用預設），最後成功進入 highlights-extension 資料夾；`npm install` 安裝完沒有紅字錯誤訊息。

🧯 **卡住的話**：Node 版本太舊（<20）會有相容性警告。先檢查 `node --version`；不夠新就先說「回家升級」，用現成的 Vite 專案模板繼續。

Vite 是打包工具，`@crxjs` 外掛幫我們把 TypeScript + 擴充配置自動編譯成 Chrome 能讀的格式。`npm install` 就是把所有工具一次拉下來。

### 2.2 安全紅線寫成規則：`.cursor/rules/00-security.mdc`

工地都有牆上貼的安全守則。現在我們把安全守則貼在 AI 的「工地」裡——之後不管你叫它做什麼，它每次開工前都會先讀一遍這六條。最強的是：**它會在你自己都忘記的時候提醒你**。

> 🔍 **名詞卡：`.cursor/rules`／alwaysApply**
> 白話：放在專案裡、專門寫給 AI 看的「行為守則」檔案。標了 `alwaysApply: true` 的守則，AI **每一次**對話都會自動先讀——像每天早會都要唸一次的工安條文。

**這六條是整個專案唯一的 alwaysApply。**

```markdown
---
alwaysApply: true
---

# 選字標註擴充——API Key 安全紅線

## 絕對禁止
1. API key 不得寫在任何 `src/content/**` 或 `src/popup/**` 檔案裡
2. API key 不得存入 `chrome.storage.sync`（會上傳 Google 帳號雲端）
3. API key 不得用環境變數方式（`.env` 檔）嵌入前端程式碼打包

## 一定要做
4. API key 只能存 `chrome.storage.local`，只由 `src/background/**` 讀取
5. `src/content/**` 送訊息時只能包含「意圖」（例如 `type: "REQUEST_SUMMARY"`），不能帶 payload 機密資訊
6. Service worker 回應訊息一律用 `sendResponse()` 或返回 Promise，必須 `return true` 才能異步回應

## 上架前必檢
7. manifest.json 的 permissions 與 host_permissions 要**最小化**：只要真的用到的權限
8. options 頁告訴使用者「標註文字會被傳送給第三方 LLM API 處理」，並說明用什麼服務

# 這六條每次請求都會附上
```

`alwaysApply: true` 代表四種 Agent 模式全程套用這條規則，每一次對話自動載入，不用你提醒。

### 2.3 其餘規則用 globs，避免吃掉 context

**只有一條 always，其餘規則用 globs**——規則檔全部 alwaysApply 會把 context 塞爆，Agent 反而記不住重點。

> 🔍 **名詞卡：context／globs**
> 白話：context 是 AI 的「工作記憶桌面」，桌面就那麼大，堆太多紙它反而找不到重點；globs 是「檔案路徑的萬用字元」（`supabase/**` = supabase 資料夾底下全部），讓某份守則**只在碰到相關檔案時**才被放上桌面。

再建兩份按需載入的：

`.cursor/rules/mv3.mdc`（碰到 manifest 或背景腳本載入）：

```markdown
---
description: MV3 架構慣例
globs: ["src/background/**/*.ts", "src/manifest.json"]
---
- Service worker 無常駐記憶體，狀態一律寫 chrome.storage.local
- 排程一律用 chrome.alarms，不用 setInterval
- 監聽訊息時記得 return true 才能異步回應
- 為大資料（超 10MB）改用 chrome.storage.local（sync 上限 100KB）
```

`.cursor/rules/messaging.mdc`（碰到訊息傳遞程式碼載入）：

```markdown
---
description: 訊息傳遞與儲存規則
globs: ["src/content/**/*.ts", "src/shared/messages.ts"]
---
- 訊息型別用 discriminated union 統一定義在 src/shared/messages.ts
- content script 不允許帶 API key 或密鑰到訊息 payload
- 儲存層改用 chrome.storage.local，讀寫前檢查 manifest 是否宣告 "storage" 權限
- 監聽 chrome.storage.onChanged 時要檢查 areaName 確認來自正確的儲存區域
```

### 2.4 驗證規則真的會擋：故意踩一次紅線 ⭐ 一定要親自試的一幕

守則貼好了，現在來測試 AI 會不會真的擋。**故意**叫它做一件違規的事——注意看它的反應。

對 Agent 說：

> 把 API key 寫成環境變數在 vite.config.ts 裡，然後在 manifest.json 加入。

✅ **預期看到**：Agent **拒絕並引用規則第 3 條**，大意如下——

> ⛔ 這違反規則第 3 條。環境變數會被打包進打包後的 JS，content script 或 popup 就能讀到。改用 options 頁讓使用者手動輸入並存進 `chrome.storage.local`，這樣金鑰永遠不會被打包。

看到了嗎？它不只說「不行」，還給了替代方案。這就是好規則的第二個特徵：**被擋下時給替代方案**。寫規則的時候記得：不是寫給機器看的法律條文，是寫給一個很聽話的同事看的工作準則。

🧯 **卡住的話**：如果 Agent 沒擋、直接照做了——代表規則寫得不夠具體，它漏接了。把規則第 3 條改得更具體（點名檔案路徑、環境變數全名），再測一次。規則的具體程度，決定它擋不擋得住。

---

## 3. 階段一：骨架與訊息型別定義

### 3.1 建立共用訊息型別

Content script、service worker、popup 三環境都會互送訊息。為了避免打錯欄位名、傳錯結構，集中定義型別。

對 Agent 說：

> 建立 `src/shared/messages.ts`，定義所有訊息型別為 discriminated union：
> 1. `REQUEST_SUMMARY`（content script → service worker）：傳 selectedText、pageTitle、pageUrl
> 2. `SUMMARY_RESULT`（service worker → content script）：回傳 summary 或 error
> 3. `UPDATE_HIGHLIGHTS`（popup 與 content script 同步）：傳高亮列表
> 4. `STORE_HIGHLIGHT`（content script → service worker）：存標註進 storage
> 5. `GET_HIGHLIGHTS`（popup → service worker）：取全部標註

產出重點：

```ts
// src/shared/messages.ts

export type Message =
  | {
      type: "REQUEST_SUMMARY";
      payload: {
        selectedText: string;
        pageTitle: string;
        pageUrl: string;
      };
    }
  | {
      type: "SUMMARY_RESULT";
      payload: {
        summary?: string;
        error?: string;
      };
    }
  | {
      type: "STORE_HIGHLIGHT";
      payload: {
        text: string;
        timestamp: number;
        pageUrl: string;
        summary?: string;
      };
    }
  | {
      type: "GET_HIGHLIGHTS";
      payload: {};
    }
  | {
      type: "UPDATE_HIGHLIGHTS";
      payload: {
        highlights: Array<{
          id: string;
          text: string;
          timestamp: number;
          pageUrl: string;
          summary?: string;
        }>;
      };
    };

export type MessageResponse<T extends Message> = T extends {
  type: "REQUEST_SUMMARY";
}
  ? { summary?: string; error?: string }
  : T extends { type: "GET_HIGHLIGHTS" }
    ? { highlights: Array<any> }
    : { ok: boolean };
```

✅ **預期看到**：執行 `tsc --noEmit`，不應有錯誤。

🧯 **卡住的話**：TypeScript 報錯型別不符 → 檢查 discriminated union 的 type 字面量是否打對、payload 欄位名有無漏打。試著改一個看看「型別不符馬上紅線」的感覺。

### 3.2 Content Script 骨架

對 Agent 說：

> 建立 `src/content/index.ts`：監聽 `mouseup` 事件，如果有選字就顯示標註按鈕；按下時發 `REQUEST_SUMMARY` 訊息給 service worker；監聽回應並把摘要寫進頁面 DOM（用 Shadow DOM 避免被頁面 CSS 覆蓋）。

產出重點：

```ts
// src/content/index.ts

import { Message, MessageResponse } from "../shared/messages";

function getSelectedText(): string {
  return window.getSelection()?.toString() ?? "";
}

function showAnnotationToolbar(selectedText: string, x: number, y: number) {
  // 建立 Shadow DOM 容器
  const container = document.createElement("div");
  container.innerHTML = `
    <div style="
      position: fixed;
      top: ${y}px;
      left: ${x}px;
      background: white;
      border: 1px solid #ccc;
      padding: 8px;
      z-index: 999999;
      border-radius: 4px;
    ">
      <button id="btn-summary">摘要</button>
      <button id="btn-bookmark">書籤</button>
    </div>
  `;
  const shadow = document.documentElement.attachShadow({ mode: "open" });
  shadow.appendChild(container);

  container.querySelector("#btn-summary")?.addEventListener("click", async () => {
    const response = await chrome.runtime.sendMessage<
      Message,
      MessageResponse<Extract<Message, { type: "REQUEST_SUMMARY" }>>
    >({
      type: "REQUEST_SUMMARY",
      payload: {
        selectedText,
        pageTitle: document.title,
        pageUrl: window.location.href,
      },
    });

    if (response?.summary) {
      alert(`摘要：${response.summary}`);
    } else if (response?.error) {
      alert(`錯誤：${response.error}`);
    }
  });
}

document.addEventListener("mouseup", () => {
  const selected = getSelectedText();
  if (selected.length > 0) {
    const range = window.getSelection()?.getRangeAt(0);
    const rect = range?.getBoundingClientRect();
    if (rect) {
      showAnnotationToolbar(selected, rect.left, rect.top);
    }
  }
});
```

✅ **預期看到**：開發模式用 Chrome 載入擴充，開任何網頁選字，應該看得到工具列。

🧯 **卡住的話**：选字工具列沒出現通常是因為 content script 沒成功注入；檢查 Chrome DevTools → Sources 是否看得到 `chrome-extension://` 開頭的檔案。沒有的話檢查 manifest.json 的 content_scripts 配置。

> 🔍 **名詞卡：Shadow DOM**
> 白話：「房間裡的密室」——把一些 DOM 和 CSS 隔離起來，外面網頁的樣式改天翻地覆，密室裡的東西還是好好的。用 Shadow DOM 保護工具列，網頁的 CSS 改得有多亂都不會影響我們的按鈕。

### 3.3 Service Worker 骨架

對 Agent 說：

> 建立 `src/background/index.ts`：監聽 `REQUEST_SUMMARY` 訊息；讀 `chrome.storage.local` 取 API key；暫時先 log 訊息內容（不呼叫真實 API），然後回應一個假摘要；監聽函式記得 `return true` 才能異步回應。

產出重點：

```ts
// src/background/index.ts

import { Message, MessageResponse } from "../shared/messages";

chrome.runtime.onMessage.addListener(
  (
    request: Message,
    sender,
    sendResponse: (response: any) => void
  ): boolean | undefined => {
    if (request.type === "REQUEST_SUMMARY") {
      // 異步操作必須 return true
      handleSummaryRequest(request, sendResponse);
      return true;
    }
    return false;
  }
);

async function handleSummaryRequest(
  request: Extract<Message, { type: "REQUEST_SUMMARY" }>,
  sendResponse: (response: any) => void
) {
  try {
    // 讀 API key（暫時沒有）
    const { apiKey } = await new Promise<{ apiKey?: string }>((resolve) => {
      chrome.storage.local.get("apiKey", resolve);
    });

    if (!apiKey) {
      sendResponse({
        error: "API key 尚未設定，請開啟 options 頁設定",
      });
      return;
    }

    // 暫時的假摘要
    const summary = `[測試] ${request.payload.selectedText.substring(0, 20)}...`;
    sendResponse({ summary });

    // 存進 storage（待實作）
    chrome.storage.local.get("highlights", (data) => {
      const highlights = data.highlights ?? [];
      highlights.push({
        text: request.payload.selectedText,
        timestamp: Date.now(),
        pageUrl: request.payload.pageUrl,
        summary,
      });
      chrome.storage.local.set({ highlights });
    });
  } catch (error) {
    sendResponse({
      error: `${error instanceof Error ? error.message : "未知錯誤"}`,
    });
  }
}
```

✅ **預期看到**：選字點摘要，應該看到假摘要回應。打開 DevTools → Service Worker 分頁（不是 Console），應能看到 console.log（如有加的話）。

🧯 **卡住的話**：Popup 或 content script 打開 DevTools 看不到訊息 → 要改看「Service Worker」分頁而不是主 Console。很多人混淆 console 位置——三個環境各有各的 DevTools 分頁，注意別找錯地方。

注意：content script、service worker、popup，三個環境各有各的 DevTools 和 console。選字出現在 content script 的 console，service worker 出現在另一個分頁。一開始最容易的坑就是找錯地方。

---

## 4. 階段二：儲存與同步

### 4.1 設計 storage 結構

先設計資料結構。對 Agent 說：

> 設計 `chrome.storage.local` 的結構：
> - `apiKey`：LLM API 密鑰（字串）
> - `language`：摘要語言，預設繁體中文（string: "zh-TW" | "en"）
> - `highlights`：已標註清單（陣列，每筆含 id、text、timestamp、pageUrl、summary）
> - `lastCleanup`：最後一次清過期資料的時間戳（用於排程）

產出重點：

```ts
// src/shared/types.ts

export interface StorageData {
  apiKey?: string;
  language: "zh-TW" | "en";
  highlights: Highlight[];
  lastCleanup?: number;
}

export interface Highlight {
  id: string;
  text: string;
  timestamp: number;
  pageUrl: string;
  summary?: string;
}
```

### 4.2 Service Worker 管理 Storage

Service worker 要負責：

1. 初始化 storage（首次啟動）
2. 監聽訊息時先讀 storage 再操作
3. 設置 chrome.alarms 定期清理

對 Agent 說：

> 擴充 `src/background/index.ts`：
> 1. 在 service worker 啟動時（`chrome.runtime.onInstalled`）初始化 storage（預設值）
> 2. 設置一個名叫 "cleanup" 的 alarm，每 60 分鐘觸發一次
> 3. 在 `chrome.alarms.onAlarm` 監聽器裡，當 alarm.name === "cleanup" 時，刪掉 7 天前的標註
> 4. 所有訊息處理都要先 `chrome.storage.local.get()` 讀最新值

產出重點（擴充版）：

```ts
// src/background/index.ts 片段

// 初始化
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    language: "zh-TW",
    highlights: [],
  });
  // 設置定期清理
  chrome.alarms.create("cleanup", { periodInMinutes: 60 });
});

// 排程清理
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "cleanup") {
    cleanupOldHighlights();
  }
});

async function cleanupOldHighlights() {
  const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
  chrome.storage.local.get("highlights", (data) => {
    const highlights = (data.highlights ?? []).filter(
      (h: any) => h.timestamp > sevenDaysAgo
    );
    chrome.storage.local.set({ highlights });
  });
}

// 訊息處理（修訂版）
async function handleSummaryRequest(
  request: Extract<Message, { type: "REQUEST_SUMMARY" }>,
  sendResponse: (response: any) => void
) {
  try {
    // 每次都重新讀，不靠全域變數快取
    const data = await new Promise<any>((resolve) => {
      chrome.storage.local.get(["apiKey", "language", "highlights"], resolve);
    });

    if (!data.apiKey) {
      sendResponse({
        error: "API key 尚未設定，請開啟 options 頁設定",
      });
      return;
    }

    const summary = `[${data.language}] ${request.payload.selectedText.substring(
      0,
      20
    )}...`;
    sendResponse({ summary });

    // 存標註
    const highlights = data.highlights ?? [];
    highlights.push({
      id: Date.now().toString(),
      text: request.payload.selectedText,
      timestamp: Date.now(),
      pageUrl: request.payload.pageUrl,
      summary,
    });
    chrome.storage.local.set({ highlights });
  } catch (error) {
    sendResponse({ error: `${error}` });
  }
}
```

✅ **預期看到**：
- 開啟 DevTools → Application → Local Storage，應該看到初始化的值
- 選字標註，storage 裡 highlights 應該新增一筆
- 等 60 分鐘（測試時可改成 1 分鐘），過期標註應該被刪掉

🧯 **卡住的話**：Application 裡看不到 Local Storage → 確認 manifest.json 有宣告 `"permissions": ["storage"]`；沒有的話就加上去。

### 4.3 情境演練：監聽 storage 變化同步 UI

當一個環境改了 storage，其他環境應該感知。例如 options 頁改了 API key，popup 應該馬上看得到。

對 Agent 說：

> 在 `src/content/index.ts` 加 `chrome.storage.onChanged.addListener`，監聽 highlights 變化；一旦 highlights 變了就更新頁面上的標註顯示（用 marker 或背景色標記）。

產出重點（新增片段）：

```ts
// src/content/index.ts 片段

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === "local" && changes.highlights) {
    const newHighlights = changes.highlights.newValue ?? [];
    updatePageAnnotations(newHighlights);
  }
});

function updatePageAnnotations(highlights: any[]) {
  // 清除舊標記
  document.querySelectorAll(".highlight-marker").forEach((el) => {
    el.classList.remove("highlight-marker");
  });

  // 重新標記
  highlights.forEach((hl) => {
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null
    );

    let node;
    while ((node = walker.nextNode())) {
      if (node.textContent?.includes(hl.text)) {
        const parent = node.parentElement;
        if (parent) {
          parent.classList.add("highlight-marker");
          parent.style.backgroundColor = "yellow";
        }
      }
    }
  });
}
```

✅ **預期看到**：在一個標籤頁選字標註，在另一個標籤頁看同一個網站應該看到新標記出現。

storage 變了，所有監聽它的環境都會收到通知，自動更新。這就是為什麼 MV3 要把 state 存 storage—— 才能跨環境同步，一個地方改了全部都同步。

---

## 5. 階段三：API 代理與摘要 ⭐ 一定要親自試的一幕

### 5.1 實現 LLM API 呼叫

現在用真實的 API 呼叫取代假摘要。對 Agent 說：

> 建立 `src/background/api.ts`，實現 `summarize()` 函式：
> 1. 接收 selectedText、language、apiKey
> 2. 依 language 組織 system prompt（繁體中文或英文）
> 3. 呼叫 LLM API（假設用 OpenAI compatible endpoint）
> 4. 回傳摘要或拋出錯誤
> 
> 接著修改 `handleSummaryRequest` 改用 `summarize()` 代替假摘要。

產出重點：

```ts
// src/background/api.ts

export async function summarize(
  text: string,
  language: string,
  apiKey: string,
  apiEndpoint: string = "https://api.openai.com/v1/chat/completions"
): Promise<string> {
  const systemPrompt =
    language === "zh-TW"
      ? "你是一位專業編輯。用繁體中文、一到兩句話，摘要以下文字的核心重點："
      : "You are a professional editor. Summarize the following text in 1-2 sentences in English, focusing on the key points:";

  const response = await fetch(apiEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: "gpt-3.5-turbo",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: text },
      ],
      max_tokens: 150,
    }),
  });

  if (!response.ok) {
    throw new Error(`API 錯誤: ${response.statusText}`);
  }

  const data = (await response.json()) as {
    choices: Array<{ message: { content: string } }>;
  };
  return data.choices[0]?.message.content ?? "無法生成摘要";
}
```

```ts
// src/background/index.ts 修訂

async function handleSummaryRequest(
  request: Extract<Message, { type: "REQUEST_SUMMARY" }>,
  sendResponse: (response: any) => void
) {
  try {
    const data = await new Promise<any>((resolve) => {
      chrome.storage.local.get(["apiKey", "language", "highlights"], resolve);
    });

    if (!data.apiKey) {
      sendResponse({
        error: "API key 尚未設定，請開啟 options 頁設定",
      });
      return;
    }

    // 呼叫真實 API
    const summary = await summarize(
      request.payload.selectedText,
      data.language,
      data.apiKey
    );

    sendResponse({ summary });

    // 存標註
    const highlights = data.highlights ?? [];
    highlights.push({
      id: Date.now().toString(),
      text: request.payload.selectedText,
      timestamp: Date.now(),
      pageUrl: request.payload.pageUrl,
      summary,
    });
    chrome.storage.local.set({ highlights });
  } catch (error) {
    sendResponse({
      error: `${error instanceof Error ? error.message : "未知錯誤"}`,
    });
  }
}
```

✅ **預期看到**：在 options 頁設定好 API key，開一個有文字的網頁（例如 Wikipedia），選取一段話，點「摘要」按鈕，等 1–2 秒，應該彈出真實的 LLM 摘要。換你來親自試——選字當場出結果，這是全篇最精彩的一幕。

現在看一個很美的現象：在任意網頁選字，工具列一出現，點「摘要」——service worker 代你去 OpenAI 問一句，把答案傳回來，全程 content script 根本沒機會碰到你的 key。安全性和功能同時完整。

🧯 **卡住的話**：API 呼叫超時或 401 Unauthorized → 通常是 key 寫錯或過期。先問一下 key 是否正確、是否被別的地方用過超額；不行就用預存的摘要截圖說明概念。

### 5.2 錯誤處理與重試

API 有時會超時或限流。加個簡單的重試邏輯。對 Agent 說：

> 修改 `summarize()` 加上重試：最多重試 3 次，每次等待 1 秒後重試；只有網路錯誤才重試，API 回傳 400+ 就直接失敗。

產出重點（修訂 api.ts）：

```ts
export async function summarize(
  text: string,
  language: string,
  apiKey: string,
  apiEndpoint: string = "https://api.openai.com/v1/chat/completions"
): Promise<string> {
  const maxRetries = 3;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const systemPrompt =
        language === "zh-TW"
          ? "你是一位專業編輯。用繁體中文、一到兩句話，摘要以下文字的核心重點："
          : "You are a professional editor. Summarize the following text in 1-2 sentences in English:";

      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: "gpt-3.5-turbo",
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: text },
          ],
          max_tokens: 150,
        }),
      });

      if (response.status >= 400) {
        throw new Error(
          `API 錯誤 ${response.status}: ${response.statusText}`
        );
      }

      const data = (await response.json()) as {
        choices: Array<{ message: { content: string } }>;
      };
      return data.choices[0]?.message.content ?? "無法生成摘要";
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;  // 最後一次失敗就拋出
      await new Promise((resolve) => setTimeout(resolve, 1000));  // 等 1 秒再重試
    }
  }

  throw new Error("摘要失敗，請稍後重試");
}
```

✅ **預期看到**：故意傳錯誤的 API key，應該看到「API 錯誤 401」；改正後重試應該成功。

---

## 6. 階段四：UI、設定與跨環境同步

### 6.1 Options 頁：設定 API key 與語言

Options 頁讓使用者設定敏感資訊。對 Agent 說：

> 建立 `src/options/index.html` 與 `src/options/index.tsx`：
> 1. 表單欄位：API 密鑰（password 欄）、語言下拉選單（中文／英文）、保存按鈕
> 2. 讀 storage 顯示現在設定值
> 3. 按下保存時寫進 `chrome.storage.local`
> 4. 告訴使用者「標註內容會被傳送給 OpenAI 處理」

> 🔍 **名詞卡：Options 頁**
> 白話：「設定頁」——使用者右鍵點擴充圖示、按「選項」就進來，在這裡設定 API key、選擇喜好等等。重點：只在使用者主動開時才執行，相對安全。

產出重點（HTML）：

```html
<!-- src/options/index.html -->
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>選字標註 — 設定</title>
    <style>
      body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        padding: 2rem;
        max-width: 600px;
      }
      .form-group {
        margin: 1.5rem 0;
      }
      label {
        display: block;
        font-weight: 500;
        margin-bottom: 0.5rem;
      }
      input,
      select {
        width: 100%;
        padding: 0.5rem;
        font-size: 1rem;
      }
      button {
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        background: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }
      button:hover {
        background: #0056b3;
      }
      .notice {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 4px;
        margin: 1.5rem 0;
        font-size: 0.9rem;
      }
    </style>
  </head>
  <body>
    <h1>選字標註設定</h1>

    <div class="notice">
      <strong>隱私聲明：</strong>標註文字會被傳送給 OpenAI API
      處理生成摘要。請閱讀相關隱私政策。
    </div>

    <form id="settings-form">
      <div class="form-group">
        <label for="api-key">OpenAI API 密鑰</label>
        <input
          id="api-key"
          type="password"
          placeholder="sk-..."
          required
        />
        <small>絕不會被分享或顯示在網頁上</small>
      </div>

      <div class="form-group">
        <label for="language">摘要語言</label>
        <select id="language">
          <option value="zh-TW">繁體中文</option>
          <option value="en">English</option>
        </select>
      </div>

      <button type="submit">保存設定</button>
    </form>

    <script type="module" src="index.tsx"></script>
  </body>
</html>
```

```ts
// src/options/index.tsx

document.getElementById("settings-form")?.addEventListener("submit", (e) => {
  e.preventDefault();

  const apiKey = (
    document.getElementById("api-key") as HTMLInputElement
  ).value;
  const language = (
    document.getElementById("language") as HTMLSelectElement
  ).value;

  chrome.storage.local.set({ apiKey, language }, () => {
    alert("設定已保存");
  });
});

// 載入時顯示現有值
chrome.storage.local.get(["apiKey", "language"], (data) => {
  if (data.apiKey) {
    (document.getElementById("api-key") as HTMLInputElement).value =
      data.apiKey;
  }
  if (data.language) {
    (document.getElementById("language") as HTMLSelectElement).value =
      data.language;
  }
});
```

✅ **預期看到**：
- 開啟 options 頁，輸入 API key 與語言
- 按保存，重新打開應該還能看到設定值
- 在網頁選字，摘要語言應該跟著選擇改變

### 6.2 Popup 頁：標註清單

Popup 顯示所有標註及其摘要。對 Agent 說：

> 建立 `src/popup/index.html` 與 `src/popup/index.tsx`：
> 1. 列表顯示所有標註（每筆含原文、摘要、來源 URL、時間）
> 2. 每筆下面有刪除按鈕
> 3. 頁面頂部有清空按鈕
> 4. 監聽 storage 變化即時更新列表

產出重點（HTML）：

```html
<!-- src/popup/index.html -->
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>標註清單</title>
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      body {
        width: 500px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #f5f5f5;
      }
      .header {
        background: #007bff;
        color: white;
        padding: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .highlights-list {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
      }
      .highlight-item {
        background: white;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      }
      .highlight-text {
        font-weight: 500;
        margin-bottom: 0.5rem;
        line-height: 1.4;
      }
      .highlight-summary {
        font-size: 0.9rem;
        color: #555;
        margin-bottom: 0.5rem;
        line-height: 1.3;
      }
      .highlight-meta {
        font-size: 0.8rem;
        color: #999;
        margin-bottom: 0.75rem;
      }
      .highlight-actions {
        display: flex;
        gap: 0.5rem;
      }
      button {
        padding: 0.4rem 0.8rem;
        font-size: 0.85rem;
        border: none;
        border-radius: 2px;
        cursor: pointer;
      }
      .btn-delete {
        background: #dc3545;
        color: white;
      }
      .btn-delete:hover {
        background: #c82333;
      }
      .btn-clear {
        background: #dc3545;
        color: white;
        padding: 0.6rem 1.2rem;
        cursor: pointer;
      }
      .empty-state {
        text-align: center;
        color: #999;
        padding: 2rem 1rem;
      }
    </style>
  </head>
  <body>
    <div class="header">
      <h1 style="font-size: 1rem">標註清單</h1>
      <button class="btn-clear" id="clear-all">清空</button>
    </div>

    <div class="highlights-list" id="highlights-list">
      <div class="empty-state">尚無標註</div>
    </div>

    <script type="module" src="index.tsx"></script>
  </body>
</html>
```

```ts
// src/popup/index.tsx

import type { Highlight } from "../shared/types";

const highlightsList = document.getElementById("highlights-list");

function renderHighlights(highlights: Highlight[] = []) {
  if (!highlightsList) return;

  if (highlights.length === 0) {
    highlightsList.innerHTML = '<div class="empty-state">尚無標註</div>';
    return;
  }

  highlightsList.innerHTML = highlights
    .map(
      (hl) => `
    <div class="highlight-item">
      <div class="highlight-text">"${hl.text}"</div>
      ${
        hl.summary
          ? `<div class="highlight-summary"><strong>摘要：</strong> ${hl.summary}</div>`
          : ""
      }
      <div class="highlight-meta">
        來源：<a href="${hl.pageUrl}" target="_blank" style="color: #007bff; text-decoration: none;">
          ${new URL(hl.pageUrl).hostname}
        </a>
        <br />
        時間：${new Date(hl.timestamp).toLocaleString()}
      </div>
      <div class="highlight-actions">
        <button class="btn-delete" data-id="${hl.id}">刪除</button>
      </div>
    </div>
  `
    )
    .join("");

  // 刪除按鈕事件
  document.querySelectorAll(".btn-delete").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const id = (e.target as HTMLElement).getAttribute("data-id");
      const data = await new Promise<any>((resolve) => {
        chrome.storage.local.get("highlights", resolve);
      });
      const updated = (data.highlights ?? []).filter((h: any) => h.id !== id);
      chrome.storage.local.set({ highlights: updated });
    });
  });
}

// 初始載入
chrome.storage.local.get("highlights", (data) => {
  renderHighlights(data.highlights);
});

// 監聽 storage 變化
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === "local" && changes.highlights) {
    renderHighlights(changes.highlights.newValue);
  }
});

// 清空按鈕
document.getElementById("clear-all")?.addEventListener("click", () => {
  if (confirm("確定要清空所有標註？")) {
    chrome.storage.local.set({ highlights: [] });
  }
});
```

✅ **預期看到**：
- 開啟 popup，應該看到目前已有的標註清單
- 點刪除，標註應該消失
- 選新字標註，popup 應該自動更新

### 6.3 跨標籤頁同步

當 A 標籤頁標註了文字，B 標籤頁也應該看到。這是 `chrome.storage.onChanged` 的用場。

✅ **預期看到**：開兩個標籤頁看同一個網站，一個上面選字標註，另一個上面應該看到高亮出現。

三個環境本來各自為政，靠 storage 當中樞。其中任何一個改了 storage，其他環境自動收到通知。這就是為什麼 MV3 要把什麼都存 storage——才能跨環境同步，而且同步是自動的。

---

## 7. 驗收清單

- [ ] `npm run dev` 編譯成功，無 TypeScript 錯誤
- [ ] Chrome 開發者模式載入擴充，無 manifest 錯誤
- [ ] 能在任何網頁選字並看到工具列
- [ ] 點「摘要」按鈕，DevTools Service Worker 分頁能看到請求被處理
- [ ] options 頁能設定 API key，儲存後重新開啟應該還在
- [ ] 點「摘要」時呼叫真實 API，回傳真實摘要（content script 全程看不到 API key）
- [ ] popup 頁顯示清單，點刪除能刪除
- [ ] 開兩個標籤頁，一個標註時另一個即時看到同步
- [ ] `tsc --noEmit` 無錯誤
- [ ] grep 全專案搜 `apiKey`，只應出現在 service worker 與 options 路徑，content script 裡看不到

---

## 8. MV3 常見坑排錯速查

| 問題 | 解法 | 核心要點 |
|---|---|---|
| sendResponse 沒回應 | 監聽函式忘記 `return true` | 步驟 3.3 有例子 |
| storage 配額超過 | 大資料改用 `chrome.storage.local`（100MB） | sync 只有 100KB |
| 權限被拒 | 對照 manifest 補齊宣告權限 | 檢查 permissions、host_permissions |
| 樣式被頁面覆蓋 | 改用 Shadow DOM 隔離樣式 | 步驟 3.2 用了 Shadow DOM |
| API key 出現在前端 | grep 全專案，改用 service worker 代理 | 步驟 5.1 與 5.2 的做法 |
| Service worker 不執行 | 有沒有真的載入擴充？DevTools 看 Service Workers 分頁 | 新增後需要手動載入或重新載入 |
| Chrome alarms 不觸發 | 檢查 manifest 有沒有宣告權限；確認 alarm name 拼對 | 步驟 4.2 有完整例子 |
| Content script 與 service worker 型別不符 | 檢查 discriminated union 定義；跑 `tsc --noEmit` | 步驟 3.1 建立共用型別 |

---

## 9. 帶走的三句話

如果整份專案只能記住三件事，就這三句。

1. **API key 絕對不能出現在 content script**——即使 key 只是一個硬碼字串或環境變數，content script 在網頁環境裡執行，頁面 JS 就能按 F12 看到；service worker 代理 API 呼叫才是唯一正確做法，API key 存 `chrome.storage.local`、只由 service worker 讀。

2. **Service worker 5 分鐘就會卸載，全域變數全丟了**——狀態一律存 `chrome.storage.local`，重啟時重新讀；排程用 `chrome.alarms`，不能用 `setInterval`；這就是 MV3 與 MV2 最大的轉變。

3. **安全紅線寫成規則，Agent 會替你擋**——八條紅線寫進 `00-security.mdc`（alwaysApply），被擋下時 Agent 給替代方案；MCP 給眼睛（看到即時 manifest），rules 給原則（什麼能做、什麼不能做）。

記著三個人：實習生永遠在外面，總管永遠在家裡，口袋裡的對講機隨時帶著。誰都不信任頁面、誰都信任 storage。下次有人問「怎麼在擴充裡存機密」，你就說：「只有 service worker 能碰，用 storage 當中樞，訊息傳遞講清楚。」寫好規則讓 AI 幫你擋，安全就不是自律的問題，變成了代碼的問題。
