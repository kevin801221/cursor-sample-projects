# 第六位：Sentry MCP — 線上錯誤即時監控與自動診斷修復

> **用途分類**：🚨 監控與日誌 (Monitoring & Error Tracking)  
> **憑證等級**：🟡 B 級（需 Sentry Auth Token 與 Org Slug）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Sentry MCP** 讓 Cursor Agent 具備「連接線上生產環境 Error Trace」的能力。

當生產環境發生 Unhandled Exception 或前端 React 崩潰時，Sentry MCP 可以讓 Cursor Agent 直接讀取最新的 Issue 詳情、StackTrace、發生頻率與受影響使用者環境。Agent 能自動對照專案本地的原始碼行數，精確推斷出問題成因並產出 Hotfix PR。

### 核心能力清單
- **即時線上異常查詢**：依據 Project、環境 (staging/production) 列出最新發生的未解決 Issue。
- **完整堆疊追蹤 (StackTrace) 讀取**：取得出錯時的呼叫棧、區域變數快照與 Breadcrumbs 行為歷程。
- **根因分析 (Root Cause Analysis)**：結合本機 Git 紀錄與最新代碼，分析引發 Exception 的具體 Commit。

---

## 2. 官方文件與開源專案

- **Sentry 官方網站**：[https://sentry.io](https://sentry.io)
- **MCP Server 開源專案**：[modelcontextprotocol/servers/tree/main/src/sentry](https://github.com/modelcontextprotocol/servers/tree/main/src/sentry)
- **Sentry API 文件**：[Sentry Developer Documentation](https://docs.sentry.io/api/)

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 第 1 步：取得 Sentry 權杖與組織名稱
1. 登入 Sentry → **Settings** → **Developer Settings** → **User Auth Tokens**（或 Internal Integration）。
2. 給予 `issue:read`、`project:read`、`event:read` 權限。
3. 在終端設定環境變數：
   ```bash
   export SENTRY_AUTH_TOKEN="sntrys_xxxx"
   export SENTRY_ORG="my-company-org"
   ```

### 第 2 步：設定 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第六位-Sentry/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "sentry": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sentry"],
      "env": {
        "SENTRY_AUTH_TOKEN": "${env:SENTRY_AUTH_TOKEN}",
        "SENTRY_ORG": "${env:SENTRY_ORG}"
      }
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `list_issues` | 查詢專案中最新發生的未解決 Sentry Issue 清單 |
| `get_issue` | 讀取特定 Issue 的統計資訊、錯誤次數與標籤 |
| `get_latest_event_for_issue` | 取得引發此 Issue 的最新一次 Event（含完整 StackTrace 與環境） |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：排查 Production 最新報錯
```markdown
請使用 Sentry MCP 查詢 production 環境專案 backend-api 最近一小時發生的最高頻率 Issue，並分析該 StackTrace 指向我們專案中哪一個檔案的哪一行，提出修復程式碼。
```

### 情境 2：自動化 Release 驗收與錯誤回歸檢查
```markdown
我們剛才部署了 v2.4.0，請用 sentry 工具檢查 release:v2.4.0 是否有出現任何新的 TypeError 或未被捕捉的例外。
```

---

## 6. 資安與防護提醒

- 確保 Sentry 中的 PII（個人可識別資訊）已在 SDK 端進行適當遮蔽（Data Scrubbing）。
- Auth Token 僅需給予唯讀（Read-Only）權限即可滿足絕大多數除錯需求。
