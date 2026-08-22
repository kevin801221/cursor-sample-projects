---
name: cv-data-collection
description: 為 autocv pipeline 挑選與下載 CV 資料集時使用：在 Roboflow Universe 選資料集、把 workspace/project/version 填進 config、設定 ROBOFLOW_API_KEY、執行 uv run autocv data 並驗證下載結果、或要換新資料集時載入。
---

# CV 資料蒐集檢查清單（Roboflow Universe → autocv）

貫穿範例：aquarium（`brad-dwyer/aquarium-combined` v6，7 類、638 張、類別不平衡）。

## 1. 在 Roboflow Universe 挑資料集

逐項檢查，任一項不過就換資料集：

- [ ] **標註品質抽查**：隨機開 10~20 張圖，看 bbox 是否貼合、有無漏標／錯類。抽查發現 >10% 有問題就放棄（pipeline 的 `split` 步驟也會在格式錯誤比例 >10% 時中止）
- [ ] **授權**：確認 License 允許你的用途（aquarium 是 CC BY 4.0）。找不到授權聲明 = 不用
- [ ] **規模**：小模型（yolov8n/s）練習與 demo，數百張可行（aquarium 638 張）；正式應用建議每類至少數百個 bbox
- [ ] **類別定義清晰度**：類別名稱是否互斥、無語意重疊（例如同時有 "fish" 和 "goldfish" 就要小心）；aquarium 的 7 類（fish/jellyfish/penguin/puffin/shark/starfish/stingray）定義清楚
- [ ] **類別平衡**：看 Universe 頁面的 class 分佈；不平衡（如 aquarium 的 fish 遠多於 stingray）不是否決條件，但要記下來，後續看 per-class 指標時會用到
- [ ] **格式**：確認提供 YOLOv8 匯出格式（config 的 `roboflow.format: yolov8`）

## 2. 把 Universe 頁面填進 config

Universe 資料集網址即包含所有欄位：

```
https://universe.roboflow.com/<workspace>/<project>/dataset/<version>
https://universe.roboflow.com/brad-dwyer/aquarium-combined/dataset/6
```

對照 `configs/aquarium.yaml` 的寫法：

```yaml
roboflow:
  workspace: brad-dwyer        # 網址第 1 段
  project: aquarium-combined   # 網址第 2 段
  version: 6                   # 網址 dataset/ 後的數字（int，不加引號）
  format: yolov8               # 固定用 yolov8
  api_key_env: ROBOFLOW_API_KEY
```

決策規則：

- **換資料集 = 新增一個 config，不改程式碼**。複製 `configs/template.yaml` 或 `configs/aquarium.yaml` 改欄位即可
- **每個資料集用獨立的 paths 子目錄**，避免 `data` 下載（`overwrite=True`）與 `split` 輸出互相覆蓋：

```yaml
paths:
  raw: data/raw/aquarium            # 每個資料集一個子目錄
  processed: data/processed/aquarium
  runs: runs                        # runs 可共用，靠 train.name 區分
```

- 同一資料集的多個實驗階梯（如 `aquarium.yaml` / `aquarium-s.yaml`）：`roboflow` 與 `paths` 完全相同，只改 `train` 區塊，資料只下載一次

## 3. API Key（.env）

- [ ] `cp .env.example .env`，填入 `ROBOFLOW_API_KEY=<你的 key>`（從 https://app.roboflow.com/settings/api 取得）
- [ ] `.env` 放 repo 根目錄（`data` 步驟用 `load_dotenv(root / ".env")` 讀取，root 是執行時的 cwd，所以指令要在 repo 根目錄下執行）
- [ ] key 只放 `.env`，不寫進 config；config 只放環境變數名 `api_key_env: ROBOFLOW_API_KEY`
- 看到錯誤「ROBOFLOW_API_KEY 未設定」→ 就是 `.env` 缺檔或沒填值

## 4. 下載與驗證

```bash
uv run autocv data -c configs/aquarium.yaml
```

成功會印出 `DOWNLOAD_OK: <路徑>`。接著逐項驗證：

- [ ] `data/raw/aquarium/` 下有 `train/`、`valid/`、`test/` 子目錄，各含 `images/` 與 `labels/`
- [ ] `data/raw/aquarium/data.yaml` 存在，且：
  - `nc` 等於 Universe 頁面的類別數（aquarium 為 `nc: 7`）
  - `names` 清單與預期類別一致、順序合理
- [ ] 圖片張數合理：`find data/raw/aquarium -name '*.jpg' | wc -l` 對照 Universe 頁面標示的張數（aquarium ≈ 638）
- [ ] 抽開 2~3 個 `labels/*.txt`：每行 5 欄（class_id cx cy w h），座標在 [0,1]

驗證通過才往下跑：

```bash
uv run autocv split -c configs/aquarium.yaml
```

`split` 會合併 Roboflow 預切分的 train/valid/test、依 `dataset.split`（預設 [0.7, 0.2, 0.1]）與 `dataset.seed` 重切到 `paths.processed`，並印出圖片總數、bbox 總數、類別分佈——在這裡再次確認類別不平衡的實際數字。

## 5. 常見錯誤對照

| 症狀 | 原因 | 處理 |
|---|---|---|
| 「ROBOFLOW_API_KEY 未設定」 | `.env` 缺檔或空值 | 見第 3 節 |
| split 報「找不到 images/ 與 labels/」 | 還沒跑 `data`，或 config 的 `paths.raw` 指錯目錄 | 先 `uv run autocv data`，確認 raw 路徑 |
| `data.yaml` 的 nc/names 與預期不符 | Universe 上選錯 version | 回頭核對網址的 `dataset/<version>` |
| 換資料集後舊資料不見 | 兩個 config 共用同一個 `paths.raw`（下載是 overwrite） | 每個資料集獨立子目錄，見第 2 節 |
