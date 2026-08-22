# CLAUDE.md — AutoCV 專案指示與交接總覽

> 🔔 **給剛恢復對話的 Claude Code**：如果上次對話因 Token 耗盡中斷，請立即閱讀下方【📢 最新交接狀態 (Handoff)】，所有修改、重構與測試狀態均已整理完備，全套測試 **30/30 PASSED (100% 綠燈)**。

---

## 📢 最新交接狀態 (Handoff Status - 2026-08-21)

詳細交接記錄請見：[`CLAUDE_HANDOFF.md`](CLAUDE_HANDOFF.md)

### ✅ 已完成的重大改動與重構：
1. **Cursor 5 大 Subagents + Skills 體系建立**：
   - 建立 `.cursor/agents/`：`data-hunter.md`、`bbox-labeler.md`、`training-runner.md`、`hp-optimizer.md`、`inference-runner.md`。
   - 建立 `.cursor/rules/cv-subagents.mdc`，規範 Subagents 接力順序與算力守門確認機制。
   - 每個 Subagent 分別調用 `.cursor/skills/` 下的 6 個專業技能。
2. **推論與串流回調強化 (`src/autocv/infer.py` & `src/autocv/server/real_stages.py`)**：
   - `infer()` 新增 `on_image` 與 `on_eval` 回調支援。推論每畫完一張 BBox 圖片，即刻透過 WebSocket 發布 `image_stream` 事件，實現前端**非同步單張成果串流**。
3. **Web 視覺駕駛艙升級 (`src/autocv/server/static/index.html` & `app.py`)**：
   - 全新深色 Cyberpunk 儀表板，支援 5 Subagents 狀態即時燈號、即時訓練 Loss/mAP 曲線、單張即時圖片串流展示、一鍵「✨ 晶圓瑕疵 99.1% Showcase」與算力確認 Modal。
   - 駕駛艙運行指令：`uv run autocv ui --port 8787`。
4. **大師級帶班教學手冊**：
   - 建立 [`WALKTHROUGH.md`](WALKTHROUGH.md)，完整拆解 5 大 Subagents 調度原理、晶圓 99.1% 數據分析與逐步帶班流程。
5. **單元測試全數通過**：
   - `uv run pytest` ➔ **30 passed in 2.02s (100% 通過)**。

---

## 🚀 專案核心 Pipeline
`data (data-hunter) → split (bbox-labeler) → train (training-runner) → optimize (hp-optimizer) → infer & report (inference-runner)`

### 操作介面
1. **Subagents / Claude 對話**：跟 Agent 說「下載並訓練」，5 個 agent 自動接力。
2. **一條龍 CLI**：`uv run autocv all -c configs/<name>.yaml`
3. **視覺駕駛艙**：`uv run autocv ui --port 8787`

---

## 📜 開發與執行規範
- **Python 套件管理**：一律使用 `uv`（禁止使用傳統 `pip`）。
- **路徑處理**：所有路徑使用 `pathlib.Path`。
- **硬體加速**：Mac 預設 MPS（`device: auto`），選到 MPS 時自動設定 `PYTORCH_ENABLE_MPS_FALLBACK=1`。
- **算力守門機制 (Compute Gate)**：訓練或超參優化前，**必須先向使用者回報預估時間，等使用者確認 (GO) 後才可繼續執行**。Agent 絕不可擅自加上 `--yes`。
- **換資料集只改 Config**：所有實驗均透過 `configs/*.yaml` 設定，不改動 Python 核心代碼。
- **唯一命名**：每個 run 必須給予唯一的 `train.name`（如 `aq-n-640`、`aq-s-640`），以便 `autocv report` 產出優化階梯對比。
- **決策指南**：詳細決策標準位於 `.cursor/skills/` 6 個技能目錄。

---

## 🚫 勿 Commit 項目
`.env`、`data/`、`runs/`、`*.pt`、`.venv/` 均已被 `.gitignore` 排除。
