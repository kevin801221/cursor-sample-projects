#!/usr/bin/env bash
#
# demo.sh — 講師的遙控器
#
#   ./demo.sh          列出所有幕
#   ./demo.sh 3        跑第 3 幕
#   ./demo.sh stop     關掉 dev server
#
# 全程離線：不需要任何 API key，不連任何外部網站。
set -uo pipefail

cd "$(dirname "$0")"
PORT_FILE=".demo-port"
PID_FILE=".demo-server.pid"
LOG_FILE=".demo-server.log"

# ---------------------------------------------------------------- 小工具

hr() { printf '=%.0s' {1..72}; echo; }

banner() {
  echo
  hr
  echo "【第 $1 幕】$2"
  echo "📺 螢幕上會出現：$3"
  echo "🎯 這一幕在教：$4"
  hr
  echo
}

# 訊息一律走 stderr：server_url() 是被 $(...) 抓 stdout 的，
# 任何印到 stdout 的字都會被當成網址的一部分（第一次跑會混進 npm install 的輸出）
die() {
  {
    echo
    echo "❌ $1"
    echo "🧯 救援：$2"
  } >&2
  exit 1
}

need_node() {
  command -v node >/dev/null 2>&1 || die "找不到 node" "先安裝 Node.js 18+：https://nodejs.org"
  local major
  major="$(node -p 'process.versions.node.split(".")[0]')"
  [ "$major" -ge 18 ] || die "Node.js 版本太舊（目前 v$major）" "升級到 Node.js 18 以上再跑一次"
}

need_deps() {
  if [ ! -d node_modules ]; then
    echo "第一次跑，先裝套件（約 10–30 秒，之後就不用了）…" >&2
    npm install >&2 || die "npm install 失敗" "檢查網路，或改用 npm install --registry=https://registry.npmjs.org"
  fi
}

# 回傳 dev server 的網址；沒開就開一個（Vite 會自己找沒被占用的 port）
server_url() {
  local url=""
  if [ -f "$PORT_FILE" ]; then
    local p
    p="$(cat "$PORT_FILE")"
    if curl -s --max-time 2 "http://localhost:$p/" 2>/dev/null | grep -q "Rooftop Dash"; then
      echo "http://localhost:$p"
      return
    fi
  fi
  if curl -s --max-time 2 "http://localhost:5173/" 2>/dev/null | grep -q "Rooftop Dash"; then
    echo "5173" > "$PORT_FILE"
    echo "http://localhost:5173"
    return
  fi

  need_deps
  echo "啟動 Vite dev server…" >&2
  : > "$LOG_FILE"
  npm run dev >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"

  local i port=""
  for i in $(seq 1 40); do
    port="$(grep -oE 'localhost:[0-9]+' "$LOG_FILE" 2>/dev/null | head -1 | cut -d: -f2)"
    [ -n "$port" ] && break
    sleep 0.5
  done
  [ -n "$port" ] || die "dev server 起不來" "看看 $LOG_FILE 裡的錯誤訊息，或直接手動跑 npm run dev"
  echo "$port" > "$PORT_FILE"
  url="http://localhost:$port"
  echo "$url"
}

open_url() {
  local url="$1"
  echo "👉 網址：$url"
  if command -v open >/dev/null 2>&1; then
    open "$url"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url"
  else
    echo "（請自己把上面的網址貼到瀏覽器）"
  fi
}

stop_server() {
  if [ -f "$PID_FILE" ]; then
    local pid
    pid="$(cat "$PID_FILE")"
    pkill -P "$pid" 2>/dev/null
    kill "$pid" 2>/dev/null
    rm -f "$PID_FILE" "$PORT_FILE"
    echo "✅ dev server 已關閉"
  else
    echo "（沒有由 demo.sh 啟動的 dev server）"
  fi
}

show_file() {
  echo "---------- $1 ----------"
  cat "$1"
  echo
}

# ---------------------------------------------------------------- 幕次表

