# /ingest

將新的知識來源（YouTube / PDF / DOCX / 網頁）匯入 GraphRAG 系統。

## 用法
向代理提供來源 URL 或本地路徑，例如：
- `/ingest https://www.youtube.com/watch?v=wjZofJX0v4M`
- `/ingest /path/to/document.pdf`
- `/ingest /path/to/paper.docx`
- `/ingest https://blog.example.com/post`

## 後台執行邏輯
```bash
uv run --env-file .env python -c "from ingest_pipeline import run_full_pipeline; res=run_full_pipeline('<來源>'); print(res)"
```
入庫完成後自動重整 Neo4j 與 ChromaDB 狀態。
