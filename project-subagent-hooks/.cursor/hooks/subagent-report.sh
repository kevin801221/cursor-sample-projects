#!/usr/bin/env bash
set -euo pipefail

input=$(cat)
root="${CURSOR_PROJECT_DIR:-.}"
mkdir -p "$root/.cursor/reports" "$root/.cursor/state"

get() { printf '%s' "$input" | jq -r "$1"; }
conv=$(get '.conversation_id // "unknown"')
type=$(get '.subagent_type // "unknown"')
desc=$(get '.description // ""')
task=$(get '.task // ""')
status=$(get '.status // "unknown"')
summary=$(get '.summary // ""')
files=$(printf '%s' "$input" | jq -r '(.modified_files // []) | map("- `" + . + "`") | join("\n")')

# 用 description + task 一起判斷是哪個自訂 subagent（type 可能都是 generalPurpose）
blob=$(printf '%s %s %s' "$type" "$desc" "$task" | tr '[:upper:]' '[:lower:]')
role=other
case "$blob" in
  *security*|*audit*|*稽核*) role=security-auditor ;;
  *verif*|*驗證*) role=verifier ;;
  *plan*|*計畫*|*規劃*) role=planner ;;
esac

ts=$(date +%Y%m%d-%H%M%S)
out="$root/.cursor/reports/${ts}-${role}.md"

{
  echo "# ${desc:-$role}"
  echo
  echo "- 角色：\`$role\`（subagent_type: \`$type\`）"
  echo "- 狀態：\`$status\`"
  echo "- 耗時：$(get '.duration_ms // 0') ms，工具呼叫 $(get '.tool_call_count // 0') 次"
  echo "- 對話：\`$conv\`"
  echo
  echo "## 任務"
  echo
  echo "${task:-（無）}"
  echo
  echo "## 修改的檔案"
  echo
  echo "${files:-（無 — 這是唯讀 subagent 應有的結果）}"
  echo
  echo "## 回報內容"
  echo
  echo "$summary"
} > "$out"

# 記錄這一輪跑過哪些角色，給 stop hook 用
echo "$role" >> "$root/.cursor/state/$conv.roles"

# 稽核發現 Critical → 自動把球踢回給主 agent
if [ "$status" = "completed" ] && [ "$role" = "security-auditor" ] \
  && printf '%s' "$summary" | grep -q '^Critical:'; then
  jq -n --arg p "${out#$root/}" \
    '{followup_message: ("安全稽核回報了 Critical 等級問題（完整報告：" + $p + "）。請立刻處理所有 Critical 項目，修完後再跑一次 security-auditor 確認。其他工作先暫停。")}'
  exit 0
fi

echo '{}'
