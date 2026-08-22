# 第七位：Docker MCP — 容器化環境管理與服務診斷專家

> **用途分類**：🐳 容器與 DevOps (Containers & DevOps)  
> **憑證等級**：🟢 A 級（零憑證，透過本機 Docker Daemon 通訊）  
> **通訊協議**：`stdio` (透過 `npx`)

---

## 1. 核心定位與功能簡介

**Docker MCP** 讓 Cursor Agent 具備直接檢視本機 Docker 容器生命週期、讀取 Container Logs、排查服務健康狀態的能力。

當開發微服務、本機資料庫（Redis, Postgres, LocalStack）或除錯 Dockerfile 時，工程師無需頻繁切換到 Docker Desktop 或終端機敲指令。Cursor Agent 能自動檢查服務是否正常運行、抓取 Crash 容器的最後 50 行日誌、甚至協助微調 `docker-compose.yml` 配置。

### 核心能力清單
- **容器狀態監控**：列出運行中與已停止的容器、名稱、Port 映射與狀態。
- **容器日誌讀取**：即時抓取指定 Container 的 stdout/stderr 日誌。
- **映像檔與網路檢視**：檢查本地 Docker Images、Tags、虛擬 Network 拓撲。
- **容器操作管理**：啟動、重啟或停止指定容器服務。

---

## 2. 官方文件與開源專案

- **Docker 官方網站**：[https://www.docker.com](https://www.docker.com)
- **MCP Server 開源專案**：[modelcontextprotocol/servers/tree/main/src/docker](https://github.com/modelcontextprotocol/servers/tree/main/src/docker)

---

## 3. 在專案 `.cursor/` 中安裝與配置

### 前置需求
本機需已安裝並啟動 **Docker Desktop** 或 Docker Engine（具備存取 `/var/run/docker.sock` 的權限）。

### 設定檔 [.cursor/mcp.json](file:///Users/kevinluo/cursor-class-2/十大MCP以及使用方法/第七位-Docker/.cursor/mcp.json)
```json
{
  "mcpServers": {
    "docker": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-docker"]
    }
  }
}
```

---

## 4. MCP Tools 工具清單

| 工具名稱 | 說明 |
|---|---|
| `list_containers` | 列出所有容器（包含狀態、Port 映射、名稱與 Image） |
| `get_container_logs` | 讀取指定容器的最新日誌輸出 |
| `start_container` / `stop_container` | 啟動或安全停止指定的容器 |
| `list_images` | 列出本機已建置或下載的 Docker 映像檔 |

---

## 5. 實戰 Prompt 與使用情境

### 情境 1：排查本機資料庫容器啟動失敗
```markdown
請用 docker MCP 檢查本地所有的容器狀態，如果 postgres-dev 容器已停止，請抓取它的最後 30 行 logs 幫我分析為何退出了。
```

### 情境 2：根據容器日誌除錯微服務通訊
```markdown
請讀取 redis 容器與 api-gateway 容器的日誌，幫我確認兩者之間的連線失敗是由於 Port 衝突還是認證錯誤。
```

---

## 6. 資安與防護提醒

- Docker MCP 具有操作本機行程的能力，建議搭配專案的 `guard-shell.sh` 護欄，避免 Agent 誤刪除重要的資料卷（Volume）。
- 不建議在具有 root 權限的生產伺服器上直接開放未限制的 Docker MCP。
