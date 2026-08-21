# RAG Architect：把「你的語料長什麼樣」變成可稽核的架構藍圖

> Cursor 課程 Project 15（進階課題）：一個 production 級的 MCP server——`uvx` 一行掛進 Cursor，不需要任何 API key。這是 Project 10（自建 MCP Server）的實戰進階版：不只會寫工具，還要讓 AI **自己找到工具、正確使用工具**。

一句話：**確定性路由——同樣的輸入永遠給同樣的架構；每個建議點名具體元件、講明代價、附上驗證指標。一個不能重現的架構建議，不叫建議。**

## 專案規格

| | |
|---|---|
| **最終成果** | 在 Cursor 裡問「數千頁法律合約、跨頁引用多、不能上雲，RAG 怎麼做」，AI 自動調用 `design_rag_architecture` 工具，回一份藍圖：Graph-Augmented RAG + 每層點名元件（LightRAG、Kuzu、bge-reranker-v2-m3）+ 代價（「圖是一次 schema 承諾」）+ 驗證指標（multi_hop_recall） |
| **技術棧** | Python 3.10+、uv、FastMCP（`mcp[cli]`）、標準函式庫（`re`、`urllib`、`xml.etree`）——沒有其他依賴 |
| **預估時間** | 2.5–3 小時（掛起來 10 分鐘，剩下的時間在讀懂它為什麼被設計成這樣） |
| **前置需求** | `uv` 已安裝、Cursor（或 Claude Code）；**不需要任何 API key、不用註冊任何服務** |

## 這個專案做什麼

隨便問一個模型「我的法律合約要怎麼做 RAG」，你會拿到 2023 年的答案：語意切塊、embedding、丟進 pgvector、加個 reranker。這四項裡有三項在 2026 年對這種語料是錯的，而且沒有一項告訴你這個選擇的代價。

RAG Architect 是一個 MCP server，把四個關於語料的事實（規模、複雜度、隱私邊界、領域）轉成一份可以直接動手的藍圖：

1. **推薦架構**：六選一（Code RAG / Text-to-SQL / Prompt-Cached Long Context / Layout-Aware Hybrid / Graph-Augmented / Contextual Retrieval + Reranking）
2. **每層點名元件**：不是「用個向量庫」，是「Qdrant 自架或 LanceDB embedded」
3. **代價**：「late-interaction 視覺 embedding 的索引體積是純文字的 10–30 倍」
4. **驗證指標**：ragas_faithfulness、multi_hop_recall、data_egress_events（local_only 時必須為零）
5. **研究計畫**：一組查詢字串，讓**呼叫端 agent 用自己的搜尋工具**去補最新文獻——server 自己只有 arXiv 保底引用，不跑這些查詢

## 架構圖

```
Cursor / Claude Code / 任何 MCP client
  │  stdio（uvx 直接從 git 解析套件並快取，免 clone 免路徑）
  ▼
server.py    FastMCP 介面：兩個工具 + server instructions
  │            design_rag_architecture（無狀態、一次呼叫、給 coding agent）
  │            rag_consultant（有狀態訪談、一輪一題、給對話產品）
  ▼
session.py   Slot 詞彙 + 中英文抽取（純關鍵字比對，fail-safe 否定偵測）
  │            「不可以上雲」→ local_only（否定先於同意）
  ▼
router.py    決策矩陣 —— 純函式、無 I/O、無網路
  │            先看資料型態，再看語料規模，最後才看結構
  │            同樣 slots → 永遠同一個架構（這就是它值得被信任的理由）
  ▼
research.py  arXiv 保底引用（免 key）+ 給 agent 的研究計畫
               只補引用文獻，永遠不動搖決策
```

## 三個值得偷走的設計

**1. 把「會變的」和「不准變的」拆成兩層。**
`router.py` 不做任何 I/O：給定 slots，它永遠回傳同一個架構——推導過程可稽核，使用者反駁時你能指出「是哪個 slot 判錯了」而不是跟結論吵架。即時研究（`research.py`）只負責補引用，**永遠不會動搖決策**。一個會因為今天某篇部落格排名變動而改變的架構建議，本來就不叫建議。

**2. 隱私判斷要 fail-safe。**
「不可以上雲」這個字串**包含**「可以上雲」——舊版的抽取器把否定句讀成同意，一個把部署邊界判反的隱私路由器。現在：否定先被偵測（`_NEGATED_CLOUD` regex）、任何地端訊號壓過同時出現的雲端字眼、不確定時一律回 `local_only`。錯也要錯在嚴格的那一邊。

**3. 工具形狀決定會不會被自動調用。**
舊工具是 `rag_consultant(session_id, user_message)`：agent 得自己捏一個 id、跑完四輪訪談——agent 會迴避這種工具。新工具 `design_rag_architecture` 無狀態、全部參數選填、直接吃中英文自由文字、一次呼叫給答案；缺欄位時回 `NEEDS_INPUT` 加上**剛好一個**要問使用者的問題。名字也有差：`rag_consultant` 是名詞，對應不到任何使用者會打的字；`design_rag_architecture` 是動詞片語，直接對應「設計一個 RAG 架構」。

