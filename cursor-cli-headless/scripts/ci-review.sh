#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "🔍 啟動 Cursor CLI 本地自動化 Code Review"
echo "========================================="

# 1. 模擬取得 Git Diff（若無則取 git status）
DIFF_CONTENT=$(git diff HEAD~1 2>/dev/null || git status -s || echo "No diff found")

if [ -z "$DIFF_CONTENT" ] || [ "$DIFF_CONTENT" = "No diff found" ]; then
  echo "⚠️ 沒有偵測到重大變更，將針對目前目錄主要檔案進行快速掃描。"
  DIFF_CONTENT="掃描專案代碼安全與架構健康度。"
fi

# 2. 透過 Headless 模式呼叫 Cursor Agent
echo "🤖 正在請求 Cursor Agent 進行資安與品質審查..."

if command -v cursor >/dev/null 2>&1; then
  cursor -p "你是一位嚴格的資安與架構審查員。請使用繁體中文審查以下變更內容，檢查是否有 SQL Injection、硬編碼密碼或未處理的異常：
$DIFF_CONTENT" \
    --force \
    --output-format text > review-output.md
  echo "✅ 審查完成！報告已產出至 review-output.md"
else
  echo "⚠️ 本機尚未安裝 cursor 指令。請先執行：curl https://cursor.com/install -fsS | bash"
fi
