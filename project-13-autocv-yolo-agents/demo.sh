#!/usr/bin/env bash
# Project 13: AutoCV 5 個 AI Agent 自動訓練 YOLO 課堂遙控器
# 所有幕都跑真實指令／真實檔案——沒有假數字。
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"
REPO_DIR="$WORKSPACE/auto-cv-train-optimization-claude_code"
cd "$REPO_DIR" || exit 1

banner() {
  echo
  echo "========================================================================"
  echo "【第 $1 幕】$2"
  echo "📺 螢幕上會出現：$3"
  echo "🎯 這一幕在教：$4"
  echo "========================================================================"
  echo
}

need_data() {
  if [ ! -f data/processed/aquarium/data.yaml ]; then
    echo "⚠️  尚未下載/切分 aquarium 資料集。課前先跑："
    echo "    uv run autocv data  -c configs/aquarium.yaml"
    echo "    uv run autocv split -c configs/aquarium.yaml"
    return 1
  fi
}

need_report() {
  if [ ! -f runs/report/report.md ]; then
    echo "⚠️  尚未產出成績單。課前先跑完至少一個訓練，再："
    echo "    uv run autocv report -c configs/aquarium.yaml"
    return 1
  fi
}

list_scenes() {
  echo
  echo "======================================================================"
  echo "  Project 13：AutoCV 5 個 AI Agent 自動訓練 YOLO － 課堂放映清單"
  echo "======================================================================"
  echo "  1  Agent 團隊三層體系 (.cursor/)      螢幕：agents / skills / rules 接力規範"
  echo "  2  aquarium 難資料集配置              螢幕：Roboflow 下載配置與階梯三兄弟"
  echo "  3  真實資料品管與切分 (bbox-labeler)  螢幕：638 張合併、標註驗證、類別不平衡"
  echo "  4  真實優化階梯成績 ⭐                螢幕：autocv report 快取秒出各 run test mAP"
  echo "  5  metric 視覺化成績單 ⭐             螢幕：階梯表 / per-class AP / 混淆矩陣"
  echo "  6  啟動 AutoCV 訓練視覺化駕駛艙       螢幕：燈號、即時曲線+ETA、成績單面板、訓練去重"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "Agent 團隊三層體系 (.cursor/)" \
    "印出接力規範 + 5 個 agents 與 6 個 skills 清單" \
    "agents 是誰做事、skills 是怎麼判斷、rules 是怎麼接力"
  cat .cursor/rules/cv-subagents.mdc
  echo
  echo "── 5 個 agents ──";  ls .cursor/agents/
  echo "── 6 個 skills ──";  ls .cursor/skills/
}

scene_2() {
  banner 2 "aquarium 難資料集配置" \
    "檢視 configs/aquarium.yaml 與階梯三個 config 的差異" \
    "換資料集只改 config；每階只動一個變因、name 唯一"
  cat configs/aquarium.yaml
  echo
  echo "── 階梯三兄弟（一次只動一個變因）──"
  grep -H -E "^  (model|name|imgsz|batch):" configs/aquarium.yaml configs/aquarium-s.yaml configs/aquarium-s800.yaml
}

scene_3() {
  banner 3 "真實資料品管與切分 (bbox-labeler)" \
    "live 跑 autocv split：合併 638 張、逐行驗證標註、印類別分佈" \
    "資料品管先於訓練；類別不平衡在這裡就看得到"
  need_data || return 1
  uv run autocv split -c configs/aquarium.yaml
}

scene_4() {
  banner 4 "真實優化階梯成績" \
    "live 跑 autocv report：metrics.json 快取命中，秒出各 run 的 test mAP" \
    "一次只動一個變因，Δ 才能歸因；快取讓重跑零成本"
  need_data || return 1
  uv run autocv report -c configs/aquarium.yaml
}

scene_5() {
  banner 5 "metric 視覺化成績單" \
    "印出 report.md 的階梯表與 per-class 表，列出所有圖檔" \
    "指標判讀順序：ladder → curves → per-class → confusion/PR → dataset_stats"
  need_report || return 1
  sed -n '1,40p' runs/report/report.md
  echo
  echo "── 圖檔（投影時直接 open）──"
  ls runs/report/*.png
  echo "    open runs/report/ladder.png runs/report/per_class_ap.png"
}

scene_6() {
  banner 6 "啟動 AutoCV 訓練視覺化駕駛艙" \
    "瀏覽器開啟：5 Agent 燈號、即時曲線含耗時/ETA、下載位置、成績單面板" \
    "訓練去重：同名 run 已有權重 → 免守門直接推論+出成績單"
  echo "▶ 執行：uv run autocv ui   （瀏覽器 http://127.0.0.1:8787）"
  echo "▶ 選 configs/aquarium.yaml 按 Run——已訓練過的 run 會直接跳過訓練，"
  echo "  曲線瞬間重播歷史、推論與成績單照常更新。要重練：CLI 加 --force。"
}

case "${1:-}" in
  "") list_scenes ;;
  1) scene_1 ;;
  2) scene_2 ;;
  3) scene_3 ;;
  4) scene_4 ;;
  5) scene_5 ;;
  6) scene_6 ;;
  *) echo "無效幕次：$1"; list_scenes; exit 1 ;;
esac
