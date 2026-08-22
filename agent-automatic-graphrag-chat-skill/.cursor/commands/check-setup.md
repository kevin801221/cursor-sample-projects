# /check-setup

執行 GraphRAG 起飛前系統環境與相依套件檢查。

## 執行指令
```bash
uv run --env-file .env python .cursor/scripts/check_setup.py
```
若需要檢查付費 API 金鑰：
```bash
uv run --env-file .env python .cursor/scripts/check_setup.py --full
```
全綠通過輸出：`ALL CHECKS PASSED — 可以開始 Phase 1`。
