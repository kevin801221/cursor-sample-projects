# /run-app

同時啟動 GraphRAG 後端 API 服務與 React 前端力導向圖視覺化介面。

## 執行指令
1. 後端 (FastAPI):
   ```bash
   uv run --env-file .env uvicorn chatbot_server:app --port 8000
   ```
2. 前端 (Vite React):
   ```bash
   cd frontend && npm run dev -- --port 5180
   ```

## 存取連結
- 前端視覺化對話介面：`http://localhost:5180`
- 後端 Swagger API 文件：`http://localhost:8000/docs`
- 地端 Neo4j Browser：`http://localhost:7474`
