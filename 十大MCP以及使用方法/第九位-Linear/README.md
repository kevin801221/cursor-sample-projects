# 第九位：Linear MCP — 現代敏捷專案管理與 Issue 自動化

> **用途分類**：📋 專案管理與工單 (Project Management)  
> **憑證等級**：🟡 B 級（需 Linear Personal API Key）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Linear MCP** 讓 Cursor Agent 融入團隊日常的敏捷專案管理（Agile Sprint）節奏。

在軟體開發中，頻繁切換到專案管理看板建立 Ticket、更新狀態與撰寫進度報告常常打斷工程師的心流。Linear MCP 讓 Agent 能夠直接讀取指派給你的任務、了解驗收標準（Acceptance Criteria）、自動將完成的代碼與 Linear Issue 關聯，並自動將 Issue 狀態推移至 "In Review" 或 "Done"。

### 核心能力清單
- **工單搜尋與讀取**：列出當前 Sprint 或指派給當前用戶的 Issues。
- **自動開單與補齊細節**：將對話中討論出的 Bug 或 Refactor 項目自動轉化為結構化 Linear Issue。
- **狀態與優先權更新**：在代碼實作完成時自動更新進度狀態。
- **專案與 Cycle 關聯**：查詢專案里程碑與 Epic 進度。

---

## 2. 官方文件與開源專案

- **Linear 官方網站**：[https://linear.app](https://linear.app)
- **MCP Server 開源專案**：[modelcontextprotocol/servers/tree/main/src/linear](https://github.com/modelcontextprotocol/servers/tree/main/src/linear)
- **Linear API 文件**：[Linear Developers](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 第 1 步：取得 Linear API Key
1. 登入 Linear → 點擊左上角工作區名稱 → **Settings**。
2. 導航至 **My Account** → **API**。
3. 在 **Personal API keys** 區塊建立新 Key，並複製該 Token。
4. 在本機設定環境變數：
   ```bash
   export LINEAR_API_KEY="lin_api_xxxx"
   ```

### 第 2 步：設定 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第九位-Linear/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-linear"],
      "env": {
        "LINEAR_API_KEY": "${env:LINEAR_API_KEY}"
      }
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `linear_list_issues` | 依據團隊、指派對象或狀態查詢 Issue 清單 |
| `linear_get_issue` | 讀取指定 Issue (例如 `ENG-102`) 的詳細規格與描述 |
| `linear_create_issue` | 建立新的 Issue 並設定 Priority、Estimate 與 Assignee |
| `linear_update_issue` | 更新 Issue 的狀態（如 `In Progress`, `Done`）或留言 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：根據 Linear 工單自動開始實作
```markdown
請使用 Linear MCP 查詢指派給我的 Issue「ENG-304」，讀取其 Acceptance Criteria，並在目前專案中建立對應的 API 路由。
```

### 情境 2：審查程式碼時自動回報技術債
```markdown
我們剛才完成使用者註冊功能，但缺少 Rate Limiting。請幫我在 Linear 的 Backend 團隊建立一張 Priority 2 的 Issue，標題為「[TechDebt] 加上 Redis Rate Limit 中介軟體」，並附上實作建議。
```

---

## 6. 資安與防護提醒

- Linear API Key 擁有修改專案看板的權限，請透過 `${env:LINEAR_API_KEY}` 管理。
- 建立工單時請避免將真實客戶機密資料直接寫入 Issue Title 或 Description 中。
