#!/usr/bin/env bash
# 把本 skill 掛給 Claude Code / Cursor / Codex 三個工具。
#
# 設計原則：SKILL.md 是唯一真相來源，三個平台各自只放一個「指路的殼」。
# 不複製內容——複製就會漂移，改了一份忘了另外兩份是遲早的事。
#
# 用法:
#   ./install.sh                 # 裝到目前目錄的專案
#   ./install.sh /path/to/proj   # 裝到指定專案
#   ./install.sh --global        # 裝到使用者層（Claude Code / Codex；Cursor 規則只有專案層）
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# skill 名取自 SKILL.md 的 frontmatter，不是資料夾名——clone 下來的資料夾
# 常跟 repo 同名（agent-automatic-graphrag-chat-skill），跟 frontmatter 對不上
# 會讓 Claude Code 找不到這個 skill。
NAME="$(sed -n 's/^name:[[:space:]]*//p' "$SKILL_DIR/SKILL.md" | head -1)"
NAME="${NAME:-yt-graphrag-bot}"
DESC="從 YouTube / PDF / DOCX / 網頁 URL 建出完整 GraphRAG 問答機器人的教學工作流：來源擷取 → 向量庫 → 知識圖譜 → 強 RAG → 方法驗證 → FastAPI 後端 → React 力導向圖前端。"

GLOBAL=0
TARGET="$PWD"
case "${1:-}" in
  --global) GLOBAL=1 ;;
  "")       ;;
  *)        TARGET="$(cd "$1" && pwd)" ;;
esac

say() { printf '  %s\n' "$*"; }

# 每個平台的殼都講同一件事：先讀 SKILL.md，再照它做。
body() {
  cat <<EOF
動手前**先完整讀取** \`$SKILL_DIR/SKILL.md\`，然後嚴格照它執行。

不可省略的硬規則：
- 照 Phase 順序 0 → 1 → 2 → 3 → 4+5 → 4.5 → 6，不跳步。
- 第一個動作永遠是 \`uv run python scripts/check_setup.py\`，沒全綠不准往下。
- 所有 Python 指令一律 \`uv run\` 開頭，工作目錄設在 \`$SKILL_DIR\`。
- 每個 Phase 的「✅ 成功判準」沒達成前，不要進下一個 Phase。
- 深度內容按需讀 \`$SKILL_DIR/references/\` 下的檔案。
EOF
}

echo "skill: $NAME"
echo "來源:  $SKILL_DIR"
echo

# ---------- Claude Code ----------
# 原生支援 SKILL.md，直接 symlink 整個目錄，scripts/ 與 references/ 的相對路徑才不會斷。
if [ "$GLOBAL" = 1 ]; then CC_DIR="$HOME/.claude/skills"; else CC_DIR="$TARGET/.claude/skills"; fi
mkdir -p "$CC_DIR"
rm -rf "${CC_DIR:?}/$NAME"
ln -s "$SKILL_DIR" "$CC_DIR/$NAME"
echo "[✓] Claude Code"; say "$CC_DIR/$NAME -> symlink"; say "用法：直接描述需求即可自動觸發，或 /$NAME"

# ---------- Codex ----------
# 專案層讀 AGENTS.md；使用者層的 prompts/ 會變成 /指令。
if [ "$GLOBAL" = 1 ]; then
  mkdir -p "$HOME/.codex/prompts"
  { echo "# $NAME"; echo; body; } > "$HOME/.codex/prompts/$NAME.md"
  echo "[✓] Codex"; say "$HOME/.codex/prompts/$NAME.md"; say "用法：/$NAME"
else
  AG="$TARGET/AGENTS.md"
  touch "$AG"
  # 用標記包住，重跑不會疊加（先刪舊區塊再寫新的）
  if grep -q "<!-- $NAME:begin -->" "$AG" 2>/dev/null; then
    sed -i.bak "/<!-- $NAME:begin -->/,/<!-- $NAME:end -->/d" "$AG" && rm -f "$AG.bak"
  fi
  {
    echo "<!-- $NAME:begin -->"
    echo "## Skill: $NAME"
    echo
    echo "$DESC"
    echo
    echo "只要使用者提到「YouTube 影片做 RAG / 問答機器人」「PDF、DOCX、網頁做知識庫問答」"
    echo "「影片或文件轉知識圖譜」「GraphRAG 教學」「帶學生做 RAG 專案」——即使沒講出"
    echo "「GraphRAG」這個詞——都適用本 skill。"
    echo
    body
    echo "<!-- $NAME:end -->"
  } >> "$AG"
  # 變數後面緊接全形字時一定要用 ${}，否則 bash 會把全形字吃進變數名
  echo "[✓] Codex"; say "${AG}（已加入標記區塊，重跑會覆蓋不會疊加）"
fi

# ---------- Cursor ----------
# Cursor 的規則是專案層的，--global 也裝到 $TARGET。
mkdir -p "$TARGET/.cursor/rules" "$TARGET/.cursor/commands"
{
  echo "---"
  echo "description: $DESC"
  echo "alwaysApply: false"
  echo "---"
  echo
  echo "# $NAME"
  echo
  body
  echo
  echo "@$SKILL_DIR/SKILL.md"
} > "$TARGET/.cursor/rules/$NAME.mdc"
{ echo "# $NAME"; echo; body; } > "$TARGET/.cursor/commands/$NAME.md"
echo "[✓] Cursor"
say "$TARGET/.cursor/rules/$NAME.mdc（描述命中時自動載入）"
say "$TARGET/.cursor/commands/$NAME.md（用法：/${NAME}）"
[ "$GLOBAL" = 1 ] && say "註：Cursor 規則只有專案層，已裝到 $TARGET"

echo
echo "下一步："
echo "  cd $SKILL_DIR && uv sync"
echo "  export GOOGLE_API_KEY=... && export NEO4J_PASSWORD=..."
echo "  uv run python scripts/check_setup.py"
echo "  完整逐步教學：$SKILL_DIR/WALKTHROUGH.md"
