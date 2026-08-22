# 第五位：Figma MCP — 設計稿像素級還原與前端元件生成

> **用途分類**：🎨 設計與前端 (Design & UI/UX)  
> **憑證等級**：🟡 B 級（需 Figma Personal Access Token）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Figma MCP** 連接設計師與前端工程師，消弭「設計稿與程式碼」之間的資訊落差。

透過 Figma MCP，Cursor Agent 能直接讀取 Figma 專案檔案、Frame 與元件節點的詳細屬性（包含精確的 Padding、Gap、Flex/Grid 佈局、字型層級、HEX 色碼、Radius 與陰影值），自動將設計圖轉換為 100% 符合規範的 React / Vue / Tailwind CSS 元件。

### 核心能力清單
- **節點結構與樣式解析**：直接擷取特定 Component 或 Frame 的 Auto Layout、色彩 Tokens 與字級規範。
- **SVG 與圖片資源導出**：自動提取設計稿中的圖示與向量資源。
- **精準程式碼生成**：產出語意化 HTML + Tailwind CSS，保留精準間距與響應式斷點。

---

## 2. 官方文件與開源專案

- **Figma REST API 官方文件**：[https://www.figma.com/developers/api](https://www.figma.com/developers/api)
- **社群與官方 MCP 專案**：`figma-developer-mcp` 或 `@modelcontextprotocol/server-figma`

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 第 1 步：取得 Figma Personal Access Token
1. 登入 Figma → 點擊左上角頭像 → **Settings**。
2. 滾動至 **Personal access tokens** 區塊，點擊 **Generate new token**。
3. 命名並設定權限（通常需 `File content: Read`）。
4. 在本機設定環境變數：
   ```bash
   export FIGMA_ACCESS_TOKEN="figd_xxxx"
   ```

### 第 2 步：設定 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第五位-Figma/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "figma": {
      "command": "npx",
      "args": ["-y", "figma-developer-mcp", "--figma-api-key", "${env:FIGMA_ACCESS_TOKEN}"]
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `get_file` | 取得指定 Figma 檔案的整體結構樹狀圖 |
| `get_node` | 取得特定 Component 或 Frame 節點的詳細 CSS 與 Auto Layout 屬性 |
| `get_image` | 渲染並下載指定節點為 PNG/SVG 圖片資源 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：設計稿元件轉換為 React 元件
```markdown
請讀取 Figma 檔案（File Key: `abc123xyz`, Node ID: `45:120`）裡的「PricingCard」元件，並為我撰寫一份符合 Tailwind CSS 規範的 React Component（包含 TypeScript 型別定義）。
```

### 情境 2：設計系統色彩與間距 Token 提取
```markdown
請讀取 Figma 設計稿中的 Global Color Styles 與 Typography，幫我更新專案中的 tailwind.config.js 主題設定。
```

---

## 6. 資安與防護提醒

- 確保 `FIGMA_ACCESS_TOKEN` 不會隨代碼庫簽入 Git。
- 請確認公司專案之 Figma 存取權限，避免使用個人帳號讀取機密未公開專案。
