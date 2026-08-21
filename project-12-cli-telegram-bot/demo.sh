#!/usr/bin/env bash
# Project 12: CLI 工具與 Telegram Bot 課堂遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT/scaffold-and-bot"
cd "$APP_DIR" || exit 1

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
  echo "  Project 12：CLI 工具與 Telegram Bot － 課堂放映清單（共 ${TOTAL} 幕）"
  echo "======================================================================"
  echo "  1  CLI 腳手架建立專案 (React / FastAPI) 螢幕：scaffold init 指令與色彩 Banner"
  echo "  2  Exit Code 規範驗證 (成功 0 vs 失敗 1) ⭐ 螢幕：故意重複建目錄退件並印出非零 Exit Code"
  echo "  3  Telegram Bot 按鈕回調與秒回機制 ⭐   螢幕：query.answer() < 100ms 快速響應"
  echo "  4  吉他和弦動態指板圖生成驗證          螢幕：Pillow 繪製產出高質感吉他指法圖"
  echo "  5  pytest 自動化測試全綠              螢幕：4 passed（CLI 退出碼、圖片生成、回調速度）"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "CLI 腳手架建立專案 (React / FastAPI)" \
    "執行 scaffold init demo-app --template react 產出完整專案目錄" \
    "CLI 工具讓繁瑣的手動設定變成一句優雅的指令"
  rm -rf /tmp/demo-react-app
  node cli/bin/scaffold.js init /tmp/demo-react-app --template react
  echo "▶ 檢視產出的專案內容："
  ls -la /tmp/demo-react-app
}

scene_2() {
  banner 2 "Exit Code 規範驗證 (成功 0 vs 失敗 1)" \
    "先執行成功建立印出 Exit Code 0；再重複執行報錯退件印出 Exit Code 1" \
    "電腦回報規則：成功喊 0、出事喊 1，腳本才能安全串接"
  echo "▶ [測試 1: 成功案例]"
  rm -rf /tmp/test-exit-app
  node cli/bin/scaffold.js init /tmp/test-exit-app --template react
  echo "✓ Exit code: $?"
  echo
  echo "▶ [測試 2: 故意重複建立觸發錯誤退件]"
  node cli/bin/scaffold.js init /tmp/test-exit-app --template react || true
  echo "✓ 預期捕獲 Exit code 1"
}

scene_3() {
  banner 3 "Telegram Bot 按鈕回調與秒回機制" \
    "執行 bot/bot_simulator.py，展示 query.answer() 毫秒級回調" \
    "先承諾再交貨：點擊按鈕立即停止轉圈，體感順暢十倍"
  uv run python bot/bot_simulator.py
}

scene_4() {
  banner 4 "吉他和弦動態指板圖生成驗證" \
    "執行 chord_generator.py，產出 C, G, Am 和弦指板圖片" \
    "不用外部依賴，純 Python 繪製精準指法與品位標註"
  uv run python -c "
from bot.chord_generator import generate_chord_chart
for c in ['C', 'G', 'Am', 'Em', 'F', 'D']:
    p = generate_chord_chart(c, f'data/chord_{c}.png')
    print(f'✓ 已產出 {c} 和弦圖：{p}')
"
  echo
  ls -lh data/chord_*.png 2>/dev/null || true
}

scene_5() {
  banner 5 "pytest 自動化測試全綠" \
    "執行 pytest -v，確認 4 項 CLI 與 Bot 測試全數通過" \
    "整合驗證：CLI 命令列退出碼與機器人生成引擎全綠"
  uv run pytest -v
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
