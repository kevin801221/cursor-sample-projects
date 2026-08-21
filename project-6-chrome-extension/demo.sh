#!/usr/bin/env bash
# Project 6: Chrome 擴充功能 (Manifest V3) 課堂遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT/chrome-extension"
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
  echo "  Project 6：Chrome 擴充功能 (Manifest V3) － 課堂放映清單（共 ${TOTAL} 幕）"
  echo "======================================================================"
  echo "  1  MV3 三角色架構與安全性規則檢查   螢幕：實習生/總管/對講機與 .cursor/rules"
  echo "  2  Content Script 金鑰安全稽核 ⭐   螢幕：check_security.mjs 掃描確認 0 處金鑰洩露"
  echo "  3  訊息傳遞 (Message Passing) 機制 螢幕：sendMessage 跨環境通訊實作碼"
  echo "  4  啟動 Web 課堂放映模擬器 ⭐       螢幕：瀏覽器開啟模擬頁，現場選字、AI 摘要與儲存"
  echo "  5  擴充功能檔案清單與規格驗收       螢幕：manifest.json / popup / options 結構驗證"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "MV3 三角色架構與安全性規則檢查" \
    "印出 .cursor/rules/chrome-extension-security.mdc" \
    "實習生（content）派去別人家，身上絕對不能帶保險箱鑰匙（API Key）"
  cat .cursor/rules/chrome-extension-security.mdc
}

scene_2() {
  banner 2 "Content Script 金鑰安全稽核" \
    "執行 check_security.mjs，驗證 content.js 0% 包含金鑰與 MV3 格式合規" \
    "安全不能靠運氣：用自動化靜態檢查確保擴充功能不把金鑰送給造訪過的網頁"
  node check_security.mjs
}

scene_3() {
  banner 3 "訊息傳遞 (Message Passing) 機制" \
    "檢視 content.js (sendMessage) 與 background.js (onMessage) 的通訊實作" \
    "只有總管（Service Worker）能接觸金鑰並代理發送 LLM 請求"
  echo "▶ content.js 發送端："
  grep -n -A 10 "chrome.runtime.sendMessage" content.js
  echo
  echo "▶ background.js 接收與代理端："
  grep -n -A 15 "chrome.runtime.onMessage" background.js
}

scene_4() {
  banner 4 "啟動 Web 課堂放映模擬器" \
    "啟動本地 Python HTTP 伺服器，於瀏覽器開啟 simulator.html" \
    "課堂眼見為憑：免裝擴充功能，直接在網頁選字、彈出浮動工具列、AI 摘要與筆記儲存"
  echo "▶ 開啟課堂模擬器：http://localhost:8086/simulator.html"
  python3 -m http.server 8086
}

scene_5() {
  banner 5 "擴充功能檔案清單與規格驗收" \
    "顯示 manifest.json 與所有擴充前端檔案" \
    "符合 Chrome Web Store 發佈標準的乾淨專案結構"
  cat manifest.json
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
