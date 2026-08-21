# Chrome 擴充功能選字標註工具

> Cursor 課程 Project 6（第 27 章）：Manifest V3。
> 一句話：**API key 放錯地方，等於把金鑰送給每個造訪過的網頁**——content script 按 F12 就看得到，service worker 代理 API 呼叫才是唯一正確做法。

## 專案規格

| | |
|---|---|
| **最終成果** | 選字標註、跨裝置同步、popup 清單、AI 摘要 |
| **技術棧** | Manifest V3、Vite + @crxjs/vite-plugin、chrome.storage |
| **預估時間** | 6–8 小時，含上架素材準備 |
| **前置需求** | Chrome 開發者模式、Chrome Web Store 開發者帳號 |

## 這個擴充功能做什麼

- 選取任一網頁文字，浮出標註與摘要工具列
- 標註結果存進 chrome.storage，跨裝置自動同步
- popup 顯示所有標註清單，支援檢視、編輯、刪除
- 點「摘要」時呼叫 LLM API，但 API key 絕不碰觸 content script
- 支援 5 分鐘閒置後 service worker 自動卸載與復活

## 三個執行環境分工

```
瀏覽器網頁（Content Script）    操作頁面 DOM，處理選字事件
    ↕ chrome.runtime.sendMessage（訊息傳遞）
Service Worker                 呼叫外部 API，保管 API key
    ↕ chrome.storage + 訊息回傳
Popup / Options                使用者介面，設定 API key、切換語言
```

**絕對紅線**：API key 只能存 `chrome.storage.local`（絕不用 sync），只由 service worker 讀取；content script 全程看不到金鑰，任何外部 API 呼叫都由 service worker 代理。

| 環境 | 能力 | 限制 |
|---|---|---|
| content script | 操作頁面 DOM | 不受信任，禁放金鑰 |
| service worker | 呼叫外部 API | 5 分鐘閒置會被卸載 |
| popup / options | 使用者介面 | 開啟時才存在 |

## 四階段開發流程

| 階段 | 做什麼 | 驗收 |
|---|---|---|
| 1. 骨架與配置 | 建 Vite + MV3 專案、寫 `.cursor/rules` | Agent 自動遵守架構 |
| 2. 訊息與儲存 | content script 送訊息、service worker 讀寫 storage | 跨環境訊息通暢 |
| 3. API 代理 | service worker 讀 API key、呼叫 LLM、存摘要 | 摘要結果確實入庫 |
| 4. UI 與體驗 | popup 清單、options 頁設定、跨裝置同步 | 標註顯示正常、同步無誤 |

## 專案結構

```
highlights-extension/
├── .cursor/rules/
│   ├── 00-security.mdc          # 六條安全紅線，全專案唯一的 alwaysApply
│   ├── mv3.mdc                  # MV3 架構慣例（globs 按需載入）
│   └── messaging.mdc            # 訊息傳遞與 storage 慣例
├── src/
│   ├── content/
│   │   └── index.ts             # content script：監聽選字、發訊息
│   ├── background/
│   │   ├── index.ts             # service worker：訊息監聽、API 代理
│   │   └── api.ts               # LLM API 呼叫封裝
│   ├── popup/
│   │   ├── index.html
│   │   ├── index.tsx            # popup：清單頁面
│   │   └── style.css
│   ├── options/
│   │   ├── index.html
│   │   ├── index.tsx            # options：設定 API key、語言
│   │   └── style.css
│   ├── shared/
│   │   ├── messages.ts          # 訊息型別定義（discriminated union）
│   │   └── types.ts             # 通用型別
│   └── manifest.json            # MV3 manifest（權限宣告）
├── vite.config.ts               # Vite + @crxjs/vite-plugin 配置
└── walkthrough.md               # 完整逐步教學
```

## 三條鐵律（本課核心）

1. **API key 絕不進 content script，安全紅線寫成規則**——六條紅線寫進 `00-security.mdc`（alwaysApply），一旦金鑰被塞進任何前端程式碼，Agent 會直接拒絕。
2. **Service worker 是唯一的 API 代理**——content script 送出 `REQUEST_SUMMARY` 訊息，service worker 讀 key、發請求、回應結果；這樣即使頁面裡的 JS 監聽網路也看不到密鑰。
3. **狀態全進 storage，不靠全域變數**——service worker 每 5 分鐘會被卸載，標註資料、API key、設定值一律寫進 `chrome.storage.local`；新啟動時重新讀取。

## 快速開始

```bash
npm install
npm run dev                     # Vite dev server + 自動載入 Chrome unpacked 擴充
# 開發者模式開啟，訪問任何網頁選字試試看

npm run build                   # 產生最終打包
npm run test:messages          # 驗證 discriminated union 型別通過
```

完整建置步驟、MV3 概念、訊息傳遞設計、API key 安全做法、5 分鐘卸載與 chrome.alarms 排程，見 **[walkthrough.md](./walkthrough.md)**。
