#!/usr/bin/env bash
set -euo pipefail
input=$(cat)
file_path=$(printf '%s' "$input" | jq -r '.file_path // empty')

deny() {
  jq -n --arg m "$1" '{permission: "deny", user_message: $m}'
  exit 0
}

case "$file_path" in
  # 範本檔是安全的，先放行，順序很重要
  *.env.example|*.env.sample|*.env.template) ;;
  *.env|*.env.*|*.pem|*.key|*.p12|*id_rsa*|*/secrets/*|*/.aws/*)
    deny "已阻擋讀取機密檔案：${file_path##*/}（.cursor/hooks/guard-secrets.sh）"
    ;;
esac

jq -n '{permission: "allow"}'
