#!/usr/bin/env bash
# Project 15: RAG Architect MCP Server 課堂遙控器
# 六幕全部離線、唯讀、秒出——只展示 repo 真實檔案，不起 server、不連網。
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"
REPO_DIR="$WORKSPACE/rag-architect-mcp"
cd "$REPO_DIR" || exit 1

TOTAL=6

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
  echo "  Project 15：RAG Architect MCP Server － 課堂放映清單"
  echo "======================================================================"
  echo "  1  一行掛進 Cursor (.cursor/mcp.json)   螢幕：uvx 設定物件 + 各家 client 對照表"
  echo "  2  確定性路由決策矩陣 (router.py) ⭐    螢幕：六種架構常數 + select_architecture 分支"
  echo "  3  fail-safe 隱私抽取 (session.py) ⭐   螢幕：「不可以上雲」的否定偵測 regex"
  echo "  4  Tool schema 設計 (server.py)         螢幕：四段式 description + 無狀態工具簽名"
  echo "  5  Skill 與 /rag 指令                   螢幕：拿到藍圖之後該怎麼用的判斷力"
  echo "  6  測試即 bug 清單 (test_*.py)          螢幕：22 個測試名，每個都是出過的 bug"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "一行掛進 Cursor" \
    ".cursor/mcp.json 的 uvx 設定 + client-configs 的各家對照表" \
    "MCP 掛在 client 上；同一個物件到處能用，免 key、免 clone、免絕對路徑"
  echo "--- .cursor/mcp.json（本 repo 用 Cursor 打開即開箱可用）---"
  cat .cursor/mcp.json
  echo
  echo "--- client-configs/README.md：各家 client 放哪 ---"
  grep -n -A 9 "Where each client wants it" client-configs/README.md
}

scene_2() {
  banner 2 "確定性路由的決策矩陣 (router.py)" \
    "六種架構常數，以及 select_architecture 的分支：型態 → 規模 → 結構" \
    "純函式、無 I/O、同輸入永遠同輸出——可稽核，才值得被信任"
  echo "--- 六種可能的架構（router.py 頂部常數）---"
  grep -n "^CAG\|^CONTEXTUAL\|^LAYOUT\|^GRAPH\|^TEXT_TO_SQL\|^CODE" rag_architect/router.py
  echo
  echo "--- select_architecture：資料型態先於一切 ---"
  grep -n -A 16 "def select_architecture" rag_architect/router.py
  echo
  echo "--- 底線：路由不做任何 I/O ---"
  grep -n "The routing is pure" rag_architect/router.py
}

scene_3() {
  banner 3 "fail-safe 隱私抽取 (session.py)" \
    "「不可以上雲」包含「可以上雲」——否定偵測的 regex 與註解" \
    "隱私判反是資安事故：否定先偵測、地端訊號壓過雲端字眼、不確定回 local_only"
  echo "--- 否定偵測 regex（舊版把否定句讀成同意）---"
  grep -n -B 3 -A 6 "_NEGATED_CLOUD = " rag_architect/session.py
  echo
  echo "--- 抽取邏輯：任何地端訊號都壓過同時出現的雲端字眼 ---"
  grep -n -B 1 -A 2 "Fail safe" rag_architect/session.py
}

scene_4() {
  banner 4 "Tool schema 設計 (server.py)" \
    "四段式 tool description + 無狀態、全選填的工具簽名" \
    "工具會不會被 AI 自動調用，是 description 和形狀設計出來的，不是求來的"
  echo "--- DESIGN_DESCRIPTION 四段式：回傳什麼／何時用／怎麼呼叫／何時不該用 ---"
  grep -n -A 23 "^DESIGN_DESCRIPTION" rag_architect/server.py
  echo
  echo "--- 工具簽名：無狀態、全部選填、不用捏 session id ---"
  grep -n -A 7 "^def design_rag_architecture" rag_architect/server.py
}

scene_5() {
  banner 5 "Skill 與 /rag 指令" \
    "SKILL.md 的 Procedure（拿到藍圖後怎麼用）+ /rag 指令全文" \
    "MCP 工具給能力，skill 給判斷力：呈現取捨而不是倒 JSON、反駁 = slot 判錯"
  echo "--- skills/rag-architect/SKILL.md：使用者反駁時查 slot，不吵結論 ---"
  grep -n -A 6 "^## When the user pushes back" skills/rag-architect/SKILL.md
  echo
  echo "--- commands/rag.md：/rag 指令全文 ---"
  cat commands/rag.md
}

scene_6() {
  banner 6 "測試即 bug 清單 (test_rag_architect.py)" \
    "22 個測試函式名——每一個名字就是一個真的出過的 bug" \
    "回歸測試的正確寫法：翻過的車立紀念碑；不連網、不需要 pytest、一個指令跑完"
  echo "--- 檔頭宣言 ---"
  head -n 5 test_rag_architect.py
  echo
  echo "--- 22 座 bug 紀念碑 ---"
  grep -n "^def test_" test_rag_architect.py
  echo
  echo "--- 共 $(grep -c "^def test_" test_rag_architect.py) 項；現場驗證指令：uv run python test_rag_architect.py ---"
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
