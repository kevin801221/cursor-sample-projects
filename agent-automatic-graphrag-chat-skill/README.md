# yt-graphrag-bot

**丟一個 YouTube 連結（或 PDF / DOCX / 網頁），建出一個會回答內容、會附時間戳引用、
還會即時高亮知識圖譜的問答機器人。**

一個可以掛給 **Claude Code / Cursor / Codex** 三個工具使用的 skill。
LLM 走 Gemini，套件用 uv 管理。

![問答畫面](docs/screenshot.png)

三個視圖是**同一次檢索的三種投影**：對話說「答案是什麼」，圖譜說「牽涉哪些概念、
怎麼連」，底部時間軸說「這些話是從影片的哪幾個位置撈出來的」。

---

## 這是什麼

這既是一個**可以跑的專案**，也是一份**教材**。

跑完你會有：一個左聊天右圖譜的網頁。問一個問題 → 答案出現、附可點的來源連結
（影片跳到第幾秒 / PDF 跳到第幾頁）→ 右側相關節點同步變橘色 → 點任一節點 →
鄰居子圖瞬間展開 → 底部時間軸亮出證據在影片的分布。

但它真正想教的是一個模式：

> **skill = 腳本（確定性步驟）+ MCP（即時查詢驗證）+ 分階段指引**

每個 Phase 結束都有「驗證點」——**邊建邊驗，而不是最後才 debug**。
而且每個 MCP 驗證點都附「無 MCP 替代指令」，環境沒接 MCP 也不會卡住。

## 快速開始

