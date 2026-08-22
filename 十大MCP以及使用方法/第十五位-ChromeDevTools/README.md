# 第十五位：Chrome DevTools MCP — 深度前端除錯、效能與無障礙稽核

> **用途分類**：🛠️ 前端診斷與 DevTools (Frontend Diagnostics & Auditing)  
> **憑證等級**：🟢 A 級（零憑證，連接本機 Chrome 遠端除錯協定 CDP）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Chrome DevTools MCP** 將 Google Chrome 的開發者工具（DevTools Protocol）直接開放給 Cursor Agent。

相較於一般的 Headless 瀏覽器測試，Chrome DevTools MCP 更聚焦於底層的「深入診斷」：即時分析 Core Web Vitals（如 LCP, CLS, INP 效能指標）、捕獲 Memory Heap Snapshot 排查記憶體洩漏、進行 a11y（無障礙）無障礙對比度與 ARIA 標籤審查、以及監控 WebSocket / Fetch 網路封包細節。

### 核心能力清單
- **效能分析 (LCP & Core Web Vitals)**：精確測量首屏繪製時間與慢速渲染元件。
- **無障礙 (Accessibility / a11y) 稽核**：自動掃描頁面色對比度、焦點順序與螢幕報讀器相容性。
- **記憶體洩漏 (Memory Leak) 診斷**：比對 Heap Snapshots 找出未被釋放的 Closure 或 DOM 節點。
- **網路與 Console 日誌監聽**：即時攔截 Network 請求瀑布圖與 Console 報錯。

---

## 2. 官方文件與開源專案

- **Chrome DevTools Protocol (CDP)**：[https://chromedevtools.github.io/devtools-protocol/](https://chromedevtools.github.io/devtools-protocol/)
- **MCP Server 開源專案**：`@chrome-devtools/mcp` 或相關 CDP 橋接工具

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 前置需求
啟動本地 Chrome 並開啟遠端除錯埠（Remote Debugging Port）：
```bash
# macOS 啟動帶有 remote-debugging-port 的 Chrome
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

### 設定檔 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第十五位-ChromeDevTools/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "@chrome-devtools/mcp"]
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `audit_accessibility` | 針對當前頁面執行 a11y 無障礙規範稽核並回報不合規元素 |
| `measure_performance` | 測量頁面的 LCP、FID/INP 與 CLS 等核心 Web 指標 |
| `get_console_messages` | 讀取當前 Chrome 分頁的所有 Console 警告與報錯 |
| `capture_heap_snapshot` | 擷取當前頁面的記憶體快照以分析 Leak 物件 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：全自動無障礙（a11y）稽核與修復
```markdown
請使用 chrome-devtools 工具對 http://localhost:3000 進行無障礙審查，列出所有對比度不足的文字以及缺少 aria-label 的按鈕，並在專案代碼中完成修正。
```

### 情境 2：排查 React 元件記憶體洩漏
```markdown
請連線本地 Chrome，在操作「開啟/關閉 Modal」10 次後擷取 Heap Snapshot，幫我分析是否有未清理的 Event Listener 導致記憶體洩漏。
```

---

## 6. 資安與防護提醒

- 遠端除錯埠（Port 9222）請僅綁定於 `127.0.0.1` 本機端，切勿對外網開放。
- 測試過程中請避免在已登入敏感帳號的正式瀏覽器 Profile 執行除錯。
