# 第四位：PostgreSQL MCP — 關聯式資料庫結構解析與 SQL 專家

> **用途分類**：🗄️ 資料庫 (Database)  
> **憑證等級**：🟡 B 級（需資料庫連線字串 `DATABASE_URL`）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**PostgreSQL MCP** 讓 Cursor Agent 具備直接連線 PostgreSQL 資料庫、讀取即時 Table Schema、執行診斷查詢的能力。

在開發後端 API 或排查 SQL 效能時，工程師常需手動切換到 DBeaver、DataGrip 或 psql 複製欄位結構。PostgreSQL MCP 讓 Agent 隨時調用最新資料庫定義（DDL）、檢查外鍵關聯、生成精準的 ORM 查詢或 Migration 腳本，避免欄位名稱或型態不匹配的低級錯誤。

### 核心能力清單
- **動態 Schema 檢視**：即時讀取資料表名稱、欄位型別、主鍵外鍵、索引資訊。
- **唯讀/分析型查詢執行**：執行安全查詢，分析資料筆數分佈與關聯情況。
- **SQL 語法與索引最佳化**：根據實際執行的 `EXPLAIN ANALYZE` 計畫給出索引調優建議。

---

## 2. 官方文件與開源專案

- **官方專案**：[modelcontextprotocol/servers/tree/main/src/postgres](https://github.com/modelcontextprotocol/servers/tree/main/src/postgres)
- **PostgreSQL 官方文件**：[PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 第 1 步：準備連線字串
確保環境中具備 PostgreSQL 連線資訊，例如：
`postgresql://user:password@localhost:5432/my_database`

在終端環境變數中設定（或放置於未納入版控的環境檔）：
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/my_dev_db"
```

### 第 2 步：設定 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第四位-PostgreSQL/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "${env:DATABASE_URL}"
      ]
    }
  }
}
```

> ⚠️ **資安警語**：
> 1. **永遠不要連線至正式生產資料庫 (Production DB)**！建議僅連接本機開發庫（Localhost Docker）或 Staging 測試庫。
> 2. 連線帳號請盡量給予 **唯讀權限 (Read-Only)**，防止 Agent 誤執行 `DROP TABLE` 或破壞性資料修改。

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `query` | 執行傳入的 SQL 查詢語法並回傳 JSON 結果 |
| `list_tables` | 列出目前資料庫中的所有 Table 與 View |
| `describe_table` | 檢視指定資料表的完整欄位結構、型態與約束 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：根據現有 Schema 撰寫 Prisma / Drizzle Schema
```markdown
請使用 postgres MCP 讀取現有 orders 與 users 資料表的 Schema，幫我轉換為標準的 Prisma Schema 定義，包含一對多的關聯關係。
```

### 情境 2：排查慢查詢與索引建議
```markdown
請查詢 order_items 資料表的索引結構，並針對「依據 user_id 篩選且以 created_at 排序」的場景給予複合索引的建立建議。
```

---

## 6. 資安與防護提醒

- 建議搭配專案內的 [guard-shell.sh](file:///Users/kevinluo/cursor-class-2/project-subagent-hooks/.cursor/hooks/guard-shell.sh) 與 [guard-mcp.sh](file:///Users/kevinluo/cursor-class-2/project-subagent-hooks/.cursor/hooks/guard-mcp.sh) 護欄，杜絕含有密碼的資料庫連線字串被外洩。
