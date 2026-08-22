#!/usr/bin/env bash
# beforeMCPExecution：MCP 是資料離開本機的通道，這個 hook 是海關。
# 設計目標是同時管住主 agent 與 subagent 的出境資料（subagent 的 MCP 工具是繼承來的）；
# 但「subagent 內部呼叫是否逐一觸發本 hook」官方文件未載明——安全底線不要只押在這裡。
set -euo pipefail
input=$(cat)

tool=$(printf '%s' "$input" | jq -r '.tool_name // "unknown"')
# tool_input 可能是物件也可能是字串，一律序列化成文字再掃描
args=$(printf '%s' "$input" | jq -r '.tool_input | if type == "string" then . else tojson end')

# 出境檢查：參數裡出現 secrets 特徵就攔下（API key、AWS key、私鑰、連線字串）
if printf '%s' "$args" | grep -qE 'sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|://[^/[:space:]]+:[^@[:space:]]+@'; then
  jq -n --arg t "$tool" \
    '{permission: "deny",
      user_message: ("已阻擋 MCP 呼叫 " + $t + "：參數疑似夾帶 secrets（guard-mcp.sh）"),
      agent_message: "你嘗試把疑似 secrets 的內容當參數送給外部 MCP tool，已被 hook 阻擋。請改用去識別化的內容重試，secrets 永遠不該離開本機。"}'
  exit 0
fi

jq -n '{permission: "allow"}'
