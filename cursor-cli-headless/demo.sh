#!/usr/bin/env bash
# Cursor CLI 與 Headless 自動化：課堂放映遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1

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
  echo "  第 19 章：Cursor CLI 與 Headless 自動化 － 課堂放映清單（共 ${TOTAL} 幕）"
  echo "======================================================================"
  echo "  1  安裝與版本驗證              螢幕：curl 安裝指令與 cursor --version"
  echo "  2  互動模式常用斜線指令        螢幕：/clear, /compact, /model 說明"
  echo "  3  Headless 模式與輸出格式     螢幕：-p, --force, text vs json 三格式"
  echo "  4  忘記 --force 的致命陷阱     螢幕：對照有無 --force 的執行行為"
  echo "  5  本地 CI 模擬自動 Code Review 螢幕：執行 scripts/ci-review.sh 產出報告"
  echo "  6  GitHub Actions 與兩層設定   螢幕：.github/workflows 與 cli-config.json"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "安裝與版本驗證" \
    "顯示安裝指令與 CLI 版本" \
    "Cursor CLI 是一切 Headless 與自動化的基礎"
  echo "官方安裝指令："
  echo "  curl https://cursor.com/install -fsS | bash"
  echo
  if command -v cursor >/dev/null 2>&1; then
    echo "✔ 偵測到本機已安裝 cursor："
    cursor --version 2>/dev/null || echo "cursor-cli installed"
  else
    echo "ℹ 尚未安裝，請複製上方指令進行安裝。"
  fi
}

scene_2() {
  banner 2 "互動模式常用斜線指令" \
    "列出終端機 TUI 模式的高頻 Slash Commands" \
    "/clear、/compact、/model 控制 Context 與模型切換"
  cat << 'EOF'
  /clear    - 清空當前對話歷史
  /compact  - 壓縮 context，保留重要摘要
  /model    - 切換使用的底層模型（如 claude-3-5-sonnet）
  /help     - 列出可用指令與快速鍵
EOF
}

scene_3() {
  banner 3 "Headless 模式與輸出格式" \
    "演示 -p 參數與 --output-format 格式" \
    "text 供人看、json 供 CI/腳本解析、stream-json 供串流監控"
  echo "1. text 格式（預設）："
  echo '   cursor -p "檢查程式碼" --force --output-format text'
  echo
  echo "2. json 格式（CI 解析）："
  echo '   cursor -p "檢查程式碼" --force --output-format json'
  echo
  echo "3. stream-json 格式（即時串流）："
  echo '   cursor -p "檢查程式碼" --force --output-format stream-json'
}

scene_4() {
  banner 4 "忘記 --force 的致命陷阱" \
    "解析 CI 永遠卡住超時 6 小時的根本原因" \
    "Non-interactive 環境沒有 TTY，無 --force 必卡死"
  cat << 'EOF'
❌ 錯誤寫法（CI 內永久卡住）：
   cursor -p "重構此檔案並跑測試"
   -> 終端停在：Allow Cursor to write to file? [y/n]
   -> CI 無人按鍵，卡住直到 Timeout 失敗！

✅ 正確寫法（無條件自動核准工具執行）：
   cursor -p "重構此檔案並跑測試" --force
EOF
}

scene_5() {
  banner 5 "本地 CI 模擬自動 Code Review" \
    "檢視並執行 scripts/ci-review.sh" \
    "在本地端一鍵觸發 Headless Agent 審查 Git Diff"
  cat scripts/ci-review.sh
  echo
  echo "--- 執行本地模擬 ---"
  ./scripts/ci-review.sh || true
}

scene_6() {
  banner 6 "GitHub Actions 與兩層設定" \
    "檢視 CI workflow 與 .cursor/cli-config.json" \
    "專案層設定覆蓋全域設定，安全定義自動核准與拒絕指令"
  echo "--- ① .cursor/cli-config.json ---"
  cat .cursor/cli-config.json
  echo
  echo "--- ② .github/workflows/cursor-code-review.yml ---"
  cat .github/workflows/cursor-code-review.yml
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
