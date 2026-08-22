# 📋 CLAUDE_HANDOFF.md — Claude Code 工作交接手冊

> **本文件專供接手本專案的 Claude Code 閱讀。**  
> 記錄了先前會話中斷前已完成的代碼修改、架構重構、測試驗證結果，以及接手後的下一步執行建議。

---

## 🔍 1. 當前系統狀態與測試總結

| 檢查項目 | 當前狀態 | 備註 |
|---|---|---|
| **單元測試 (`uv run pytest`)** | **30 / 30 PASSED (100%)** | 覆蓋 cli, config, device, report, server, split-validate |
| **Python 環境** | Python 3.11 + `uv` | 使用 `uv.lock` 精確鎖定依賴 |
| **Cursor 5 大 Subagents** | 已建立於 `.cursor/agents/` | 分工明確，各自綁定 `.cursor/skills/` |
| **Web 駕駛艙服務** | 正常運行於 `http://localhost:8787` | 支援 WebSocket 即時日誌與單張非同步圖片串流 |
| **現有成果展示** | 晶圓瑕疵 WM-811K (99.1% mAP) | 成果圖位於 `docs/results/`，可一鍵展示 |

---

## 🛠️ 2. 先前完成的代碼修改清單 (Code Changes)

### A. Subagents & Skills 體系 (`.cursor/`)
- **`.cursor/agents/`**：
  - `data-hunter.md`：負責 Roboflow 原始資料集下載（調用 `cv-data-collection`）。
  - `bbox-labeler.md`：負責 YOLO 標註品管與切分（調用 `cv-dataset-qc`）。
  - `training-runner.md`：負責硬體加速訓練與算力守門確認（調用 `cv-training`）。
  - `hp-optimizer.md`：負責超參數調優與階梯規劃（調用 `cv-hyperparameter-tuning` & `cv-optimization-ladder`）。
  - `inference-runner.md`：負責推論、BBox 繪製與成績單輸出（調用 `cv-metrics-viz`）。
- **`.cursor/rules/cv-subagents.mdc`**：
  - 常駐生效之協作規則，規範 Subagent 接力順序與算力守門閘門。

### B. 即時非同步串流推論 (`src/autocv/infer.py`)
- 修改 `infer(cfg, root, on_image=None, on_eval=None)`：
  - 支援單張圖片預測完成即時回調 `on_image`（傳遞圖片路徑、檢測框座標、類別與信心分數）。
  - 支援測試集評估完成回調 `on_eval`（傳遞 `map50`, `map`, `precision`, `recall`）。

### C. 後端事件轉發 (`src/autocv/server/real_stages.py` & `app.py`)
- 在 `real_stages.py` 的 `infer_run` 中接入回調，每完成一張推論即 `emit(Event("image_stream", ...))`。
- 在 `app.py` 中新增 `/showcase` 端點，並支援直接讀取 `docs/results/` 成果圖。

### D. 現代化 Web 視覺駕駛艙 (`src/autocv/server/static/index.html`)
- 採用深色現代科技感設計（Inter + Fira Code 字體、毛玻璃卡片、發光按鈕）。
- **5 Subagent 狀態指示燈**：即時掌握當前執行階段。
- **訓練與驗證即時曲線**：Epoch / Loss / mAP@0.5 實時繪製。
- **即時非同步圖片串流 (Async Streaming Gallery)**：推論階段**完成一張即時呈現一張帶有 Bounding Box 的成果圖**。
- **一鍵 Showcase**：點擊「✨ 晶圓瑕疵 99.1% Showcase」可瞬間載入並演示已訓練好的 99.1% mAP 成果。

### E. 教學手冊與說明文檔
- 撰寫了大師級教學手冊 [`WALKTHROUGH.md`](WALKTHROUGH.md)。
- 更新了 [`README.md`](README.md) 與 [`CLAUDE.md`](CLAUDE.md)。

---

## 🎯 3. 接手後的下一步建議 (Next Steps for Claude Code)

當使用者要求繼續執行任務時，可直接進行以下操作：

1. **執行水族館 (Aquarium) 優化階梯實測**：
   ```bash
   # 1. 下載並切分水族館資料集 (需配置 ROBOFLOW_API_KEY)
   uv run autocv data -c configs/aquarium.yaml
   uv run autocv split -c configs/aquarium.yaml

   # 2. 執行 Baseline 訓練 (R0: aq-n-640)
   uv run autocv train -c configs/aquarium.yaml

   # 3. 升級模型訓練 (R1: aq-s-640)
   uv run autocv train -c configs/aquarium-s.yaml

   # 4. 產出階梯比較成績單
   uv run autocv report -c configs/aquarium.yaml
   ```

2. **啟動視覺駕駛艙進行演示**：
   ```bash
   uv run autocv ui --port 8787
   ```

3. **執行測試確保無 Regression**：
   ```bash
   uv run pytest
   ```
