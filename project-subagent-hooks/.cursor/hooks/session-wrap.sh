#!/usr/bin/env bash
set -euo pipefail

input=$(cat)
root="${CURSOR_PROJECT_DIR:-.}"
conv=$(printf '%s' "$input" | jq -r '.conversation_id // "unknown"')
status=$(printf '%s' "$input" | jq -r '.status // ""')
loop=$(printf '%s' "$input" | jq -r '.loop_count // 0')
roles="$root/.cursor/state/$conv.roles"

# 中斷或出錯就不囉嗦
[ "$status" = "completed" ] || { echo '{}'; exit 0; }

# 這輪完全沒改過檔案（純問答），不需要驗證
[ -f "$roles" ] || { echo '{}'; exit 0; }

if ! grep -q '^verifier$' "$roles" && [ "$loop" -lt 1 ]; then
  jq -n '{followup_message: "這一輪還沒有跑過 verifier。請用 verifier subagent 實際執行測試並回報結果，不要只是宣稱完成。"}'
  exit 0
fi

echo '{}'
