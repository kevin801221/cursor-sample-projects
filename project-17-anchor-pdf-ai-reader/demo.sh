#!/usr/bin/env bash
# Project 17: Anchor 框選論文問 AI（local-first）課堂遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"
REPO_DIR="$WORKSPACE/Anchor_knowledge.ai"
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
  echo "  Project 17：Anchor 框選論文問 AI（local-first）－ 課堂放映清單"
  echo "======================================================================"
  echo "  1  這是什麼 App（README + 骨架）    螢幕：產品自述、檔案結構與各檔行數"
  echo "  2  四把 system prompt (prompts.py)  螢幕：雙通道原則：文字為準、圖補版面"
  echo "  3  region.py 雙通道抽取 ⭐          螢幕：81 行全文：座標、TEXTFLAGS、dpi 夾取"
  echo "  4  /api/ask SSE 串流管線 ⭐         螢幕：穩定前綴 + gen() 四步 + error frame"
  echo "  5  記憶蒸餾與兩跳擴展 ⭐            螢幕：蒸餾 prompt、not evidence 條款、search()"
  echo "  6  wiki agent 與確定性 fallback     螢幕：兩個工具逛圖譜、失敗退純 Python 組頁"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "這是什麼 App（README + 骨架）" \
    "repo README 的產品自述、根目錄檔案結構、後端各檔行數" \
    "region-first 的產品洞察：框住你卡住的那一塊，而不是 chat with 整份 PDF"
  echo "── README.md 的產品自述 ─────────────────────────────────────"
  sed -n '19,26p' README.md
  echo
  echo "── 根目錄（前端 src/ + 後端五個 .py + 測試 + 設計文件）────────"
  ls
  echo
  echo "── 後端五個檔案的行數（全部讀得完）──────────────────────────"
  wc -l main.py region.py prompts.py memory.py deck.py
}

scene_2() {
  banner 2 "四把 system prompt (prompts.py)" \
    "27 行全文：<region_text> 為準、圖補版面、殘字標 [推測]、數學一律 LaTeX" \
    "prompt 是產品規格：雙通道的優先序要明文寫給模型，不是靠模型自己猜"
  cat prompts.py
}

scene_3() {
  banner 3 "region.py 雙通道抽取" \
    "81 行全文：fitz 座標不翻 y、TEXTFLAGS_TEXT 防 payload 暴漲、dpi 夾取省頻寬" \
    "每行註解都是一次實測換來的坑；掃描檔不丟例外、標 is_scanned 走純圖模式"
  cat region.py
}

scene_4() {
  banner 4 "/api/ask SSE 串流管線" \
    "build_contents 的穩定前綴（implicit cache）與 gen() 的四步管線註解" \
    "串流時代的錯誤處理：HTTP 已經 200，例外只能包成 error frame 塞進串流"
  echo "── build_contents：圖+原文放最前面 → implicit cache 命中點 ──"
  grep -n -A 18 "def build_contents" main.py
  echo
  echo "── /api/ask 的 gen()：抽取 → thread → 寫 DB → 串流 ──────────"
  grep -n -A 30 "async def gen():" main.py
  echo
  echo "── 為什麼錯誤只能轉 error frame ──────────────────────────────"
  grep -n -B 1 -A 1 "HTTP 已 200" main.py
}

scene_5() {
  banner 5 "記憶蒸餾與兩跳擴展" \
    "蒸餾 prompt（只抽長期價值、偏好要明講）、not evidence 條款、search() 兩跳" \
    "把模型輸出當不受信任的輸入；記憶可以引導、不是證據，當下框住的內容永遠優先"
  echo "── 蒸餾 prompt：日常翻譯回零節點、偏好要 explicit ────────────"
  grep -n -A 8 "Extract only durable research memory" main.py
  echo
  echo "── 記憶注入的紀律條款（format_memory_context）────────────────"
  grep -n -B 2 -A 3 "must not override" memory.py
  echo
  echo "── search()：FTS5 找種子 → 圖上最多擴展兩跳 ──────────────────"
  grep -n -A 6 "def search" memory.py
}

scene_6() {
  banner 6 "wiki agent 與確定性 fallback" \
    "WIKI_AGENT_PROMPT（兩個工具逛圖、絕不杜撰）與 _wiki_fallback 純 Python 組頁" \
    "每個 LLM 呼叫都要有一條不靠 LLM 的退路；agent 失敗不能開天窗"
  echo "── agent 的任務書：先逛圖（最多兩跳）再動筆 ──────────────────"
  grep -n -A 9 "WIKI_AGENT_PROMPT = " main.py
  echo
  echo "── 沒模型也要能出頁：確定性 fallback ─────────────────────────"
  grep -n -A 10 "def _wiki_fallback" main.py
  echo
  echo "── 後端測試防護網（含座標地基 4 條 assert）───────────────────"
  ls tests/
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
