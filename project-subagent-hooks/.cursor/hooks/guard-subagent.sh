#!/usr/bin/env bash
# subagentStart：在 subagent 被 spawn「之前」把關——連生出來的機會都不給。
# 注意：這個事件的 permission 只支援 allow|deny，回 "ask" 會被 Cursor 當成 deny。
set -euo pipefail
input=$(cat)

root="${CURSOR_PROJECT_DIR:-.}"
mkdir -p "$root/.cursor/state"

get() { printf '%s' "$input" | jq -r "$1"; }
stype=$(get '.subagent_type // "unknown"')
task=$(get '.task // ""')

# 留痕：記下每一次 spawn（誰、要做什麼）
printf '%s\t%s\t%s\n' "$(date +%Y%m%d-%H%M%S)" "$stype" "${task:0:120}" \
  >> "$root/.cursor/state/subagent-spawns.log"

# 護欄：任務描述帶部署／正式環境字眼的 subagent，不准自動生成
shopt -s nocasematch
if [[ "$task" =~ (deploy|production|正式環境|上線|發布) ]]; then
  jq -n \
    '{permission: "deny",
      user_message: "已阻擋 subagent 生成：任務涉及部署／正式環境，請由人類直接下指令（guard-subagent.sh）"}'
  exit 0
fi

jq -n '{permission: "allow"}'
