"""多輪對話記憶管理 —— 鐵律 3 的容器。

「那病假呢？」之所以能被理解，不是因為模型變聰明了，
而是因為這裡記著上一輪講過什麼。
"""

from __future__ import annotations

from langchain.memory import ConversationBufferMemory

# memory_key 要跟 ConversationalRetrievalChain 期待的變數名一致，
# 改成別的名字，chain 找不到歷史就會當作每次都是第一句話。
MEMORY_KEY = "chat_history"

# 記憶只保留最近幾輪。
#   ConversationBufferMemory 本身是「全部都記」，對話一長就會把 LLM 的
#   context window 塞爆（而且每輪都要付那些 token 的錢）。
#   課堂 demo 用不到那麼長，留 10 輪當上限，順便把「記憶會爆掉」這件事寫成程式碼。
MAX_TURNS = 10


def create_memory() -> ConversationBufferMemory:
    """建立對話記憶。

    三個參數都不能少：
      memory_key="chat_history" → chain 靠這個名字找歷史
      return_messages=True      → 回傳訊息物件而不是一坨字串，格式化交給我們自己控制
      output_key="answer"       → **最容易踩的坑**。chain 同時吐出 answer 和
                                   source_documents，不指定的話記憶不知道該記哪個，
                                   會把整包來源文件塞進歷史，下一輪的改寫就全毀了。
    """
    return ConversationBufferMemory(
        memory_key=MEMORY_KEY,
        return_messages=True,
        output_key="answer",
    )


def trim_memory(memory: ConversationBufferMemory, max_turns: int = MAX_TURNS) -> None:
    """把記憶裁到最近 max_turns 輪（一輪 = 一則使用者訊息 + 一則助手訊息）。"""
    messages = memory.chat_memory.messages
    if len(messages) > max_turns * 2:
        memory.chat_memory.messages = messages[-max_turns * 2 :]


def clear_memory(memory: ConversationBufferMemory) -> None:
    """清除對話。

    注意只清記憶、**不重建 chain**——chain 重建等於重連向量庫，
    在 Streamlit 裡會讓畫面卡好幾秒，而且完全沒必要。
    """
    memory.clear()


if __name__ == "__main__":
    memory = create_memory()
    assert memory.memory_key == MEMORY_KEY
    assert memory.output_key == "answer", "output_key 沒設好，來源文件會污染對話歷史"

    for i in range(12):
        memory.save_context({"question": f"問題 {i}"}, {"answer": f"回答 {i}"})
    assert len(memory.chat_memory.messages) == 24

    trim_memory(memory, max_turns=3)
    assert len(memory.chat_memory.messages) == 6, len(memory.chat_memory.messages)
    assert "問題 11" in memory.chat_memory.messages[-2].content
    print("✓ 記憶裁切：12 輪 → 只留最近 3 輪（6 則訊息），保留的是最新的那幾輪")

    clear_memory(memory)
    assert memory.chat_memory.messages == []
    print("✓ 清除對話：memory.clear() 之後歷史歸零")
