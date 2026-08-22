# MCP 設定與分工

本 skill 刻意示範「腳本做確定性的事、MCP 做需要即時查詢/互動的事」這個分工原則。
上課時先講清楚這個原則，同學才知道什麼時候該寫腳本、什麼時候該接 MCP。

| 環節 | 工具 | 為什麼用 MCP 而不是腳本 |
|---|---|---|
| 查 LangChain/LangGraph 最新 API | **Langchain-docs MCP** | API 迭代極快，模型記憶會過期；寫程式前先查官方文件 |
| VectorDB 互動查詢/除錯 | **Chroma MCP** 或 **Qdrant MCP** | 教學時能即時「看見」向量庫裡有什麼，不用另寫查詢腳本 |
| GraphDB 查詢與 schema 探索 | **Neo4j MCP (mcp-neo4j-cypher)** | 自然語言下 Cypher，即時驗證圖譜長對了沒 |
| 前端 Copilot 對話介面 | **CopilotKit MCP** | Agent-native 前端框架（AG-UI 協定），查元件用法與整合方式 |

## 各 MCP 安裝（claude_desktop_config.json / .mcp.json）

版本註記：以下套件名為撰寫時的官方名稱，安裝前用 Langchain-docs MCP 或官網確認最新版。

### Langchain-docs（若尚未連接）
Remote MCP，直接加 URL：`https://docs.langchain.com/mcp`

### Chroma MCP
```json
{
  "mcpServers": {
    "chroma": {
      "command": "uvx",
      "args": ["chroma-mcp", "--client-type", "persistent",
               "--data-dir", "/absolute/path/to/chroma_db"]
    }
  }
}
```
`--data-dir` 必須指向 Step 2 的 `--persist` 目錄，兩邊才是同一個庫。

### Neo4j MCP
```json
{
  "mcpServers": {
    "neo4j": {
      "command": "uvx",
      "args": ["mcp-neo4j-cypher"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your-password"
      }
    }
  }
}
```

### Neo4j 本體（教學用最快啟動）
```bash
docker run -d --name neo4j-teach \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:5
```
瀏覽器開 http://localhost:7474 可以視覺化驗證圖譜——上課展示效果極好。

## 課堂驗證流程（MCP 的教學價值就在這裡）

建完每一層後，用對應 MCP 立刻驗證，不要等到最後才 debug：

1. Step 2 之後 → 用 Chroma MCP：「列出 collection yt_rag 前 5 筆和它們的 metadata」
   確認 `chunk_index`、`url_at_time` 都在。
2. Step 3 之後 → 用 Neo4j MCP：「找出 MENTIONED_IN 關係最多的前 10 個 Entity」
   確認實體有正確去重合併（若同義詞沒合併，回頭調 Step 3 的抽取 prompt）。
3. 寫前端之前 → 用 CopilotKit MCP 查 `useCopilotChat` / AG-UI 最新用法。

## 常見坑

- **MCP 連的庫和腳本寫的庫不是同一個**：路徑用絕對路徑，且 Chroma 的
  `collection_name` 兩邊要一致。這是課堂上最常見的「明明存了卻查不到」。
- **Neo4j MCP 有寫入能力**：教學環境無妨，正式環境要用 read-only 帳號。
- **uvx 未安裝**：`brew install uv`（或 `curl -LsSf https://astral.sh/uv/install.sh | sh`），
  也可以改用 `npx` 版本的對應 server。
