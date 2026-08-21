#!/usr/bin/env bash
# Project 7: Python 爬蟲價格監控 PriceBot 課堂遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT/pricebot"
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
  echo "  Project 7：Python 爬蟲價格監控 PriceBot － 課堂放映清單（共 ${TOTAL} 幕）"
  echo "======================================================================"
  echo "  1  爬蟲倫理與合法合規檢查       螢幕：.cursor/rules/crawler-ethics.mdc 規範"
  echo "  2  執行爬取任務 (常規價格收集)  螢幕：robots.txt 通過、BeautifulSoup 解析、寫入 SQLite"
  echo "  3  模擬價格跳水與 Telegram 告警 ⭐ 螢幕：商品特價 -20%、觸發降價告警推播"
  echo "  4  pytest 自動化測試全綠       螢幕：3 passed（robots 阻擋、Pydantic 驗證、降價偵測）"
  echo "  5  啟動 Streamlit 價格監控儀表板 ⭐ 螢幕：瀏覽器開啟價格折線圖與商品管理控制台"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "爬蟲倫理與合法合規檢查" \
    "印出 crawler-ethics.mdc 規則檔：遵守 robots.txt、禮貌延遲、不抓個資" \
    "合法合規比技術難度更重要——動手前先確認四件事"
  cat .cursor/rules/crawler-ethics.mdc
}

scene_2() {
  banner 2 "執行爬取任務 (常規價格收集)" \
    "執行 PriceCrawler 抓取 4 款商品並建立 SQLite 價格歷史庫" \
    "先探索、再解析、Pydantic 嚴格清洗與驗證型別"
  uv run python -c "from src.crawler import PriceCrawler; crawler = PriceCrawler(); crawler.crawl_mock_store(apply_discount=False)"
}

scene_3() {
  banner 3 "模擬價格跳水與 Telegram 告警" \
    "模擬商品特價（鍵盤降價 -20%），系統自動偵測並派發 Telegram 降價推播" \
    "比對歷史價格庫，精準計算降幅並自動派發推播"
  uv run python -c "from src.crawler import PriceCrawler; crawler = PriceCrawler(); crawler.crawl_mock_store(apply_discount=True)"
}

scene_4() {
  banner 4 "pytest 自動化測試全綠" \
    "執行 pytest -v，確認 3 項合規與降價測試全數通過" \
    "用可執行的測試證明爬蟲安全與商業邏輯正確"
  uv run pytest -v
}

scene_5() {
  banner 5 "啟動 Streamlit 價格監控儀表板" \
    "啟動 Streamlit 伺服器，瀏覽器開啟價格趨勢分析儀表板" \
    "可視化展示：即時點擊爬取、商品價格歷史折線圖與 Telegram 狀態"
  echo "▶ 啟動 Streamlit 儀表板..."
  uv run streamlit run app.py
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
