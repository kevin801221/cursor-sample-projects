#!/usr/bin/env bash
set -euo pipefail

input=$(cat)
root="${CURSOR_PROJECT_DIR:-.}"
conv=$(printf '%s' "$input" | jq -r '.conversation_id // "unknown"')
status=$(printf '%s' "$input" | jq -r '.status // ""')
loop=$(printf '%s' "$input" | jq -r '.loop_count // 0')
edited="$root/.cursor/state/$conv.edited"
roles="$root/.cursor/state/$conv.roles"

# 中斷或出錯就不囉嗦
[ "$status" = "completed" ] || { echo '{}'; exit 0; }

# 這輪完全沒改過檔案（純問答、純查詢），不需要驗證。
# .edited 記號由 afterFileEdit 的 format-edit.sh 寫入。
[ -f "$edited" ] || { echo '{}'; exit 0; }

# 改過檔，但 verifier 沒跑過（roles 由 subagentStop 的 subagent-report.sh 寫入；
# grep -s：連 roles 檔都不存在 = 一個 subagent 都沒 spawn，更要催）
if ! grep -qs '^verifier$' "$roles" && [ "$loop" -lt 1 ]; then
  jq -n '{followup_message: "這一輪改了檔案，但還沒有跑過 verifier。請用 verifier subagent 實際執行測試並回報結果，不要只是宣稱完成。"}'
  exit 0
fi

echo '{}'
