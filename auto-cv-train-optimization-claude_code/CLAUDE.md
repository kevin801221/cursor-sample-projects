# auto-cv-train-optimization-claude_code

通用 CV 自動訓練模板。改一個 `configs/*.yaml`，一行指令或跟 Claude Code 對話即可跑完整 pipeline。

## Pipeline
`data → split → train → optimize → infer`

兩種介面：
1. **CLI**：`uv run autocv all -c configs/wafer.yaml`
2. **Claude Code agents**：跟 Claude 說「下載並訓練」，5 個 agent 自動接力

## 規則
- Python 套件用 `uv` 管理（禁止 pip）
- 所有路徑用 `pathlib.Path`
- Mac 預設 MPS（`device: auto`）
- 訓練/優化前一定先報預估時間並等使用者確認（agent 不可加 `--yes`）
- 換資料集只改 config，不改程式碼

## 不要 commit 的東西
`.env`、`data/`、`runs/`、`*.pt` 已在 `.gitignore`。
