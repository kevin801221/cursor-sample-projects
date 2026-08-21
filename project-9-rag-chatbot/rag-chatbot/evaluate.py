"""測試集評估腳本 —— 用數字回答「這個 RAG 到底準不準」。

分開量兩件事，這是本課的重點：

  答案正確率 ── 回答裡有沒有講到該講的東西
  來源正確率 ── 那個答案是不是**真的**從對的文件推出來的

為什麼要分開？因為「答對但來源錯」是最危險的一種——
模型靠訓練資料矇對了，但它引用的文件其實沒寫這件事。
今天矇對，明天換個問題就矇錯，而且你完全看不出來。這種題目會被單獨標記出來。

跑法：
    DEMO_OFFLINE=1 uv run evaluate.py
"""

from __future__ import annotations

import sys

from src.embeddings import count_documents, provider_label
from src.retriever import ask

# 這個標記代表「這題文件裡根本沒有，正確答案就是承認找不到」
NOT_FOUND = "__NOT_FOUND__"

# 回答時引用證據的句型（見 src/offline_llm.py 與 src/prompts.py）。
# 用它來判斷「系統有沒有把某份文件當成答案的依據」。
CITATION_MARK = "根據《"

# ─────────────────────────────────────────────────────────────────────
# 測試集：三類題目
#   A. 文件中明確寫到的       → 應該答得出來，而且引用對的段落
#   B. 需要跨段落彙整的       → 答案散在兩個地方，考驗 k 夠不夠大
#   C. 文件中根本沒有的       → 應該老實說「找不到」，而不是腦補
# ─────────────────────────────────────────────────────────────────────

TEST_SET: list[dict] = [
    # ── A 類：明確寫到的 ──
    {
        "category": "A 明確寫到",
        "question": "年假沒休完可以遞延到什麼時候？",
        "expect_answer": ["3 月 31 日"],
        "expect_source": ["年假"],
    },
    {
        "category": "A 明確寫到",
        "question": "病假有給薪嗎？",
        "expect_answer": ["折半"],
        "expect_source": ["病假"],
    },
    {
        "category": "A 明確寫到",
        "question": "加班可以事後補單嗎？",
        "expect_answer": ["事前", "不行"],
        "expect_source": ["加班"],
    },
    {
        "category": "A 明確寫到",
        "question": "報帳的發票一定要有統一編號嗎？",
        "expect_answer": ["12345678", "統一編號"],
        "expect_source": ["統編", "統一編號"],
    },
    {
        "category": "A 明確寫到",
        "question": "遠端工作一週最多幾天？",
        "expect_answer": ["3 天", "3 日"],
        "expect_source": ["遠端"],
    },
    {
        "category": "A 明確寫到",
        "question": "進修補助每年上限多少？",
        "expect_answer": ["30,000"],
        "expect_source": ["進修"],
    },
    # ── B 類：需要跨段落彙整 ──
    {
        "category": "B 跨段落",
        "question": "加班選了補休，六個月內沒休掉會怎麼樣？",
        "expect_answer": ["折發", "折算"],
        "expect_source": ["補休", "加班"],
    },
    # ── C 類：文件中根本沒有 ──
    {
        "category": "C 文件沒有",
        "question": "休閒假怎麼請？",
        "expect_answer": NOT_FOUND,
        "expect_source": None,
    },
    {
        "category": "C 文件沒有",
        "question": "公司的股票選擇權怎麼發放？",
        "expect_answer": NOT_FOUND,
        "expect_source": None,
    },
    {
        "category": "C 文件沒有",
        "question": "可以帶寵物來上班嗎？",
        "expect_answer": NOT_FOUND,
        "expect_source": None,
    },
]


def check_answer(case: dict, answer: str) -> bool:
    if case["expect_answer"] == NOT_FOUND:
        return "找不到" in answer
    # 用「包含任一關鍵字」而不是精確比對——回答的措辭本來就會不一樣，
    # 硬要字字相同只會量到 LLM 的文風，量不到對錯。
    return any(keyword in answer for keyword in case["expect_answer"])


def check_sources(case: dict, answer: str, sources: list) -> bool:
    if case["expect_source"] is None:
        # 文件裡沒有的題目，「來源正確」的定義是：
        # 系統沒有把任何一段無關的文件當成答案的依據。
        return CITATION_MARK not in answer
    haystack = "\n".join(
        f"{doc.metadata.get('locator', '')} {doc.metadata.get('source', '')} {doc.page_content}"
        for doc in sources
    )
    return any(keyword in haystack for keyword in case["expect_source"])


def main() -> int:
    print(f"Provider：{provider_label()}")
    if count_documents() == 0:
        print("✗ 向量庫是空的。請先執行：uv run offline_index.py --reset", file=sys.stderr)
        return 1
    print(f"測試題數：{len(TEST_SET)}")
    print("=" * 76)

    answer_hits = 0
    source_hits = 0
    dangerous: list[str] = []

    for index, case in enumerate(TEST_SET, 1):
        result = ask(case["question"])
        answer, sources = result["answer"], result["sources"]

        answer_ok = check_answer(case, answer)
        source_ok = check_sources(case, answer, sources)
        answer_hits += answer_ok
        source_hits += source_ok

        expect = (
            "回答「找不到」"
            if case["expect_answer"] == NOT_FOUND
            else "／".join(case["expect_answer"])
        )
        print(f"\ntest_{index}: 「{case['question']}」  [{case['category']}]")
        print(f"  answer : {'✓' if answer_ok else '✗'}（期望包含：{expect}）")
        print(f"  sources: {'✓' if source_ok else '✗'}（期望引用：{case['expect_source'] or '不應引用任何來源'}）")
        if not (answer_ok and source_ok):
            first_line = answer.strip().splitlines()[0] if answer.strip() else "(空白)"
            print(f"  實際回答第一行：{first_line[:60]}")

        if answer_ok and not source_ok:
            dangerous.append(f"test_{index}")

    total = len(TEST_SET)
    print("\n" + "=" * 76)
    print("總結：")
    print(f"  答案正確率：{answer_hits}/{total} ({100 * answer_hits / total:.0f}%)")
    print(f"  來源正確率：{source_hits}/{total} ({100 * source_hits / total:.0f}%)")
    if dangerous:
        print(f"  ⚠ 危險題目（答對但來源錯）：{', '.join(dangerous)}")
        print("     這類題目最可怕——答案看起來對，但它引用的文件其實沒寫這件事。")
    else:
        print("  危險題目（答對但來源錯）：無")

    if answer_hits < total:
        print("\n【已知上限｜離線模式】")
        print("  離線回答器判斷「有沒有找到」靠的是字面相似度加一個門檻。")
        print("  「公司的股票選擇權怎麼發放？」這種題目，光是句首多了「公司的」三個字，")
        print("  就因為「公司」在手冊裡到處都是而把分數推過門檻，於是它硬答了。")
        print("  這正是鐵律 4 要練的診斷：問題不在 LLM，在檢索階段的相似度算法。")
        print("  把 OPENAI_API_KEY 設好再跑一次，同一份程式碼換成真 LLM 就會答對。")

    # 這個門檻刻意不設 100%。離線抽取式回答器有已知的上限，
    # 課堂上看到一兩題失手是好事——那正是「診斷是哪個階段出問題」的教材。
    passed = answer_hits >= total - 2 and source_hits >= total - 2
    print("\n判定：" + ("✓ 通過（容許 2 題以內的失手）" if passed else "✗ 未通過，錯太多了"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
