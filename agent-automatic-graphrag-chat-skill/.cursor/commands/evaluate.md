# /evaluate

執行 GraphRAG 方法驗證：Baseline (Naive Vector RAG) vs Strong GraphRAG A/B 盲評。

## 執行指令
1. 產出評估題目集：
   ```bash
   uv run --env-file .env python .cursor/scripts/05_evaluate_rag.py --generate source.json --n 10
   ```
2. 啟動 A/B 評測 (需先啟動後端伺服器)：
   ```bash
   uv run --env-file .env python .cursor/scripts/05_evaluate_rag.py --run eval_set.json --api http://localhost:8000
   ```
評測完成後將輸出勝負統計與 `eval_report.json`。
