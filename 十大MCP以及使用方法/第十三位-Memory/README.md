# 第十三位：Memory MCP — 跨對話長效知識圖譜與個人偏好記憶庫

> **用途分類**：🧠 長期記憶與圖譜 (Long-term Memory & Knowledge Graph)  
> **憑證等級**：🟢 A 級（零憑證，本機檔案儲存）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Memory MCP** 解決了大型語言模型「開新對話就失憶」的痛點，在本地建立一個基於知識圖譜（Knowledge Graph）的持久化長效記憶體。

每當你向 Cursor Agent 表達特定的開發習慣（例如：「我偏好使用函式型元件而不是類別」、「我們的 API 回傳一律採用 `{ code, data, msg }` 包裝」）或專案中的特殊命名約定時，Memory MCP 能自動將實體（Entities）、關係（Relations）與觀察（Observations）持久化記錄下來。在未來的每一次對話中，Agent 都能隨時讀取這些記憶，保持風格與架構的一致性。

### 核心能力清單
- **知識圖譜實體管理**：建立、更新、刪除實體節點與其特徵屬性。
- **關係網路鏈結**：記錄不同模組、概念或人事物之間的關聯。
- **跨 Session 持久化**：記憶資料完全儲存在本機，不隨對話視窗關閉而消失。

---

## 2. 官方文件與開源專案

- **MCP Server 官方專案**：[modelcontextprotocol/servers/tree/main/src/memory](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 設定檔 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第十三位-Memory/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

> 💡 **全域啟用建議**：若希望個人開發偏好在所有專案中生效，可將上述配置加到 `~/.cursor/mcp.json` 中。

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `create_entities` | 建立新的實體節點（包含實體名稱、類型與描述清單） |
| `create_relations` | 建立兩個實體之間的關聯（例如 `UserModule` -> `depends_on` -> `AuthService`） |
| `read_graph` | 讀取目前本地記憶中的完整知識圖譜結構 |
| `search_nodes` | 依據關鍵字檢索相關實體與觀察紀錄 |
| `delete_entities` | 刪除過期或無效的記憶實體 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：記錄團隊架構規範與個人習慣
```markdown
請記住：本專案所有資料庫操作一律使用 Drizzle ORM，且所有金額欄位在資料庫一律存成整數（Cent 分為單位）。請將此規則存入 Memory。
```

### 情境 2：在新對話中喚醒歷史規範
```markdown
請讀取 Memory 中的專案規範，並為我設計一套電子錢包餘額扣款的 API 路由。
```

---

## 6. 資安與防護提醒

- Memory 檔案儲存於本機使用者目錄下，請定期備份或確認是否包含個人隱私資料。
- 記憶庫僅限本地存取，不需依賴外部第三方雲端資料庫。
