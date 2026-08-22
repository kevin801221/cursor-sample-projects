# 第十二位：Brave Search MCP — 獨立即時全網搜尋與技術新知檢索

> **用途分類**：🔍 網頁搜尋 (Web Search)  
> **憑證等級**：🟡 B 級（需 Brave Search API Key，每月提供 2,000 次免費額度）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Brave Search MCP** 賦予 Cursor Agent 獨立且無廣告偏差的即時全網搜尋能力。

當遇到最新的軟體 Bug、剛釋出的開源專案版本差異，或是需要查詢特定的 CVE 資安漏洞時，Brave Search 能提供乾淨、及時的搜尋結果。相較於依賴一般搜尋引擎，Brave Search API 返回結構化的標題、描述與來源 URL，讓 Agent 能夠第一時間掌握全網最新解答。

### 核心能力清單
- **全網關鍵字即時搜尋**：查詢最新技術文章、StackOverflow 討論串、GitHub Issue 解法。
- **在地與即時新聞過濾**：依據時間範圍獲取最即時的技術快訊。
- **無追蹤與隱私保護**：Brave 獨立索引庫，不收集個人隱私與搜尋指紋。

---

## 2. 官方文件與開源專案

- **Brave Search API 官方網站**：[https://brave.com/search/api/](https://brave.com/search/api/)
- **MCP Server 開源專案**：[modelcontextprotocol/servers/tree/main/src/brave-search](https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search)

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 第 1 步：取得 Brave Search API Key
1. 前往 [Brave Search API Dashboard](https://api.search.brave.com/) 註冊帳號。
2. 訂閱 Free Tier（每月免費 2,000 點查詢）。
3. 取得 API Key 並設定環境變數：
   ```bash
   export BRAVE_API_KEY="BSAxxxx"
   ```

### 第 2 步：設定 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第十二位-BraveSearch/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${env:BRAVE_API_KEY}"
      }
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 參數 (Parameters) | 說明 |
|---|---|---|
| `brave_web_search` | `query`: 關鍵字, `count`: 回傳筆數 | 執行網頁搜尋並回傳標題、網址與內文摘要 |
| `brave_local_search` | `query`: 查詢字串 | 搜尋在地商業與地點相關資訊 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：排查極罕見的套件編譯錯誤
```markdown
我在升級 Vite 6 時遇到了報錯「[vite] Internal server error: Failed to resolve import 'node:crypto' from esbuild」，請使用 brave_web_search 搜尋社群最近的解法與 Workaround。
```

### 情境 2：查詢第三方 API 最新變更
```markdown
請搜尋 Stripe API 2026 年關於 Webhook Signature 驗證是否有任何重大更新或棄用公告。
```

---

## 6. 資安與防護提醒

- 搜尋查詢字串應避免包含公司敏感資訊或內部專案專有名詞。
- 請妥善保護 `BRAVE_API_KEY`，避免公開洩漏。
