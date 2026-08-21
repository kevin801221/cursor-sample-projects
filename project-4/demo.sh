#!/usr/bin/env bash
# Project 4: React Native + Expo 習慣追蹤 App 課堂遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT/habit-tracker"
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
  echo "  Project 4：習慣追蹤 App (Expo/RN) － 課堂放映清單（共 ${TOTAL} 幕）"
  echo "======================================================================"
  echo "  1  專案架構與 Scope 規則檢查     螢幕：.cursor/rules/00-scope.mdc 邊界約束"
  echo "  2  資料模型與 Streak 計算驗證 ⭐  螢幕：連續天數算法與離線種子資料"
  echo "  3  狀態持久化與打卡邏輯         螢幕：HabitCard 狀態切換與 completedDates 陣列"
  echo "  4  啟動 App（手機模擬器視圖）⭐   螢幕：瀏覽器開啟 iPhone 框架之習慣追蹤 App"
  echo "  5  打包編譯驗收                 螢幕：npm run build 成功產出"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "專案架構與 Scope 規則檢查" \
    "印出 00-scope.mdc 規則檔：強制開發順序與 UI 邊界約束" \
    "行動端 UI 一改就跑版，用規則和 Checkpoint 雙重把關"
  cat .cursor/rules/00-scope.mdc
}

scene_2() {
  banner 2 "資料模型與 Streak 計算驗證" \
    "顯示 types/habit.ts 與 calculateStreak 演算法" \
    "先定義尺寸（型別）再裁縫（UI），避免先做畫面後接資料的返工"
  cat src/types/habit.ts
}

scene_3() {
  banner 3 "狀態持久化與打卡邏輯" \
    "檢視 habitStorage.ts 的 loadHabits / saveHabits 離線持久化邏輯" \
    "離線打卡先行，同步做在背景層"
  grep -n -A 15 "calculateStreak" src/services/habitStorage.ts
}

scene_4() {
  banner 4 "啟動 App（手機模擬器視圖）" \
    "啟動 Vite 開發伺服器，於瀏覽器中展示高質感 iPhone 模擬器與打卡互動" \
    "眼見為憑：點擊按鈕完成打卡、Streak 連續天數自動累加、切換深淺色主題"
  echo "▶ 啟動 Habit Tracker 伺服器..."
  npm run dev
}

scene_5() {
  banner 5 "打包編譯驗收" \
    "TypeScript 靜態檢查與 Vite 打包產出" \
    "零警告零錯誤的產出"
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
