#!/usr/bin/env bash
# 課堂遙控器。
#   ./demo.sh      列出所有幕
#   ./demo.sh 3    跑第 3 幕
#
# 預設走離線模式（DEMO_OFFLINE=1）：不需要 OPENAI_API_KEY、不需要網路。
# 想示範接真 OpenAI 的版本：DEMO_OFFLINE=0 ./demo.sh 7

set -uo pipefail
cd "$(dirname "$0")"

: "${DEMO_OFFLINE:=1}"
export DEMO_OFFLINE

TOTAL_SCENES=10

banner() {
  echo
  echo "========================================================================"
  echo "【第 $1 幕】$2"
  echo "📺 螢幕上會出現：$3"
  echo "🎯 這一幕在教：$4"
  echo "========================================================================"
  echo
}

rescue() {
  echo
  echo "------------------------------------------------------------------------"
  echo "🧯 這一幕沒跑成功。救援步驟："
  echo "$1" | sed 's/^/   /'
  echo "------------------------------------------------------------------------"
  return 1
}

need_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "✗ 找不到 uv。安裝：curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
  fi
}

need_index() {
  local count
  count=$(uv run python -c "from src.embeddings import count_documents; print(count_documents())" 2>/dev/null | tail -1)
  if [ -z "$count" ] || [ "$count" = "0" ]; then
    echo "⚠️  向量庫是空的，先自動幫你跑第 4 幕（建索引）…"
    echo
    uv run offline_index.py --reset || return 1
    echo
  fi
}

list_scenes() {
  echo
  echo "======================================================================"
  echo "  RAG 知識庫 Chatbot － 課堂放映清單（共 ${TOTAL_SCENES} 幕）"
  if [ "$DEMO_OFFLINE" = "1" ]; then
    echo "  目前模式：離線（不需要 API key、不需要網路）"
  else
    echo "  目前模式：DEMO_OFFLINE=0，有 OPENAI_API_KEY 就會走真的 OpenAI"
  fi
  echo "======================================================================"
  cat <<'MENU'

  1  環境與示範語料        螢幕：provider 是哪一個、示範用的員工手冊 PDF 產生成功（8 頁）
  2  載入文件，出處跟著走    螢幕：PDF 8 頁 / Markdown 17 章，每塊都帶著 source 與頁碼
  3  切塊的兩個旋鈕        螢幕：一張表，chunk_size 越大相似度越低（精準度被稀釋）
  4  建立向量索引 ⭐        螢幕：Added 21 chunks to ChromaDB、chroma_db 資料夾出現
  5  先看檢索本身          螢幕：top-4 區塊與距離；問文件沒有的東西時距離明顯變大
  6  壞掉的版本 ⭐          螢幕：問「休閒假怎麼請？」→ 系統自信地拿出差住宿規定硬掰
  7  修好的版本 ⭐          螢幕：同一個問題 →「我找不到『休閒假』的相關內容」
  8  多輪對話：那病假呢？ ⭐  螢幕：追問被改寫成「病假規則是什麼？」；沒記憶的對照組失敗
  9  用數字驗收            螢幕：10 題評估，答案正確率 9/10、來源正確率 9/10
 10  Streamlit 聊天介面     螢幕：瀏覽器開啟聊天視窗，可上傳檔案、可切換防幻覺開關

  用法：./demo.sh 4
MENU
  echo
}

scene_1() {
  banner 1 "環境與示範語料" \
    "provider 標示為離線模式，員工手冊 PDF 產生成功並通過中文抽取檢查" \
    "課堂不能靠 API key 吃飯——同一份程式碼，換掉 provider 就能離線跑完整條 RAG"
  need_uv
  echo "▶ uv sync"
  uv sync --quiet || rescue "uv sync 失敗。檢查網路，或改用 pip install -e ." || return 1
  echo "✓ 依賴就緒"
  echo
  echo "▶ 目前的 provider"
  uv run python -c "from src.embeddings import provider_label; print('  ' + provider_label())" || return 1
  echo
  echo "▶ 產生示範用的員工手冊 PDF（reportlab 內建 CJK 字型，不下載任何字型檔）"
  uv run python make_sample_pdf.py || rescue "reportlab 沒裝好。跑 uv sync 再試一次。" || return 1
  echo
  ls -lh data/
}

