# 第二位：GitHub MCP — 現代版控、PR 審查與 Issue 追蹤中樞

> **用途分類**：🐙 版本控制 (Version Control)  
> **憑證等級**：🟡 B 級（需個人存取權杖 PAT）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**GitHub MCP** 是讓 Cursor Agent 跨越本機檔案系統，直接與遠端 GitHub 儲存庫對接的強大橋樑。

透過 GitHub MCP，Cursor Agent 不僅能讀寫本機程式碼，還能自動化日常的開源協作與團隊流程：直接檢查 PR Diff、自動撰寫 PR 審查意見（Code Review）、搜尋其他公開儲存庫的優質實作、建立與指派 Issue、甚至自動讀取 CI/CD Actions 失敗日誌。

### 核心能力清單
- **PR 審查與建立**：自動分析當前分支改動，自動開 Pull Request 並撰寫高品質 PR Description。
- **Issue 雙向追蹤**：查詢待修復的 Issue、更新狀態、將討論留言直接加到 Issue 串中。
- **全網代碼檢索**：直接利用 GitHub Code Search 尋找特定 API 的最佳實踐或開源專案寫法。
- **分支與 Release 管理**：讀取 Commit 歷史、比對 Tag 差異、自動生成 CHANGELOG。

---

## 2. 官方文件與開源專案

- **官方專案**：[modelcontextprotocol/servers/tree/main/src/github](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- **GitHub 官方文件**：[GitHub REST & GraphQL API](https://docs.github.com/en/rest)

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 第 1 步：取得 GitHub Personal Access Token (PAT)
1. 前往 GitHub → **Settings** → **Developer Settings** → **Personal access tokens** → **Fine-grained tokens** (或 Tokens classic)。
2. 勾選權限：`repo` (完整存取儲存庫代碼、Issues、PRs)、`read:org` (若需存取組織儲存庫)。
3. 生成 Token 並將其存放在系統環境變數中（例如在 `~/.zshrc` 或 `~/.bashrc` 加入 `export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxx"`）。

### 第 2 步：設定 `.cursor/mcp.json`
在專案根目錄建立 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第二位-GitHub/.cursor/mcp.json)：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

> 🔒 **安全最佳實踐**：強烈建議使用 `${env:GITHUB_PERSONAL_ACCESS_TOKEN}` 插值語法，**切勿將明文 Token 直接寫進 JSON 檔並推上版控**！

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `create_or_update_file` | 在遠端儲存庫建立或更新檔案 |
| `search_repositories` | 搜尋 GitHub 上的相關開源專案 |
| `create_issue` / `get_issue` | 建立新 Issue 或讀取 Issue 詳情與留言 |
| `create_pull_request` | 建立 PR 並設定 Base/Head 分支與標題內容 |
| `list_pull_requests` | 列出目前開放中的 PR 清單 |
| `get_pull_request` / `create_pull_request_review` | 取得 PR 完整 Diff 並發表審查評論 |
| `search_code` | 在 GitHub 跨儲存庫搜尋程式碼片段 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：全自動 Code Review 與開 PR
```markdown
請分析我目前分支與 main 的差異，為我在 GitHub 上開一個 PR，標題遵循 Conventional Commits，並附上清晰的改動摘要與驗收步驟清單。
```

### 情境 2：自動化 Issue 診斷與修復回報
```markdown
請讀取 Issue #42 的討論內容，分析使用者回報的 Bug，在專案中找出修復方法並回覆 Issue 留言說明排查結果。
```

---

## 6. 資安與防護提醒

- 建議為 Token 設定最小必要權限與過期時間（如 30-90 天）。
- 在配合 Cursor Agent 自動建立 PR 或推送檔案前，建議使用 `guard-shell.sh` 阻止強制推送（`git push --force`）。
