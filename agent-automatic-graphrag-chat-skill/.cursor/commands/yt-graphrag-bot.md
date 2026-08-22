# /yt-graphrag-bot

啟動 GraphRAG 問答機器人全套建構流程。

## 執行流程
1. **起飛前檢查**：
   ```bash
   uv run --env-file .env python .cursor/scripts/check_setup.py
   ```
2. **來源入庫**：
   使用者若提供 YouTube 連結、PDF、DOCX 或網頁 URL，直接調用入庫管線：
   ```bash
   uv run --env-file .env python -c "from ingest_pipeline import run_full_pipeline; run_full_pipeline('<來源>')"
   ```
3. **啟動後端與前端**：
   - 後端：`uv run --env-file .env uvicorn chatbot_server:app --port 8000`
   - 前端：`cd frontend && npm run dev -- --port 5180`
4. **確認服務可用**：
   - 瀏覽器開啟：`http://localhost:5180`
