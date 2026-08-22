# 第三位：Playwright MCP — 真實瀏覽器自動化與 E2E 驗收守門員

> **用途分類**：🌐 瀏覽器與測試 (Browser & Testing)  
> **憑證等級**：🟢 A 級（零憑證，本機驅動）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Playwright MCP** 賦予 Cursor Agent 一雙「看見網頁真實樣貌的眼睛」與「點擊互動的雙手」。

過往 AI 開發前端或除錯時，只能「腦補」網頁渲染後的結果；有了 Playwright MCP，Cursor Agent 能自動啟動 Headless Chromium，造訪本機開發伺服器（如 `http://localhost:3000`），執行點擊、填寫表單、觸發 API、檢查 Console Log，甚至擷取網頁截圖並分析視覺排版錯誤。

### 核心能力清單
- **網頁瀏覽與導航**：造訪指定 URL 並等待網路或 DOM 載入完成。
- **DOM 元素互動**：精確點擊按鈕、下拉選單、輸入文字框、上傳檔案。
- **視覺截圖與排版校驗**：擷取全頁面或特定元素截圖，供多模態 Agent 比對設計稿。
- **Console 與 Network 監聽**：即時捕捉前端 JavaScript 報錯與 4xx/5xx API 異常。

---

## 2. 官方文件與開源專案

- **Playwright 官方網站**：[https://playwright.dev](https://playwright.dev)
- **MCP Server 開源專案**：[ExecuteAutomation/playwright-mcp-server](https://github.com/executeautomation/playwright-mcp-server) 或 `@modelcontextprotocol/server-puppeteer`

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 前置需求
本機需具備 Node.js 環境。首次啟動時會自動下載或複用系統的 Playwright 瀏覽器核心。

### 設定檔 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第三位-Playwright/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 參數 (Parameters) | 說明 |
|---|---|---|
| `playwright_navigate` | `url`: 目標網址 | 開啟瀏覽器並導航至指定頁面 |
| `playwright_screenshot` | `name`: 圖片檔名, `selector`: 元素選擇器 | 擷取畫面並儲存截圖 |
| `playwright_click` | `selector`: CSS 或 XPath 選擇器 | 模擬滑鼠點擊元素 |
| `playwright_fill` | `selector`: 輸入框選擇器, `value`: 文字 | 在指定表單欄位填入字串 |
| `playwright_evaluate` | `script`: JavaScript 程式碼 | 在瀏覽器執行環境內執行自訂腳本 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：全自動 E2E 註冊流程驗收
```markdown
請啟動本地伺服器後，使用 Playwright MCP 造訪 http://localhost:3000/register，填寫測試帳號進行註冊，驗證是否能成功跳轉到 /dashboard，並截圖回報。
```

### 情境 2：排查前端渲染與 JS 報錯
```markdown
請用 Playwright 造訪 http://localhost:3000/cart，點擊「結帳」按鈕，並檢查是否有任何 Console 報錯或未處理的 Promise 異常。
```

---

## 6. 資安與防護提醒

- 避免讓 Playwright 在未受信任的公開網頁上執行未經驗證的 `evaluate` 腳本。
- 若測試需登入憑證，請使用獨立的測試環境帳號，切勿輸入真實 Production 密碼。
