#!/usr/bin/env bash
input=$(cat)
mkdir -p "${CURSOR_PROJECT_DIR:-.}/.cursor/hooks/log"
event=$(printf '%s' "$input" | jq -r '.hook_event_name // "unknown"')
printf '%s\n' "$input" | jq '.' \
  >> "${CURSOR_PROJECT_DIR:-.}/.cursor/hooks/log/${event}.jsonl"
echo '{}'
