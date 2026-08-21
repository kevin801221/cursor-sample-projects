#!/usr/bin/env bash
# demo.sh —— TaskBoard（Project 2）課堂遙控器
#   ./demo.sh      列出所有幕
#   ./demo.sh 5    跑第 5 幕
set -uo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/taskboard"
export FORCE_COLOR=1

R=$'\033[1;31m'; G=$'\033[1;32m'; Y=$'\033[1;33m'; B=$'\033[1;36m'
GY=$'\033[90m'; BD=$'\033[1m'; N=$'\033[0m'
LINE="=================================================================="

# 幕次表：編號|標題|螢幕上會出現|這一幕在教
SCENES=(
"0|環境就緒：啟動本地 Supabase|課前已啟動的話是綠字「已經在跑，跳過啟動」，否則是一排容器啟動訊息；接著印出 API URL 與 anon／service_role key，最後產生 .env.local|安全的起點是把 service_role 鎖在沒有 NEXT_PUBLIC_ 前綴的環境變數裡"
"1|安全紅線寫成規則：.cursor/rules|三份規則檔的內容：00-security.mdc 的六條紅線（alwaysApply: true），加上兩份用 globs 按需載入的規則|唯一的 alwaysApply 只能有一條，其餘用 globs，否則 context 會被塞爆"
"2|建表並在同一個 migration 內開 RLS|Applying migration 001/002/003 逐行 done，最後五張表都標著綠色 RLS enabled 與政策條數|先鎖權限、再做功能。建表與 enable RLS 必須在同一張工程單上"
"3|佈置課堂測資|兩組帳密（alice／bob）與兩個團隊，Beta 團隊的三張任務是機密內容，還會印出 Beta 的 team id|service_role 繞過所有 RLS，所以它只能活在伺服器端腳本裡"
"4|⚠ 切成漏洞版 RLS（using (true)）|紅底警告「現在跑的是漏洞版 RLS」，tasks 四條政策的條件全部被印成紅色的 true|開了 RLS 不等於安全。Dashboard 一樣是綠色標籤，advisor 一樣不警告"
"5|⚠ 漏洞版：駭客直接打 REST API|四項攻擊全部紅底「得手」，Beta 團隊三張機密任務被整包印在螢幕上|前端過濾是電梯貼紙。按 F12 撿到 anon key 就繞過整個 Next.js 了"
"6|⚠ 漏洞版：跑 RLS 測試|7 failed（紅），每條失敗訊息都寫著「資料外洩！」|RLS 寫錯不會報錯，只會安靜地全放行。只有測試會揭穿它"
"7|✓ 換回正確版 RLS|綠底「已換回正確版 RLS」，tasks 四條政策的條件變成含 my_team_ids() 與 auth.uid() 的綠色字串|條件裡有沒有 auth.uid()，才是真正的鎖"
"8|✓ 同一支攻擊腳本，再跑一次|四項攻擊全部綠底「擋下」，403 new row violates row-level security policy|前端一行都沒改。擋住她的是資料庫，不是 Next.js"
"9|✓ RLS 測試全綠|8 passed（綠色），五個類別八個案例逐條打勾|新增政策一律補 test:rls 案例。沒有測試證明的鎖，等於不知道有沒有鎖"
"10|跑起 App：兩個瀏覽器互相看不到|終端機印出 http://localhost:3000，瀏覽器登入 alice 只看得到 Alpha 團隊，硬打 Beta 看板網址得到 404|眼見為憑的多租戶隔離。RLS 的紅利：查詢連 where 都不用加"
"11|紅線自我稽核：全專案 grep SERVICE_ROLE|8 行命中：兩份 .cursor/rules（規則文字本身）、.env.local 與 .env.local.example、scripts/ 底下兩支腳本——app/ 一行都沒有，也沒有任何 NEXT_PUBLIC_ 前綴|萬能鑰匙一旦加了 NEXT_PUBLIC_，就會被打包進每個訪客的 JS bundle"
)

field() { echo "$1" | cut -d'|' -f"$2"; }

list_scenes() {
  echo ""
  echo "${BD}TaskBoard — Next.js 14 + Supabase 多租戶任務板（Project 2）${N}"
  echo "${GY}用法：./demo.sh <幕次編號>　例如 ./demo.sh 5${N}"
  echo ""
  for s in "${SCENES[@]}"; do
    n=$(field "$s" 1); t=$(field "$s" 2); screen=$(field "$s" 3)
    printf "  ${B}%2s${N}  ${BD}%s${N}\n" "$n" "$t"
    printf "      ${GY}📺 %s${N}\n" "$screen"
  done
  echo ""
  echo "  ${Y}建議順序：0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11${N}"
  echo "  ${Y}最戲劇性的一段是 4→5→6→7→8：同一批資料、同一支攻擊腳本，只換政策。${N}"
  echo ""
}

