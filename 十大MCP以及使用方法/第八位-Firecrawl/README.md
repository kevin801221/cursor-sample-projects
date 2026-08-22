# 第八位：Firecrawl MCP — 智慧網頁爬蟲與 LLM-Ready Markdown 擷取

> **用途分類**：🕷️ 網頁擷取 (Web Scraping & Crawling)  
> **憑證等級**：🟡 B 級（需 Firecrawl API Key）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Firecrawl MCP** 是專為大型語言模型打造的高品質網頁擷取工具。

傳統的網頁爬蟲往往夾雜著繁雜的 HTML 標籤、導航選單、廣告與 JavaScript 雜訊。Firecrawl 能自動繞過 JavaScript 渲染、驗證碼與反爬機制，將任何目標網址（包含整站深度爬取）精確轉換為語意乾淨、格式標準的 Markdown，讓 Cursor Agent 能在極低 Token 消耗下快速消化外部文章、API 規格或技術部落格。

### 核心能力清單
- **Single Page Scrape**：單頁精準抓取並轉換為乾淨 Markdown。
- **Deep Crawl & Site Mapping**：整站網站地圖遍歷與子頁面批量擷取。
- **結構化資料抽取 (Extract)**：根據 JSON Schema 規範直接從網頁提取結構化物件。
- **Search & Scrape**：結合搜尋與內文抓取，快速彙整特定主題。

---

## 2. 官方文件與開源專案

- **Firecrawl 官方網站**：[https://firecrawl.dev](https://firecrawl.dev)
- **MCP Server 開源專案**：[mendableai/firecrawl-mcp-server](https://github.com/mendableai/firecrawl-mcp-server)
- **Firecrawl 文件**：[Firecrawl Docs](https://docs.firecrawl.dev)

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 第 1 步：取得 Firecrawl API Key
1. 前往 [firecrawl.dev](https://firecrawl.dev) 註冊帳號並取得 API Key（提供免費額度）。
2. 在終端中設定環境變數：
   ```bash
   export FIRECRAWL_API_KEY="fc-xxxx"
   ```

### 第 2 步：設定 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第八位-Firecrawl/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "${env:FIRECRAWL_API_KEY}"
      }
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 參數 (Parameters) | 說明 |
|---|---|---|
| `firecrawl_scrape` | `url`: 目標網址 | 將單一網頁轉為乾淨 Markdown |
| `firecrawl_crawl` | `url`: 根網址, `limit`: 上限頁數 | 進行子路徑深度爬取 |
| `firecrawl_map` | `url`: 網站網址 | 快速取得網站所有公開子頁面 URL 清單 |
| `firecrawl_extract` | `urls`: 網址清單, `schema`: JSON Schema | 自目標網頁提取結構化資料 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：快速學習競爭對手或新技術官方教學
```markdown
請使用 Firecrawl MCP 抓取 https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview 的內容，並為我總結出五大實戰技巧。
```

### 情境 2：抽取商品或技術規格為 JSON
```markdown
請使用 firecrawl_extract 抓取某官方規格頁面，並幫我轉換為 TypeScript Interface 與測試用的 Mock Data。
```

---

## 6. 資安與防護提醒

- 遵守目標網站的 `robots.txt` 與使用條款，避免高頻抓取造成對方伺服器負擔。
- 金鑰請妥善保管於系統環境變數中，切勿 commit 至 Git。
