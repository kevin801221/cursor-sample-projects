#!/usr/bin/env bash
# Project 3: UI 元件庫 (Figma/截圖轉 React 元件庫) 課堂遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT/component-library"
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
  echo "  Project 3：Figma/截圖轉 React 元件庫 － 課堂放映清單（共 ${TOTAL} 幕）"
  echo "======================================================================"
  echo "  1  Design Tokens 結構與規格表   螢幕：tokens.ts 與 tokens.css 集中定義"
  echo "  2  紅線阻擋與靜態規則稽核 ⭐     螢幕：check.mjs 掃描所有元件，確認 0 處寫死十六進位"
  echo "  3  四大核心元件與 A11y 檢驗     螢幕：Button / Input / Card / Modal 屬性與焦點測試"
  echo "  4  啟動互動元件展示台 (Web) ⭐   螢幕：瀏覽器開啟現代元件庫展示台與 Props 控制台"
  echo "  5  打包編譯與構建驗證          螢幕：npm run build 成功產出 dist/ 靜態資源"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "Design Tokens 結構與規格表" \
    "印出 tokens.ts 與 index.css 中的色彩、間距、圓角標準規格" \
    "設計系統先行：色票與規格表統一，全站元件自動長得像一家人"
  cat src/tokens/tokens.ts
}

scene_2() {
  banner 2 "紅線阻擋與靜態規則稽核" \
    "check.mjs 自動檢查：全數元件 0 寫死色碼、全數包含 A11y 標籤" \
    "寫進 .cursor/rules，讓 AI 在生成程式碼時主動阻擋一次性樣式"
  node check.mjs
}

scene_3() {
  banner 3 "四大核心元件與 A11y 檢驗" \
    "顯示 Button、Input、Card、Modal 的實作碼與 A11y aria-* 屬性" \
    "無障礙不是最後才加的功能——Input 標籤關聯、Modal ESC 關閉第一天就要做對"
  echo "▶ Input.tsx A11y 標籤："
  grep -n "aria-" src/components/Input.tsx
  echo
  echo "▶ Modal.tsx 鍵盤 ESC 與焦點處理："
  grep -n "Escape" src/components/Modal.tsx
}

scene_4() {
  banner 4 "啟動互動元件展示台 (Web)" \
    "啟動 Vite 開發伺服器，瀏覽器展示高質感 Dark/Light 主題元件庫展示台" \
    "眼見為憑：透過即時 Props 面板切換 Variant、Size、Loading 與 Modal"
  echo "▶ 啟動 Vite 展示伺服器..."
  npm run dev
}

scene_5() {
  banner 5 "打包編譯與構建驗證" \
    "TypeScript 靜態檢查 (tsc -b) 與 Vite 打包成功，產出 dist/index.html" \
    "發佈前驗證：零警告零錯誤的乾淨 Bundle"
  npm run build
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
