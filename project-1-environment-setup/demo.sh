#!/usr/bin/env bash
# Project 1: 環境準備日 課堂遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TOTAL=3

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
  echo "  第 0 課：環境準備日 － 課堂放映清單（共 ${TOTAL} 幕）"
  echo "======================================================================"
  echo "  1  裝機五件套快速檢驗    螢幕：Node.js、uv、Git、Docker 版本確認"
  echo "  2  大檔預載與備援確認    螢幕：說明 Docker / 雲端備援切換策略"
  echo "  3  全自動健康診斷報告 ⭐  螢幕：全綠色診斷報表，所有核心工具一次檢驗"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "裝機五件套快速檢驗" \
    "印出各工具版本號，確認 Node.js >= 20、uv 與 Git 皆已就緒" \
    "把必然會發生的失敗前移——在寫第一行程式碼前確認工具版本"
  echo "▶ node -v" && node -v
  echo "▶ git --version" && git --version
  echo "▶ uv --version" && uv --version
  echo "▶ docker --version" && docker --version 2>/dev/null || echo "docker 未啟動或未安裝"
}

scene_2() {
  banner 2 "大檔預載與備援確認" \
    "展示 neo4j 與 supabase 映像檔的預載指令與無 Docker 時的雲端替代方案" \
    "公司電腦被擋 Docker 時不要慌，所有實戰專案皆有免費雲端備援路徑"
  echo "【本地模式預載指令】"
  echo "  docker pull neo4j:5"
  echo "  npx supabase start"
  echo
  echo "【無 Docker 雲端備援】"
  echo "  project-2: Supabase 雲端免費專案"
  echo "  project-14: Neo4j Aura 雲端免費執行個體"
  echo "✓ 備援方案就緒"
}

scene_3() {
  banner 3 "全自動健康診斷報告" \
    "診斷器輸出全綠健康檢查表，確認 5 件套與環境全部就緒" \
    "驗證指令比「我裝好了」更可信，看到綠字才是真正的就緒"
  python3 "$ROOT/doctor.py"
}

case "${1:-}" in
  "") list_scenes ;;
  1) scene_1 ;;
  2) scene_2 ;;
  3) scene_3 ;;
  *) echo "無效幕次：$1"; list_scenes; exit 1 ;;
esac
