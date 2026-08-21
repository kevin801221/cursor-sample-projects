"""RAG 知識庫 Chatbot 的核心模組。

四階段對應到四個檔案：
  切塊 → chunker.py
  嵌入 → embeddings.py
  檢索 → retriever.py
  生成 → prompts.py + offline_llm.py（離線 provider）

這裡做一件事：在任何模組讀 os.getenv 之前先把 .env.local 載進來。
放在套件的 __init__ 是刻意的——這樣不管入口是 app.py、offline_index.py
還是 `uv run python -c "from src.retriever import ask"`，環境變數都保證讀得到。
"""

import os
import warnings

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env.local"))

# ConversationBufferMemory 與 ConversationalRetrievalChain 在新版 LangChain 被標記為
# deprecated（官方推薦改用 LangGraph）。本課刻意教這兩個類別，因為它們把
# 「記憶」與「改寫問題」拆得最清楚，適合第一次學 RAG 的人。
# 這裡把警告關掉，純粹是為了讓課堂螢幕乾淨——不是為了假裝它沒 deprecated。
#
# 注意順序：一定要先 import langchain 再設 filter。
# langchain 的 __init__ 會呼叫 surface_langchain_deprecation_warnings()，
# 主動把這類警告調回 "default"；先設 filter 會被它蓋掉。
try:
    import langchain  # noqa: F401  ← 只是為了讓它先跑完自己的 warning 設定
    from langchain_core._api.deprecation import (
        LangChainDeprecationWarning,
        LangChainPendingDeprecationWarning,
    )

    warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
    warnings.filterwarnings("ignore", category=LangChainPendingDeprecationWarning)
except ImportError:  # pragma: no cover - 換版本時不要因為這行就整個掛掉
    pass
