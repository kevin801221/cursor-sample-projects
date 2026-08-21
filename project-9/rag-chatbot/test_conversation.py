"""多輪對話測試 —— 鐵律 3：追問要補完問題，不是重起對話。

這支程式演一件事：同樣一句「那婚假呢？」，
  有記憶 → 被補成「婚假規則是什麼？」→ 查得到、答得對
  沒記憶 → 原封不動拿去查 → 查不到，只能說「找不到」

跑法：
    DEMO_OFFLINE=1 uv run python test_conversation.py
"""

from __future__ import annotations

import sys

from src.embeddings import count_documents, provider_label
from src.retriever import ask, ask_conversational, create_conversational_qa_chain, format_sources

LINE = "─" * 72


def show(turn: str, question: str, result: dict) -> None:
    print(f"\n【{turn}】使用者問：{question}")
    rewritten = result.get("generated_question", question)
    if rewritten.strip() != question.strip():
        print(f"  ↳ 檢索前被改寫成：「{rewritten}」  ← 記憶在這裡發揮作用")
    else:
        print(f"  ↳ 檢索前沒有改寫（原句直接拿去查）：「{rewritten}」")
    print("  回答：")
    for line in result["answer"].splitlines():
        print(f"    {line}")
    print(f"  來源：{format_sources(result['sources'])}")


def main() -> int:
    print(f"Provider：{provider_label()}")
    if count_documents() == 0:
        print("✗ 向量庫是空的。請先執行：uv run offline_index.py --reset", file=sys.stderr)
        return 1

    chain, memory = create_conversational_qa_chain()

    print(LINE)
    print("第一部分：有記憶的多輪對話")
    print(LINE)

    r1 = ask_conversational(chain, "年假規則是什麼？")
    show("第 1 輪", "年假規則是什麼？", r1)

    r2 = ask_conversational(chain, "那病假呢？")
    show("第 2 輪", "那病假呢？", r2)

    r3 = ask_conversational(chain, "那婚假呢？")
    show("第 3 輪", "那婚假呢？", r3)

    print("\n" + LINE)
    print("第二部分：對照組——同一句「那婚假呢？」，但沒有任何對話記憶")
    print(LINE)
    solo = ask("那婚假呢？")
    print("\n【單輪】使用者問：那婚假呢？（系統不知道前面聊過什麼）")
    print("  ↳ 沒有記憶可以參考，「那婚假呢？」原封不動被拿去做向量檢索")
    print("  回答：")
    for line in solo["answer"].splitlines():
        print(f"    {line}")

    print("\n" + LINE)
    print("驗收")
    print(LINE)

    failures: list[str] = []

    if "病假" not in r2["generated_question"]:
        failures.append("第 2 輪沒有把「那病假呢？」補成含「病假」的完整問題")
    if "病假" not in r2["answer"]:
        failures.append("第 2 輪答案沒講到病假")
    if "婚假" not in r3["generated_question"]:
        failures.append("第 3 輪沒有把「那婚假呢？」補成含「婚假」的完整問題")
    if "找不到" in r3["answer"]:
        failures.append("第 3 輪有記憶卻還是答不出婚假")
    if "找不到" not in solo["answer"]:
        failures.append("對照組沒有失敗——這樣就示範不出記憶的價值了")

    if failures:
        for f in failures:
            print(f"✗ {f}")
        return 1

    print(f"✓ 「那病假呢？」被補成「{r2['generated_question']}」，答案講到病假")
    print(f"✓ 「那婚假呢？」被補成「{r3['generated_question']}」，答案講到婚假")
    print("✓ 對照組（沒有記憶）問同一句「那婚假呢？」→ 只能回答「找不到」")
    print("\n結論：多出來的那句記憶，就是「查得到」和「查不到」的差別。")

    memory.clear()
    assert memory.chat_memory.messages == []
    print("✓ memory.clear() 之後對話歸零（Streamlit 的「清除對話」按鈕就是按這個）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
