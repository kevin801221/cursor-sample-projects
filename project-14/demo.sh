#!/usr/bin/env bash
# Project 14: GraphRAG 知識圖譜問答 課堂遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"
REPO_DIR="$WORKSPACE/agent-automatic-graphrag-chat-skill"
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
  echo "  Project 14：GraphRAG 知識圖譜問答系統 － 課堂放映清單"
  echo "======================================================================"
  echo "  1  環境與相依套件檢查 (check_setup)  螢幕：LanceDB / NetworkX / RAG 管線檢查"
  echo "  2  來源資料擷取與轉錄 (00/01)        螢幕：YouTube 轉錄與 Markdown 切塊資料清洗"
  echo "  3  知識圖譜構建 (03_build_graph) ⭐  螢幕：實體 (Entity) 與關聯 (Relation) 抽取"
  echo "  4  GraphRAG 混合檢索問答展示 ⭐      螢幕：向量檢索 + 圖譜多跳推理 (Multi-hop) 答案"
  echo "  5  RAG 評估指標分析 (05_evaluate)    螢幕：忠實度 (Faithfulness) 與答案相關性評分"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "環境與相依套件檢查" \
    "執行 check_setup.py，檢查向量庫與圖譜依賴" \
    "建置 GraphRAG 前先確認向量庫與 NetworkX 拓撲環境"
  uv run python scripts/check_setup.py 2>/dev/null || python3 scripts/check_setup.py
}

scene_2() {
  banner 2 "來源資料擷取與轉錄" \
    "檢視 00_ingest_source.py 與資料切塊結構" \
    "垃圾進垃圾出——好的 RAG 從乾淨的語意切塊開始"
  head -n 30 scripts/00_ingest_source.py
}

scene_3() {
  banner 3 "知識圖譜構建 (03_build_graph)" \
    "檢視實體識別與關聯抽取流程" \
    "不只記住文字，更記住概念與概念之間的關係網"
  grep -n -A 25 "def extract_entities" scripts/03_build_graph.py || head -n 35 scripts/03_build_graph.py
}

scene_4() {
  banner 4 "GraphRAG 混合檢索問答展示" \
    "展示 04_chatbot_server.py 混合檢索邏輯" \
    "單純向量找不到的跨章節跨實體關聯，交給知識圖譜多跳推理"
  grep -n -A 25 "hybrid_search" scripts/04_chatbot_server.py || head -n 35 scripts/04_chatbot_server.py
}

scene_5() {
  banner 5 "RAG 評估指標分析 (05_evaluate)" \
    "檢視 RAGAS / 離線評估腳本" \
    "沒有評估指標的 RAG 只是玄學，用嚴格基準給答案打分"
  head -n 35 scripts/05_evaluate_rag.py
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
