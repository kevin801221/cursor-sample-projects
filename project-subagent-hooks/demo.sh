#!/usr/bin/env bash
# Project Subagent + Hooks: 課堂放映遙控器
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1

TOTAL=8

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
  echo "  1  核心心智模型與 Subagent 定義  螢幕：planner / auditor / verifier / researcher"
  echo "  2  Hooks 骨架與七大鉤子配置    螢幕：.cursor/hooks.json 配置解析"
  echo "  3  護欄一：攔截機密 .env 讀取 ⭐ 螢幕：guard-secrets.sh 放行 example 阻擋 .env"
  echo "  4  護欄二：攔截破壞性指令 ⭐     螢幕：guard-shell.sh 攔 migrate reset / drop，force push 轉 ask"
  echo "  5  執行功能測試驗收            螢幕：node --test 原生測試 3/3 通過"
  echo "  6  Subagent 報告落檔與閉環回修  螢幕：subagent-report.sh 偵測 Critical 自動踢球"
  echo "  7  護欄三：MCP 出境海關 ⭐      螢幕：guard-mcp.sh 攔截夾帶 secrets 的 MCP 參數"
  echo "  8  護欄四：Subagent 拒生把關    螢幕：guard-subagent.sh 拒絕部署型 subagent + 留痕"
  echo
  echo "  用法：./demo.sh <編號>"
  echo
}

scene_1() {
  banner 1 "核心心智模型與 Subagent 定義" \
    "檢視 .cursor/agents/ 裡的四大專業分工角色" \
    "Subagent 決定「誰來做這件事」，隔離 Context 與平行處理"
  echo "--- ① planner.md (先想再做，巢狀開 Explore + MCP 查文件) ---"
  cat .cursor/agents/planner.md
  echo
  echo "--- ② security-auditor.md (平行資安稽核，讀 checklist skill) ---"
  cat .cursor/agents/security-auditor.md
  echo
  echo "--- ③ verifier.md (懷疑論驗證) ---"
  cat .cursor/agents/verifier.md
  echo
  echo "--- ④ docs-researcher.md (subagent 調用 MCP 查官方文件) ---"
  cat .cursor/agents/docs-researcher.md
}

scene_2() {
  banner 2 "Hooks 骨架與七大鉤子配置" \
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
    "確定性攔截 migrate reset 與 drop table（deny＋給替代方案），force push 轉 ask 問人"
  echo "1. 模擬 Agent 嘗試執行 prisma migrate reset:"
  echo '{"command": "npx prisma migrate reset --force"}' | .cursor/hooks/guard-shell.sh
  echo
  echo "2. 模擬 Agent 嘗試執行 drop table:"
  echo '{"command": "psql -c \"drop table users\""}' | .cursor/hooks/guard-shell.sh
  echo
  echo "3. 模擬 Agent 嘗試執行 force push（不擋死，轉 ask 問人）:"
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

scene_7() {
  banner 7 "護欄三：MCP 出境海關" \
    "執行 guard-mcp.sh 模擬夾帶 secrets 的 MCP 呼叫" \
    "MCP 是資料離開本機的通道，beforeMCPExecution 是海關（subagent 內部呼叫是否逐一觸發，官方未載明——請實測驗證）"
  echo "1. 模擬 Agent 用 context7 查文件（乾淨參數，應放行）:"
  echo '{"tool_name": "context7_query", "tool_input": {"query": "express rate limit middleware"}}' | .cursor/hooks/guard-mcp.sh
  echo
  echo "2. 模擬 Agent 把 API key 夾在 MCP 參數裡外送（應攔截）:"
  echo '{"tool_name": "some_tool", "tool_input": {"body": "please review sk-abc123def456ghi789jkl"}}' | .cursor/hooks/guard-mcp.sh
}

scene_8() {
  banner 8 "護欄四：Subagent 拒生把關" \
    "執行 guard-subagent.sh 模擬 spawn 部署型 subagent" \
    "subagentStart 在分身出生前把關——連生出來的機會都不給（注意：此事件回 ask 會被當 deny）"
  echo "1. 模擬 spawn 一般稽核任務的 subagent（應放行）:"
  echo '{"subagent_type": "generalPurpose", "task": "audit DELETE /api/account"}' | .cursor/hooks/guard-subagent.sh
  echo
  echo "2. 模擬 spawn 部署型 subagent（應拒生）:"
  echo '{"subagent_type": "shell", "task": "deploy the new build to production"}' | .cursor/hooks/guard-subagent.sh
  echo
  echo "spawn 留痕（.cursor/state/subagent-spawns.log 最後 3 筆）："
  tail -n 3 .cursor/state/subagent-spawns.log
}

case "${1:-}" in
  "") list_scenes ;;
  1) scene_1 ;;
  2) scene_2 ;;
  3) scene_3 ;;
  4) scene_4 ;;
  5) scene_5 ;;
  6) scene_6 ;;
  7) scene_7 ;;
  8) scene_8 ;;
  *) echo "無效幕次：$1"; list_scenes; exit 1 ;;
esac
