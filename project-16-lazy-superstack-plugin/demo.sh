#!/usr/bin/env bash
# Project 16: Lazy Superstack — 把一包 agent 能力搬進 Cursor 課堂遙控器
# 每一幕投影 Claude Code plugin 的真實檔案，教的是它在 Cursor 的對應落點
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"
REPO_DIR="$WORKSPACE/lazy-cloud-devops"
cd "$REPO_DIR" || exit 1

TOTAL=6

banner() {
  echo
  echo "========================================================================"
  echo "【第 $1 幕】$2"
  echo "📺 螢幕上會出現：$3"
  echo "🎯 這一幕在教：$4"
  echo "========================================================================"
  echo
}

list_scenes() {
  echo
  echo "======================================================================"
  echo "  Project 16：把一包 agent 能力搬進 Cursor － 課堂放映清單"
  echo "======================================================================"
  echo "  1  plugin.json 盤點              螢幕：四批要搬進 Cursor 的貨（skills/commands/hooks/mcp）"
  echo "  2  Skill 層與策展表 ⭐           螢幕：五份 Markdown 紀律 → .cursor/rules/*.mdc 的素材"
  echo "  3  Hook 現場注入                 螢幕：SessionStart 注入 → Cursor sessionStart / alwaysApply"
  echo "  4  Command 層 (/lazy-ship)       螢幕：prompt 檔 → .cursor/commands/，frontmatter 差異"
  echo "  5  MCP 兩級啟用 ⭐               螢幕：同一段 JSON 搬進 .cursor/mcp.json 就能用"
  echo "  6  策展紀律與 footprint gate     螢幕：授權合規與硬閘門——跨編輯器不豁免"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "plugin.json 盤點——搬家前的物品清單" \
    "整份 .claude-plugin/plugin.json——四批要搬進 Cursor 的貨都列在這" \
    "skills→.cursor/rules、commands→.cursor/commands、hooks→.cursor/hooks.json、mcpServers→.cursor/mcp.json"
  cat .claude-plugin/plugin.json
}

scene_2() {
  banner 2 "Skill 層與策展表" \
    "skills/README.md 來源對照表 + vendored skill 檔頂的合規註記" \
    "這批 Markdown 紀律就是 Cursor rules 的素材（.mdc）；Cursor 2.4+ 連 SKILL.md 都直接吃——複製時 LICENSE 與註記要跟著走"
  cat skills/README.md
  echo
  echo "── vendored skill 的檔頂合規註記（pm-brainstorming 前 8 行）──"
  sed -n '1,8p' skills/pm-brainstorming/SKILL.md
}

scene_3() {
  banner 3 "Hook 現場注入" \
    "hooks.json 的 SessionStart matcher，接著現場執行注入腳本" \
    "規則是被注入 context 才生效——Cursor 也有 .cursor/hooks.json 的 sessionStart（要輸出 JSON 的 additional_context）；內容固定時 alwaysApply rule 更省事"
  cat hooks/hooks.json
  echo
  echo "── 現場執行 bash hooks/inject-ponytail.sh ──"
  bash hooks/inject-ponytail.sh
}

scene_4() {
  banner 4 "Command 層 (/lazy-ship 與 /superstack-doctor)" \
    "lazy-ship 的 frontmatter 與 Hard rules、doctor 的鐵律" \
    "prompt 檔可直接搬進 .cursor/commands/（1.6+）；但 allowed-tools 與 \$1/\$2 在 Cursor 沒有官方等價物——doctor 鐵律只剩 prompt 自律這層"
  sed -n '1,15p' commands/lazy-ship.md
  echo "..."
  grep -n -A 5 "Hard rules" commands/lazy-ship.md
  echo
  echo "── /superstack-doctor 的鐵律 ──"
  grep -n -A 3 "鐵律" commands/superstack-doctor.md
}

scene_5() {
  banner 5 "MCP 兩級啟用" \
    "plugin.json 裡的 A 級（僅 2 個、零憑證）+ B 級範本的 _doc 說明" \
    "MCP 是跨工具協議——同一段 JSON 搬進 .cursor/mcp.json 就能用；A 級直掛、B 級補憑證再掛（用 \${env:NAME} 插值），_doc 註解欄位搬之前要清掉"
  echo "── A 級（寫進 plugin.json，預設開）──"
  sed -n '39,51p' .claude-plugin/plugin.json
  echo
  echo "── B 級（mcp-optional.example.json，按需開，各附 _doc 說明）──"
  grep -n '"_doc"' mcp-optional.example.json
}

scene_6() {
  banner 6 "策展紀律與 footprint gate" \
    "THIRD_PARTY_NOTICES 的三種處置定義 + deploy-gcp.sh 的 300MB 閘門" \
    "授權合規與硬閘門跨編輯器不豁免——複製進 .cursor/ 的每個檔案都要帶著 LICENSE；最強的規則寫成會 fail 的 bash，在哪個編輯器都能跑"
  sed -n '1,10p' THIRD_PARTY_NOTICES.md
  echo "..."
  echo "── deploy-gcp.sh 的 footprint gate（image 超過 MAX_IMAGE_MB 直接拒絕部署）──"
  grep -n -A 5 "footprint gate" scripts/deploy-gcp.sh
}

case "${1:-}" in
  "") list_scenes ;;
  1) scene_1 ;;
  2) scene_2 ;;
  3) scene_3 ;;
  4) scene_4 ;;
  5) scene_5 ;;
  6) scene_6 ;;
  *) echo "無效幕次：$1"; list_scenes; exit 1 ;;
esac
