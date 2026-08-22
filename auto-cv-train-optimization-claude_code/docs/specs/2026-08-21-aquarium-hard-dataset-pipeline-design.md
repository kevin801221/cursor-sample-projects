# 設計文件：真實訓練較難資料集 + 流程強化 + 正式 Cursor Skills

日期：2026-08-21 ｜ 作者：kevin（AI 協作起草）｜ 狀態：自主模式執行，供事後審閱

## 背景與目標

Project 13 現況：wafer 資料集 mAP@0.5 已飽和（99.1%），教學上「優化空間」只能用嘴講；
`infer` 只輸出兩個總體 mAP 數字，沒有 per-class AP、confusion matrix、PR curve、
訓練曲線與跑次比較；`.cursor/skills/` 不存在。

本次三個目標：

1. **真的訓練一個較難的資料集**：Roboflow `brad-dwyer/aquarium-combined` v6
   （7 類水下生物、638 張、小物件 + 類別不平衡；yolov8n 典型 mAP@0.5 ≈ 0.7x，
   優化空間真實存在）。在本機 M4 Max（MPS）跑真實的優化階梯（≥3 個 run）。
2. **強化 pipeline**：新增 `autocv report`（評估 + metric 視覺化 + Markdown 報告）、
   修正 split 丟棄預切分資料的 bug、train run 可命名以支援階梯比較。
3. **正式 Cursor Skills**：`.cursor/skills/` 下 6 個 SKILL.md，覆蓋資料蒐集 →
   資料品管 → 訓練 → 超參 → 指標視覺化 → 優化階梯方法論。

## 考慮過的方案

- **資料集**：VisDrone（太大，單 run 數小時）、african-wildlife（需新增
  ultralytics 資料來源，且難度中等）、**Aquarium（採用：走既有 Roboflow 路徑、
  規模適中、難度真實、視覺上適合教學）**。
- **視覺化**：互動 HTML dashboard（超出需求、駕駛艙已有即時視圖）vs
  **matplotlib 靜態 PNG + report.md（採用：可進 git、可進投影片、零新依賴）**。
- **報告指標來源**：只評 test（學生看不到 val/test 差異）vs **val + test 都評
  （採用：直接教「val 調參、test 報成績」）**。

## 變更清單

### A. Pipeline（`src/autocv/`）

1. `config.py`：`TrainCfg` 加 `name: str = "train"`（run 目錄名，階梯比較用）。
2. `train.py`：`name="train"` → `name=cfg.train.name`。
3. `split.py`：`_find_src` → 掃 `raw/`、`raw/train|valid|test/` 全部 images/labels
   配對後合併再切分（修正：原本只吃 `train/`，Roboflow 預切分的 valid/test 被丟棄）。
4. 新增 `report.py` + CLI `autocv report`：
   - 掃 `runs/*/weights/best.pt`，缺 `metrics.json` 的 run 跑 `model.val`
     （val + test 各一次），存總體 + per-class 指標（快取，重跑不重評）。
   - 產出 `runs/report/`：
     - `training_curves.png`：各 run 的 mAP@0.5:0.95 與 box loss 對 epoch（疊圖）
     - `ladder.png`：各 run 的 mAP@0.5 / mAP@0.5:0.95 分組長條（test）
     - `per_class_ap.png`：最佳 run 的 per-class AP 分組長條（test）
     - `dataset_stats.png`：類別實例分佈 + bbox 面積直方圖（train split）
     - 從 val 輸出複製 confusion matrix / PR curve
     - `report.md`：階梯表（val/test 並列）+ per-class 表 + 圖 + 判讀說明
   - 色盤：dataviz 已驗證分類色盤固定順序（#2a78d6/#eb6834/#1baf7a/#eda100），
     每圖 ≤4 series、單軸、直接標籤。
5. `cli.py`：註冊 `report`；`all` 一條龍尾端接 report。

### B. 真實訓練（優化階梯）

| Run | config | 變因 | 預估 |
|---|---|---|---|
| R0 `aq-n-640` | configs/aquarium.yaml | yolov8n, 640px, 60ep, b16 | ~15 分 |
| R1 `aq-s-640` | configs/aquarium-s.yaml | 模型 n→s（一次一變因） | ~35 分 |
| R2 `aq-s-800` | configs/aquarium-s800.yaml | 解析度 640→800, b8 | ~55 分 |

`optimize`（演化搜尋）不在本次執行範圍（20 輪 × 短訓 > 2 小時），階梯已足夠
展示方法論；skills 會教何時值得跑。

### C. Cursor Skills（`.cursor/skills/<name>/SKILL.md`，繁中，frontmatter 同
`project-subagent-hooks` 前例）

| Skill | 覆蓋 |
|---|---|
| `cv-data-collection` | Roboflow Universe 挑選準則、config 填法、下載後驗證 |
| `cv-dataset-qc` | 標註驗證判讀、切分、class imbalance / 小物件警訊、leakage |
| `cv-training` | 模型/解析度/batch/epochs 決策、MPS 注意、過擬合判讀 |
| `cv-hyperparameter-tuning` | 何時值得 tune、iterations/epochs 取捨、結果套用 |
| `cv-metrics-viz` | autocv report、mAP50 vs mAP50-95、PR/confusion 判讀、per-class 找弱點 |
| `cv-optimization-ladder` | 一次一變因、run 命名、階梯表維護、何時停 |

### D. 文件

- project-13 `README.md` / `walkthrough.md` / `demo.sh`：換上 aquarium 真實數字、
  新增 skills 章節與 `autocv report` 用法。
- companion `README.md` / `CLAUDE.md`：pipeline 圖加 report、規則加 skills。

## 測試

- 既有 23 個測試不得紅。
- 新增：config `train.name`、split 多來源目錄合併、report 純函式
  （results.csv 解析、階梯表 Markdown 渲染、labels 統計）——不依賴
  ultralytics 重載。

## 驗收

1. `pytest` 全綠、`ruff check` 乾淨。
2. `runs/` 有 ≥3 個真實訓練 run，`runs/report/report.md` 有真實階梯表與全部圖。
3. `.cursor/skills/` 6 個 SKILL.md 齊備。
4. 教學文件數字與真實結果一致（不再有虛構的 99.1%→demo 腳本假數字）。
