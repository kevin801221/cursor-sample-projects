# WALKTHROUGH：Cursor 5 大 Subagent 驅動的電腦視覺自動訓練實戰指南

> **這是一份專為「講師帶班」與「AI 視覺工程師」設計的完整實戰教學手冊。**  
> 在本專案中，AutoCV 不是零散的腳本或單純的 Skill，而是由 **5 個具備專業分工的 Cursor Subagents**（位於 `.cursor/agents/`）組成的高效工程團隊。每個 Subagent 封裝了對應的專業技能（`.cursor/skills/`），在你的 Mac 上完成從資料抓取、品質切分、模型訓練、超參調優到 Bounding Box 串流可視化的全自動閉環。

---

## 🤖 5 大 Subagent 與 Skill 體系架構

Cursor Agent 透過讀取 `.cursor/rules/cv-subagents.mdc` 協調 5 個專屬 Subagents，每個 Subagent 依循專屬 Skill 指南做出專業決策：

```
                             ┌───────────────────────────────┐
                             │       Cursor Subagents        │
                             └───────────────┬───────────────┘
                                             │ 依序接力執行
     ┌───────────────────────────────────────┴───────────────────────────────────────┐
     ▼                                       ▼                                       ▼
┌──────────────┐                       ┌──────────────┐                       ┌─────────────────┐
│ data-hunter  │                       │ bbox-labeler │                       │ training-runner │
│ (資料獵人)    │                       │ (品管切分員)  │                       │ (訓練執行員)    │
└──────┬───────┘                       └──────┬───────┘                       └────────┬────────┘
       │ 調用                                 │ 調用                                  │ 調用
       ▼                                      ▼                                       ▼
.cursor/skills/cv-data-collection     .cursor/skills/cv-dataset-qc             .cursor/skills/cv-training
(Roboflow 下載與驗證)                  (標註合法性/小物件警訊)                  (模型階梯/MPS記憶體配比)

                                             │ (訓練完成後分流)
                         ┌───────────────────┴───────────────────┐
                         ▼                                       ▼
                ┌──────────────────┐                   ┌──────────────────┐
                │ inference-runner │                   │   hp-optimizer   │
                │ (主考官/出成績單)  │ ◄─────────────────┤  (超參數調優專家) │
                └────────┬─────────┘   回填最佳超參續跑    └────────┬─────────┘
                         │ 調用                                  │ 調用
                         ▼                                       ▼
            .cursor/skills/cv-metrics-viz           .cursor/skills/cv-hyperparameter-tuning
            (PR曲線/混淆矩陣/階梯報告)               (Ultralytics Tuner/演化搜尋)
```

---

## 📊 成果樣本與訓練數據檢驗 (Trained Samples Showcase)

本專案內建兩大標準資料集驗證，學生可直接驗收模型成果：

### 1. 半導體晶圓瑕疵偵測 (Wafer WM-811K) — 現成頂級成果
- **資料集**：半導體晶圓瑕疵（8 種缺陷型態：Center, Donut, Scratch, Edge-Ring 等）
- **模型**：`YOLOv8n`（在 Mac MPS 硬體加速下完成訓練）
- **測試集表現 (Test Split - 42 張)**：
  - 🏆 **mAP@0.5**：**`0.9913` (99.13%)**
  - 📐 **mAP@0.5:0.95**：**`0.7633`**
  - 🎯 **Precision (精確率)**：**`0.9331`**
  - 🚀 **Recall (召回率)**：**`0.9968`** (幾乎零漏檢！)
- **成果圖檔**：位於 `docs/results/pred_*.png`，每張圖片均帶有精準的紅色預測 Bounding Box 與 Confidence 標籤。

### 2. 水族館水下多目標偵測 (Aquarium v6) — 階梯優化實戰
- **資料集**：7 類水下生物（魚、水母、海龜、企鵝、鯊魚、魟魚等），小物件與嚴重類別不平衡。
- **優化階梯比較**：
  - R0 (`aq-n-640`)：YOLOv8n, 640px, 60ep ➔ 建立 Baseline
  - R1 (`aq-s-640`)：升級 YOLOv8s ➔ 提高特徵抽取能力
  - R2 (`aq-s-800`)：放大解析度至 800px ➔ 專攻遠處小魚辨識

---

## 👣 帶班逐步實戰流程 (Step-by-Step Guide)

---

### Step 0：環境準備與 Cursor Subagents 載入

#### 🎯 目標與原理
確認 Python 環境由 `uv` 統一管理，載入硬體加速（Mac 優先使用 MPS，Linux/Windows 使用 CUDA）。

#### 💻 實作指令
```bash
cd auto-cv-train-optimization-claude_code
uv sync
```
複製環境變數範本（若需從 Roboflow 下載新資料集）：
```bash
cp .env.example .env
# 編輯 .env 填入 ROBOFLOW_API_KEY=...
```

---

### Step 1：呼叫 `data-hunter` 下載原始資料

#### 🎯 目標與原理
`data-hunter` 負責將 Roboflow 上的資料安全下載至 `data/raw/`。

#### 🤖 Cursor Agent 對話方式
> **「請扮演 data-hunter，幫我下載 wafer 資料集」**

#### 💻 CLI 等效指令
```bash
uv run autocv data -c configs/wafer.yaml
```

#### ✅ 成功判準
`data/raw/` 目錄下產生 `train/`、`valid/`、`test/` 圖片與標註，並輸出 `data.yaml`。

---

### Step 2：呼叫 `bbox-labeler` 進行品管與切分

#### 🎯 目標與原理
標註資料常有座標超出範圍 [0, 1]、類別缺失或標註遺失。`bbox-labeler` 依據 `.cursor/skills/cv-dataset-qc/SKILL.md` 進行格式校驗，並標準化切分至 `data/processed/`。

