# 第十四位：Cloudflare MCP — 邊緣運算 Workers、KV/D1 與全域 DNS 控制台

> **用途分類**：☁️ 雲端邊緣與 Serverless (Serverless & Edge Cloud)  
> **憑證等級**：🟡 B 級（需 Cloudflare API Token 與 Account ID）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Cloudflare MCP** 讓 Cursor Agent 具備直接管理與除錯 Cloudflare 全球邊緣網路資源的能力。

現代 Full-stack 與 AI 應用越來越多部署在 Cloudflare Workers、Pages、D1 (Serverless SQLite)、KV 與 Vectorize 向量資料庫上。Cloudflare MCP 讓 Agent 能夠直接讀取 Workers 部署狀態、即時查詢 D1 資料庫、檢查 DNS 記錄與快取規則，極大加速邊緣架構的開發與運維速度。

### 核心能力清單
- **Workers & Pages 部署管理**：檢視 Workers 腳本清單、最新部署版本與執行日誌。
- **邊緣儲存 (KV / D1 / R2) 檢索**：直接發起 D1 SQL 查詢或檢查 KV Key-Value 資料。
- **DNS 記錄與 CDN 快取管理**：查詢與調整 Zone DNS 解析與快取設定。

---

## 2. 官方文件與開源專案

- **Cloudflare 官方網站**：[https://cloudflare.com](https://cloudflare.com)
- **MCP Server 官方專案**：[cloudflare/mcp-server-cloudflare](https://github.com/cloudflare/mcp-server-cloudflare)
- **Cloudflare API 文件**：[Cloudflare API Docs](https://developers.cloudflare.com/api/)

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 第 1 步：取得 Cloudflare API Token 與 Account ID
1. 登入 Cloudflare Dashboard → 右上角 **My Profile** → **API Tokens**。
2. 建立 Token（範本可選 **Edit Cloudflare Workers**，或依需求自訂 Workers, D1, DNS 權限）。
3. 前往 Workers & Pages 頁面，右側側欄可複製 **Account ID**。
4. 設定本機環境變數：
   ```bash
   export CLOUDFLARE_API_TOKEN="cf_token_xxxx"
   export CLOUDFLARE_ACCOUNT_ID="cf_account_xxxx"
   ```

### 第 2 步：設定 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第十四位-Cloudflare/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "cloudflare": {
      "command": "npx",
      "args": ["-y", "@cloudflare/mcp-server-cloudflare"],
      "env": {
        "CLOUDFLARE_API_TOKEN": "${env:CLOUDFLARE_API_TOKEN}",
        "CLOUDFLARE_ACCOUNT_ID": "${env:CLOUDFLARE_ACCOUNT_ID}"
      }
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `list_workers` | 列出帳號下所有 Cloudflare Workers 專案 |
| `d1_query` | 向指定 D1 資料庫發送 SQL 查詢語法 |
| `kv_get` / `kv_list` | 讀取 KV 命名空間內的鍵值資料 |
| `list_dns_records` | 檢視指定網域的 DNS A/CNAME/TXT 記錄清單 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：檢驗 Cloudflare D1 資料庫狀態
```markdown
請使用 cloudflare MCP 的 d1_query 工具，查詢我的 d1-prod 資料庫中最近 5 筆 user_sessions 記錄，確認欄位格式是否正常。
```

### 情境 2：排查 Workers 部署與綁定設定
```markdown
請列出 auth-worker 的所有環境變數與 KV/D1 Bindings 設定，確認是否有遺漏的變數。
```

---

## 6. 資安與防護提醒

- 避免建立擁有全域 Global API Key 權限的萬能 Token，請依據專案範圍限定 Token 權限。
- 嚴禁透過 MCP 直接變更生產環境的權威 DNS 記錄，避免引發服務中斷。