scene_2() {
  banner 2 "載入文件，出處跟著走" \
    "PDF 8 頁、Markdown 17 章，每個區塊都印出自己的 source 與頁碼/章節" \
    "引用能力不是最後才加的功能——出處要在載入的第一步就塞進 metadata"
  need_uv
  echo "▶ loader 自我檢查"
  uv run python -m src.loader || rescue "找不到 data/員工手冊.md？先跑 ./demo.sh 1" || return 1
  echo
  echo "▶ 實際載入 + 切塊，看看每一塊記得什麼"
  uv run python - <<'PY' || return 1
from src.loader import load_pdf, load_markdown
from src.chunker import chunk_documents

pdf_docs = load_pdf("data/sample_handbook.pdf")
md_docs = load_markdown("data/faqs.md")
chunks = chunk_documents(pdf_docs + md_docs)
print(f"  Loaded {len(pdf_docs)} pages (PDF) + {len(md_docs)} sections (Markdown)")
print(f"  Chunked into {len(chunks)} pieces")
print()
print("  前 4 個區塊的出處：")
for c in chunks[:4]:
    print(f"    source={c.metadata['source']:<22} locator={c.metadata['locator']:<28} 字數={len(c.page_content)}")
print()
print("  第一個區塊的前 120 字：")
print("   ", chunks[0].page_content[:120].replace("\n", " "))
PY
}

scene_3() {
  banner 3 "切塊的兩個旋鈕：chunk_size 與 chunk_overlap" \
    "一張對照表：同一段病假條文塞進越大的區塊，相似度從 0.178 一路掉到 0.105" \
    "鐵律 2——四個數字不是隨便訂的。太大稀釋精準度，太小切斷上下文"
  need_uv
  uv run python -m src.chunker || rescue "先跑 ./demo.sh 1 產生示範語料" || return 1
}

scene_4() {
  banner 4 "建立向量索引（第一個里程碑）" \
    "Added 21 chunks to ChromaDB、./chroma_db exists: True" \
    "鐵律 5——離線索引與線上查詢分家：這一步慢慢做一次，之後每次查詢都秒回"
  need_uv
  echo "▶ uv run offline_index.py --reset --persist"
  uv run offline_index.py --reset --persist || \
    rescue "常見原因：
1. data/sample_handbook.pdf 不存在 → 先跑 ./demo.sh 1
2. chroma_db/ 沒有寫入權限 → chmod -R u+w chroma_db/
3. 換過 embedding provider → rm -rf chroma_db/ 之後重跑" || return 1
  echo
  echo "▶ 索引真的落在磁碟上了嗎"
  ls -la chroma_db/ | head -8
}

scene_5() {
  banner 5 "先看檢索本身（還沒有 LLM 參與）" \
    "三個問題各自的 top-4 區塊與距離；「休閒假」那一組距離明顯大很多" \
    "RAG 答不好時要先分清楚：是「找不到」還是「找到了但講錯」"
  need_uv
  need_index || return 1
  uv run python - <<'PY' || return 1
from src.embeddings import query_collection

for q in ["年假規則是什麼？", "加班費怎麼算？", "休閒假怎麼請？"]:
    print(f"\n▶ 查詢：{q}")
    print(f"  {'距離':>8}  {'出處':<44} 內容開頭")
    print("  " + "-" * 92)
    for r in query_collection(q, k=4):
        m = r["metadata"]
        src = f"{m['source']}｜{m['locator']}"
        head = r["content"].strip().replace("\n", " ")[:30]
        print(f"  {r['distance']:>8.3f}  {src:<44} {head}…")
print()
print("讀法：距離越小越相關。「休閒假」在手冊裡根本不存在，")
print("      所以它的 top-4 距離全都逼近 2.0——代表向量幾乎正交，一點關係都沒有。")
print("      注意：檢索**永遠**會回傳 k 個結果，它不會說「我沒找到」。")
print("      判斷『到底有沒有答案』是下一階段（生成）的責任——也就是第 6、7 幕的重點。")
PY
}

scene_6() {
  banner 6 "壞掉的版本：把防幻覺的 system prompt 拿掉" \
    "問「休閒假怎麼請？」→ 系統回「關於「休閒假」，公司規定如下：」然後貼出差住宿與出勤規定" \
    "沒有 system prompt 的 RAG 一樣會腦補——它會把檢索到的任何東西當成答案"
  need_uv
  need_index || return 1
  uv run python - <<'PY' || return 1
from src.retriever import ask, format_sources
from src.prompts import LOOSE_SYSTEM_PROMPT

print("這一版用的 system prompt（注意：沒有任何『找不到就說不知道』的指令）：")
print("-" * 72)
for line in LOOSE_SYSTEM_PROMPT.splitlines():
    print("  " + line)
print("-" * 72)

q = "休閒假怎麼請？"
print(f"\n▶ 提問：{q}（提醒：員工手冊裡根本沒有「休閒假」這種東西）\n")
r = ask(q, strict=False)
print(r["answer"])
print(f"\n它引用的來源：{format_sources(r['sources'])}")
print("\n看清楚：出差住宿、遠端出勤——沒有一項跟休閒假有關，但它講得理直氣壯。")
PY
}