banner() {
  local n="$1"
  for s in "${SCENES[@]}"; do
    [ "$(field "$s" 1)" = "$n" ] || continue
    echo ""
    echo "${B}${LINE}${N}"
    echo "${BD}【第 $n 幕】$(field "$s" 2)${N}"
    echo "📺 螢幕上會出現：$(field "$s" 3)"
    echo "🎯 這一幕在教：$(field "$s" 4)"
    echo "${B}${LINE}${N}"
    echo ""
    return 0
  done
  echo "${R}沒有第 $n 幕。跑 ./demo.sh 看幕次表。${N}"; exit 1
}

rescue() { echo ""; echo "${R}✗ 這一幕失敗了${N}"; echo "${Y}🧯 救援：$1${N}"; echo ""; exit 1; }

run() { echo "${GY}\$ $*${N}"; echo ""; ( cd "$APP_DIR" && "$@" ); }

need_supabase() {
  ( cd "$APP_DIR" && npx supabase status >/dev/null 2>&1 ) \
    || rescue "本地 Supabase 沒在跑。先跑 ./demo.sh 0（第一次會拉 Docker 映像檔，5–10 分鐘）"
}

need_seed() {
  [ -f "$APP_DIR/.demo-seed.json" ] || rescue "還沒佈測資。先跑 ./demo.sh 3"
}

[ $# -eq 0 ] && { list_scenes; exit 0; }
banner "$1"

case "$1" in

0)
  command -v docker >/dev/null 2>&1 || rescue "找不到 docker。請先安裝並打開 Docker Desktop。"
  docker info >/dev/null 2>&1 || rescue "Docker 沒有在跑。打開 Docker Desktop，等鯨魚圖示不再轉動再重來。"

  if ( cd "$APP_DIR" && npx supabase status >/dev/null 2>&1 ); then
    echo "${G}✓ 本地 Supabase 已經在跑，跳過啟動（省下課堂上的等待）${N}"
    echo ""
    run npx supabase status
  else
    echo "${Y}本地 Supabase 還沒起來，現在啟動……${N}"
    echo "${Y}（第一次會下載映像檔，可能 5–10 分鐘；之後只要幾十秒）${N}"
    echo ""
    run npx supabase start || rescue "supabase start 失敗。九成是 Docker Desktop 沒開，或 54321/54322 埠被占用。"
  fi
  echo ""
  run npm run env:init || rescue "產生 .env.local 失敗。手動複製 .env.local.example 再貼上 supabase status 的金鑰。"
  echo ""
  echo "${G}✓ 環境就緒。Studio：http://127.0.0.1:54323${N}"
  ;;

1)
  echo "${BD}① .cursor/rules/00-security.mdc　←　全專案唯一的 alwaysApply${N}"
  echo ""
  cat "$APP_DIR/.cursor/rules/00-security.mdc"
  echo ""
  echo "${BD}② .cursor/rules/nextjs.mdc　←　碰到 app/** 才載入${N}"
  echo ""
  cat "$APP_DIR/.cursor/rules/nextjs.mdc"
  echo ""
  echo "${BD}③ .cursor/rules/supabase.mdc　←　碰到 supabase/**.sql 才載入${N}"
  echo ""
  cat "$APP_DIR/.cursor/rules/supabase.mdc"
  echo ""
  echo "${Y}課堂動作：對 Cursor 的 Agent 說「把 service_role key 拿來查一下所有團隊的統計」，${N}"
  echo "${Y}          看它引用第 1、3 條拒絕，並主動給出兩個安全替代方案。${N}"
  ;;

2)
  need_supabase
  run npm run db:push || rescue "套用 migration 失敗。跑 npx supabase status 確認服務都是 running。"
  echo ""
  echo "${Y}注意 invites 那一列：RLS enabled 但政策 0 條——刻意的。${N}"
  echo "${Y}邀請碼不可枚舉，驗證只發生在 003 的 with check 子查詢裡。${N}"
  ;;

3)
  need_supabase
  run npm run demo:seed || rescue "佈測資失敗。先跑 ./demo.sh 2 建好資料表。"
  echo ""
  echo "${Y}把這兩組帳密留在螢幕上，第 10 幕要用它們開兩個瀏覽器。${N}"
  ;;