需要：Python 3.12+、[uv](https://docs.astral.sh/uv/)、Docker、
一把免費的 [Google AI Studio](https://aistudio.google.com) 金鑰。

```bash
git clone git@github.com:kevin801221/agent-automatic-graphrag-chat-skill.git
cd agent-automatic-graphrag-chat-skill
uv sync

export GOOGLE_API_KEY="AIza..."      # GEMINI_API_KEY 也吃
export NEO4J_PASSWORD="你自訂的密碼"

docker run -d --name neo4j-teach -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD neo4j:5 && sleep 25

uv run python scripts/check_setup.py     # 沒全綠不要往下
```

> 金鑰放 `.env` 的話，每條指令要加 `--env-file .env`。
> 用 `export` 的話請寫進 `~/.zshenv`（**不是 `~/.zshrc`**）——
> 非互動 shell 不讀 `.zshrc`，agent 開的 shell 會看不到。

全綠之後：

```bash
uv run python scripts/00_ingest_source.py "<你的影片網址>" --out source.json
uv run python scripts/02_ingest_vectordb.py source.json --persist ./chroma_db
uv run python scripts/03_build_graph.py source.json

cp scripts/04_chatbot_server.py chatbot_server.py
uv run uvicorn chatbot_server:app --port 8010
```

逐步教學（含每一步的「為什麼」、成功判準、卡住怎麼辦）：**[WALKTHROUGH.md](WALKTHROUGH.md)**

> **選材建議**：挑 20 分鐘以上的影片。語料太小（總 chunk < ~30）時，
> naive baseline 光 `k=5` 就撈走大半語料，方法驗證那步一定測不出差異。

## 掛給編輯器用

```bash
./install.sh                 # 裝到目前目錄的專案
./install.sh --global        # Claude Code / Codex 裝到使用者層
```

| 平台 | 產生什麼 | 怎麼用 |
|---|---|---|
| **Claude Code** | `.claude/skills/yt-graphrag-bot`（symlink） | 講「我想拿這支影片做問答機器人」就會觸發，或 `/yt-graphrag-bot` |
| **Cursor** | `.cursor/rules/*.mdc` + `.cursor/commands/*.md` | 描述命中時自動載入，或 `/yt-graphrag-bot` |
| **Codex** | `AGENTS.md` 標記區塊 / `~/.codex/prompts/*.md` | 自動讀，或 `/yt-graphrag-bot` |

三個平台各放一個**指路的殼**，內容都指向同一份 `SKILL.md`——不複製，因為複製就會漂移。
`install.sh` 可重複執行，`AGENTS.md` 用標記包住，重跑會覆蓋不會疊加。

## 資料流

```
YouTube URL ─┐
PDF / DOCX ──┼─ [1] 00_ingest_source.py 統一入口
網頁 URL ────┘     每種來源都有 免費地端 / 付費雲端 兩條路線
                  → 正規化 source.json（帶可回溯 ref：時間戳 / 頁碼 / 網址）
       └─ [2] 聚合 + 切塊 → Chroma VectorDB
       └─ [3] Gemini 抽三元組 → Neo4j（Entity─REL─Entity─MENTIONED_IN─Chunk）
            └─ [4] 強 RAG：Multi-Query → 向量檢索 → RRF 融合 → 圖譜擴展 → 生成
                 └─ [5] FastAPI /chat + /graph + /chunks
                      └─ [4.5] 方法驗證：naive vs 強 RAG 的 A/B 盲評
                      └─ [6] React 力導向圖前端
```

**VectorDB 和 GraphDB 不是二選一**：圖譜負責「找到相關概念與其連結」，
chunk 負責「提供原文證據與時間戳」。兩者用 `chunk_index` ↔ `chunk_id` 精確對齊。

## 檔案

| | |
|---|---|
| `SKILL.md` | 流程編排、判斷邏輯、每步的「為什麼」。三個平台都讀這份 |
| `WALKTHROUGH.md` | 一步一步的操作教學，含預期輸出與卡點速查 |
| `EVALUATION.md` | 實跑評估報告：修過哪些缺陷、哪些沒修、哪些沒驗證 |
| `scripts/` | 七支 .py，確定性、可重跑、**冪等** |
| `references/` | MCP 設定 / 前端 / 方法驗證，按需載入不塞爆主文件 |
| `install.sh` | 三平台安裝 |

前端程式碼在 `references/frontend-graph.md` 裡（完整可貼上的 `App.jsx` + `index.css`）。

## 三個值得偷走的設計

**1. 把必然會發生的失敗前移。**
Google 每隔一陣子改模型名，任何寫死模型名的教材都會過期。
`check_setup.py` 會拿你的金鑰**真的去問一次 Google「有哪些模型可用」**，
不在清單裡就印出可用清單叫你 export。
把 Phase 3 的神秘 404，變成 Phase 0 的一行提示。

**2. 引用必須可回溯，而且要看得見。**
影片時間戳和 PDF 頁碼是同一件事的不同外衣。做 RAG 最容易被信任的不是答案本身，
是「我可以點過去自己確認」。前端的時間軸就是把這件事變成畫面。

**3. 方法宣稱要有雙證據。**
`05_evaluate_rag.py` 做的是 naive 向量 RAG vs 強 RAG 的 LLM-as-judge 盲評
（隨機換位防位置偏誤）。一個方法可以宣稱「目前最好」，若且唯若：
**與文獻對齊 + 在自己的評估集上數據不輸 + 每個被否決的候選都留有紀錄**。
缺任何一條都只是「我覺得不錯」。

## 誠實的限制

這個 repo 的 [EVALUATION.md](EVALUATION.md) 記錄了實跑找到的每一個缺陷——
包含**已修的**（LangChain 1.x 的 `.content` 是 list 不是字串、跨來源圖譜汙染、
markdown 亂炸的根因在後端 prompt…）和**刻意沒修的**（judge 與受測 pipeline 同級模型、
Neo4j 沒建索引、圖譜同義詞未正規化…）。

還沒驗證的也寫在裡面：付費解析路線（LlamaParse / Tavily）、whisper fallback。

> 知道自己的證據有多強，比證據看起來多漂亮更重要。

## 授權

MIT
