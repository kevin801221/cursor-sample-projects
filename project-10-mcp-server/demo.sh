#!/usr/bin/env bash
# Project 10 · Company Knowledge & Tickets MCP Server —— 課堂放映遙控器
#
#   ./demo.sh          列出所有幕
#   ./demo.sh 3        跑第 3 幕
#   ./demo.sh reset    把 data/tickets.json 還原成課前狀態
#
# 全程離線：create_ticket 走本地 provider（DEMO_OFFLINE 預設開），不需要任何 API key。

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$ROOT/company-mcp-server"
cd "$APP" || exit 1

BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31;1m'; GREEN=$'\033[32;1m'
YELLOW=$'\033[33m'; CYAN=$'\033[36m'; OFF=$'\033[0m'
LINE="=================================================================="

banner() {  # banner <幕號> <標題> <螢幕上會出現> <這一幕在教>
  printf '\n%s%s%s\n' "$BOLD" "$LINE" "$OFF"
  printf '%s【第 %s 幕】%s%s\n' "$BOLD" "$1" "$2" "$OFF"
  printf '📺 螢幕上會出現：%s\n' "$3"
  printf '🎯 這一幕在教：%s\n' "$4"
  printf '%s%s%s\n\n' "$BOLD" "$LINE" "$OFF"
}

step() {  # step <說明> ；印出接下來要跑的指令
  printf '%s$ %s%s\n' "$CYAN" "$1" "$OFF"
}

hint() {
  printf '\n%s🧯 救援提示：%s%s\n' "$YELLOW" "$1" "$OFF"
}

ensure_deps() {
  if [ ! -d node_modules ]; then
    printf '%s第一次跑，先安裝依賴（需要網路，裝完之後的 demo 都不用網路）…%s\n' "$DIM" "$OFF"
    npm install --silent || { hint "npm install 失敗。檢查網路，或用 npm install --registry=https://registry.npmjs.org/ 重試。"; exit 1; }
  fi
}

ensure_build() {
  ensure_deps
  if [ ! -f dist/index.js ] || [ -n "$(find src -name '*.ts' -newer dist/index.js -print -quit)" ]; then
    printf '%s偵測到還沒編譯（或 src 比 dist 新），先跑 npm run build…%s\n' "$DIM" "$OFF"
    npm run build || { hint "TypeScript 編譯失敗。先看錯誤訊息第一行，多半是 import 路徑少了 .js 副檔名。"; exit 1; }
  fi
}

list_scenes() {
  printf '\n%sProject 10 · MCP Server 課堂幕次%s   %s(離線可跑，不需要 API key)%s\n' "$BOLD" "$OFF" "$DIM" "$OFF"
  printf '%s\n' "$LINE"
  printf '%s  幕  標題                        螢幕上會出現%s\n' "$BOLD" "$OFF"
  printf '  1   專案骨架與編譯              npm run build 跑完，dist/ 裡出現 index.js／tools／resources\n'
  printf '  2   協定長什麼樣（tools/list）  JSON-RPC 請求與回應原文，兩個工具的 inputSchema\n'
  printf '  3   呼叫工具＋分頁              search_knowledge_base 回傳 200 字摘要、total／hasMore\n'
  printf '  4   Zod 擋下壞紙條              isError:true 與「搜尋字串不能空白」等中文訊息\n'
  printf '  5   建立工單（有副作用）        回傳 TKT-0004 created successfully\n'
  printf '  6   ⭐ 外部 API 壞掉時          約 8000 ms 後回「連線逾時（8 秒）」；503 時回「工單沒有建立」\n'
  printf '  7   Resource tickets://all      工單清單 JSON，最後一筆就是剛剛建的那張\n'
  printf '  8   Prompt triage_ticket        先查知識庫再決定要不要開票的指引全文\n'
  printf '  9   ⭐ 反面教材：污染 stdout    同一支 server 兩次：JSON.parse 失敗 ✗ vs 成功 ✔\n'
  printf ' 10   自我檢查                    11 條 ✔，含逾時、分頁、無 console.log\n'
  printf ' 11   接進 Cursor                 產生 .cursor/mcp.json（絕對路徑）與重啟指引\n'
  printf '%s\n' "$LINE"
  printf '用法：%s./demo.sh 3%s   還原資料：%s./demo.sh reset%s\n\n' "$BOLD" "$OFF" "$BOLD" "$OFF"
}

scene_1() {
  banner 1 "專案骨架與編譯" \
    "專案結構樹、npm run build 的 tsc 輸出、dist/ 底下產生的 .js 檔" \
    "MCP server 就是一支普通的 Node 程式；先打好樑柱（初始化＋編譯）再裝家具（工具）"
  step "find src data -type f | sort"
  find src data -type f | sort
  printf '\n'
  step "npm run build && ls dist dist/tools dist/resources"
  ensure_deps
  npm run build || { hint "編譯失敗就看錯誤第一行。ESM 專案的 import 一定要帶 .js（import ... from \"./tools/search.js\"）。"; return 1; }
  ls dist dist/tools dist/resources
}

scene_2() {
  banner 2 "協定長什麼樣：initialize 與 tools/list" \
    "一來一往的 JSON-RPC 原文：送出 REQUEST（青色）→ 收到 RESPONSE（綠色），含兩個工具的 inputSchema" \
    "MCP 不是魔法，就是 stdin／stdout 上的 JSON 紙條；Cursor 側欄的 Connected 就是 initialize 成功"
  ensure_build
  # MCP_INSPECT_FULL=1：inspect.mjs 預設截斷超過 34 行的回應，tools/list 有 74 行，
  # 不加這個變數 create_ticket 的 inputSchema 會被截掉，就對不上上面那句「兩個工具」。
  step "MCP_INSPECT_FULL=1 node scripts/inspect.mjs tools"
  MCP_INSPECT_FULL=1 node scripts/inspect.mjs tools || hint "沒有回應就先跑 npm run build，再確認 dist/index.js 存在。"
}

scene_3() {
  banner 3 "呼叫工具：搜尋、tag 過濾、分頁" \
    "search_knowledge_base 回傳 {id,title,tag,excerpt}，excerpt 最多 200 字（KB-001 剛好斷在「三、憑證」）；翻頁時 total 不變、文章不重複" \
    "鐵律 2：回傳精簡。整篇 content 對模型沒用，只會塞爆 context"
  ensure_build
  step "node scripts/inspect.mjs search page"
  node scripts/inspect.mjs search page || hint "找不到文章就檢查 data/knowledge.json 是否存在、是否為合法 JSON（node -e \"JSON.parse(require('fs').readFileSync('data/knowledge.json'))\"）。"
}

scene_4() {
  banner 4 "Zod 擋下壞紙條" \
    "三個失敗回應，isError:true，訊息是「搜尋字串不能空白」「limit 最多 20」「priority 只能是 low、medium 或 high」" \
    "第一道防線：模型亂填參數時，工具要用人話退件，而不是丟 stack trace"
  ensure_build
  step "node scripts/inspect.mjs zod"
  node scripts/inspect.mjs zod || hint "若看到英文的 Zod 錯誤，代表 schema 少寫了中文訊息參數。"
}

scene_5() {
  banner 5 "建立工單：有副作用的動作" \
    "create_ticket 回 {\"ticketId\":\"TKT-00xx\",\"message\":\"Ticket TKT-00xx created successfully\"}" \
    "Tools 會改變世界（工單真的被寫進 data/tickets.json），所以描述裡要提醒模型「先查再開」"
  ensure_build
  step "node scripts/inspect.mjs ticket"
  node scripts/inspect.mjs ticket || hint "寫檔失敗請確認 data/tickets.json 存在且可寫；要回到課前狀態就跑 ./demo.sh reset。"
}

scene_6() {
  banner 6 "⭐ 外部 API 壞掉時：逾時與 5xx" \
    "第一段等 8 秒後回「Ticket API 連線逾時（8 秒）」（右上角會顯示 8000 ms 出頭）；第二段秒回「Ticket API 回傳 503，工單沒有建立」" \
    "AbortController 逾時保護＋錯誤可讀：模型看得懂才會換策略，看到 stack trace 只會盲目重試"
  ensure_build
  printf '%s（第一段會刻意等 8 秒——那 8 秒就是逾時保護在數秒，別以為當掉了）%s\n\n' "$DIM" "$OFF"
  step "DEMO_TICKET_DELAY_MS=99000 node scripts/inspect.mjs timeout"
  DEMO_TICKET_DELAY_MS=99000 node scripts/inspect.mjs timeout
  printf '\n'
  step "DEMO_TICKET_FAIL=1 node scripts/inspect.mjs fail"
  DEMO_TICKET_FAIL=1 node scripts/inspect.mjs fail || hint "沒看到逾時訊息就檢查 src/tools/tickets.ts 的 AbortController 有沒有把 signal 傳進 fetch。"
}

scene_7() {
  banner 7 "Resource tickets://all" \
    "resources/list 列出一個資源，resources/read 回傳工單清單 JSON——最後一筆就是第 5 幕建的那張" \
    "Resources 是「給我看現在的狀態」，Tools 是「請做一件事」；清單只給 5 個欄位，不給 description 全文"
  ensure_build
  step "node scripts/inspect.mjs resources"
  node scripts/inspect.mjs resources || hint "讀不到就確認 data/tickets.json 是合法 JSON 陣列。"
}

scene_8() {
  banner 8 "Prompt triage_ticket" \
    "prompts/get 回傳一整段中文指引：先 search_knowledge_base，查得到就回答、查不到才 create_ticket" \
    "Prompts 是「預設路線」——把人的決策流程寫死成一鍵套用，模型才不會一有抱怨就開票"
  ensure_build
  step "node scripts/inspect.mjs prompts"
  node scripts/inspect.mjs prompts || hint "prompts/list 空的話，檢查 Server 建構子的 capabilities 有沒有寫 prompts: {}。"
}

scene_9() {
  banner 9 "⭐ 反面教材：一行 console.log 毀掉整個 server" \
    "同一支 server 跑兩次：壞的那次 stdout 第一行是 [debug] server starting...，JSON.parse 失敗 ✗；好的那次是純 JSON，✔" \
    "鐵律 3：stdout 唯一合法內容是 JSON-RPC 訊息。除錯訊息一律 console.error 走 stderr"
  ensure_build
  step "node scripts/break-stdout.mjs"
  node scripts/break-stdout.mjs
  printf '\n'
  step "grep -rn 'console.log' src/"
  if grep -rn 'console.log' src/; then
    printf '%s☝ 命中的兩行都是 src/index.ts 的註解（在解釋這個反模式），沒有任何一行是真正的呼叫。%s\n' "$YELLOW" "$OFF"
  else
    printf '%s（沒有任何命中）%s\n' "$DIM" "$OFF"
  fi
}

scene_10() {
  banner 10 "自我檢查：非平凡邏輯都有 assert 守著" \
    "11 行 ✔：搜尋、tag、分頁、三種 Zod 退件、建票、Resource 欄位、逾時、503、無 console.log，最後印「全部檢查通過」" \
    "先驗後接（鐵律 1）：接進 Cursor 之前，每條路徑都要有跑得起來的驗證"
  ensure_build
  step "node scripts/check.mjs"
  node scripts/check.mjs || hint "哪一條 ✘ 就看它的錯誤第一行；check.mjs 跑完會自動還原 data/tickets.json。"
}

scene_11() {
  banner 11 "接進 Cursor：產生 .cursor/mcp.json（絕對路徑）" \
    "終端機印出剛寫好的 .cursor/mcp.json 內容，args 是這台機器上的絕對路徑，接著是重啟 Cursor 的三步驟指引" \
    "相對路徑會因為 Cursor 啟動時的工作目錄而失效；絕對路徑才保證找得到"
  ensure_build
  mkdir -p "$APP/.cursor"
  cat > "$APP/.cursor/mcp.json" <<JSON
{
  "mcpServers": {
    "company-knowledge": {
      "command": "node",
      "args": ["$APP/dist/index.js"],
      "env": {
        "KNOWLEDGE_API_URL": "https://api.tickets.local",
        "DEMO_OFFLINE": "1"
      }
    }
  }
}
JSON
  step "cat .cursor/mcp.json"
  cat "$APP/.cursor/mcp.json"
  printf '\n'
  step "node -e \"JSON.parse(require('fs').readFileSync('.cursor/mcp.json'));\" && ls -l dist/index.js"
  if node -e "JSON.parse(require('fs').readFileSync('.cursor/mcp.json'))"; then
    printf '%s✔ JSON 語法合法%s\n' "$GREEN" "$OFF"
  else
    printf '%s✘ JSON 語法有問題%s\n' "$RED" "$OFF"
  fi
  ls -l dist/index.js
  cat <<TXT

${BOLD}接下來在 Cursor 做這三步：${OFF}
  1. 用 Cursor 開啟資料夾：${CYAN}$APP${OFF}
     （或把上面那段 JSON 貼進 ~/.cursor/mcp.json，就變成全域可用）
  2. 完全結束 Cursor 再重新開啟（Cmd+Q，不是關視窗）
  3. Settings → Features → MCP，側欄應顯示 ${GREEN}company-knowledge  Connected${OFF}
     再問 Agent：「這個 MCP Server 提供哪些工具和資源？」
     它應該答出 search_knowledge_base、create_ticket、tickets://all、triage_ticket

${YELLOW}🧯 沒有 Connected 時的順序：${OFF}
  a. ls "$APP/dist/index.js"          檔案在不在
  b. node "$APP/dist/index.js"        會不會當場報錯（正常會停住等 stdin，Ctrl+C 離開）
  c. 檢查 mcp.json 是不是絕對路徑、JSON 有沒有多逗號
  d. grep -rn 'console.log' src/      有沒有人偷偷加了除錯訊息
TXT
}

reset_data() {
  cp "$APP/data/tickets.seed.json" "$APP/data/tickets.json"
  printf '%s✔ data/tickets.json 已還原成課前的 3 筆工單（.cursor/mcp.json 保留，第 11 幕會覆寫）。%s\n' "$GREEN" "$OFF"
}

case "${1:-}" in
  ""|list|--list|-l) list_scenes ;;
  reset) reset_data ;;
  1) scene_1 ;;
  2) scene_2 ;;
  3) scene_3 ;;
  4) scene_4 ;;
  5) scene_5 ;;
  6) scene_6 ;;
  7) scene_7 ;;
  8) scene_8 ;;
  9) scene_9 ;;
  10) scene_10 ;;
  11) scene_11 ;;
  *) printf '%s不認得的幕次「%s」。%s跑 ./demo.sh 看有哪些幕。\n' "$RED" "$1" "$OFF"; exit 1 ;;
esac