list_scenes() {
  cat <<'LIST'

  Rooftop Dash — 課堂放映表（./demo.sh <編號>）

  1  環境檢查與自我檢查        螢幕：node/npm 版本 + 綠色 ✅ 檢查清單全過
  2  起遊戲：主選單 → 第 1 關   螢幕：ROOFTOP DASH 標題，進場後角色會跑會跳、敵人在巡邏
  3  規則檔就是教材            螢幕：三個 .mdc 規則檔的完整內容印在終端機
  4  第 2 關：金幣與出口門      螢幕：Coins 0/7、紅色的門；收齊後門變綠、過關
  5  暫停：按 P                螢幕：整個畫面靜止 + 半透明黑幕 + 白色 PAUSED
  6  一個數字改變整個手感       螢幕：改 constants.js 存檔，遊戲不重整就變成月球跳
  7  沉默故障（壞的）           螢幕：紅色數據面板，穿模次數一直往上加，console 全綠
  8  沉默故障（修好的）         螢幕：同一個畫面變綠色，穿模 0 次，角色穩穩落地
  9  打包與 base 路徑          螢幕：npm run build 成功 + preview 打得開

  stop  關掉 dev server

LIST
}

# ---------------------------------------------------------------- 各幕

scene_1() {
  banner 1 "環境檢查與自我檢查" \
    "node 與 npm 版本，接著一整排綠色 ✅（穿模算術 + 兩關關卡資料）" \
    "非平凡邏輯要留一個跑得起來的檢查；不是靠肉眼看程式碼"
  need_node
  echo "node $(node --version)　npm $(npm --version)"
  need_deps
  echo
  node physics-check.mjs || die "自我檢查沒過" "照著紅色 ❌ 那行改 src/constants.js 的數值，再跑一次 ./demo.sh 1"
}

scene_2() {
  banner 2 "起遊戲：主選單 → 第 1 關" \
    "黃色 ROOFTOP DASH 標題與閃爍的『按 SPACE 開始』；進場後角色能跑能跳，紅色敵人來回巡邏，HUD 顯示 Lives: 3 Coins: 0/5" \
    "Vite + Phaser 的骨架：一個 Game 實例、三個場景、場景之間切得動"
  local url
  url="$(server_url)" || exit 1
  echo "課堂動作：按 SPACE 進遊戲 → ← → 移動 → SPACE 跳躍 → 故意去撞紅色敵人扣一命"
  open_url "$url/"
}

scene_3() {
  banner 3 "規則檔就是教材" \
    ".cursor/rules 三個 .mdc 檔的完整內容（架構規則、Phaser 慣例、八欄位模板）" \
    "一檔一職責 + 常數置頂：把規則寫成檔案，Agent 才會照著做"
  show_file ".cursor/rules/00-architecture.mdc"
  show_file ".cursor/rules/phaser.mdc"
  show_file ".cursor/rules/prompt-template.mdc"
  echo "課堂動作：在 Cursor 裡對 Agent 說「把 PlayScene 的跳躍改成 setVelocityY(-700)」，"
  echo "          它應該拒絕並要求改用 constants.js。沒擋下來就是規則沒生效（重啟 Cursor）。"
}

scene_4() {
  banner 4 "第 2 關：金幣與出口門" \
    "HUD 顯示『第 2 關 · 天台缺口　Coins: 0/7』與『出口門：鎖住（還差 7 顆）』；收齊後門從紅變綠，走進門就過關" \
    "狀態存 registry 不存 this；出口門的判斷條件寫在 constants，不寫死在場景"
  local url
  url="$(server_url)" || exit 1
  echo "課堂動作：先故意跑去撞門（會跳出「門還鎖著，還差 N 顆」）→ 再去收金幣 → 回頭進門"
  echo "提示：不想真的玩，就在 DevTools 打："
  echo "      s = __game.scene.getScene('PlayScene'); s.coins.getChildren().slice().forEach(c => s.onCoin(s.player, c))"
  open_url "$url/?demo=level2"
}

