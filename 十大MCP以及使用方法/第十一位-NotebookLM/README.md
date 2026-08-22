# 第十一位：NotebookLM MCP — 智慧文獻研究與專屬知識庫問答

> **用途分類**：🧠 知識研究與筆記 (Knowledge & Research)  
> **憑證等級**：🟡 B 級（需 Google 授權或 NotebookLM Token）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**NotebookLM MCP** 讓 Cursor Agent 具備「直接調用 Google NotebookLM 筆記庫與研究文獻來源」的能力。

Google NotebookLM 具備極強的多文檔 Grounded RAG（具備精準引述與來源對齊的問答）能力。透過 NotebookLM MCP，你可以將龐大的架構設計文件、RFC 提案、論文 PDF、會議記錄上傳至 NotebookLM 筆記本中，Cursor Agent 即可在撰寫程式碼時，即時發起跨筆記本的深層次問答，確保實作邏輯 100% 符合團隊規格書。

### 核心能力清單
- **專屬筆記本檢索**：查詢特定 NotebookLM 筆記本內的文檔與摘要。
- **精準引用問答 (Source-Grounded QA)**：以文獻來源為基礎進行問答，杜絕模型胡言亂語。
- **主題摘要與觀點提煉**：快速從多個來源（PDF、Google Docs、YouTube 逐字稿）提煉系統架構核心重點。

---

## 2. 官方文件與專案資源

- **Google NotebookLM 官方網站**：[https://notebooklm.google.com](https://notebooklm.google.com)
- **MCP 社群專案**：`notebooklm-mcp` 或相關 NotebookLM API 橋接工具

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 第 1 步：準備認證憑證
依據所使用的 NotebookLM MCP 套件說明取得 Session Token 或 API 憑證，並設定環境變數：
```bash
export NOTEBOOKLM_AUTH_TOKEN="your_token_here"
```

### 第 2 步：設定 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第十一位-NotebookLM/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "notebooklm-mcp"],
      "env": {
        "NOTEBOOKLM_AUTH_TOKEN": "${env:NOTEBOOKLM_AUTH_TOKEN}"
      }
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `list_notebooks` | 列出目前帳號下的所有 NotebookLM 筆記本 |
| `query_notebook` | 針對指定筆記本進行 Grounded 問答檢索並回傳附帶引用的答案 |
| `get_sources` | 檢視特定筆記本中已上傳的文獻來源清單 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：根據架構白皮書撰寫核心模組
```markdown
請使用 notebooklm 工具查詢「系統核心架構 2026」筆記本，確認關於使用者身份驗證與 Token Refresh 機制的設計規格，並為我在 auth.service.ts 中實作該邏輯。
```

### 情境 2：比對新功能與產品需求說明書 (PRD)
```markdown
請向 NotebookLM 查詢「v3.0 PRD 需求集」，確認結帳流程中優惠券折扣的計算優先順序，並寫出對應的 unit test。
```

---

## 6. 資安與防護提醒

- 確保上傳至 NotebookLM 的文獻資料符合企業隱私與合規要求。
- 憑證建議定期輪轉更新。
