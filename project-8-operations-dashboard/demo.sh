#!/usr/bin/env bash
# 講師的遙控器：./demo.sh 看所有幕，./demo.sh N 跑第 N 幕。
# 全程離線，不需要任何 API key。
set -uo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$ROOT/dashboard"
cd "$APP_DIR" || exit 1

TOTAL=8

# ---------------------------------------------------------------- 幕次資料 ----
title() {
  case "$1" in
    1) echo "產生「刻意帶瑕疵」的資料（固定 seed，全班一模一樣）" ;;
    2) echo "先看髒資料長什麼樣：前 10 列 + 資料品質報告" ;;
    3) echo "型別陷阱：壞掉的版本 vs 修好的版本" ;;
    4) echo "清理管線：每一步都印出丟棄列數" ;;
    5) echo "四個指標與它們的分母定義" ;;
    6) echo "pytest 全綠 → 故意改壞變紅 → 還原" ;;
    7) echo "快取的威力：同一個篩選切兩次" ;;
    8) echo "開儀表板：五個頁面、篩選器、排序切換" ;;
  esac
}

screen() {
  case "$1" in
    1) echo "兩張「瑕疵注入清單」表格（email 缺失 150 列、amount 負值 200 列…），最後 501 與 2001 行" ;;
    2) echo "髒資料前 10 列（空白 email、2024年03月05日、Taipei），以及缺失率／型別／離群值報告" ;;
    3) echo "上半段：amount.sum() 吐出一個近 6000 字元的字串；下半段：轉成 float64 後總金額 927,006" ;;
    4) echo "13 個【步驟】區塊，每個都是「清理前 N 列 → 去掉「原因」-M 列 → 清理後 K 列」，最後 2000 → 1644" ;;
    5) echo "2024 全年 12 列的指標總表：MRR、ARPU、活躍客戶、次月留存率，以及總轉換率 69.4%" ;;
    6) echo "先看到 8 passed 與 4 passed，改壞後 1 failed 顯示「Obtained: 250.0 Expected: 300.0」，還原後又全綠" ;;
    7) echo "第 1 次 6–12 ms、第 2 次 0.5 ms 上下（快 15–25 倍），而計時區間內的 [DEBUG] 檔案讀取 只印一次" ;;
    8) echo "五個頁面自我檢查全 ✓，然後瀏覽器打開 localhost:8501 的儀表板" ;;
  esac
}

teaches() {
  case "$1" in
    1) echo "合成資料的瑕疵是「設計」出來的，固定 seed 才能課堂重現" ;;
    2) echo "鐵律 1：先探索、再清理——沒看過報告就寫清理邏輯是盲目的" ;;
    3) echo "amount 混進字串時 sum() 不會報錯，只會給你一個錯得離譜的答案" ;;
    4) echo "鐵律 2：每一步都印出丟棄列數，資料流失才看得見" ;;
    5) echo "鐵律 3：分母定義要統一，寫進 docstring 才不會各算各的" ;;
    6) echo "測試要能變紅才有意義；用小到能手算的資料當斷言依據" ;;
    7) echo "@st.cache_data 只快取「讀檔」，篩選與排序要留在快取外面" ;;
    8) echo "多頁儀表板 + 篩選器 + 排序切換，而且不會重新讀檔" ;;
  esac
}

files() {
  case "$1" in
    1) echo "dashboard/generate_data.py" ;;
    2) echo "dashboard/pipeline.py（explore/quality_report）、dashboard/DATA_QUALITY_REPORT.md" ;;
    3) echo "dashboard/pipeline.py（trap_demo、clean_amount_text）" ;;
    4) echo "dashboard/pipeline.py（clean_data、_step）" ;;
    5) echo "dashboard/metrics.py" ;;
    6) echo "dashboard/test_metrics.py、dashboard/test_pipeline.py" ;;
    7) echo "dashboard/data_access.py" ;;
    8) echo "dashboard/app.py、dashboard/pages/*.py" ;;
  esac
}

# ------------------------------------------------------------------ 工具 ------
banner() {
  local n="$1"
  echo
  echo "================================================================"
  echo "【第 $n 幕】$(title "$n")"
  echo "📺 螢幕上會出現：$(screen "$n")"
  echo "🎯 這一幕在教：$(teaches "$n")"
  echo "📂 建議打開的檔案：$(files "$n")"
  echo "================================================================"
  echo
}

rescue() {
  echo
  echo "----------------------------------------------------------------"
  echo "🧯 這一幕卡住了。救援提示："
  echo "   $1"
  echo "----------------------------------------------------------------"
  exit 1
}

need_uv() {
  command -v uv >/dev/null 2>&1 || {
    echo "找不到 uv。安裝：curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
  }
}

need_raw() {
  [ -f data/customers_raw.csv ] || rescue "還沒有原始資料。先跑：./demo.sh 1"
}

need_clean() {
  [ -f data/customers_clean.csv ] || rescue "還沒有清理後的資料。先跑：./demo.sh 4"
}

usage() {
  echo
  echo "================================================================"
  echo "  Project 8：營運數據儀表板（pandas + Streamlit）— 課堂幕次表"
  echo "================================================================"
  for n in $(seq 1 $TOTAL); do
    printf "\n  第 %s 幕  %s\n" "$n" "$(title "$n")"
    printf "          📺 %s\n" "$(screen "$n")"
  done
  echo
  echo "----------------------------------------------------------------"
  echo "  用法：./demo.sh N     （例如 ./demo.sh 4）"
  echo "  第一次上課請依序跑 1 → 8；第 8 幕會開瀏覽器，用 Ctrl+C 結束。"
  echo "  全程離線，不需要任何 API key。"
  echo "================================================================"
  echo
}

