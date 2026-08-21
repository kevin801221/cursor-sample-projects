# 五個 AI 團隊自動訓練電腦視覺模型 — 以 YOLO 瑕疵檢測為例

> Cursor 課程 Project 13（進階課題）：Claude Code agents + Ultralytics YOLOv8。
> 一句話：**說一句「訓練這個資料集」，5 個 AI agent 自動分工——下載資料、驗證標註、訓練模型、調超參、視覺化成果。你回來時模型已準備好上線。**

## 專案規格

| | |
|---|---|
| **最終成果** | 訓練完成的 YOLOv8 瑕疵偵測模型：99.1% mAP@0.5、76.3% mAP@0.5:0.95，含帶框視覺化與評分報告 |
| **技術棧** | Python 3.11、uv、Ultralytics YOLOv8、Roboflow API、Claude Code agents |
| **預估時間** | 4–6 小時，分「跑通 baseline」與「科學優化階梯」兩大階段 |
| **前置需求** | Mac（M1+，MPS）或有 GPU 的 Linux；Roboflow 免費帳號；Claude Code Pro；網路穩定 |

## 這個 App 做什麼

- **自動下載資料**：連接 Roboflow Universe，一行 YAML 切換任何資料集
- **自動驗證與切分**：標註品質檢查 + 智慧分割成 train/val/test（70/20/10）
- **訓練 YOLOv8 模型**：支援 nano/small/medium/large/xlarge 五種規格，訓練前先報預估時間等你確認（保護你的電費）
- **超參搜尋優化**：Ultralytics 內建演化式搜尋，自動找到最佳學習率、增幅、IoU 門檻組合
- **推論與視覺化**：用訓練好的模型預測 test set，產出帶紅框的圖片與分數報告

## 五個角色如何分工（旅館比喻）

想像一間訓練學校，五位職員接力：

| Agent | 職責 | 比喻 | 指令 |
|---|---|---|---|
| 🔴 **data-hunter** | 從 Roboflow 抓教材（圖片+標註框） | 採購部——去書店買考古題 | `autocv data` |
| 🟡 **bbox-labeler** | 驗證標註品質 + 切分成練習/模擬考/大考 | 品管部——檢查考題有沒有印錯、分成三組 | `autocv split` |
| 🔵 **training-runner** | 訓練模型（一直讀教材直到掌握） | 教練——教新人一遍遍看考古題學認瑕疵 | `autocv train` |
| 🟣 **hp-optimizer** | 調超參（找「最有效率的複習方法」） | 讀書顧問——測試哪種複習節奏、複習多少次最有效 | `autocv optimize` |
| 🟢 **inference-runner** | 推論 + 畫框 + 出成績單 | 主考官——在大考上測一次、打分數、公布成績 | `autocv infer` |

## 兩種開法 — CLI vs 對話

**① CLI 版**（給想掌控進度的人）

```bash
cd auto-cv-train-optimization-claude_code
uv venv --python 3.11 && uv pip install -e .
cp .env.example .env          # 填 ROBOFLOW_API_KEY
uv run autocv all -c configs/wafer.yaml --yes   # 一條龍
```

或分階段：

```bash
uv run autocv data -c configs/wafer.yaml      # 🔴 下載
uv run autocv split -c configs/wafer.yaml     # 🟡 驗證+切分（要按 y 確認）
uv run autocv train -c configs/wafer.yaml     # 🔵 訓練（會先報預估時間）
uv run autocv optimize -c configs/wafer.yaml  # 🟣 超參搜尋
uv run autocv infer -c configs/wafer.yaml     # 🟢 推論+視覺化
```

**② Claude Code 對話版**（給想動嘴的人）

打開 Cursor，在 Claude Code 對話框說：

> 「幫我下載並訓練 wafer 資料集」

五個 agent 自動接力，每一棒交接都看得到：
1. data-hunter 抓資料
2. bbox-labeler 驗證標註
3. training-runner 跑訓練（停下等你 GO）
4. hp-optimizer 調超參（停下等你 GO）
5. inference-runner 產出結果

**③ 視覺駕駛艙**（給想用滑鼠的人）

```bash
uv run autocv ui              # 打開瀏覽器
```

選 config、按 Run，5 階段燈號實時接力、訓練曲線即時長出、跑完看成果。

## 換成你的資料集

