---
name: cv-hyperparameter-tuning
description: 使用者想跑超參搜尋（autocv optimize / hyperparameter tuning / model.tune）、在猶豫要不要調參、或問「還能不能再擠一點 mAP」時載入。涵蓋何時值得跑、成本估算、optimize.iterations/epochs 取捨、best_hyperparameters.yaml 如何用回正式訓練。
---

# CV 超參搜尋（uv run autocv optimize）

底層是 ultralytics 的演化式 tuner（`model.tune()`，見 `src/autocv/optimize.py`）：
每個 iteration 都是一次完整短訓，用突變後的超參跑 `optimize.epochs` 輪，以 val 分數演化下一代。

## 決策規則：現在該不該跑 optimize？

先全部打勾才准跑，任何一項不成立就先去做那件事：

- [ ] baseline 已跑通：`uv run autocv train -c configs/aquarium.yaml` 完整走完、`runs/aq-n-640/` 有結果
- [ ] 資料品質問題已處理完（錯標、漏標、類別不平衡的取捨已有結論）——**先修資料永遠比調參划算**
- [ ] 階梯上的手動變因都爬完了（模型尺寸 n→s、imgsz、epochs……如 `configs/aquarium.yaml` R0 → `configs/aquarium-s.yaml` R1 一次只動一個變因）
- [ ] 目標明確：只期待再擠 1~3 pp，不是指望調參救一個爛 baseline
- [ ] 成本可接受（見下方估算）——資料集小（如 aquarium 638 張）、單輪短訓便宜時最划算

不值得跑的典型訊號：
- baseline 還沒跑通或 mAP 明顯異常 → 先 debug pipeline
- 混淆矩陣顯示某類別幾乎全漏（如 aquarium 的稀有類）→ 先處理資料／類別不平衡
- 手動階梯還有便宜的變因沒試（換 s 模型往往比 8 輪 tune 更快拿到更多 pp）

## 成本估算（動手前必算）

總時間 ≈ `optimize.iterations` × 單輪短訓時間。

- 單輪短訓時間：拿 baseline 訓練的實際耗時，按 epochs 比例換算
  （例：60 epochs 花 T 分鐘 → 10 epochs 約 T/6 分鐘）
- aquarium 例：`iterations: 8` × 10-epoch 短訓 ≈ 8 個短訓的時間，跑之前心裡要有數
- 指令本身也會印預估並要求確認；batch 跑用 `--yes`/`-y` 跳過確認

## config 欄位（`optimize:` 區塊，見 src/autocv/config.py）

```yaml
optimize:
  iterations: 8   # 演化代數 = 短訓次數（預設 20）
  epochs: 10      # 每次短訓的 epochs（預設 15）
```

取捨規則：
- `epochs` 是**代理指標**：用 10 epochs 的 val 分數猜 60 epochs 的排名，本質有風險——
  短訓贏家不保證長訓也贏（學習率/增強類超參尤其會翻盤）
- `epochs` 太小（<10）→ 排名噪音大，搜到的超參不可信
- `epochs` 太大 → 成本線性爆炸；預算固定時，優先給 `iterations`（演化要夠多代才有用）
- `imgsz`、`batch`、起始 model 沿用 `train:` 區塊——tune 條件要跟正式訓練一致，代理才準

## 執行步驟

1. 前置：`data/processed/aquarium/data.yaml` 必須存在，否則會被擋下並提示先跑
   `uv run autocv split -c configs/aquarium.yaml`
2. 跑搜尋：
   ```bash
   uv run autocv optimize -c configs/aquarium.yaml
   ```
3. 或一條龍以 optimize 取代 train：
   ```bash
   uv run autocv all -c configs/aquarium.yaml --optimize --yes
   ```
4. 結果在 `runs/tune/`，最佳超參 → `runs/tune/best_hyperparameters.yaml`
   （注意：name 固定 `tune` 且 `exist_ok=True`，重跑會寫進同一個目錄）

## 把結果用回正式訓練

- `uv run autocv train` **不會**自動讀 `best_hyperparameters.yaml`（train.py 只傳
  data/epochs/batch/imgsz/device）——結果要手動接回去
- 手動接法：用 ultralytics 直接以 tune 出的超參跑完整訓練，例如
  ```bash
  uv run yolo detect train data=data/processed/aquarium/data.yaml \
    model=yolov8n.pt epochs=60 imgsz=640 batch=16 \
    cfg=runs/tune/best_hyperparameters.yaml project=runs name=aq-n-640-tuned
  ```
- 驗收：tuned 完整訓練 vs 原 baseline，比 val mAP；沒贏就回退，別戀戰

## 評估紀律

- [ ] 挑超參只看 **val**，test 不參與（完整 val/test 分工見 **cv-optimization-ladder**）
- [ ] tuned run 與 baseline 用同一份 split（`dataset.seed: 42` 不動）才可比
- [ ] 不要拿 tune 過程中短訓的分數當成果宣稱——那是 10-epoch 代理，正式數字以完整訓練為準