# ------------------------------------------------------------------ 各幕 ------
scene_1() {
  need_uv
  echo "▶ uv sync（第一次會裝套件，之後幾秒就好）"
  uv sync --quiet || rescue "套件裝不起來。檢查網路，或先跑 uv sync 看完整錯誤訊息。"
  echo "▶ uv run python generate_data.py"
  uv run python generate_data.py || rescue "Faker 沒裝好？跑 uv add faker 再試一次。"
  echo
  echo "▶ wc -l data/*_raw.csv   （501 與 2001＝含表頭，代表 500 與 2000 列）"
  wc -l data/customers_raw.csv data/transactions_raw.csv
}

scene_2() {
  need_raw
  echo "▶ uv run python pipeline.py --report"
  uv run python pipeline.py --report || rescue "讀不到 CSV？先跑 ./demo.sh 1 產生資料。"
  echo
  echo "（同樣的內容整理成文件版：dashboard/DATA_QUALITY_REPORT.md）"
}

scene_3() {
  need_raw
  echo "▶ uv run python pipeline.py --trap"
  uv run python pipeline.py --trap || rescue "讀不到 CSV？先跑 ./demo.sh 1 產生資料。"
}

scene_4() {
  need_raw
  echo "▶ uv run python pipeline.py"
  uv run python pipeline.py || rescue "看終端機最後一行的錯誤；多半是 data/*_raw.csv 不見了，重跑 ./demo.sh 1。"
  echo
  echo "▶ wc -l data/*_clean.csv   （比原始檔少，就是被丟掉的髒資料）"
  wc -l data/customers_clean.csv data/transactions_clean.csv
  echo
  echo "（完整日誌留在 dashboard/pipeline.log）"
}

scene_5() {
  need_clean
  echo "▶ uv run python metrics.py"
  uv run python metrics.py || rescue "先跑 ./demo.sh 4 產生 data/*_clean.csv。"
}

scene_6() {
  echo "▶ uv run pytest -q          （metrics 4 個 + pipeline 4 個 = 8 passed）"
  uv run pytest -q || rescue "測試紅了。看第一個 FAILED 的檔名與行號，那就是壞掉的地方。"
  echo
  echo "▶ uv run pytest test_metrics.py -v   （課本第 7.2 節的畫面：4 passed）"
  uv run pytest test_metrics.py -v
  echo
  echo "================================================================"
  echo "  現在故意把 monthly_mrr 改壞：拿掉「只算 amount > 0」這個條件"
  echo "  （改的是 .demo_broken/ 裡的複製品，原始碼一個字都沒動）"
  echo "================================================================"
  rm -rf .demo_broken && mkdir -p .demo_broken
  cp metrics.py test_metrics.py .demo_broken/
  # 用 perl 而不是 sed，macOS 與 Linux 的行為才會一致
  perl -i -pe 's/rows = df\[\(df\["month"\] == year_month\) & \(df\["amount"\] > 0\)\]/rows = df[df["month"] == year_month]/' .demo_broken/metrics.py
  echo "▶ uv run pytest .demo_broken/test_metrics.py -q"
  uv run pytest .demo_broken/test_metrics.py -q
  echo
  echo "  ↑ 1 failed：MRR 變成 250（100 + 200 - 50），少了「濾掉退款」那一刀。"
  echo "    這就是為什麼測試資料要小到能手算——250 跟 300 的差別，你一眼看得出來。"
  rm -rf .demo_broken
  echo
  echo "▶ 還原後再跑一次：uv run pytest -q"
  uv run pytest -q || rescue "還原後還是紅的？檢查 .demo_broken 是否已刪除（rm -rf dashboard/.demo_broken）。"
}

scene_7() {
  need_clean
  echo "▶ uv run python data_access.py"
  uv run python data_access.py 2>/dev/null || rescue "先跑 ./demo.sh 4 產生 data/*_clean.csv。"
}

scene_8() {
  need_clean
  echo "▶ uv run python smoke_app.py   （不開瀏覽器先確認五個頁面都不會炸）"
  uv run python smoke_app.py 2>/dev/null || rescue "有頁面壞了，上面那一行 ✗ 就是壞掉的檔案。"
  echo
  echo "================================================================"
  echo "  接下來瀏覽器會打開 http://localhost:8501"
  echo "  課堂動線："
  echo "    1) 首頁三張 KPI 卡片 → 展開「四個指標的分母定義」"
  echo "    2) 左側切到「概覽」看 MRR 走勢，再切到「地區分析」"
  echo "    3) ⭐ 切換「排序方式」radio，柱子重排——回頭看終端機，"
  echo "       [DEBUG] 檔案讀取 還是只印過一次"
  echo "    4) 拉左邊的方案／地區／月份篩選器，圖表跟著變"
  echo "  結束請按 Ctrl+C"
  echo "================================================================"
  echo
  uv run streamlit run app.py || rescue "port 8501 被占用？改用：uv run streamlit run app.py --server.port 8502"
}

# ------------------------------------------------------------------ 進入點 ----
if [ $# -eq 0 ]; then
  usage
  exit 0
fi

case "$1" in
  1|2|3|4|5|6|7|8)
    banner "$1"
    "scene_$1"
    echo
    echo "✅ 第 $1 幕結束。"
    ;;
  *)
    echo "只有第 1 到第 $TOTAL 幕。直接跑 ./demo.sh 看幕次表。"
    exit 1
    ;;
esac
