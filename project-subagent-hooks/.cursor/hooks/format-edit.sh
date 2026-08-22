#!/usr/bin/env bash
# 注意：這個 hook 不能往 stdout 印任何東西，
# 所有工具輸出都要導掉，否則會被當成無效的 JSON 回應。
input=$(cat)
file_path=$(printf '%s' "$input" | jq -r '.file_path // empty')

# 給 stop hook 的記號：這個對話改過檔案（session-wrap.sh 靠它判斷要不要催驗證）
conv=$(printf '%s' "$input" | jq -r '.conversation_id // "unknown"')
root="${CURSOR_PROJECT_DIR:-.}"
mkdir -p "$root/.cursor/state" && touch "$root/.cursor/state/$conv.edited"

[ -f "$file_path" ] || exit 0

case "$file_path" in
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.md)
    npx --no-install prettier --write "$file_path" >/dev/null 2>&1 || true
    ;;
esac

exit 0