## 快速開始

掛進 Cursor（專案層 `.cursor/mcp.json`，或全域 `~/.cursor/mcp.json`）：

```json
{
  "mcpServers": {
    "rag-architect": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/kevin801221/rag-architect-mcp", "rag-architect-mcp"]
    }
  }
}
```

本地開發（跑你自己的修改）：

```bash
cd rag-architect-mcp
uv sync
uv run python test_rag_architect.py   # 22 項檢查，不連網、不需要 pytest
uv run rag-architect-mcp              # stdio server
```

Claude Code 用戶可以直接裝 plugin（多拿到 skill 和 `/rag` 指令）：

```bash
/plugin marketplace add kevin801221/rag-architect-mcp
/plugin install rag-architect@rag-architect-marketplace
```

## 核心教學重點

| 主題 | 重點 | 對應檔案 |
|---|---|---|
| MCP 掛載 | 同一個 `mcpServers` 物件到處都能用；`uvx --from git+...` 免 clone 免路徑 | `.cursor/mcp.json`、`client-configs/` |
| 確定性路由 | 純函式決策矩陣 vs 讓 LLM 即興回答；「可稽核」是信任的來源 | `rag_architect/router.py` |
| Slot 抽取 | 中英文關鍵字詞表 + fail-safe 否定偵測 + 數字分桶 | `rag_architect/session.py` |
| Tool schema 設計 | description 四段式、動詞片語命名、無狀態 + 全選填 + `NEEDS_INPUT` | `rag_architect/server.py` |
| 自動調用的四道機制 | server instructions → tool description → 工具形狀 → skill，各自獨立 | `README_zh.md` §怎麼讓 coding agent 自己找到它 |
| 測試即 bug 清單 | 22 項測試每一項對應一個真的出過的 bug | `test_rag_architect.py` |

## 誠實的限制

- **Slot 抽取是關鍵字詞表，不是 NLU**——講法不在 `session.py` 的詞表裡就抽不到（此時工具會回 `NEEDS_INPUT` 問你，而不是亂猜；這是設計的接手點）。
- **決策矩陣是 2026 年的快照**——LightRAG、ColQwen2.5、bge-m3 這些選型會過時。但因為路由可稽核，過時的時候你知道要改哪一行；`research_plan` 也明講「如果現行證據支持，就去反駁這份藍圖」。
- **arXiv 保底最多 5 篇**，回應會直說這是保底而非完整覆蓋；真正的文獻檢索交給呼叫端 agent 自己的搜尋工具。
- **`rag_consultant` 的 session 存在 server 行程記憶體**——重啟即消失；上限 256 個（LRU 淘汰），這是刻意的有界設計，不是持久化方案。
- **skill 與 `/rag` 指令是 Claude Code plugin 才有**——Cursor 掛 MCP 只拿到兩個工具（工具本身已內建 description 與 instructions，足夠觸發自動調用）。

> 知道自己的建議會過時、並且把「怎麼發現它過時」寫進回應裡，比假裝永遠正確更值錢。

---

## 檔案結構

**程式碼在 `../rag-architect-mcp/`**，本資料夾只有教學三件套（README.md / walkthrough.md / demo.sh）。

```
rag-architect-mcp/
├── rag_architect/
│   ├── server.py            # FastMCP 介面：兩個工具、server instructions
│   ├── router.py            # 決策矩陣——純函式，無 I/O，無網路
│   ├── session.py           # Slot 詞彙、中英文抽取、有上限的 session
│   ├── research.py          # arXiv（免 key）+ 選配 Tavily + 給 agent 的研究計畫
│   └── __init__.py
├── test_rag_architect.py    # 22 項檢查，每項對應一個真的出過的 bug
├── .cursor/mcp.json         # Cursor 專案層 MCP 設定（本 repo 開箱即用）
├── .mcp.json                # Claude Code 專案層 MCP 設定
├── client-configs/          # 一份 mcp.json 通吃所有 client + 各家放哪的對照表
├── skills/rag-architect/    # SKILL.md：教 Claude 拿到藍圖後該怎麼用
├── commands/rag.md          # /rag 指令（Claude Code plugin）
├── .claude-plugin/          # plugin.json + marketplace.json
├── pyproject.toml           # 唯一依賴：mcp[cli]>=1.6.0
├── README.md / README_zh.md # 完整英文／繁中文件
└── uv.lock
```

## 帶走的三句話

1. **確定性是信任的來源**——`router.py` 無 I/O、同輸入同輸出，所以使用者反駁時，你查的是「哪個 slot 判錯了」，不是「要不要換個說法再吹一次」。
2. **建議 = 元件 + 代價 + 驗證指標**——「用 GraphRAG」不是建議；「LightRAG 起步、圖是一次 schema 承諾、用 multi_hop_recall 驗證」才是。缺任何一項都只是關鍵字。
3. **工具會不會被 AI 自動調用，是設計出來的**——description 寫使用者真正會打的字、名字用動詞片語、形狀做成無狀態一次呼叫、缺欄位回一個問題而不是報錯。這四件事每一件都比「多寫幾個工具」值錢。

## 授權

MIT