#### 🤖 Cursor Agent 對話方式
> **「請呼叫 bbox-labeler 驗證標註並切分資料集」**

#### 💻 CLI 等效指令
```bash
uv run autocv split -c configs/wafer.yaml
```

#### ✅ 成功判準
印出 train / val / test 圖片數與 BBox 統計，並確認 `data/processed/data.yaml` 產生完成。

---

### Step 3：呼叫 `training-runner` 啟動模型訓練

#### 🎯 目標與原理
`training-runner` 依據 `.cursor/skills/cv-training/SKILL.md` 規劃訓練參數。**它具備算力守門機制（Compute Gate），會先計算預估時間並向使用者確認後才啟動**。

#### 🤖 Cursor Agent 對話方式
> **「請呼叫 training-runner 開始訓練」**  
> *(Agent 會回報預估耗時，等您回覆 "GO" 後才開始訓練)*

#### 💻 CLI 等效指令
```bash
uv run autocv train -c configs/wafer.yaml
```

#### ✅ 成功判準
輸出 `runs/<name>/weights/best.pt`，並產出訓練曲線 `results.csv` 與 `results.png`。

---

### Step 4：(可選) 呼叫 `hp-optimizer` 進行超參數搜尋

#### 🎯 目標與原理
當 Baseline 模型的 mAP 遇到瓶頸時，`hp-optimizer` 使用遺傳演算法搜尋最佳學習率（lr0, lrf）、動量（momentum）與數據增強參數。

#### 🤖 Cursor Agent 對話方式
> **「請呼叫 hp-optimizer 幫我搜尋最佳超參數」**

#### 💻 CLI 等效指令
```bash
uv run autocv optimize -c configs/wafer.yaml
```

#### ✅ 成功判準
在 `runs/tune/` 下產出 `best_hyperparameters.yaml`。

---

### Step 5：呼叫 `inference-runner` 產出推論與成績單

#### 🎯 目標與原理
`inference-runner` 作為最終主考官，在獨立的測試集上進行推論，繪製帶有紅色 BBox 的視覺化圖檔，並產出全維度成績單（`report.md`）。

#### 🤖 Cursor Agent 對話方式
> **「請呼叫 inference-runner 進行測試集推論並產出評估成績單」**

#### 💻 CLI 等效指令
```bash
# 1. 測試集推論並繪製 BBox 圖片
uv run autocv infer -c configs/wafer.yaml

# 2. 產出評估報告與指標圖表
uv run autocv report -c configs/wafer.yaml
```

#### ✅ 成功判準
- `runs/infer/pred_*.png`：產生帶框測試圖片。
- `runs/report/report.md`：產生包含 mAP、PR 曲線、混淆矩陣與階梯比較表的完整成績單！

---

## 🌐 Step 6：啟動 Web 視覺化駕駛艙 (Cockpit UI)

本專案內建強大的 **AutoCV 視覺駕駛艙**，支援**非同步串流顯示**（完成一張即時呈現一張 BBox 成果圖）！

### 啟動駕駛艙
```bash
uv run autocv ui --port 8787
```
打開瀏覽器存取：**[http://localhost:8787](http://localhost:8787)**

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │ ⚡ AutoCV Subagent Cockpit                   [configs/wafer.yaml ▼]    │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 🤖 5 大 Subagent 接力流水線                                            │
 │ [data-hunter] ➔ [bbox-labeler] ➔ [training-runner] ➔ [inference-runner] │
 ├───────────────────────────────────┬────────────────────────────────────┤
 │ 💻 即時執行動態 (Live Logs)        │ 📈 訓練與驗證指標曲線 (Loss / mAP)  │
 │ > [training-runner] Epoch 15/60   │   mAP@0.5: 0.9913   Loss: 0.0124   │
 ├───────────────────────────────────┴────────────────────────────────────┤
 │ 🔬 即時推論與 Bounding Box 視覺化串流 (Real-time Async Gallery)          │
 │ [晶圓圖 1 - Defect 0.98]  [晶圓圖 2 - Defect 0.96]  [晶圓圖 3 - Defect 0.99]...│
 └────────────────────────────────────────────────────────────────────────┘
```

### 駕駛艙演示亮點
1. **5 Subagent 狀態指示燈**：即時顯示目前由哪一個 Subagent 正在掌舵（RUNNING / DONE / WAITING CONFIRM）。
2. **算力守門閘門 Modal**：訓練前彈出互動確認框，點擊「🚀 確認開始 (GO)」才開始運算。
3. **即時非同步圖片串流 (Async Streaming Gallery)**：推論階段**每完成一張預測，畫面立即動態彈出一張帶框成果圖**，不必苦等整批結束！
4. **✨ 晶圓瑕疵 99.1% Showcase 按鈕**：一鍵載入已訓練完成的 99.1% mAP 晶圓展示成果與 10 張高解析度標註圖，供課堂瞬間展示！

---

## 💡 課堂教學核心心法 (Pedagogical Insights)

1. **為什麼要分成 5 個 Subagent？**
   - 避免單一大模型「身兼數職」造成指令漂移。將「抓資料」、「品管」、「訓練」、「調參」、「推論打分」拆開，每一步都有嚴格的輸入與輸出契約（Input/Output Contracts）。
2. **為什麼標註品管（QC）比訓練更重要？**
   - Garbage in, garbage out。座標出界或空白標註會直接導致 Loss 震盪；`bbox-labeler` 在切分前先清洗，能省下數小時無效訓練時間。
3. **一次只動一個變因（One Variable at a Time）**：
   - 進行階梯優化時（如 n-640 ➔ s-640），保持其餘參數完全一致，才能用科學數據歸因性能提升。
