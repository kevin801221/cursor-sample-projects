---
name: cv-training
description: 要跑 uv run autocv train、修改 configs/*.yaml 的 train 區塊（model/imgsz/batch/epochs/name/device）、規劃模型階梯實驗（n→s→m）、或判讀訓練曲線是否過擬合時載入。提供訓練前的決策樹與檢查清單。
---

# cv-training：autocv 訓練決策

適用專案：`uv run autocv train -c configs/<name>.yaml`（train 邏輯在 `src/autocv/train.py`，config 結構在 `src/autocv/config.py` 的 `TrainCfg`）。
貫穿範例：aquarium（Roboflow `brad-dwyer/aquarium-combined` v6，7 類、638 張、類別不平衡）→ `configs/aquarium.yaml`（R0）與 `configs/aquarium-s.yaml`（R1）。

## 訓練前決策樹（依序回答，答案直接寫進 config 的 train 區塊）

### 1. model — 先跑通再加大
- [ ] 第一輪一律 `yolov8n.pt`：先驗證 pipeline 全通、拿到基準線（aquarium R0 = `aquarium.yaml`）
- [ ] 基準線出來後才升 `yolov8s.pt` / `yolov8m.pt`，且**一次只動這一個變因**（R1 = `aquarium-s.yaml`，只有 model 從 n 換 s，其餘全同）
- [ ] 不要跳過 n 直接上 m：沒有基準線就無法歸因「變好是因為模型大，還是別的」

### 2. imgsz — 看物件大小決定
- [ ] 預設值 416（`TrainCfg` 預設），一般資料集夠用
- [ ] 小物件多（如 aquarium 的遠處小魚）→ 提高到 640；仍抓不到再考慮 800
- [ ] imgsz 提高 = 記憶體與時間都變貴，必須連動調 batch（見下）

### 3. batch — MPS 記憶體經驗值
- [ ] imgsz 640 → batch 16（aquarium 兩個 config 都是這組）
- [ ] imgsz 800 → batch 8
- [ ] 訓練中途 OOM / 系統卡死 → batch 砍半重跑，不要先動 imgsz
- [ ] CUDA 卡記憶體較大時可再放大，但同一組階梯實驗內 batch 保持一致

### 4. epochs — 60 起跳，看曲線再加
- [ ] 起手 60（aquarium 兩個 config 均為 60；`TrainCfg` 預設 50 偏保守）
- [ ] 訓練完看 `runs/<name>/results.csv` 曲線：val mAP 還在爬 → 加 epochs 續跑；早已平掉 → 不必加
- [ ] 不要一開始就設 300「以防萬一」：先短跑驗證方向，時間留給階梯比較

### 5. name — 一定要取有意義的名字
- [ ] 格式建議 `<資料集縮寫>-<模型>-<imgsz>`，如 `aq-n-640`、`aq-s-640`
- [ ] **禁用預設名 `train`**：`train.py` 用 `exist_ok=True`，同名 run 會互相覆蓋，階梯比較（`uv run autocv report -c ...`）就做不了
- [ ] 換任何一個變因（model/imgsz/epochs）→ 換新 name，舊 run 保留當對照組

### 6. device — 通常不用動
- [ ] 留 `auto`：`src/autocv/device.py` 的 `pick_device` 依 mps → cuda → cpu 順序挑，選到 mps 時自動設 `PYTORCH_ENABLE_MPS_FALLBACK=1`
- [ ] 填非 auto 值（如 `cpu`）會原樣使用、不做可用性檢查——只在除錯（懷疑 MPS 數值問題）時才手動指定

## 執行檢查清單

- [ ] 先確認 `data/processed/<dataset>/data.yaml` 存在；沒有就先跑
      `uv run autocv split -c configs/aquarium.yaml`（train.py 找不到 data.yaml 會直接退出）
- [ ] 跑 `uv run autocv train -c configs/aquarium.yaml`，**先看預估輸出再按確認**：
      train 圖片數、epochs/batch/device、預估時間、輸出目錄 `runs/<name>/`
- [ ] 預估時間的意義是電費與時間的安全邊界：預估遠超預期（打錯 epochs、batch 太小）就 Abort 改 config
- [ ] `--yes` 只在使用者**明確授權**跳過確認時用（如排程跑整條 `uv run autocv all -c ... --yes`）；agent 不得自行加 `--yes`
- [ ] 訓練完成輸出 `runs/<name>/weights/best.pt`，後續 `uv run autocv infer -c ...` 與 `uv run autocv report -c ...` 都吃它

## 過擬合判讀（訓練後看 runs/<name>/results.csv）

| 現象 | 判定 | 動作 |
|---|---|---|
| train box_loss 持續降、val mAP 同步升 | 正常 | epochs 可再加 |
| train box_loss 持續降、val mAP 停滯 | 開始過擬合 | 停在此 epochs；取 best.pt 即可（best 已是 val 最佳） |
| train box_loss 持續降、val mAP 反轉下降 | 明顯過擬合 | 減 epochs 或加資料/增強；小資料集（638 張）本來就容易發生 |
| train/val 都爛 | 欠擬合或資料問題 | 先查 split 與標註，再考慮升 model 或 imgsz |

## 階梯實驗

- 鐵律：一次只動一個變因、`train.name` 必換、`dataset:`/`paths:` 不動
- 加開下一階（n→s、imgsz、optimize）的完整流程與檢查清單見 **cv-optimization-ladder**；跑完後判讀 report 指標（含 per-class）見 **cv-metrics-viz**
