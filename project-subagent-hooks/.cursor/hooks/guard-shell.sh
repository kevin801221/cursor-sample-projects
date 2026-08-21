#!/usr/bin/env bash
set -euo pipefail
input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.command // empty')

respond() {
  jq -n --arg p "$1" --arg u "$2" --arg a "$3" \
    '{permission: $p, user_message: $u, agent_message: $a}'
  exit 0
}

shopt -s nocasematch

# 不可逆的資料操作 → 直接擋，並告訴 agent 該怎麼改做
if [[ "$cmd" =~ (migrate[[:space:]]+reset|drop[[:space:]]+(table|database)|truncate[[:space:]]+table) ]]; then
  respond deny \
    "已阻擋破壞性資料庫指令" \
    "這個指令會清空資料，已被 hook 阻擋。請改用可逆的 migration，或建立獨立的測試資料庫。需要重置正式資料時請交給人類執行。"
fi

if [[ "$cmd" =~ rm[[:space:]]+-rf[[:space:]]+(/|~|\$HOME) ]]; then
  respond deny \
    "已阻擋 rm -rf 指令" \
    "這個刪除指令的範圍過大，已被 hook 阻擋。請明確指定要刪除的相對路徑。"
fi

# force push → 不擋死，改成問人
if [[ "$cmd" =~ push.*--force ]]; then
  respond ask \
    "agent 想執行 force push：$cmd" \
    "force push 需要人工核准。"
fi

jq -n '{permission: "allow"}'