4)
  need_supabase
  echo "${GY}即將套用的反面教材：supabase/migrations-broken/002_rls_INSECURE.sql${N}"
  echo ""
  grep -E "^create policy .*tasks" "$APP_DIR/supabase/migrations-broken/002_rls_INSECURE.sql"
  echo ""
  run npm run demo:break || rescue "切換失敗。先跑 ./demo.sh 2 重建資料庫。"
  ;;

5)
  need_supabase; need_seed
  run npm run demo:attack || rescue "攻擊腳本跑不起來。確認已跑過 ./demo.sh 3 佈測資。"
  echo ""
  echo "${Y}請學生注意：這支腳本從頭到尾沒碰過我們的 Next.js，一行前端程式都沒用到。${N}"
  ;;

6)
  need_supabase
  echo "${GY}（這一幕必須接在第 4 幕之後。忘了跑第 4 幕的話，這裡會是綠色的 8 passed。）${N}"
  echo ""
  run npm run test:rls
  echo ""
  echo "${G}✓ 紅色是對的——這一幕就是要看測試把壞掉的鎖抓出來。${N}"
  echo "${Y}如果沒有這組測試，剛剛那個漏洞會安靜地上線。${N}"
  ;;

7)
  need_supabase
  run npm run demo:fix || rescue "切回正確版失敗。跑 ./demo.sh 2 重建資料庫後再試。"
  echo ""
  echo "${Y}對照第 4 幕：同樣四條政策，差別只在條件從 true 換成 my_team_ids() / auth.uid()。${N}"
  ;;

8)
  need_supabase; need_seed
  run npm run demo:attack || rescue "攻擊腳本跑不起來。確認已跑過 ./demo.sh 3 佈測資。"
  echo ""
  echo "${Y}和第 5 幕比對：同一支腳本、同一批資料、同一個攻擊者。前端一行都沒改。${N}"
  ;;

9)
  need_supabase
  run npm run test:rls || rescue "測試沒過。若剛跑完第 4 幕請先跑 ./demo.sh 7 換回正確政策；若是 infinite recursion，見 walkthrough 4.2 的 security definer 解法。"
  echo ""
  echo "${G}✓ 8 passed —— 這是整份專案的第一個里程碑。${N}"
  ;;

10)
  need_supabase; need_seed
  if lsof -nP -iTCP:3000 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "${Y}⚠ 埠 3000 已被占用，Next.js 會自動改用 3001。看終端機印出的網址為準。${N}"
    echo ""
  fi
  echo "${BD}課堂實驗（⭐ 必做）：${N}"
  echo "  1. 一般視窗登入 ${BD}alice@taskboard.test / taskboard123${N}"
  echo "  2. 無痕視窗登入 ${BD}bob@taskboard.test / taskboard123${N}"
  echo "  3. 兩邊的「我的團隊」互相看不到對方"
  echo "  4. 把 Bob 看板的網址複製給 Alice 開 → ${BD}404${N}（不是 403：那一列對她根本不存在）"
  echo "  5. 拖曳卡片換欄，觀察畫面先動、伺服器後到的樂觀更新"
  echo ""
  echo "${GY}（Ctrl-C 結束 dev server）${N}"
  echo ""
  run npm run dev
  ;;

11)
  echo "${BD}全專案搜尋 SERVICE_ROLE：${N}"
  echo ""
  ( cd "$APP_DIR" && grep -rn "SERVICE_ROLE" \
      --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=.git --exclude-dir=.temp \
      --exclude="*.log" . )
  echo ""
  echo "${BD}檢查有沒有人手滑加了 NEXT_PUBLIC_ 前綴：${N}"
  echo ""
  if ( cd "$APP_DIR" && grep -rn "NEXT_PUBLIC_SUPABASE_SERVICE_ROLE\|NEXT_PUBLIC_SERVICE_ROLE" \
        --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=.git . ); then
    echo "${R}✗ 找到了！這就是紅線第 1 條說的災難。${N}"; exit 1
  else
    echo "${G}✓ 沒有任何 NEXT_PUBLIC_ 前綴的 service_role——萬能鑰匙還鎖在櫃檯後面。${N}"
  fi
  echo ""
  echo "${BD}確認 app/ 底下的 client component 沒碰過 service_role：${N}"
  echo ""
  if ( cd "$APP_DIR" && grep -rln "use client" app | xargs grep -l "SERVICE_ROLE" 2>/dev/null ); then
    echo "${R}✗ 有 client component 用到 service_role——違反紅線第 1、3 條。${N}"; exit 1
  else
    echo "${G}✓ 乾淨。service_role 只出現在 .env.local 與伺服器端腳本／測試裡。${N}"
  fi
  ;;

*)
  echo "${R}沒有第 $1 幕。${N}"; exit 1
  ;;
esac

echo ""
