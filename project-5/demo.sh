#!/usr/bin/env bash
# Project 5: FastAPI 後端 API 與短網址服務 課堂遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT/shortenurl"
cd "$APP_DIR" || exit 1

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
  echo "  Project 5：FastAPI 後端與短網址服務 － 課堂放映清單（共 ${TOTAL} 幕）"
  echo "======================================================================"
  echo "  1  分層架構與三層職責守則檢查   螢幕：Routers / Services / Repositories 邊界規則"
  echo "  2  Pydantic 安檢門阻擋壞請求 ⭐  螢幕：非法 URL 格式直接在門口被 422 退回"
  echo "  3  短網址生成與資料庫寫入       螢幕：URLService 產出 6 碼短網址並存入 SQLite"
  echo "  4  BackgroundTask 非同步點擊分析 ⭐ 螢幕：轉址毫秒級秒回，點擊次數在背景自動增加"
  echo "  5  pytest 自動化測試全綠       螢幕：4 passed（建立、衝突、驗證、轉址分析）"
  echo "  6  啟動服務與管理介面 (Web/Docs) ⭐ 螢幕：瀏覽器開啟 Swagger /docs 與管理後台"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "分層架構與三層職責守則檢查" \
    "印出 architecture.mdc 與 app/ 目錄架構" \
    "外場（router）不進冷藏庫、倉管（repo）不炒菜——三層邊界嚴格劃分"
  cat .cursor/rules/architecture.mdc
  echo
  echo "▶ 程式目錄架構："
  ls -R app/
}

scene_2() {
  banner 2 "Pydantic 安檢門阻擋壞請求" \
    "檢視 schemas/url.py 中的 field_validator 網址驗證規則" \
    "壞資料在門口就擋下，不浪費後端運算與資料庫連線"
  grep -n -A 20 "validate_target_url" app/schemas/url.py
}

scene_3() {
  banner 3 "短網址生成與資料庫寫入" \
    "檢視 services/url_service.py 與 repositories/url_repo.py 協同實作" \
    "業務邏輯集中在 Service，資料庫操作隔離在 Repository"
  grep -n -A 25 "def shorten_url" app/services/url_service.py
}

scene_4() {
  banner 4 "BackgroundTask 非同步點擊分析" \
    "檢視 url_router.py 中的 BackgroundTasks 調度" \
    "一邊端菜給客人（307 Redirect），一邊在背景記帳，轉址零延遲"
  grep -n -A 20 "redirect_short_url" app/routers/url_router.py
}

scene_5() {
  banner 5 "pytest 自動化測試全綠" \
    "執行 pytest -v，四項核心測試全數通過 (4 passed)" \
    "沒有測試證明的架構，等於不知道有沒有寫對"
  uv run pytest -v
}

scene_6() {
  banner 6 "啟動服務與管理介面 (Web/Docs)" \
    "啟動 Uvicorn 伺服器，瀏覽器開啟 http://localhost:8000 (Swagger 在 /docs)" \
    "可視化展示：建立短網址、複製連結、點擊轉址、即時點擊次數與日誌"
  echo "▶ 啟動 FastAPI 服務：http://localhost:8000"
  uv run uvicorn app.main:app --reload --port 8000
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
