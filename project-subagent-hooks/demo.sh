#!/usr/bin/env bash
# Project Subagent + Hooks: 課堂放映遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1

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
  echo "  Project Subagent + Hooks － 課堂放映清單（共 ${TOTAL} 幕）"
  echo "======================================================================"
  echo "  1  核心心智模型與 Subagent 定義  螢幕：planner / security-auditor / verifier"
  echo "  2  Hooks 骨架與五大鉤子配置    螢幕：.cursor/hooks.json 配置解析"
  echo "  3  護欄一：攔截機密 .env 讀取 ⭐ 螢幕：guard-secrets.sh 放行 example 阻擋 .env"
  echo "  4  護欄二：攔截破壞性指令 ⭐     螢幕：guard-shell.sh 攔截 migrate reset / drop"
  echo "  5  執行功能測試驗收            螢幕：node --test 原生測試 3/3 通過"
  echo "  6  Subagent 報告落檔與閉環回修  螢幕：subagent-report.sh 偵測 Critical 自動踢球"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "核心心智模型與 Subagent 定義" \
    "檢視 .cursor/agents/ 裡的三大專業分工角色" \
    "Subagent 決定「誰來做這件事」，隔離 Context 與平行處理"
  echo "--- ① planner.md (先想再做) ---"
  cat .cursor/agents/planner.md
  echo
  echo "--- ② security-auditor.md (平行資安稽核) ---"
  cat .cursor/agents/security-auditor.md
  echo
  echo "--- ③ verifier.md (懷疑論驗證) ---"
  cat .cursor/agents/verifier.md
}

scene_2() {
  banner 2 "Hooks 骨架與五大鉤子配置" \
    "檢視 .cursor/hooks.json 與 failClosed 安全屬性" \
    "Hook 決定「什麼一定會發生、什麼絕對不准發生」"
  cat .cursor/hooks.json
}

scene_3() {
  banner 3 "護欄一：攔截機密 .env 讀取" \
    "執行 guard-secrets.sh 模擬讀取 .env.example 與 .env" \
    "白名單範本放行，機密憑證與金鑰在 context 層直接攔截"
  echo "1. 模擬 Agent 嘗試讀取 .env.example (安全範本):"
  echo '{"file_path": "project/.env.example"}' | .cursor/hooks/guard-secrets.sh
  echo
  echo "2. 模擬 Agent 嘗試讀取 .env (正式機密):"
  echo '{"file_path": "project/.env"}' | .cursor/hooks/guard-secrets.sh
}

scene_4() {
  banner 4 "護欄二：攔截破壞性指令" \
    "執行 guard-shell.sh 模擬危險指令" \
    "確定性攔截 migrate reset 與 drop table，並反饋替代方案給 Agent"
  echo "1. 模擬 Agent 嘗試執行 prisma migrate reset:"
  echo '{"command": "npx prisma migrate reset --force"}' | .cursor/hooks/guard-shell.sh
  echo
  echo "2. 模擬 Agent 嘗試執行 force push:"
  echo '{"command": "git push origin main --force"}' | .cursor/hooks/guard-shell.sh
}

scene_5() {
  banner 5 "執行功能測試驗收" \
    "執行 node --test 原生測試" \
    "驗證 DELETE /api/account 正常刪除、越權 403 阻擋、二次確認 400 阻擋"
  node --test tests/*.test.mjs
}

scene_6() {
  banner 6 "Subagent 報告落檔與閉環回修" \
    "模擬 security-auditor 回報發現 Critical 漏洞" \
    "Hook 自動產生 followup_message 強制主 Agent 停下工作回頭修復"
  echo '{"conversation_id": "demo_conv_123", "subagent_type": "generalPurpose", "description": "security audit", "task": "audit DELETE /api/account", "status": "completed", "summary": "Critical: 缺少使用者身分驗證 — routes/account.ts:15 — 加上 session 檢查"}' | .cursor/hooks/subagent-report.sh
  echo
  echo "產出的報告檔案："
  ls -t .cursor/reports/ | head -n 3
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
