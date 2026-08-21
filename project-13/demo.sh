#!/usr/bin/env bash
# Project 13: AutoCV 5 個 AI Agent 自動訓練 YOLO 課堂遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"
REPO_DIR="$WORKSPACE/auto-cv-train-optimization-claude_code"
cd "$REPO_DIR" || exit 1

TOTAL=5

banner() {
  echo
  echo "========================================================================"
  echo "【第 $1 幕】$2"
  echo "📺 螢幕上會出現：$3"
  echo "🎯 這一幕在教：$4"
  echo "========================================================================"
  echo
}

list_scenes() {
  echo
  echo "======================================================================"
  echo "  Project 13：AutoCV 5 個 AI Agent 自動訓練 YOLO － 課堂放映清單"
  echo "======================================================================"
  echo "  1  5 個 AI Agent 團隊架構與角色分工 螢幕：Data / Split / Train / Eval / Opt 各職責"
  echo "  2  晶圓瑕疵資料集配置 (wafer.yaml) 螢幕：Roboflow 下載配置、類別與模型參數"
  echo "  3  模擬 5 Agent 接力訓練工作流 ⭐  螢幕：各 Agent 接力狀態、mAP@0.5 指標與損失曲線"
  echo "  4  優化階梯 (R1–R5) 比較與調校策略 ⭐ 螢幕：一次只動一個變因，科學推升 mAP"
  echo "  5  啟動 AutoCV 訓練視覺化駕駛艙     螢幕：瀏覽器開啟五階段燈號與訓練即時面板"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "5 個 AI Agent 團隊架構與角色分工" \
    "印出 CLAUDE.md 中的 5 個 Agent 職責說明" \
    "打一句話讓 agents 接力訓練模型；分工明確才不會互踩狀態"
  cat CLAUDE.md
}

scene_2() {
  banner 2 "晶圓瑕疵資料集配置 (wafer.yaml)" \
    "檢視 configs/wafer.yaml 設定檔內容" \
    "標準化配置檔：鎖定圖片尺寸、Batch Size、Epochs 與模型架構"
  cat configs/wafer.yaml
}

scene_3() {
  banner 3 "模擬 5 Agent 接力訓練工作流" \
    "展示 5 個 Agent 的接力日誌：資料抽取 → 資料切分 → YOLO 訓練 → 推論評估 → 優化建議" \
    "流水線作業：每個 Agent 的輸出是下一個 Agent 的輸入"
  echo "▶ Agent 1 (DataPrep): 檢查晶圓瑕疵圖片 450 張，標註格式 YOLOv8 ✓"
  echo "▶ Agent 2 (Splitter): 切分 Train (70%) / Val (20%) / Test (10%) ✓"
  echo "▶ Agent 3 (Trainer) : 載入 yolov8n.pt，執行 50 epochs 訓練... ✓"
  echo "▶ Agent 4 (Evaluator): 驗算 mAP@0.5 = 0.842, Precision = 0.881 ✓"
  echo "▶ Agent 5 (Optimizer): 提出 R1 優化建議（提高解析度 imgsz 640->800）✓"
}

scene_4() {
  banner 4 "優化階梯 (R1–R5) 比較與調校策略" \
    "展示優化階梯演進表：Baseline 0.842 → R1 (800px) 0.871 → R2 (Augment) 0.895 → R3 (yolov8s) 0.923" \
    "科學優化法：一次只動一個變因，用客觀指標衡量，幾乎一定把成績推得更好"
  echo "------------------------------------------------------------------------"
  echo "  階梯 | 優化手法               | mAP@0.5 | 提升幅度 | 狀態"
  echo "------------------------------------------------------------------------"
  echo "  R0   | Baseline (wafer, 640px)| 0.842   | -        | 基準線"
  echo "  R1   | 提高解析度 (800px)     | 0.871   | +2.9%    | ✓ 採納"
  echo "  R2   | Mosaic + HSV 增強      | 0.895   | +2.4%    | ✓ 採納"
  echo "  R3   | 升級模型 (yolov8s)     | 0.923   | +2.8%    | ✓ 採納"
  echo "------------------------------------------------------------------------"
}

scene_5() {
  banner 5 "啟動 AutoCV 訓練視覺化駕駛艙" \
    "啟動 Streamlit / UI 儀表板，即時呈現訓練燈號與推論成果" \
    "視覺化成果展示與即時推論紅框預覽"
  echo "▶ 提示：執行 uv run autocv ui 即可啟動完整視覺化駕駛艙"
}

case "${1:-}" in
  "") list_scenes ;;
  1) scene_1 ;;
  2) scene_2 ;;
  3) scene_3 ;;
  4) scene_4 ;;
  5) scene_5 ;;
  *) echo "無效幕次：$1"; list_scenes; exit 1 ;;
esac
