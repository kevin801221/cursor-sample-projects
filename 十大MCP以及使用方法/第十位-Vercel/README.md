# 第十位：Vercel MCP — 現代前端雲端部署與預覽環境管制

> **用途分類**：🚀 部署與雲端平台 (Deployment & Cloud)  
> **憑證等級**：🟡 B 級（需 Vercel Access Token）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Vercel MCP** 讓 Cursor Agent 連接 Vercel 雲端部署平台，實現從「寫完程式碼」到「上線預覽與日誌診斷」的一體化閉環。

在現代 Web 開發（特別是 Next.js / Svelte / Remix 等全端應用）中，本地 build 通過不代表在 Vercel 邊緣網路（Edge Functions / Serverless）上也能順暢執行。Vercel MCP 讓 Agent 能夠查詢專案部署狀態、抓取 Build / Runtime 報錯日誌、檢視 Preview URL，並協助檢查專案環境變數設定。

### 核心能力清單
- **部署狀態追蹤**：查詢最新 Git Commit 觸發的 Deployment 狀態（Building, Ready, Error）。
- **雲端 Build Logs 檢視**：遠端抓取建置失敗的完整 log，自動分析錯誤成因。
- **預覽網址與 Alias 管理**：取得 Preview 網址並回傳給開發者或交給 Playwright 進行 E2E 驗收。
- **環境變數檢查**：列出專案在 Development, Preview, Production 上的變數鍵名（不外洩值）。

---

## 2. 官方文件與開源專案

- **Vercel 官方網站**：[https://vercel.com](https://vercel.com)
- **MCP Server 開源專案**：[modelcontextprotocol/servers/tree/main/src/vercel](https://github.com/modelcontextprotocol/servers/tree/main/src/vercel)
- **Vercel REST API**：[Vercel API Docs](https://vercel.com/docs/rest-api)

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 第 1 步：取得 Vercel Access Token 與 Project ID
1. 登入 Vercel → 點擊個人頭像 → **Account Settings** → **Tokens**。
2. 建立新 Token 並複製。
3. 前往專案頁面 → **Settings** → **General**，找到 **Project ID**。
4. 在本機設定環境變數：
   ```bash
   export VERCEL_TOKEN="vercel_token_xxxx"
   export VERCEL_PROJECT_ID="prj_xxxx"
   ```

### 第 2 步：設定 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第十位-Vercel/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "vercel": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-vercel"],
      "env": {
        "VERCEL_TOKEN": "${env:VERCEL_TOKEN}",
        "VERCEL_PROJECT_ID": "${env:VERCEL_PROJECT_ID}"
      }
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `list_deployments` | 列出專案最近的部署紀錄與各分支狀態 |
| `get_deployment` | 取得特定 Deployment 的詳細資訊與狀態 |
| `get_deployment_logs` | 讀取 Build 過程或 Runtime 產生的日誌 |
| `list_projects` | 列出帳號下關聯的所有 Vercel 專案 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：排查 Vercel Build 失敗原因
```markdown
剛才推送到 main 分支的部署失敗了，請用 vercel MCP 讀取最新的 deployment logs，分析為何在 SSR 階段發生錯誤並幫我修復。
```

### 情境 2：取得 Preview 網址並進行測試
```markdown
請確認目前分支在 Vercel 上的 Preview Deployment 是否已經 Ready，並將 Preview URL 傳給 Playwright 進行首頁載入測試。
```

---

## 6. 資安與防護提醒

- 嚴禁透過 MCP 將 Production 環境變數的機密值（Secrets）輸出到對話 Context 中。
- 請遵守最小權限原則，設定 Scope 限定特定 Project。