scene_5() {
  banner 5 "暫停：按 P" \
    "角色、敵人、金幣全部定格，畫面壓上半透明黑幕與置中白色 PAUSED，背景音樂停止" \
    "只暫停 update 沒暫停 physics 角色會繼續掉；遮罩只能有一層，連按 P 不准越來越黑"
  local url
  url="$(server_url)" || exit 1
  echo "課堂動作：進遊戲後連按 P 五下 —— 畫面不會越來越黑（遮罩只有一層），再按一下就恢復"
  open_url "$url/?demo=level1"
}

scene_6() {
  banner 6 "一個數字改變整個手感" \
    "改完 constants.js 存檔的瞬間，Vite 自動重新載入頁面並直接回到第 1 關，跳躍高度從約 150px 變成約 300px" \
    "常數置頂（鐵律 2）：調手感只碰一個檔案、一個數字，碰不到碰撞邏輯"
  local url
  url="$(server_url)" || exit 1
  echo "現在的值："
  grep -n "JUMP_VELOCITY:" src/constants.js
  echo
  echo "課堂動作：把 src/constants.js 的 PLAYER.JUMP_VELOCITY 從 520 改成 800，存檔（不用動瀏覽器）。"
  echo "          網址列的 ?demo=level1 會讓它自動跳回第 1 關，馬上就能跳給學生看。"
  echo "          注意上限：MAX_VELOCITY_Y 是 900，設超過 900 就會被限速削掉、反而沒感覺。"
  echo "          示範完記得改回 520，再跑 ./demo.sh 1 確認自我檢查全綠。"
  open_url "$url/?demo=level1"
}

scene_7() {
  banner 7 "沉默故障（壞的版本）" \
    "紅色數據面板：CONTINUOUS_COLLISION = false，最高速度 5000+ px/s、單幀位移 84px > 平台厚度 20px，『已經穿過平台 N 次』的 N 一直加，畫面每次穿過都閃紅" \
    "鐵律 3：程式跑得好好的、console 一行錯誤都沒有，但遊戲是壞的——只有玩才發現"
  local url
  url="$(server_url)" || exit 1
  echo "課堂動作：打開 DevTools Console 給學生看 —— 一行紅字都沒有，但角色一直掉出地板。"
  open_url "$url/?demo=tunneling"
}

scene_8() {
  banner 8 "沉默故障（修好的版本）" \
    "同一個畫面轉綠：CONTINUOUS_COLLISION = true，最高速度被壓在 900 px/s、單幀位移 15px < 20px，『穿模 0 次』，角色每次都穩穩站在平台上" \
    "setMaxVelocity() 不是可選的；修好的路徑跟壞掉的是同一份程式碼，差別只有一個布林值"
  local url
  url="$(server_url)" || exit 1
  echo "對照重點：兩個網址只差 &fix=1，程式碼一行都沒改，改的是 PHYSICS.CONTINUOUS_COLLISION。"
  grep -n "CONTINUOUS_COLLISION" src/constants.js | head -3
  open_url "$url/?demo=tunneling&fix=1"
}

scene_9() {
  banner 9 "打包與 base 路徑" \
    "npm run build 印出 dist/index.html 與 dist/assets/index-xxx.js，接著 preview 打開一模一樣的遊戲" \
    "vite.config.js 的 base：設成 './' 才能部署到子路徑，不然上線後資源 404、畫面全黑"
  need_deps
  npm run build || die "build 失敗" "先跑 ./demo.sh 1 確認環境，再看終端機第一個 error 指到哪個檔案"
  echo
  grep -n "base" vite.config.js | head -3
  echo
  echo "課堂動作：npm run preview 之後打開網址；再把 base 改成 '/wrong/' 重 build 一次，"
  echo "          會看到白畫面 + console 一堆 404 —— 這就是部署後最常見的那個坑。"
}

# ---------------------------------------------------------------- 進入點

case "${1:-}" in
  "")     list_scenes ;;
  stop)   stop_server ;;
  1|2|3|4|5|6|7|8|9) "scene_$1" ;;
  *)      echo "不認得的參數：$1"; list_scenes; exit 1 ;;
esac