1. 上 [Roboflow Universe](https://universe.roboflow.com)，找一個資料集（或上傳自己的）
2. 複製 `configs/template.yaml`，只改三行：
   - `workspace`：你的 Roboflow 工作區名
   - `project`：資料集名稱
   - `version`：版本編號

**就這樣。不用改任何 Python 程式碼。**醫療影像、PCB 瑕疵、農作物病蟲害、零售貨架——同一套引擎。

## 安全設計：你的電費，你決定

`train` 和 `optimize` 都會先算出預估時間、**停下來等你確認才開跑**。

為什麼？訓練會燒電卡，`--yes` 自動通過是常見坑（有人粗心加了就默默跑 6 小時）。**這個專案故意設計成：沒有自動化的確認，每次都要你眼睛看到預估時間、親手按『GO』。** 這不是 bug，是安全邊界。

## 快速開始（30 秒）

```bash
git clone git@github.com:kevin801221/auto-cv-train-optimization-claude_code.git
cd auto-cv-train-optimization-claude_code
uv venv --python 3.11 && uv pip install -e .
cp .env.example .env
# 編輯 .env，填入 ROBOFLOW_API_KEY（在 Roboflow 帳號設定複製）
uv run autocv all -c configs/wafer.yaml --yes
```

跑完你拿到：
- `runs/train/weights/best.pt` — 訓練好的模型
- `runs/infer/pred_*.png` — 帶紅框的預測成果（10 張）
- `runs/infer/summary.md` — mAP 報告

## 專案結構

```
auto-cv-train-optimization-claude_code/
├── .claude/agents/              # 五個 agent 定義
│   ├── data-hunter.md
│   ├── bbox-labeler.md
│   ├── training-runner.md
│   ├── hp-optimizer.md
│   └── inference-runner.md
├── configs/
│   ├── template.yaml            # 你的資料集改這個
│   └── wafer.yaml               # 教學用範本
├── src/autocv/
│   ├── cli.py                   # 五個指令的入口
│   ├── data.py                  # Roboflow 下載
│   ├── split.py                 # 標註驗證 + 切分
│   ├── train.py                 # YOLOv8 訓練
│   ├── optimize.py              # 超參搜尋
│   ├── infer.py                 # 推論 + 視覺化
│   └── server/                  # UI 駕駛艙（Flask）
├── data/
│   ├── raw/                     # Roboflow 原始下載
│   └── processed/               # 切分後的 train/val/test
├── runs/                        # 訓練/推論輸出（git 忽略）
│   ├── train/
│   ├── tune/
│   └── infer/
└── .env                         # ROBOFLOW_API_KEY（自己複製 .env.example）
```

## 四階段流程

| 階段 | 時間 | 做什麼 | 驗收 |
|---|---|---|---|
| 1. 環境 + baseline | 1.5 小時 | 裝環境、跑通一次 autocv all，拿到 99.1% mAP@0.5 | `runs/infer/summary.md` 有成績 |
| 2. 覺察指標 | 20 分 | 發現 mAP@0.5:0.95 只有 76.3% ≠ 99.1%，說明選錯指標就看不到優化空間 | 理解「99.1% 不是神，是題目太簡單」|
| 3. 科學優化階梯 | 2 小時 | 一階一階爬：解析度↑、模型↑、epoch↑、超參搜尋、門檻調整，每階紀錄漲幅 | 階梯成績表 |
| 4. 遷移到難資料集 | 1 小時 | 上 Roboflow Universe 換真正困難的資料集、重爬階梯 | 在新資料集上複製流程 |

## 指令速查

```bash
# 個別步驟
uv run autocv data      -c configs/wafer.yaml     # 只下載
uv run autocv split     -c configs/wafer.yaml     # 只驗證+切分
uv run autocv train     -c configs/wafer.yaml     # 只訓練
uv run autocv optimize  -c configs/wafer.yaml     # 只超參搜尋
uv run autocv infer     -c configs/wafer.yaml     # 只推論

# 一條龍
uv run autocv all       -c configs/wafer.yaml [--optimize] [--yes]

# 視覺駕駛艙
uv run autocv ui
```

## 帶走的三句話

1. **指標選得太寬鬆，會讓你誤以為沒東西可學**——mAP@0.5 只要碰到靶就給分（99.1% 飽和），但 mAP@0.5:0.95 要越靠紅心分越高（76.3% 才是實話），改指標優化空間立刻出現。
2. **優化一定一次只動一個變因**——改解析度、改模型大小、改訓練長度，每改一個都記下漲幅。同時改三個，你永遠搞不清誰功勞最大。
3. **Test set 神聖不可侵犯**——調參（confidence threshold、NMS IoU）只能在 validation set 上調，最後用 test set 報成績。在 test 上調參 = 看著大考題目複習，當然高分，但考新題就爆掉。

---

## 常見前置檢查

- 🐍 **Python 3.11+** ：`python --version`
- 🎒 **uv 已裝**：`uv --version`（沒有就 `curl -LsSf https://astral.sh/uv/install.sh | sh`）
- 🔑 **Roboflow API key** ：[帳號設定](https://roboflow.com/account) → Copy API key → 填進 `.env`
- ⚡ **GPU 或 MPS** ：`uv run python -c "from ultralytics import YOLO; m = YOLO('yolov8n.pt'); print(m.device)"` 確認裝置不是 CPU
- 📁 **網路夠快**：Wafer 資料集～100 MB，視網速 1–5 分鐘

## 完整逐步教學見

**[walkthrough.md](./walkthrough.md)** — 完整逐步教學，包含：
- 🚦 開始前檢查清單
- 🗺️ 學習地圖
- 🎬 開場故事（「培訓瑕疵檢測員」）
- 🔍 名詞卡（電腦視覺、YOLO、mAP、precision/recall、overfitting……）
- ❓ **想一想**（5 個思考題，附答案）
- ✅ 預期看到 / 🧯 卡住的話（每個指令的正常/失敗畫面與救援方式）
- **E 大章：科學優化階梯**（從基線 → 解析度 → 模型 → epoch → 超參 → 門檻，含階梯成績表模板）
- 驗收清單 + 排錯速查 + 帶走的三句話

