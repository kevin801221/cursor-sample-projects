#!/usr/bin/env bash
# 課前一鍵檢查：資料夾齊全、教材 repo 在位、demo.sh 全部能跑、md 連結沒有斷。
# 用法：./preflight.sh   （全綠才開課；紅字對照 TROUBLESHOOTING-MASTER.md）
# 注意：網路、API 金鑰、Docker 屬環境類，請另照各專案 walkthrough 的 🚦 檢查清單課前實測。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

FAIL=0
ok()   { echo "  ✅ $1"; }
bad()  { echo "  ❌ $1"; FAIL=1; }

echo "【1/4】17 個專案資料夾與必備檔案"
count=0
for d in project-*/; do
  count=$((count+1))
  [ -f "${d}README.md" ]            || bad "${d} 缺 README.md"
  ls "${d}"walkthrough*.md >/dev/null 2>&1 || bad "${d} 缺 walkthrough"
  [ -f "${d}demo.sh" ]              || bad "${d} 缺 demo.sh"
done
[ "$count" -eq 17 ] && ok "17 個專案資料夾都在" || bad "專案資料夾數量是 $count，不是 17"

echo "【2/4】5 個教材 repo 在同層"
for r in auto-cv-train-optimization-claude_code agent-automatic-graphrag-chat-skill \
         rag-architect-mcp lazy-cloud-devops Anchor_knowledge.ai; do
  if [ -d "$r" ] && [ -n "$(ls -A "$r" 2>/dev/null)" ]; then ok "$r"
  else bad "缺教材 repo：$r（submodule 沒抓？跑 git submodule update --init）"; fi
done

echo "【3/4】demo.sh 語法 + 放映清單實跑"
for d in project-*/; do
  f="${d}demo.sh"
  [ -f "$f" ] || continue
  bash -n "$f" 2>/dev/null || { bad "$f 語法錯誤"; continue; }
  [ -x "$f" ] || bad "$f 沒有執行權限（chmod +x 修復）"
  if (cd "$d" && ./demo.sh >/dev/null 2>&1); then ok "$d demo.sh"; else bad "$d demo.sh 無參數執行失敗"; fi
done

echo "【4/4】Markdown 相對連結完整性"
python3 - <<'EOF' || FAIL=1
import re, os, glob, sys
bad = 0
for f in glob.glob('*.md') + glob.glob('project-*/*.md'):
    base = os.path.dirname(f) or '.'
    for m in re.finditer(r'\]\(([^)#\s]+)\)', open(f).read()):
        t = m.group(1)
        if t.startswith(('http', 'mailto:')):
            continue
        if not os.path.exists(os.path.join(base, t)):
            print(f'  ❌ 斷鏈 {f} -> {t}'); bad += 1
print(f'  ✅ 連結全部有效' if bad == 0 else f'  共 {bad} 條斷鏈')
sys.exit(1 if bad else 0)
EOF

echo
if [ "$FAIL" -eq 0 ]; then
  echo "🟢 全綠——文件與放映系統就緒。環境類（網路/金鑰/Docker）請照各專案 🚦 檢查清單再確認一次。"
else
  echo "🔴 有紅字——先修上面的項目，卡住查 TROUBLESHOOTING-MASTER.md。"
  exit 1
fi
