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

## 🎮 三種操作介面 / Three ways to drive

**① 跟 Cursor / Claude Code 對話（5 大 Subagents 自動接力）**
- **Cursor 專屬 Subagents**：位於 `.cursor/agents/`（`data-hunter`, `bbox-labeler`, `training-runner`, `hp-optimizer`, `inference-runner`），每個 Subagent 各自封裝 `.cursor/skills/` 專業指南。
- 只要說一句：「**幫我下載並訓練這個資料集**」，5 個 Subagent 自動接力完成任務。
- 👉 **完整教學手冊：請參閱 [`WALKTHROUGH.md`](WALKTHROUGH.md)**。

**② 一行 CLI 指令** — 給喜歡直接掌控的工程師

| 指令 | 它做什麼 |
|---|---|
| `autocv data` | `data-hunter` 從 Roboflow 抓資料 |
| `autocv split` | `bbox-labeler` 驗證標註 + 切分 70/20/10 |
| `autocv train` | `training-runner` 訓練 YOLOv8（**算力守門閘門先問你**） |
| `autocv optimize` | `hp-optimizer` 超參搜尋，自己找最佳組合 |
| `autocv infer` | `inference-runner` 測試集推論 + 畫框 |
| `autocv report` | 產出優化階梯全維度成績單（mAP / PR 曲線 / 混淆矩陣） |
| `autocv all [--optimize]` | 一條龍全自動執行 |

**③ 視覺駕駛艙 (Visual Cockpit)** — 給想要即時監控與非同步串流成果的人

```bash
uv run autocv ui --port 8787         # 開啟瀏覽器駕駛艙
```
- **5 Subagent 狀態指示燈**：即時掌握當前由哪位 Subagent 掌舵，資料下載完成即顯示落地路徑。
- **訓練與驗證即時曲線**：Epoch / Loss / mAP@0.5 實時繪製，含**已耗時與預估剩餘時間**。
- **即時非同步圖片串流 (Async Streaming Gallery)**：推論階段**完成一張即時呈現一張帶有 Bounding Box 的成果圖**！
- **🪜 優化階梯成績單面板**：pipeline 尾端自動跑 `autocv report`，val/test 階梯表 + 圖表直接顯示在面板上。
- **✨ 晶圓瑕疵 99.1% Showcase**：一鍵載入頂級成果，瞬間展示高精準瑕疵框與全維度成績單。

---

## 換成你的資料集 / Bring your own

複製 `configs/template.yaml`，改三行：`workspace` / `project` / `version`。
**不用碰任何一行 Python。** 醫療影像、瑕疵檢測、農業、零售貨架——同一套流程。

---

## 為什麼它不會偷燒你的 GPU

`train` / `optimize` 一定先印預估時間、停下等你確認才開跑。agent 被明文禁止加 `--yes`。
**你的電費，你決定。** 這是設計，不是 bug。

而且它會**訓練去重**：同名 run 已有 `best.pt` 就自動跳過訓練（駕駛艙也不會再跳確認窗）、直接進推論與成績單；真要重練，CLI 加 `--force`。重複跑一條龍不會重燒一次 GPU。

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
