# 第一位：Context7 MCP — 官方技術文件與函式庫即時查證神器

> **用途分類**：📚 文件查證 (Documentation)  
> **憑證等級**：🟢 A 級（零憑證，隨裝即用）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Context7 MCP** 是專門為解決「LLM 知識截止日」與「第三方套件版本幻覺」而生的文件檢索伺服器。

當你在 Cursor 中詢問最新版 Next.js、Prisma、Tailwind CSS 或任何開源套件的 API 時，LLM 往往會依賴過時的記憶胡亂猜測。Context7 讓 Cursor Agent 具備直接向最新官方文件發起語意搜尋的能力，取得精確、乾淨且帶有版本標記的程式碼範例。

### 核心能力清單
- **即時官方文件檢索**：自動爬取並索引各大流行框架（React, Vue, Node.js, Python 等）的最新說明文件。
- **去除雜訊與廣告**：將官方文件轉換為 LLM 最易吸收的 Markdown 結構。
- **零 Token 負擔的按需載入**：只有當 Agent 主動調用工具時才會注入特定章節，避免佔滿 Context Window。

---

## 2. 官方文件與開源專案

- **官方網站**：[https://context7.com](https://context7.com)
- **GitHub 專案**：[https://github.com/upstash/context7](https://github.com/upstash/context7)
- **NPM 套件**：`@upstash/context7-mcp` 或 `context7-mcp`

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 方法一：專案專屬配置（推薦）
在專案根目錄下建立或編輯 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第一位-Context7/.cursor/mcp.json)：

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

### 方法二：Cursor 全域配置
若希望所有專案都能共用此 MCP，請編輯 `~/.cursor/mcp.json`（macOS/Linux）或 `%APPDATA%\cursor\mcp.json`（Windows）：

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

> 💡 **安裝後步驟**：
> 1. 存檔後，在 Cursor 中按下 `Cmd + Shift + P`（Windows: `Ctrl + Shift + P`），輸入並執行 `Developer: Reload Window`。
> 2. 前往 **Cursor Settings → Features → MCP**，確認 `context7` 呈現 **Connected（綠燈）**。

---

## 4. MCP Tools 工具清單

| 工具名稱 | 參數 (Parameters) | 說明 |
|---|---|---|
| `context7_query` | `query`: 查詢字串 (e.g. `"express rate-limit middleware"`) | 搜尋指定技術的最新官方文檔與範例 |
| `context7_get_doc` | `doc_id`: 文件識別碼 | 取得特定文件的完整章節內容 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：查詢最新版本的 Breaking Changes
```markdown
請使用 Context7 MCP 查詢 Next.js 15 的 Server Actions 最新規範，並幫我改寫目前的 API Route。
```

### 情境 2：排查不熟悉的 Library API
```markdown
我想在 FastAPI 中實作 JWT Bearer 驗證，請用 context7 工具查閱最新 fastapi-users 的寫法，不要憑空捏造過期的寫法。
```

---

## 6. 資安與防護提醒

- Context7 屬於公開文件搜尋服務，**不需傳入任何金鑰**。
- 請配合專案的 Hook 護欄（如 `guard-mcp.sh`），防止 Agent 在搜尋時誤將專案內部私鑰或敏感業務資料作為查詢參數發送出去。
