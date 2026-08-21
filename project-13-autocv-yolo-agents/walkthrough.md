# Walkthrough：在 Cursor 上把五個 AI 團隊一步一步調度出來

> 這份文件帶你做出一件事：**說一句話，5 個 AI agent 自動分工訓練電腦視覺模型**。過程中你會學會如何科學地優化——不是盲目調參、而是一次只動一個變因、用嚴格指標衡量。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先做這七件事，動手當天才不會卡）

1. **環境打好**：`uv venv --python 3.11 && uv pip install -e .` 跑一遍，確保沒有缺依賴。
2. **`.env.example` 複製成 `.env`、填 Roboflow API key**（[帳號設定 → Copy API key](https://roboflow.com/account)）。
3. **完整跑一遍 baseline**：`uv run autocv all -c configs/wafer.yaml --yes`，讓訓練、推論、UI 都驗證過。wafer 資料集大約 100 MB、訓練 5–10 分鐘，第一次跑要 20+ 分鐘先提早跑。
4. **存備援成果**：把 `runs/infer/summary.md` 與幾張 `pred_*.png` 存起來，萬一網路或 GPU 出問題可備用。
5. **試跑 Claude Code 對話版**：在 Cursor 裡對 Agent 說「幫我用 wafer.yaml 下載並訓練」，確認五個 agent 都能接力。
6. **UI 駕駛艙試跑一遍**：`uv run autocv ui`，選 config、按 Run，看 5 階段燈號、訓練曲線有沒有動起來。
7. **預讀優化階梯**（本文件 E2 節），心裡過一遍預期會發生什麼。

---

## 🗺️ 學習地圖（建議 5.5 小時充實版）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 角色介紹 | 30 分 | 閱讀理解（這是全課靈魂，慢慢看、留問題空間） |
| 環境 + 指令速查 | 15 分 | 動手做 |
| 🌊 第一波：baseline（data → split → train → infer） | 1.5 小時 | 動手做 |
| ☝️ 中場檢查：指標覺察（mAP@0.5 vs 0.5:0.95） | 20 分 | 閱讀理解 |
| ⛰️ 第二波：優化階梯（R1–R5） | 2 小時 | 動手做 |
| 難資料集挑戰 | 30 分 | 動手做 |
| 收尾與內化 | 30 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `./auto-cv-train-optimization-claude_code/`，遙控器是 `./demo.sh`（位於 `project-13-autocv-yolo-agents/` 根目錄）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 支援 5 個 Agent 接力工作流與優化階梯演練。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd auto-cv-train-optimization-claude_code && uv sync` | 同步虛擬環境與 YOLO/PyTorch 依賴 |
| 2 | 跑一次 `./demo.sh 3` | 確認 5 Agent 模擬流程與輸出日誌正常 |
| 3 | 檢查備援成果 | 確認 `runs/infer/summary.md` 與標註預覽圖片完整 |

### 放映時間軸

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:30 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §角色介紹 | 培訓檢測員比喻、5 個 Agent 角色卡、mAP 指標意義 | 多 Agent 分工與科學優化哲學 |
| 0:30–0:45 | 第 1 幕：5 Agent 分工 | `./demo.sh 1` | `auto-cv-.../CLAUDE.md` | DataPrep、Splitter、Trainer、Evaluator、Optimizer 職責 | 打一句話讓 agents 接力訓練模型 |
| 0:45–1:15 | 第 2 幕：資料集與配置 | `./demo.sh 2` | `auto-cv-.../configs/wafer.yaml` | 晶圓瑕疵資料集規格、解析度、Batch Size 與模型架構 | 配置檔先行，鎖定實驗基準線 |
| 1:15–2:45 | 第 3 幕：5 Agent 接力訓練 ⭐ | `./demo.sh 3` | `auto-cv-.../src/` | 5 階段流水線日誌：抽取 → 切分 → 訓練 → 評估 → 優化 | 流水線作業：每個 Agent 的輸出是下一個的輸入 |
| 2:45–4:45 | 第 4 幕：優化階梯 (R1–R5) ⭐ | `./demo.sh 4` | `walkthrough.md` §E2 優化階梯 | mAP 演進表：Baseline 0.842 → R1 0.871 → R2 0.895 → R3 0.923 | 一次只動一個變因，科學推升 mAP |
| 4:45–5:30 | 第 5 幕：AutoCV 駕駛艙 UI | `./demo.sh 5` | `auto-cv-.../ROADMAP.md` | 視覺化駕駛艙儀表板與紅框標註結果 | 完整電腦視覺模型落地體驗 |

---

## 🎬 開場故事：培訓一位新瑕疵檢測員

今天我們不是『訓練模型』，是『培訓一位新員工』。想像你開一家瑕疵檢測廠，要教一位沒經驗的新人快速上手。

首先，你要給他看**一大批考古題**——以前已經被驗收過、畫好紅框的瑕疵圖片。新人看一遍遍、一次次練習，漸漸學會『瑕疵長什麼樣、在哪個位置』。

但你不能給他看**所有**考古題。為什麼？因為他會背下來、到考試時遇到新題目就傻眼。所以你要分三組：
- **練習題**（70%）：讓他練習、做錯沒關係、改正再來
- **模擬考**（20%）：平時測試他練到哪裡了
- **大考**（10%）：最後驗收成績，**題目絕對不能提前看過**

訓練過程中，他『看一遍考古題』叫一個 epoch。『提高題目清晰度』對應提高圖片解析度。『換更聰慧的教練』對應換更大的模型。『改複習節奏』對應調學習率、batch 大小。

**最後的成績單叫 mAP。** 100 分制，0–100。要拿到好成績，一靠教材品質（資料集），二靠訓練方法（超參數），三靠有沒有過度記憶（overfitting）。

好消息是：我們有五位職員幫你自動化整個過程。你只要告訴他們『要訓練哪個資料集』，他們自動分工。下面我介紹每一位。

這個比喻會貫穿全課。先記住對照表：

| 新人訓練 | 模型訓練 | 5 agents | 我們用的技術 |
|---|---|---|---|
| 從書店買考古題 | 從 Roboflow 抓圖 | data-hunter 🔴 | `autocv data` |
| 檢查考題有沒有印錯、分成 3 組 | 驗證標註、切 train/val/test | bbox-labeler 🟡 | `autocv split` |
| 教練教新人讀題、練習 | 訓練模型、學認瑕疵 | training-runner 🔵 | `autocv train` |
| 試驗哪種複習節奏最有效 | 調超參數、找最佳學習率 | hp-optimizer 🟣 | `autocv optimize` |
| 大考、打分數、公布成績 | 推論、畫框、算 mAP | inference-runner 🟢 | `autocv infer` |

五個人、五種顏色、五個指令。你就像坐在老闆辦公室，五位職員接力幫你調度。命令怎麼下？兩種方式：

1. **CLI**：打字下指令。『data-hunter，去下載』→ `autocv data`
2. **Claude Code 對話**：說人話。『幫我下載並訓練』→ 五個人自動接力，你看著他們手交手的全過程。

這份文件用第二種，因為最炫、最能看出『接力』的感覺。

---

## 0. 開始前準備

動手前確認你的機器上有：
- 🐍 Python 3.11+（`python --version`）
- 🎒 uv 已裝（`uv --version`）
- 📁 clone 好專案 `auto-cv-train-optimization-claude_code`
- ✅ 跑過 `uv pip install -e .`
- 🔑 `.env` 填好 `ROBOFLOW_API_KEY`（`cp .env.example .env` 後到 Roboflow 複製 key）

> 🔍 **名詞卡：Roboflow**
> 白話：一個「圖片資料集的雲端超市」。開發者把訓練用的圖片 + 框框標註上傳到上面，別人可以下載。像 GitHub 是程式碼超市、Roboflow 就是標註圖片超市。我們今天用它的免費資料集 wafer（晶圓瑕疵檢測）。
>
> 🔍 **名詞卡：YAML**
> 白話：一種設定檔格式（不是程式碼），用 `key: value` 寫配置。比 JSON 容易讀、不用打引號和逗號。
>
> 🔍 **名詞卡：uv**
> 白話：Python 的「套件安裝員」（取代 pip）。速度快、鎖版本更嚴格、不會出現「在別人電腦跑但我這爆」的魔幻狀況。

---

## 1. 核心概念：電腦視覺 × 物件偵測 × YOLO

訓練前，先講我們在訓練什麼。

> 🔍 **名詞卡：電腦視覺（Computer Vision）**
> 白話：教電腦『看』圖片、理解圖片內容。人看到照片 0.5 秒就知道「這是狗」，電腦需要 AI 教它怎麼看。
>
> 🔍 **名詞卡：物件偵測（Object Detection）vs 影像分類（Image Classification）**
> 白話：
> - 分類：「這張照片裡是狗還是貓？」（一張圖一個標籤）
> - 偵測：「這張照片裡**哪裡有**狗、**哪裡有**貓？」（一張圖多個框框 + 每個框指出「狗」或「貓」）
>
> 比喻：分類是「測驗題『選擇』」，偵測是「在試卷上『圈出』所有的錯字並標註錯誤理由」。我們今天做偵測。
>
> 🔍 **名詞卡：YOLO（You Only Look Once）**
> 白話：一種物件偵測模型，名字超酷——「一眼看完」。就一看這張圖，所有框框位置和類別都出來了，速度快、適合實時應用（監視器、自駕車、工廠檢測）。最新版叫 YOLOv8。
>
> 🔍 **名詞卡：Bounding box（框框）**
> 白話：圖片上用矩形框出「瑕疵位置」。框就是左上角座標 + 右下角座標，或者中心座標 + 寬高。

**目標**：訓練一個 YOLO 模型，能在晶圓圖上自動找出瑕疵的位置。

> ❓ **想一想**：如果我只訓練分類模型（『有瑕疵』或『沒瑕疵』），工廠品管員怎麼知道瑕疵在哪？
>
> **答案**：看不到瑕疵位置、也沒法焦點檢修。所以一定要偵測、標出框框才行。

---

## 2. 準備資料與指標

### 2.1 Train / Val / Test 切分的意義

大考為什麼要跟練習題分開？因為你練習時可以重複做、背住答案；大考新題就現原形。模型也一樣。

- **Train 集（70%）**：訓練用——模型看著練習，參數一次次調整
- **Validation 集（20%）**：開發時測試——每個 epoch 後跑驗證集評分，看學得怎樣
- **Test 集（10%）**：最終驗收——訓練完**絕不再動**，用來報成績單

> 🔍 **名詞卡：Epoch**
> 白話：「一個完整的循環」。1 epoch = 看一遍所有訓練題。epochs 50 = 新人把所有考古題從頭到尾看 50 遍。越多遍越熟，但看太多遍會背答案（overfitting）。

### 2.2 三個關鍵指標

99.1% 聽起來超厲害對吧？但你很快會發現，『99.1% 不是模型神，是考題太簡單、及格線太寬』。真正的故事在另一個指標。

| 指標 | 全名 | 定義 | 白話 |
|---|---|---|---|
| **mAP@0.5** | mean Average Precision at IoU 0.5 | 框框只要碰到真框就算對 | 射飛鏢只要箭頭碰到靶紙就給分 |
| **mAP@0.5:0.95** | mean Average Precision at IoU 0.5–0.95 | 框框要越靠越近，分才越高 | 射飛鏢越靠紅心分越高 |
| **Precision / Recall** | 精準度 / 召回率 | 見下表 | 見下表 |

> 🔍 **名詞卡：mAP（mean Average Precision）**
> 白話：物件偵測的成績單，0–100。怎麼算？模型預測一堆框框，每個框跟真實框比較『重合度』（叫 IoU），超過門檻就算對。把所有預測都算一遍、算平均，就是 mAP。
>
> 更詳細：mAP@0.5 = IoU ≥ 0.5 的算對（碰到就行）；mAP@0.5:0.95 = IoU 0.5、0.55、0.6……到 0.95 的平均。@0.5 很寬鬆、很容易飽和；@0.5:0.95 嚴格得多。
>
> 🔍 **名詞卡：Precision（精準度）vs Recall（召回率）**
> 白話：
> - Precision：「我說是瑕疵，結果真的是瑕疵」的比例。寧可錯殺、不願放過。（工廠檢測：寧願多檢查幾件、也不能放過真瑕疵產品出廠）
> - Recall：「真的瑕疵，我有沒有找到」的比例。寧可放過、不願錯殺。（醫療診斷：寧願多做檢查、不能漏掉真病人）
>
> 比喻：Precision 像海關「寧可錯檢查無辜旅客、也不能放過走私客」；Recall 像法庭「寧可放過有罪的、不能冤枉無辜的」。

**今天的數據**：wafer 資料集
- mAP@0.5：**99.1%**（爆表、看不出差異）
- mAP@0.5:0.95：**76.3%**（才是實話，優化空間很大）

---

## 3. 環境建置與指令速查

```bash
# 進專案目錄
cd auto-cv-train-optimization-claude_code

# 建虛擬環境
uv venv --python 3.11

# 裝依賴
uv pip install -e .

# 複製並編輯 .env
cp .env.example .env
# 在 .env 填入 ROBOFLOW_API_KEY
```

五個指令的速查表：

| 指令 | 做什麼 | 會卡住嗎 |
|---|---|---|
| `uv run autocv data -c configs/wafer.yaml` | 下載資料 | ❌ 不會，自動跑完 |
| `uv run autocv split -c configs/wafer.yaml` | 驗證標註 + 切分 | ❌ 不會，自動跑完 |
| `uv run autocv train -c configs/wafer.yaml` | 訓練模型 | ⏸️ 會停下等你確認（預估時間） |
| `uv run autocv optimize -c configs/wafer.yaml` | 超參搜尋 | ⏸️ 會停下等你確認（很耗時） |
| `uv run autocv infer -c configs/wafer.yaml` | 推論 + 視覺化 | ❌ 不會，自動跑完 |

---

## 4. 🌊 第一波：Baseline 一條龍（data → split → train → infer）

現在我們走完一遍完整流程。你的任務不是『寫程式』，而是『理解每一棒的職員在做什麼』。下面我們逐個指令走過。

### 4.1 🔴 data-hunter：下載資料

```bash
uv run autocv data -c configs/wafer.yaml
```

**它在做什麼**：
1. 連到 Roboflow，用你的 API key 驗身份
2. 找到 `wafer` 專案、下第 3 版
3. 抓 images/labels（原始圖 + 標註框 txt 檔）
4. 存到 `data/raw/`

✅ **預期看到**：
```
Downloading wafer version 3...
Downloaded 1000 images + 1000 label files
Save to data/raw/
```

🧯 **卡住的話**：
- **「403 Unauthorized」**：API key 填錯或過期。檢查 `.env` 裡 `ROBOFLOW_API_KEY` 有沒有正確複製（直接從 [Roboflow 帳號設定](https://roboflow.com/account) 複製，別加引號）。
- **「Network timeout」**：網路太慢或 Roboflow 伺服器爆炸。等 1 分鐘後重跑，或用備援截圖。
- **「找不到 wafer 專案」**：可能版本號改了。直接編輯 `configs/wafer.yaml` 改 `version` 欄位（去 [Roboflow Universe 的 wafer 頁面](https://universe.roboflow.com/wm811k-paasr/wm811k) 查最新版號）。

> 🔍 **名詞卡：API key（應用程式介面金鑰）**
> 白話：發給程式用的「臨時通行證」。你登入 Roboflow 是用帳號密碼；程式不用帳號密碼，改用 API key——更安全、可以隨時撤銷。千萬不要把 key 洩漏給陌生人。

### 4.2 🟡 bbox-labeler：驗證標註 + 切分

```bash
uv run autocv split -c configs/wafer.yaml
```

**它在做什麼**：
1. 讀 `data/raw/` 底下所有 image + label 對
2. 檢查標註品質：有沒有框超出邊界、有沒有重複框、圖片格式對嗎
3. 照 config 的比例（70/20/10）分成 train/val/test
4. 複製到 `data/processed/images/{train,val,test}/` 和 `data/processed/labels/{train,val,test}/`
5. 產一份 `data/yaml` 給 YOLO 讀

✅ **預期看到**：
```
Validating annotations...
Fixing issues...
Splitting dataset:
  train: 700 images
  val:   200 images
  test:  100 images
Saved to data/processed/
data.yaml created
```

🧯 **卡住的話**：
- **「Validation error: 12 images with issues」**：標註有問題（超出邊界、重複等）。CLI 會自動試著修、超過 10% 會停下問「繼續嗎」。按 `y` 繼續或 `n` 中止。通常按 `y` 沒問題（CLI 改的是邊界調整、不會丟資料）。
- **找不到 `data/raw/`**：代表 data-hunter 沒跑或跑失敗。回頭跑 `autocv data`。

### 4.3 🔵 training-runner：訓練模型（⏸️ 會停下等你確認）

```bash
uv run autocv train -c configs/wafer.yaml
```

**它在做什麼**：
1. 算出預估訓練時間（基於資料集大小、epochs 數、batch 大小）
2. **停下來等你確認**（很重要！這是保護你的電費）
3. 你按 `y` 後開始訓練
4. 每個 epoch 後印出 train loss、val mAP
5. 訓練完存最佳權重到 `runs/train/weights/best.pt`

✅ **預期看到**：
```
Estimated time: 8 minutes on MPS
Proceed? [y/n]: y  ← 你要親手輸入
Training YOLOv8n with 700 images...
Epoch 1/50: train loss=0.45, val mAP@0.5=0.85
Epoch 2/50: train loss=0.38, val mAP@0.5=0.88
...
Epoch 50/50: train loss=0.12, val mAP@0.5=0.991
Training complete. Best weights saved to runs/train/weights/best.pt
```

🧯 **卡住的話**：
- **「CUDA out of memory」或「MPS out of memory」**：GPU 記憶體滿了。馬上調小 config：
  ```yaml
  train:
    batch: 4  # 原本是 8，改成 4
  ```
  然後重跑。（Batch 小 = 一次看少一點圖、用的記憶體少，但訓練慢點）
- **「預估時間超過 30 分鐘」**：這堂課時間不夠。改用預錄的跑結果或 epochs 改小（`train.epochs: 20` 代替 50）。
- **停著不動超過 1 分鐘**：可能在下載預訓練權重（`yolov8n.pt` 約 6 MB）。網路慢就等等。

> 🔍 **名詞卡：Batch size**
> 白話：每一次訓練「喂」給模型多少張圖。batch 8 = 一次看 8 張、調一次參數。Batch 越小越省 GPU 記憶體但訓練慢；batch 越大越快但越吃記憶體。
>
> 🔍 **名詞卡：Loss（損失）**
> 白話：模型預測的「錯誤程度」。Loss 越小越好，代表預測越準。Train loss 往下掉就代表模型在學東西。
>
> 🔍 **名詞卡：預訓練權重（Pre-trained weights）**
> 白話：別人已經訓練好的模型起點。yolov8n.pt 是在大資料集（ImageNet + COCO）上訓了幾十萬張圖、學會了「怎麼認物體」的基礎知識。我們不是從零開始，而是站在別人肩上、在他的基礎上快速調整。這叫「遷移學習」（Transfer Learning）——就像「已經會認貓狗的人來學認瑕疵，比白紙快」。

### 4.4 🟢 inference-runner：推論 + 視覺化

```bash
uv run autocv infer -c configs/wafer.yaml
```

**它在做什麼**：
1. 讀訓練好的 best.pt
2. 在 test set 上跑推論（預測每張圖的框位置 + 類別 + confidence）
3. 畫紅框標出預測結果
4. 算 mAP@0.5 和 mAP@0.5:0.95
5. 產成果圖到 `runs/infer/pred_*.png`
6. 寫成績單 `runs/infer/summary.md`

✅ **預期看到**：
```
Running inference on test set...
Processed 100 images
mAP@0.5:   0.9913
mAP@0.5:0.95: 0.7633
Precision: 0.9331
Recall:    0.9968
Visualizations saved to runs/infer/
Summary saved to runs/infer/summary.md
```

然後打開 `runs/infer/summary.md`，裡面有成績單；`runs/infer/` 資料夾有 10 張 `pred_*.png` 圖，每張都畫著紅框、框上標著 class + confidence。

🧯 **卡住的話**：
- **「找不到 best.pt」**：代表 training-runner 沒跑完或失敗。回頭檢查訓練有沒有正常完成。
- **「test/ 資料夾不存在」**：說明標註品質太差、split 被 reject 了。或是你的資料集本身不帶 test split（Roboflow 有時預切、有時不）。CLI 會自動 fallback 用 val 來推論（會在 summary 註明「used validation set」）。
- **成果圖畫得爆爛（框都不在物體上）**：要嘛訓練沒收斂（loss 沒往下），要嘛資料本身有問題。課堂備援：秀預先存的好成果圖。

---

## ☝️ 中場檢查：覺察指標選錯的陷阱

99.1% mAP。聽起來爆炸厲害對吧？想像你是工廠老闆，聽員工說『瑕疵檢測精準度 99.1%』，你會不會已經想著『可以上線了』？

但我告訴你一個秘密：**99.1% 不是因為模型天才，而是考題太簡單、及格線太寬。**

看這個 mAP@0.5:0.95 —— 76.3%。才 76 分。中等生。同一個模型、同一個資料集，只是『改一下評分標準』，成績就從『天才』掉到『中等』。

這說明什麼？**如果你看錯指標，你永遠看不到優化空間。** 99.1% 已經飽和、無法優化；76.3% 還有 24% 的上升空間。

為什麼會有兩個指標？因為在工業應用上，mAP@0.5 太寬鬆了。框框只要大概碰到瑕疵就算對，那誰來告訴你『瑕疵到底在邊界哪裡』？工廠操作員需要更精準的定位。

所以現在我們**把主指標改成 mAP@0.5:0.95**，然後爬『優化階梯』。

> ❓ **想一想**：為什麼我們不能選一個更嚴格的指標，比如 mAP@0.8？
>
> **答案**：指標越嚴格、基線越低，但太嚴格就變成「不是在考模型，是在考資料集品質」。@0.5:0.95 是業界標準（COCO 數據集用的），平衡了嚴度與公平性。

---

## ⛰️ E. 大章：科學優化階梯

這是本課的重頭戲。不是盲目調參、而是**一次只動一個變因、記下每階的漲幅**。

### E1. 建立 Baseline 協議

訓練開始前，定下「不變的規則」，之後每一階都恪守：

```yaml
train:
  model: yolov8n          # ← 固定
  epochs: 50              # ← 先固定（R3 會改）
  batch: 8                # ← 固定
  imgsz: 416              # ← 先固定（R1 會改）
  seed: 42                # ← 固定（確保可重現）

dataset:
  seed: 42                # ← 固定切分（test set 永不動）
```

為什麼要固定？因為一次改好幾個參數，你永遠搞不清哪個功勞最大。

### E2. 路線 A：優化階梯（同 wafer 資料集）

**協議**：每一階用同一份 test set、同一個 seed、同一個訓練環境（同一台機器、GPU/MPS）。每次訓練**都記錄 mAP@0.5:0.95**（改成主指標，不看 @0.5）。

#### R1：解析度 416 → 640（瑕疵通常是小目標）

```yaml
train:
  imgsz: 640  # ← 改這裡
```

**為什麼會漲**：瑕疵是小物體，圖片解析度越高越能看清細節。這幾乎是單調有利的改變。

**預期**：mAP@0.5:0.95 應該提升。（不保證百分百，但機率 > 80%）

#### R2：模型 yolov8n → yolov8s（腦容量變大）

```yaml
train:
  imgsz: 640  # ← 保持 R1 的改變
  model: yolov8s.pt  # ← 改這裡（n→s）
  # 注意：s 比 n 大，訓練可能慢 20–30%、但容量大通常表現更好
```

**為什麼會漲**：更大的模型能學到更複雜的特徵。同樣的訓練預算下，模型越大越好——前提是資料夠豐富（wafer 有 700 張 train，夠用）。

**預期**：mAP@0.5:0.95 應該繼續提升。

#### R3：訓練長度 50 → 150 epochs + 早停（複習更多遍、但防止背答案）

```yaml
train:
  imgsz: 640
  model: yolov8s.pt
  epochs: 150  # ← 改這裡
  patience: 20  # ← 新增：val mAP 20 個 epoch 沒進步就停
```

**為什麼會漲**：新人看 150 遍考古題比 50 遍更熟。但無限看會背答案，所以加 patience（早停）——val mAP 停止進步，自動停訓。

**預期**：mAP@0.5:0.95 應該繼續提升（因為能看到更多 epoch、同時 patience 防止過度擬合）。

#### R4：超參搜尋（找最佳學習率、增幅、IoU）

```bash
uv run autocv optimize -c configs/wafer.yaml
```

這一階會自動嘗試不同的超參組合（Ultralytics 內建演化式搜尋），找出哪組最高分。耗時最久（iterations × 單輪訓練）。

> 🔍 **名詞卡：超參數（Hyperparameter）**
> 白話：訓練前手動設的旋鈕。包括：學習率（lr，爬山時的『步伐大小』）、增幅（momentum，慣性）、衰減（weight decay，簽名筆的『減速制動』）……改這些不改模型結構。
>
> 🔍 **名詞卡：Overfitting（過度擬合）**
> 白話：新人把答案背下來、練習題 100 分，但模擬考只有 40 分。模型在訓練集上表現完美，但在新資料上爆。原因：訓練集太小、訓練太久、正則化太弱。
>
> 🔍 **名詞卡：Early stopping（早停）**
> 白話：設一個門檻。『val 分數 20 個 epoch 都沒進步？停下來，再訓只會更過度擬合』。自動喊停，省電、又防止背答案。

**預期**：mAP@0.5:0.95 應該漲（但漲幅通常比 R1–R3 小，因為已經調好了）。

#### R5：調 Validation 集上的門檻（免費加分）

这一階不重新訓練，只改**推論時**的參數：

```yaml
infer:
  conf: 0.25  # ← 改這裡（confidence threshold）
  nms_iou: 0.45  # ← 改這裡（NMS IoU，去重複框的門檻）
```

**怎麼找最佳門檻**：在 **validation set** 上掃遍 conf 0.1–0.9、nms_iou 0.3–0.7 的組合，找出最高 mAP 的組合，記下來。

**為什麼只能在 val 上調、不能在 test 上調**：因為在 test 上調參 = 你看著大考題目調答題策略，當然高分，但考新題就爆。**Test set 神聖不可侵犯。**

> 🔍 **名詞卡：Confidence threshold（信心門檻）**
> 白話：模型預測一個框時會說「我有 95% 把握這是瑕疵」（confidence = 0.95）。門檻設 0.25 = 信心 ≥ 25% 就輸出；設 0.5 = 只輸出信心 ≥ 50% 的。門檻高 → 誤判少（精準度高）但漏掉小物體（召回率低）；門檻低 → 都輸出（召回率高）但誤判多（精準度低）。
>
> 🔍 **名詞卡：NMS（Non-Maximum Suppression，去重複）**
> 白話：同一個瑕疵位置，模型可能預測出 3 個框（都很接近）。NMS 做的就是「刪掉多餘的、只保留信心最高的那個」。IoU 門檻 = 「多近的框才算『重複』」。

**預期**：mAP@0.5:0.95 可能小幅提升（取決於原門檻設得好不好）。

### E3. 階梯成績表模板

訓練時記下每階的成績：

| 階段 | imgsz | model | epochs | patience | mAP@0.5:0.95 | Δ | 耗時 | 備註 |
|---|---|---|---|---|---|---|---|---|
| Baseline | 416 | yolov8n | 50 | — | 0.7633 | — | 5 min | 初始 |
| R1 | **640** | yolov8n | 50 | — | — | +? | ? | 解析度↑ |
| R2 | 640 | **yolov8s** | 50 | — | — | +? | ? | 模型↑ |
| R3 | 640 | yolov8s | **150** | **20** | — | +? | ? | epoch↑ + 早停 |
| R4 | 640 | yolov8s | 150 | 20 | — | +? | ? | 超參搜尋 |
| R5 | 640 | yolov8s | 150 | 20 | — | +? | ? | 門檻調整 |

**重點**：
- 如果某階沒漲（或甚至掉分），就**回滾**並在備註寫下「為什麼沒漲」（資料集太小？超參搜尋沒收斂？）
- 每階記錄「對比 baseline 漲幅 Δ」，看到變化
- 最後一欄能寫觀察（如「R2 漲幅最大因為模型容量限制了 baseline 表現」）

### E4. 路線 B：換難資料集（Roboflow Universe 挑戰）

講完 wafer 的優化階梯後，展示「在更難的真實資料集上會怎樣」。

**挑選標準**（學會自己挑資料集）：
- 類別 ≥ 5 個（不能太簡單）
- 每張圖平均 ≥ 10 個框（物體密集）
- 有小物體比例高（解析度優化才明顯）
- 社群 baseline mAP@0.5 落在 0.5–0.8（不能太簡單、也不能不可能）

**候選資料集**（舉例）：
- [航拍無人機檢測](https://universe.roboflow.com)（小物體、密集）
- PCB 瑕疵多分類
- 貨架商品 SKU 密集偵測
- 交通號誌（小物體）

**怎麼換**：
1. 上 Roboflow Universe 找到資料集頁面
2. 複製 `workspace` / `project` / `version` 三個欄位到 `configs/new_dataset.yaml`
3. 跑 `autocv all -c configs/new_dataset.yaml --yes`（跟 wafer 完全相同流程，零改程式碼）

wafer 資料集很乾淨、瑕疵明顯，所以優化空間不大。但真實世界的資料集亂得多——小物體、遮擋、光線差……那時你會發現，R1（解析度）的幫助會更明顯、R2（模型大小）的貢獻也更大。

### E5. 進階挑戰（選配）：SAHI 切片推論

對付極小物體的絕招——把大圖切成小片、逐片推論、最後拼回去。（超出本課範圍，放進階資料裡）

---

## E6. 動手前先自己下注

在跑優化階梯前，自己猜一次：五個階段中哪一階的漲幅最大？

給自己 2 分鐘想想：
- R1：解析度 416→640
- R2：模型 n→s
- R3：epoch 50→150 + 早停
- R4：超參搜尋
- R5：門檻調整

寫下你的答案，跑完對比。

**通常的結果**（基於 wafer 資料集）：
- R1、R2、R3 通常都明顯漲（物體是小目標、模型容量和訓練長度很重要）
- R4 漲幅通常 < R1–R3（已經調好了）
- R5 可能不漲或小幅漲（原門檻已經不錯）

**教學點**：「你們的預測 vs 實際結果對比，說明什麼？」

---

## 4. 視覺駕駛艙（可選展示）

CLI 版本很透明、很適合工程師。但如果要看訓練進度、或用圖形界面，有另一種方式。

```bash
uv run autocv ui
# 打開 http://localhost:8000
```

**展示內容**：
- Config 選擇器
- Run 按鈕
- 5 階段燈號（data → split → train → optimize → infer）
- 訓練曲線實時更新（loss、mAP）
- 跑完後看 gallery（推論的帶框圖）

這個界面很漂亮、很適合投影演示、或給不懂 CLI 的人用。

---

## 驗收清單

走完這份文件後，檢查一下你會不會：

- [ ] 跑過一次 `autocv all` 的完整流程
- [ ] 理解五個 agent 的職責（data-hunter、bbox-labeler、training-runner、hp-optimizer、inference-runner）
- [ ] 看到 baseline 的成績（mAP@0.5 = 0.99+、mAP@0.5:0.95 = 0.76+）
- [ ] 理解「mAP@0.5 vs @0.5:0.95」的差異 & 為什麼要看 @0.5:0.95
- [ ] 複述「優化階梯」的五階（R1–R5）及各自改什麼參數
- [ ] 明白「train / val / test 要分開、不能在 test 上調參」
- [ ] 跑過至少一階優化（R1 或 R2），看到成績變化
- [ ] 會複製 config 改三行（workspace/project/version）換資料集
- [ ] 用 Claude Code agent 跟 AI 對話，看過「五個 agent 接力」的完整演出

## 常見坑排錯速查

| 問題 | 症狀 | 排錯方式 |
|---|---|---|
| **Roboflow 連線失敗** | 「403 Unauthorized」或「Network error」| 檢查 `.env` 裡 API key 有沒有正確複製；確認網路；重試 |
| **訓練卡住不動** | `autocv train` 停著超過 2 分鐘 | 可能在下載 yolov8n.pt（首次）。等等。或按 Ctrl+C 中止、檢查網路 |
| **GPU / MPS 記憶體爆炸** | 「CUDA out of memory」或「MPS out of memory」| 改小 batch size（`train.batch: 4`）；重跑 |
| **标註驗證失敗** | `autocv split` 報「10% 的標註有問題」| 按 `y` 讓 CLI 自動修；或編輯 config `dataset.strict: false` 略過檢查 |
| **Test set 評分奇怪** | mAP 特別低或特別高 | 檢查 test set 有沒有被洗、或根本是 train set 的複製；或資料集本身太難 |
| **Optimize 耗時太久** | `autocv optimize` 跑超過 30 分鐘 | iterations 太多。改 config `optimize.iterations: 3` 快速 demo；正式跑用默認 20 |
| **推論無框架或框架爆爛** | `autocv infer` 完成但圖片上沒框 | best.pt 沒訓練好；或模型訓練過度擬合（train loss 很低但 val loss 很高） |
| **Config 欄位打錯** | 「Unknown config field」| 對照 template.yaml 檢查拼寫（如 `imgsz` 不是 `img_size`） |
| **找不到 wafer 資料集** | 「Project not found」| wafer 版本可能更新了。去 [Universe 查](https://universe.roboflow.com/wm811k-paasr/wm811k)最新版號改 config |

## 常見誤解與正確認識

| 誤解 | 正確認識 |
|---|---|
| 「99.1% mAP 已經很完美了」 | @0.5 太寬鬆，實際是 76.3% (@0.5:0.95)——還有大優化空間 |
| 「我只要改所有參數、總會變好」 | 一次改多個參數=無法判斷誰功勞大；而且可能互相抵消效果 |
| 「直接用 test set 調參很快」 | 等於看著大考題目複習，當然高分但新題爆；這是"data leakage"，違背 ML 倫理 |
| 「Batch 越大越好」 | Batch 大→訓練快、但容易過度擬合；batch 小→慢、但泛化力強。要平衡 |
| 「Epochs 越多越好」 | 無限訓練=模型背答案（overfitting）；早停防止這個 |
| 「我的資料集比 wafer 簡單」 | 可能是因為看到的指標是 mAP@0.5（太寬鬆）；改看 @0.5:0.95 才知道真實難度 |

---

## 帶走的三句話

如果這份文件只記住三件事，就這三句。

1. **指標選得太寬鬆，會讓你誤以為沒東西可學**。mAP@0.5 碰到靶就給分（寬鬆），mAP@0.5:0.95 越靠紅心分越高（嚴格）。同一個模型、不同指標、差一倍分數。改指標優化空間立刻出現。工業應用一定要選 @0.5:0.95。

2. **優化要一次只動一個變因、記下每階的漲幅**。改解析度 + 改模型 + 改 epoch 同時改，你永遠搞不清誰功勞最大。科學方法 = 控制變數、逐步驗證。階梯成績表就是證明。

3. **Test set 神聖不可侵犯**。調參（confidence、NMS IoU）只能在 validation set 上調、在 test set 上報成績。在 test 上調參 = 看著大考題目複習，當然高分，但考新題就爆。這不是技巧、是倫理線。

---

## ❓ 五個思考題

### ❓ **想一想** 1：基礎理解

**題目**：訓練 50 epochs 和訓練 150 epochs，哪個會更容易出現 overfitting？

**答案**：150 epochs。看 50 遍考古題不會背答案，但看 150 遍、尤其沒有早停制約，模型會把細節都背下來——訓練集 99.9% 但測試集只有 60%。這就是 overfitting。

**延伸**：「那為什麼 R3 階梯要把 epochs 改成 150？」→ 因為有 `patience: 20`（早停），val mAP 20 個 epoch 沒進步自動停，防止背答案。

---

### ❓ **想一想** 2：指標理解

**題目**：你看到 mAP@0.5 = 99.1%，工廠老闆說『可以上線了』。但你改看 mAP@0.5:0.95 = 76.3% 後，為什麼要告訴他『還能優化』？

**答案**：因為 @0.5 只要框碰到瑕疵就算對（太寬鬆），99.1% 達到飽和；@0.5:0.95 要求框要精準定位，76.3% 還有 24% 的空間。同一個模型、改指標才看到真實容量。工業應用需要精準位置信息，所以看 @0.5:0.95 才有意義。

**延伸**：「如果你就硬用 mAP@0.5，你會想到『還能優化』嗎？」→ 不會，會傻傻以為已經完美。這就是「指標選錯會讓你看不到進步空間」。

---

### ❓ **想一想** 3：實驗設計

**題目**：在優化階梯裡，R2（模型 n→s）和 R1（解析度 416→640）我都想改。如果同時改，會怎樣？

**答案**：
- 同時改 = mAP 可能會更高
- 但你不知道「是 R1 功勞多、還是 R2」
- 如果 mAP 沒漲反而掉，你也不知道誰搞砸了（是 s 模型不適合、還是解析度 640 反而要求 batch 更小）
- 所以一次只改一個 = 能精確測量「這個改動的實際效果」

**延伸**：「那為什麼 R3 要『同時』加 `patience` 和改 `epochs`？」→ 因為它們是一體的（epochs 多了要防止過度擬合、所以加早停控制）；而且「長訓練 + 防過度」是一個概念。

---

### ❓ **想一想** 4：資料洩漏

**題目**：我訓練完 model v1，跑推論發現 test mAP 不夠好。我決定在 test set 上試試改 confidence 門檻 0.1→0.5，發現分數變高了。然後我把這個配置記下來、說『我優化成功了』。這樣做對嗎？

**答案**：不對。這是「data leakage」（資料洩漏）。
- 調參在 test set 上 = 你的優化配置是「根據 test 資料調出來的」
- 等於「看著大考題目複習」，當然高分
- 但用新資料評估時（新客戶的晶圓圖）就會爆
- 正確做法：調參只能在 validation set 上試、在 test set 上報成績（一次性）

**延伸**：「那 R5（門檻調整）我可以在哪個集合上調？」→ validation set（練習調整，不損傷大考公平性）。最後才用 test set 驗收。

---

### ❓ **想一想** 5：遷移學習

**題目**：訓練時我用的是 yolov8n.pt（預訓練權重）而不是從零開始。為什麼要用別人訓練過的？

**答案**：
- 從零開始 = 模型要從「看都不會看圖」學起，需要巨大資料量
- 預訓練 = 別人用 ImageNet 訓了幾十萬張圖，模型已經「會認物體」的基本能力
- 我們只要基於他的基礎、快速微調成「認瑕疵」
- 就像「已經會認貓狗的人來學認瑕疵，比白紙快」（遷移學習 Transfer Learning）
- wafer 只有 700 張訓練圖，從零開始會 overfitting 死；有預訓練就能一句話秒殺

**延伸**：那我能不用預訓練嗎？→ 理論上可以，但要 10 倍以上的資料和訓練時間；實務上不划算。

---

