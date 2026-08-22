---
name: cv-metrics-viz
description: 判讀 YOLO 訓練成果時載入——使用者要跑 uv run autocv report、解讀 mAP/precision/recall/per-class AP、看 confusion matrix 或 PR curve、比較多個 run 的階梯表、找弱點類別決定下一步優化方向時使用。
---

# CV 評估指標與視覺化判讀

貫穿範例：aquarium（brad-dwyer/aquarium-combined v6，7 類、638 張、類別不平衡）。
指令一律：`uv run autocv report -c configs/aquarium.yaml`。

## report 產出物（位置與來源）

- `runs/<run-name>/metrics.json`：每個 run 的 val+test 評估快取。`best.pt` 比它新時會自動重評；其餘情況（如換了 processed 資料）想強制重評就刪掉它
- 只有與當前 config 同一份 `data.yaml` 訓出的 run 會進報告；`tune*` 超參試驗一律排除
- `runs/report/` 下：
  - `training_curves.png`：各 run 的 val mAP@0.5:0.95 與 train box loss 逐 epoch 曲線（讀 `runs/<run>/results.csv`）
  - `ladder.png`：各 run 在 test set 的 mAP@0.5 / mAP@0.5:0.95 並排長條
  - `per_class_ap.png`：**只畫最佳 run**（test mAP@0.5:0.95 最高者）的逐類 AP
  - `dataset_stats.png`：train split 的類別實例數 + bbox 面積比例直方圖
  - `confusion_matrix_normalized.png`、`BoxPR_curve.png`：從 `runs/report/eval/<best-run>-test/` 複製來（ultralytics `plots=True` 產出）
  - `report.md`：階梯表 + 以上所有圖
- run 的先後順序 = `weights/best.pt` 的 mtime 排序，就是階梯順序；階梯表的 Δ test 是相鄰 run 的 test mAP@0.5:0.95 差
- 前置條件：`data/processed/aquarium/data.yaml` 存在（先跑 `uv run autocv split -c configs/aquarium.yaml`）、`runs/` 下至少一個 `best.pt`

## 指標判讀決策規則

### mAP@0.5 vs mAP@0.5:0.95
- [ ] 兩個都看，別只報 mAP@0.5。mAP@0.5 只要求框跟 GT 重疊 50% 就算對，太寬鬆
- [ ] mAP@0.5 高、mAP@0.5:0.95 明顯偏低 → 模型「找得到但框不準」，定位精度差。**指標太寬鬆會掩蓋優化空間**：只看 mAP@0.5 會誤判已經沒得優化
- [ ] 定位不準的第一手段：加大 `train.imgsz`（aquarium 階梯的 R2 = `aquarium-s800.yaml` 就是 640→800 這一階）；小物件多時（看 dataset_stats 的 bbox 面積直方圖左偏）尤其有效
- [ ] 對外報成績、跨 run 比較，一律以 test mAP@0.5:0.95 為準（report 選最佳 run 也是用它）

### precision / recall 與 conf 門檻
- [ ] metrics.json 裡的 precision/recall 是**單一 conf 工作點**的值，不是全貌；全貌看 BoxPR_curve.png
- [ ] 誤檢多（precision 低）→ 調高 `infer.conf`（config 的 `infer:` 區塊，預設 0.25）；漏檢多（recall 低）→ 調低
- [ ] 調 conf 屬於調參，**只准看 val**；改完 config 後跑 `uv run autocv infer -c configs/aquarium.yaml` 看 `runs/infer/pred_*.png` 實際框圖驗證
- [ ] conf 調整不改變模型好壞，只是在 PR curve 上移動工作點——curve 本身太低就得回去改訓練

### per-class AP → 找弱點類別
- [ ] 在 report.md 的 per-class 表找 AP 最低的類別，優先處理墊底 1–2 類
- [ ] 對照 dataset_stats.png：弱類別實例數是不是也墊底？aquarium 類別不平衡，弱類別多半是資料太少 → 補資料（回 Roboflow 加圖）或加增強
- [ ] 實例數不少但 AP 低 → 看 confusion matrix 是不是被混淆，或 bbox 太小 → 加大 imgsz
- [ ] 注意 per_class_ap.png 只反映最佳 run；比較不同 run 的逐類表現要各自看 `runs/<run>/metrics.json` 的 `per_class` 欄位

### confusion matrix（normalized）
- [ ] 對角線 = 該類被正確分類的比例；找對角線最暗的類別
- [ ] 非對角線亮格 = 哪兩類互相混淆（aquarium 常見於外形相近的水生類別）→ 對策是補這兩類的對比樣本，不是無腦加 epoch
- [ ] `background` 列：某類被漏檢當成背景（漏檢）；`background` 欄：背景被誤報成該類（背景誤檢）——兩者對策不同：前者補資料/降 conf，後者升 conf/補負樣本

### PR curve（BoxPR_curve.png）
- [ ] curve 越貼右上角越好；曲線下面積即 AP
- [ ] 早段（高 conf）precision 就掉 → 模型連高信心預測都會錯，訓練有根本問題
- [ ] 尾段 recall 上不去 → 有一群物件永遠偵測不到，通常是小物件或稀有類別
- [ ] 逐類 curve 分岔大 = 類別不平衡的直接證據，回去看 per-class AP 與 dataset_stats

## val / test 並列的紀律

- [ ] 階梯表 val/test 並列：調參決策（挑 conf、比較增強、選 epoch）只准引用 val 欄，test 欄只報成績——完整分工與一次一變因的階梯規則見 **cv-optimization-ladder**
- [ ] val 高、test 明顯低 → 對 val 過擬合（調參調過頭）或切分不乾淨；檢查 `dataset.seed`（aquarium 固定 42）沒被動過

## 常用流程

```bash
uv run autocv report -c configs/aquarium.yaml    # 評估所有 run + 出圖 + report.md
uv run autocv infer  -c configs/aquarium.yaml    # 抽樣推論框圖 → runs/infer/
uv run autocv report -c configs/aquarium-s.yaml  # 新階（R1）訓完後重跑，舊 run 走快取
```

判讀順序：ladder（哪一階有效）→ training_curves（有沒有收斂/過擬合）→ per-class AP（弱點在哪）→ confusion matrix + PR curve（弱在哪一種錯誤）→ dataset_stats（回到資料面找原因）。