scene_7() {
  banner 7 "修好的版本：把那條禁令加回 system prompt" \
    "同一個問題 →「根據提供的文件，我找不到「休閒假」的相關內容」；再問年假 → 附出處與頁碼" \
    "鐵律 1——查完再答、附出處、找不到就說不知道。誠實比聰明值錢"
  need_uv
  need_index || return 1
  uv run python - <<'PY' || return 1
from src.retriever import ask, format_sources
from src.prompts import QA_SYSTEM_PROMPT

print("這一版的 system prompt（第 2、3 條就是關鍵）：")
print("-" * 72)
for line in QA_SYSTEM_PROMPT.splitlines():
    print("  " + line)
print("-" * 72)

print("\n▶ 提問 1：休閒假怎麼請？（文件裡沒有）\n")
r = ask("休閒假怎麼請？", strict=True)
print(r["answer"])

print("\n" + "=" * 72)
print("\n▶ 提問 2：年假沒休完可以遞延到什麼時候？（文件裡有）\n")
r2 = ask("年假沒休完可以遞延到什麼時候？", strict=True)
print(r2["answer"])
print(f"\n來源：{format_sources(r2['sources'])}")
print("\n差別只有 system prompt 那幾行字——向量庫、retriever、LLM、k 值全都沒動。")
PY
}

scene_8() {
  banner 8 "多輪對話：「那病假呢？」" \
    "追問被改寫成「病假規則是什麼？」；最後對照組（沒有記憶）問同一句只能回答找不到" \
    "鐵律 3——追問要補完問題，不是重起對話。記憶就是查得到和查不到的差別"
  need_uv
  need_index || return 1
  uv run python test_conversation.py || \
    rescue "如果是「第 3 輪有記憶卻還是答不出婚假」：
向量庫可能是舊的，跑 ./demo.sh 4 重建索引再試。" || return 1
}

scene_9() {
  banner 9 "用數字驗收：10 題評估" \
    "逐題 answer/sources 打勾，最後印出答案正確率 9/10、來源正確率 9/10，並列出已知上限" \
    "「答對」跟「來源對」要分開量——答對但來源錯是最危險的一種，代表模型在矇"
  need_uv
  need_index || return 1
  uv run evaluate.py || \
    rescue "錯超過 2 題通常是索引沒建好。跑 ./demo.sh 4 重建再試。" || return 1
}

scene_10() {
  banner 10 "Streamlit 聊天介面" \
    "瀏覽器開啟聊天視窗：側欄顯示 provider 與區塊數、可上傳檔案、有「防幻覺開關」可即時切換" \
    "離線索引已經做完了，所以 app 啟動很快——線上查詢只負責查跟答"
  need_uv
  need_index || return 1
  echo "課堂建議的操作順序："
  echo "  1. 問「年假規則是什麼？」        → 看回答附的出處與頁碼"
  echo "  2. 追問「那病假呢？」            → 看畫面上出現「🔁 檢索前被改寫成…」"
  echo "  3. 問「休閒假怎麼請？」          → 看它誠實說找不到"
  echo "  4. 側欄關掉「防幻覺 system prompt」，再問一次「休閒假怎麼請？」→ 它開始硬掰"
  echo "  5. 側欄上傳 data/員工手冊.md    → 不用重啟就能問到新內容"
  echo "  6. 按「清除對話」               → 聊天記錄清空，但索引還在"
  echo
  echo "▶ 啟動中…（按 Ctrl+C 結束）"
  echo
  uv run streamlit run app.py || \
    rescue "port 8501 被占用的話：uv run streamlit run app.py --server.port 8502" || return 1
}

main() {
  if [ $# -eq 0 ]; then
    list_scenes
    return 0
  fi
  case "$1" in
    [1-9]|10)
      "scene_$1"
      local status=$?
      if [ $status -ne 0 ]; then
        echo
        echo "✗ 第 $1 幕結束時回傳非零。上面的救援提示看一下。"
      fi
      return $status
      ;;
    *)
      echo "✗ 沒有第 $1 幕。可用範圍：1–${TOTAL_SCENES}"
      list_scenes
      return 1
      ;;
  esac
}

main "$@"
