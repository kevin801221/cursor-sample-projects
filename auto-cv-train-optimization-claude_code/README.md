# 讓 AI Agents 團隊幫您自動訓練電腦視覺模型 — 以 YOLO 模型在 Wafer dataset 圖像為例

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/kevin801221/auto-cv-train-optimization-claude_code/actions/workflows/ci.yml/badge.svg)](https://github.com/kevin801221/auto-cv-train-optimization-claude_code/actions)
[![Stars](https://img.shields.io/github/stars/kevin801221/auto-cv-train-optimization-claude_code?style=social)](https://github.com/kevin801221/auto-cv-train-optimization-claude_code/stargazers)

> **作者 / Author：羅子嘉 (Kevin Luo)** · [@kevin801221](https://github.com/kevin801221)

> **你打一句話。5 個 AI agent 自己分工：抓資料 → 驗證切分 → 訓練 → 調參 → 產出帶框成果。你回來時，模型已經 99.1% mAP。**
>
> **You type one sentence. Five AI agents split the work — fetch, validate, train, tune, visualize. You come back to a 99.1% mAP model.**

這不是「又一個 YOLO 腳本」。這是一支**會自己接力的 AI 工程團隊**，跑在你的 Mac 上，一個 YAML 換任何資料集。下面晶圓圖上那些紅框，是它自己找出來的瑕疵——**沒有人手動標一筆**。

而你現在看到的，**還不是完整版**。往下看。

---

## 它做到的事 / What it actually pulls off

| | |
|---|---|
| **mAP@0.5** | **0.9913** |
| mAP@0.5:0.95 | 0.7633 |
| Precision / Recall | 0.9331 / 0.9968 |
| 你要做的事 | 改一行 YAML，打一句話 |

→ [**看它在 10 張晶圓圖上自己畫出的瑕疵框**](docs/results/summary.md)（每張都標了 class + confidence，沒有作弊）

---

## 30 秒，你也有一個 / 30 seconds to your own

```bash
git clone git@github.com:kevin801221/auto-cv-train-optimization-claude_code.git
cd auto-cv-train-optimization-claude_code
uv venv --python 3.11 && uv pip install -e .
cp .env.example .env          # 填 ROBOFLOW_API_KEY
uv run autocv all -c configs/wafer.yaml --yes
```

跑完你拿到：訓練好的權重、test mAP、10 張帶 bbox 成果圖、一份 `summary.md`。

---

## 兩種開法 / Two ways to drive

**① 一行 CLI** — 給喜歡掌控感的人

| 指令 | 它做什麼 |
|---|---|
| `autocv data` | 從 Roboflow 抓資料 |
| `autocv split` | 驗證標註 + 切 70/20/10 |
| `autocv train` | 訓練 YOLOv8（**燒卡前先問你**） |
| `autocv optimize` | 超參搜尋，自己找最佳組合 |
| `autocv infer` | 推論 + 畫框 + 出報告 |
| `autocv all [--optimize]` | 一條龍 |

**② 跟 Claude Code 講話** — 給想動嘴的人

打開 repo，說一句「**幫我下載並訓練這個資料集**」。
`data-hunter → bbox-labeler → training-runner → hp-optimizer → inference-runner` 五個 agent 自動接力，每一棒交接你都看得到。

**③ 視覺駕駛艙 / Visual cockpit** — 給想用看的人

```bash
uv run autocv ui          # 開瀏覽器，零指令
```
選 config、按 Run，5 階段燈即時接力、訓練曲線即時長、跑完成果圖直接看。train/optimize 前一定先跳預估時間，按確認才開跑。

![訓練中：5 階段接力 + 訓練曲線即時長 / Training in flight](docs/screenshots/cockpit-training.jpg)

![跑完：成果圖 gallery + mAP 0.9950 / Done: gallery + mAP](docs/screenshots/cockpit-done.jpg)

---

## 換成你的資料集 / Bring your own

複製 `configs/template.yaml`，改三行：`workspace` / `project` / `version`。
**不用碰任何一行 Python。** 醫療影像、瑕疵檢測、農業、零售貨架——同一套流程。

---

## 為什麼它不會偷燒你的 GPU

`train` / `optimize` 一定先印預估時間、停下等你確認才開跑。agent 被明文禁止加 `--yes`。
**你的電費，你決定。** 這是設計，不是 bug。

---

## 🔒 你還沒看到的部分 / What you haven't seen yet

你現在拿到的是**引擎**。真正的東西還沒開——而且**只給在場的人**：

- ✅ **無碼視覺駕駛艙**（已上線）：`uv run autocv ui` 開瀏覽器，選 config、按 Run，看 5 階段即時接力、訓練曲線即時長出、跑完看成果圖。
- 🔒 **一鍵雲端訓練**：本機跑不動就丟雲端，回來拿模型。
- 🔒 **多資料集競技場**：同時跑 N 個設定，自動排名選最強。
- 🔒 **模型一鍵打包**：直接吐 CoreML / ONNX，拿去上線。

這些不會發 PR 公告。**上線那天，只有 Watch / ⭐ 的人會被 ping 到，並拿到駕駛艙 beta 的早鳥邀請。**
Not announced anywhere. The day it ships, **only watchers get pinged — and first dibs on the cockpit beta.**

---

## 架構 / Architecture

引擎怎麼接力、每個模組負責什麼，看 [`docs/architecture.md`](docs/architecture.md)。

## 作者 / Author

**羅子嘉 (Kevin Luo)** — [@kevin801221](https://github.com/kevin801221)
做了東西、有想法、想要早鳥票，開 issue 或來敲我。

## License

MIT — 拿去用，做出東西了回來說一聲。
