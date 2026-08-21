#!/usr/bin/env bash
# 注意：這個 hook 不能往 stdout 印任何東西，
# 所有工具輸出都要導掉，否則會被當成無效的 JSON 回應。
input=$(cat)
file_path=$(printf '%s' "$input" | jq -r '.file_path // empty')
[ -f "$file_path" ] || exit 0

case "$file_path" in
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.md)
    npx --no-install prettier --write "$file_path" >/dev/null 2>&1 || true
    npx --no-install eslint --fix "$file_path" >/dev/null 2>&1 || true
    ;;
esac

exit 0
