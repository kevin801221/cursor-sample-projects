---
name: cv-dataset-qc
description: 處理 YOLO 資料集品管與切分時使用——執行或解讀 uv run autocv split 的輸出、驗證標註格式、判斷類別不平衡與空 label 警訊、規劃 train/val/test 切分、排查 data leakage。凡是「切資料」「檢查標註」「split 輸出怎麼看」「資料集有沒有問題」相關任務都載入本 skill。
---

# CV 資料品管與切分（autocv split）

指令：`uv run autocv split -c configs/aquarium.yaml`
程式碼：`src/autocv/split.py`；貫穿範例：aquarium（brad-dwyer/aquarium-combined v6，7 類、638 張、類別不平衡）。

## split 做了什麼（依 split.py 順序）

1. 掃描 `paths.raw`（aquarium 為 `data/raw/aquarium`）下的 `images/`+`labels/` 配對，含 Roboflow 預切分的 `train/`、`valid/`、`test/` 子目錄——**全部合併後重切**，不沿用原始切分
   - 找不到任何配對 → FileNotFoundError，先跑 `uv run autocv data -c configs/aquarium.yaml`
   - 圖片副檔名限 `.jpg .jpeg .png .bmp`
2. 逐行驗證每個 label 檔（`validate_label_file`）：
   - [ ] 每行恰好 5 欄（`class_id cx cy w h`）
   - [ ] 5 欄可解析為 int + 4 個 float
   - [ ] `class_id >= 0`
   - [ ] `cx cy w h` 全在 `[0, 1]`
   - [ ] label 檔存在（缺檔記一筆錯誤，該圖不進切分）
3. 中止規則：`異常行數 / bbox 總數 > 10%` → SystemExit，直接中止，不產出切分
4. 用 `dataset.seed`（aquarium 為 42）shuffle，依 `dataset.split`（`[0.7, 0.2, 0.1]`）切 train/val/test
5. 複製到 `paths.processed`（`data/processed/aquarium`）的 `images/{train,val,test}` 與 `labels/{train,val,test}`，寫出 `data.yaml`（path/train/val/test/nc/names）

seed 與比例都在 config 的 `dataset:` 區塊；`load_config` 會驗證 split 必須是 3 個和為 1 的比例。

## 輸出判讀（stdout 逐行）

| 輸出行 | 意義 | 檢查 |
|---|---|---|
| `圖片總數: N（來源目錄 K 組）` | 合併後總量；aquarium 應為 638 | K 應含 raw 的 train/valid/test（Roboflow 預切分） |
| `label 配對成功 / bbox 總數 / 空 label` | 空 label = 該圖 0 個 bbox（背景圖或漏標） | 空 label 比例異常高 → 先抽查是漏標還是刻意的負樣本 |
| `類別分佈: {id: count, ...}` | 各 class_id 的 bbox 數 dict | 對照 raw `data.yaml` 的 names 確認 id 對應；看不平衡程度 |
| `異常行數: X`（列前 5 筆） | 格式錯誤明細 | >0 就先看明細；>10% 會中止 |
| `train/val/test: N 張` | 實際切分張數 | 約 7:2:1 |

## 警訊清單（有一項就先停下處理，不要急著 train）

- [ ] **類別不平衡**：類別分佈中 最多實例數 / 最少實例數 > 10x → 稀有類的 metric 會很難看；aquarium 本身即不平衡，屬預期，但要在後續 report 時逐類別看，不能只看整體 mAP
- [ ] **空 label 過多**：空 label 佔比明顯偏高 → 抽 5–10 張人工目視，區分「真背景圖」vs「漏標」；漏標混入會壓低 recall
- [ ] **小物件比例高**：抽查 label 檔中 `w*h` 極小（例如 < 0.001）的 bbox 比例——split 不會自動報這項，要自己抓；小物件多 → 訓練時考慮加大 `train.imgsz`（aquarium config 用 640）
- [ ] **異常行數 > 0 但未達 10%**：不會中止，但錯誤行會被略過不計入 bbox——確認錯誤是否集中在特定來源目錄

## test set 紀律

- 切完後 `images/test` 不參與任何調參決策（挑 epoch、conf、超參一律看 val）；完整的 val/test 分工規則見 **cv-optimization-ladder**

## data leakage 常見來源

- **同一場景連拍**：水族館影片抽幀、連拍序列，幾乎相同的畫面被 random shuffle 散進 train 與 test → test 分數虛高。本 pipeline 是純隨機切分（seed shuffle），**不做 group-aware split**，此風險存在
  - 檢查法：對 test 裡分數特別高的圖，去 train 找檔名相近／畫面相似的鄰居
- **重複圖片**：合併 raw 下多個預切分目錄時，同名檔會自動加來源目錄前綴（`train_0.jpg`、`valid_0.jpg`）避免互相覆蓋；但「內容相同、檔名不同」的重複圖完全不會被偵測
- **改了 seed 或比例重切**：舊 run 的 test 圖可能落入新 train → 跨 seed 的 run 之間 metric 不可比；整個實驗階梯（aquarium.yaml R0 → aquarium-s.yaml R1）必須共用同一 `dataset.seed: 42` 與同一份 processed 切分

## 快速決策規則

- 異常行數 > 10% 中止 → 回 Roboflow 檢查匯出格式（config 的 `roboflow.format: yolov8`），不要手動修 label 硬闖
- 想換切分比例或 seed → 全部 run 作廢重跑，不能只重跑新 run
- 對照組實驗（如 R0 vs R1）改 config 時，`dataset:` 與 `paths:` 區塊必須完全相同，只動 `train:` 的單一變因（詳見 **cv-optimization-ladder**）
