# WALKTHROUGH：一步一步把 GraphRAG 問答機器人做出來

這份文件給兩種人看：

- **老師 / 自己動手的人**：照著複製貼上，一路跑到能問答的機器人。
- **帶 agent 跑的人**：每一步都標了「叫 agent 做」的說法，讓 Claude Code /
  Cursor / Codex 幫你執行。

跑完你會有：一個左邊聊天、右邊知識圖譜的網頁。問一個問題 → 答案出現、
附可點的來源連結（影片跳到第幾秒 / PDF 跳到第幾頁）、右側相關節點同步變橘色
→ 點任一節點 → 鄰居子圖瞬間展開。

**總時間**：第一次跑約 40–60 分鐘（含裝環境）。之後重跑 10 分鐘內。

---

## 目錄

| 步驟 | 在做什麼 | 大約時間 |
|---|---|---|
| [Step 0](#step-0裝-skill你只需要做一次) | 把 skill 裝進 Claude Code / Cursor / Codex | 2 分 |
| [Step 1](#step-1環境準備) | uv 環境、Gemini 金鑰、Neo4j、起飛前檢查 | 15 分 |
| [Step 2](#step-2抓來源) | YouTube / PDF / DOCX / 網頁 → `source.json` | 3 分 |
| [Step 3](#step-3切塊入向量庫) | 切塊 + 嵌入 → Chroma | 3 分 |
| [Step 4](#step-4抽知識圖譜) | LLM 抽三元組 → Neo4j | 5–15 分 |
| [Step 5](#step-5起後端強-rag--api) | 強 RAG + FastAPI | 5 分 |
| [Step 6](#step-6方法驗證用數據證明強-rag-有用) | A/B 評測、decision record | 10 分 |
| [Step 7](#step-7前端圖譜視覺化) | React 力導向圖 | 10 分 |

---

## Step 0：裝 skill（你只需要做一次）

```bash
cd <這個資料夾>
./install.sh                 # 裝到目前目錄的專案
# 或
./install.sh /path/to/proj   # 裝到指定專案
./install.sh --global        # Claude Code / Codex 裝到使用者層（全域可用）
```

它做了什麼——三個平台各放一個「指路的殼」，內容都指向同一份 `SKILL.md`：

| 平台 | 產生的檔案 | 怎麼用 |
|---|---|---|
| **Claude Code** | `.claude/skills/yt-graphrag-bot`（symlink） | 講「我想拿這支影片做問答機器人」就會自動觸發；也可以打 `/yt-graphrag-bot` |
| **Cursor** | `.cursor/rules/yt-graphrag-bot.mdc`<br>`.cursor/commands/yt-graphrag-bot.md` | 描述命中時自動載入；或打 `/yt-graphrag-bot` |
| **Codex** | 專案層 `AGENTS.md` 標記區塊<br>全域 `~/.codex/prompts/yt-graphrag-bot.md` | 自動讀 AGENTS.md；全域版打 `/yt-graphrag-bot` |

> **為什麼是「殼」而不是複製三份？**
> 複製就會漂移——改了一份忘了另外兩份是遲早的事。三個殼都只講一句話：
> 「先去讀 `SKILL.md`，然後照它做」。唯一真相來源只有一個。
> 這個取捨本身就值得跟同學講：**跨平台相容的成本，要付在結構上，不是付在複製貼上。**

`install.sh` 可以重複執行，`AGENTS.md` 用標記區塊包住，重跑會覆蓋不會疊加。

**✅ 這步成功了嗎**：`./install.sh /tmp/test` 後應看到三個 `[✓]`。

---

## Step 1：環境準備

### 1-1 裝套件（用 uv，不要用 pip）

```bash
cd <這個資料夾>
uv sync
```

一行搞定所有相依。之後**每一個 Python 指令都以 `uv run` 開頭**，
不需要 `source activate` 任何東西。

> 為什麼堅持 `uv run`：agent（Claude Code / Cursor / Codex）每次執行 shell
> 指令都是獨立的 process，`source .venv/bin/activate` 不會留到下一個指令。
> `uv run` 每次自己處理環境，這是唯一在 agent 手上百分之百可靠的做法。

### 1-2 拿 Gemini 金鑰（免費）

1. 開 https://aistudio.google.com
2. 左側 **Get API key** → **Create API key**
3. 複製那串 `AIza...`

金鑰有兩種放法，**先決定你要哪一種**，混著用一定出事：

**(a) export**（本文所有指令原樣可用）
```bash
export GOOGLE_API_KEY="AIza..."   # GEMINI_API_KEY 這個名字也行，SDK 兩個都吃
export NEO4J_PASSWORD="你自訂的密碼"
```
> ⚠️ **要寫進 `~/.zshenv`，不是 `~/.zshrc`。**
> zsh 的非互動 shell（agent 執行指令時開的那種）**只讀 `~/.zshenv`**。
> 寫在 `~/.zshrc` 你自己的終端機看得到，但 Claude Code / Cursor / Codex 開的
> shell 看不到——會出現「我明明設了它卻說沒設」這種鬼打牆。

**(b) `.env` 檔**
```bash
GOOGLE_API_KEY=AIza...
NEO4J_PASSWORD=你自訂的密碼
```
選這條的話，**本文每一條 `uv run` 都要加 `--env-file`**：
```bash
uv run --env-file .env python scripts/check_setup.py
```
`.env` 不在 skill 目錄就給路徑（`--env-file ../.env`）。
`uv` 沒辦法在 `pyproject.toml` 裡預設這個，只能每次帶——中途漏一次就會
出現「明明設了卻說沒設」。

### 1-3 起 Neo4j（知識圖譜要住的地方）

```bash
export NEO4J_PASSWORD="你自訂的密碼"

docker run -d --name neo4j-teach -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/你自訂的密碼 neo4j:5
```

**啟動要等約 20 秒**才連得上，急著往下跑會看到連線失敗。
起來之後瀏覽器開 http://localhost:7474 可以看到 Neo4j 介面（帳號 `neo4j`）。

### 1-4 起飛前檢查（沒全綠不准往下）

```bash
uv run python scripts/check_setup.py
```

它會檢查四類東西，**每個失敗項目下面都直接給你修復指令**：

```
=== 1/4 套件檢查 ===
[✓] 套件 yt-dlp
...
=== 2/4 環境變數檢查 ===
[✓] GOOGLE_API_KEY
[✓] NEO4J_PASSWORD
=== 3/4 Gemini 模型檢查 ===
[✓] Gemini API 連線
[✓] 對話模型 gemini-3.5-flash
[✓] 嵌入模型 gemini-embedding-001
=== 4/4 Neo4j 連線檢查 ===
[✓] Neo4j 連線

ALL CHECKS PASSED — 可以開始 Phase 1
```

> **第 3 項為什麼要真的打 API？**
> 因為 Google 會改模型名（`gemini-1.5` → `2.5` → `3.x`），寫死的預設值遲早過期。
> 這支檢查會拿你的金鑰真的去問一次「有哪些模型可用」，不在清單裡就直接
> 印出可用清單叫你 `export`。
> **把一個必然會發生的失敗，從 Step 3 的神秘 404 前移到 Step 1 的一行提示**
> ——這是整個 skill 最值得抄走的設計。

模型名要換就一個 export，所有腳本同時生效：

```bash
export GEMINI_MODEL="<清單裡的某支 flash>"
export GEMINI_EMBED_MODEL="<清單裡的某支 embedding>"
```

**✅ 這步成功了嗎**：最後一行是 `ALL CHECKS PASSED — 可以開始 Phase 1`。
**❌ 卡住了**：照每個 `✗` 下面的「修復 →」貼上執行，重跑直到全綠。
Neo4j 那項失敗多半只是還沒起來，等 20 秒再跑一次。

---

## Step 2：抓來源

一支腳本吃四種來源，全部正規化成同一個 `source.json`，下游完全不用改：

```bash
# YouTube（會自動 fallback：人工字幕 → 自動字幕 → 提示走 whisper）
uv run python scripts/00_ingest_source.py "https://www.youtube.com/watch?v=..." --out source.json

# PDF
uv run python scripts/00_ingest_source.py report.pdf --out source.json

# DOCX（段落 + 表格都會抽）
uv run python scripts/00_ingest_source.py spec.docx --out source.json

# 網頁
uv run python scripts/00_ingest_source.py "https://blog.example.com/post" --out source.json
```

預期輸出：

```
[*] 使用 manual 字幕，語言: en
[✓] 60 段字幕已存至 source.json
[✓] youtube 來源 60 段已存至 source.json
```

> **選材很重要，而且會影響 Step 6 的結論。**
> 挑 **20 分鐘以上、資訊密度高**的影片，或一次灌好幾份文件。
> 語料太小（總 chunk < ~30）時，Step 6 的 naive baseline 光 `k=5` 就撈走
> 大半語料，強 RAG 再厲害也沒有發揮空間，A/B 一定測不出差異。
> 實測過：一支 6 分鐘影片只產出 8 個 chunk，8 題有 6 題兩邊評分完全相同。

### 這裡有個要先問使用者的決策（付費 vs 免費）

PDF 和網頁各有兩條路線。**執行前先問**——這個「問」本身就是教學設計，
讓同學體會工具選擇是成本效益判斷，不是有錢就砸：

| 來源 | 免費地端（預設） | 付費雲端 | 什麼時候值得花錢 |
|---|---|---|---|
| PDF | pymupdf | `--engine llamaparse` | 掃描件（要 OCR）、複雜表格、多欄排版 |
| 網頁 | trafilatura | `--engine tavily` | JS 渲染頁、有反爬的網站 |
| DOCX | python-docx | **無** | 這格刻意留白：邊際效益為零就不買 |
| YouTube | yt-dlp | **無** | 同上 |

免費路線失敗時腳本會明確叫你改用哪個付費引擎——先試便宜的、失敗訊息要能指路。

### 打開 `source.json` 看一眼（重要）

```bash
uv run python -c "import json; d=json.load(open('source.json')); print(d['source_type'], len(d['segments'])); print(d['segments'][0])"
```

注意每段都有 `ref` 欄位：

- YouTube → `https://youtu.be/<id>?t=<秒>`
- PDF → `file:///.../report.pdf#page=3`
- 網頁 → 原網址

> **這是整個專案的設計核心：引用必須可回溯。**
> 影片時間戳和 PDF 頁碼是同一件事的不同外衣。做 RAG 最容易被信任的
> 不是答案本身，是「我可以點過去自己確認」。

**✅ 這步成功了嗎**：印出 `[✓] <來源類型> 來源 N 段已存至 source.json`，N ≥ 1。
**❌ 卡住了**：
- YouTube 429 → 被限流，等 5 分鐘重試。**課堂建議課前預抓好 `source.json` 發給同學**，
  一個班同時抓同一支影片幾乎必被擋。
- PDF 抽不到字 → 掃描版，加 `--engine llamaparse`（需 `LLAMA_CLOUD_API_KEY`）。
- 網頁抽不到正文 → JS 渲染頁，加 `--engine tavily`（需 `TAVILY_API_KEY`）。

---

## Step 3：切塊入向量庫

```bash
uv run python scripts/02_ingest_vectordb.py source.json --persist ./chroma_db
```

預期輸出：

```
[*] 產生 47 個 chunks
[✓] 已寫入 collection='yt_rag' at ./chroma_db
```

### 這步要講的三件事

**1. 先聚合，再切塊。**
YouTube 字幕一段只有 2~3 秒，直接嵌入品質極差（「所以呢」自己成為一個
向量有什麼意義？）。腳本先把碎片聚成 ~60 秒的自然段，才進切塊器。
PDF/DOCX/網頁在 Step 2 就已經聚合過（碎段合併到 ≥200 字）。
**嵌入單位要是完整語意段**——這是同一個原則的兩種實作。

**2. metadata 設計就是產品設計。**
`url_at_time` 讓引用可點、`chunk_index` 讓 Step 4 的圖譜能對回原文。
現在多存一個欄位，比之後回頭重跑整個 pipeline 便宜太多。

**3. 腳本是冪等的。**
重跑會先刪掉同一個 `video_id` 的舊資料。
問同學：為什麼這很重要？（答：不然改個參數重跑一次，庫裡就是兩份重複
chunk，檢索結果被自己汙染，而且看起來完全正常。）

### 驗證（建完一層就立刻驗，不要等到最後才 debug）

**有 Chroma MCP**：問「列出 collection `yt_rag` 前 5 筆與它們的 metadata」。

**沒有 MCP**（效果等價）：

```bash
uv run python -c "
import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
emb = GoogleGenerativeAIEmbeddings(model=os.environ.get('GEMINI_EMBED_MODEL','gemini-embedding-001'))
db = Chroma(collection_name='yt_rag', embedding_function=emb, persist_directory='./chroma_db')
r = db.get(limit=3)
print('chunks 總數:', db._collection.count())
print('第一筆 metadata:', r['metadatas'][0] if r['metadatas'] else '空的!')
"
```

**✅ 這步成功了嗎**：metadata 裡看得到 `chunk_index`、`url_at_time`、`source_type`。
**❌ 卡住了**：
- metadata 是「空的!」→ persist 路徑不一致，確認兩邊都是 `./chroma_db`。
- 報 dimension mismatch → 你換過 `GEMINI_EMBED_MODEL` 但沒重建庫。
  `rm -rf ./chroma_db` 重跑。**換嵌入模型 = 整個向量空間重建**，沒有例外。

---

## Step 4：抽知識圖譜

```bash
uv run python scripts/03_build_graph.py source.json
```

預期輸出（每個 chunk 一行）：

```
[*] chunk 1/47: +6 triples
[*] chunk 2/47: +5 triples
...
[✓] 圖譜完成: 213 條關係
```

**這步會跑比較久**（每個 chunk 打一次 LLM）。47 個 chunk 大約 3~10 分鐘。
Gemini 免費層有每分鐘請求上限，被限流就等一分鐘重跑——腳本是冪等的，不會寫重複。

### 這步要講的四件事

**1. 強制 JSON 輸出 + 「只抽明確陳述、不腦補」。**
這是 hallucination 控制在**資料層**的示範。等到生成階段才防就太晚了——
髒資料進了圖譜，之後每次檢索都會撈到它。

**2. 圖 schema 刻意做得很笨。**
`(Entity)-[REL {type:"包含"}]->(Entity)`——關係型別存成**屬性**而不是動態
label。動態 label 要裝 APOC 外掛，教學環境多一個安裝步驟就多一批人卡住。
**能用內建就不裝外掛**，這個取捨在教室裡的價值遠大於查詢效能。

**3. `MERGE` 而不是 `CREATE`。**
同一個實體在不同 chunk 出現會自動合併。**圖譜的價值正是把散落在影片各處
的同一概念連起來**——如果每次出現都建一個新節點，你只是做了一堆孤島。

**4. 同義詞沒合併，是特色不是 bug。**
你八成會看到「LangGraph」和「Lang Graph」變成兩個節點。
這時候回頭去 `EXTRACT_PROMPT` 加一條正規化規則、重跑、再看圖——
**這個迭代過程本身就是最好的教學素材**，比直接給一個完美的 prompt 有用。

### 驗證

**有 Neo4j MCP**：問「MENTIONED_IN 最多的前 10 個 Entity」。

**同時開 http://localhost:7474**，執行 `MATCH (n) RETURN n LIMIT 100`
讓同學親眼看到圖長出來——**課堂效果極好，這是整堂課的第一個「哇」**。

**沒有 MCP**：

```bash
uv run python -c "
import os
from neo4j import GraphDatabase
d = GraphDatabase.driver(os.environ.get('NEO4J_URI','bolt://localhost:7687'), auth=(os.environ.get('NEO4J_USER','neo4j'), os.environ['NEO4J_PASSWORD']))
with d.session() as s:
    n = s.run('MATCH (e:Entity) RETURN count(e) AS c').single()['c']
    r = s.run('MATCH (a:Entity)-[x:REL]->(b:Entity) RETURN count(x) AS c').single()['c']
    print(f'Entity 節點: {n}, REL 關係: {r}')
d.close()
"
```

**✅ 這步成功了嗎**：Entity 與 REL 數都 > 0。
**❌ 卡住了**：
- Entity = 0 → 抽取全失敗。檢查 `GOOGLE_API_KEY` 有效、免費額度沒用盡。
- 連線錯誤 → 回 Step 1 跑 `check_setup.py`。

---

## Step 5：起後端（強 RAG + API）

```bash
cp scripts/04_chatbot_server.py chatbot_server.py   # 模組名不能數字開頭
uv run uvicorn chatbot_server:app --reload --port 8000
```

**這支要一直開著**，Step 6 和 Step 7 都要打它。開另一個終端機做接下來的事。

### 「強 RAG」是哪四件事

```
問題 → ① Multi-Query 改寫成 3 個視角
     → 向量檢索（每個 query 各取 top-4）
     → ② RRF 融合去重
     → ③ 圖譜擴展（從命中 chunk 反查 Entity 一階鄰居）
     → 組 context（原文證據 + 圖譜關係）→ 生成（附時間戳引用）
```

每一步都要講「為什麼存在」，不然同學只會覺得你在堆東西：

**① Multi-Query**：解決 **vocabulary mismatch**——使用者問「怎麼記住之前
講過的話」，影片裡的詞是「檢查點機制」。同一個問題改寫成術語版 / 白話版 /
背景版三個檢索視角，總有一個對得上。

**② RRF 融合**（`score = Σ 1/(k+rank)`）：三路檢索結果要怎麼合？
RRF 只看排名不看分數，所以**不用調權重**。多路檢索最省事的融合法。

**③ 圖譜擴展**：這就是 **GraphRAG 相對純向量 RAG 的增量**。
向量檢索只能撈到「講法相似」的片段；圖譜能把「影片別處提過、但講法完全不同
的相關概念」帶進來。這是整堂課的論點，Step 6 會用數據驗證它。

**④ 防脆弱**：Multi-Query 改寫失敗（LLM 吐出爛 JSON）時，直接退回原問題繼續跑。
**加強元件永遠要有 graceful degradation**——不能讓 pipeline 因為「加強」
而變得更容易掛。這是加元件時最常被忘記的一條。

### 驗證（原樣複製兩條）

```bash
curl -s localhost:8000/graph | uv run python -c "import json,sys; d=json.load(sys.stdin); print('圖節點:', len(d['nodes']), '邊:', len(d['links']))"

curl -s -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"question":"這個內容主要在講什麼"}' \
  | uv run python -c "import json,sys; d=json.load(sys.stdin); print('answer:', d['answer'][:80]); print('sources:', len(d['sources']), '| graph_nodes:', len(d['graph_nodes']))"
```

**✅ 這步成功了嗎**：第一條印出節點/邊 > 0；第二條印出非空 answer、sources ≥ 1。
**❌ 卡住了**：
- `Connection refused` → server 沒起來，看 uvicorn 那個終端機的錯誤。
- answer 說「不知道」→ **這是正常的，代表它誠實**。換一個跟內容真的相關的問題再測。
- `graph_nodes = 0` 但 answer 正常 → 圖譜擴展沒撈到東西，回 Step 4 確認 Entity 數 > 0。

---

## Step 6：方法驗證（用數據證明強 RAG 有用）

這是整份教材方法論含金量最高的一段。前面加了 Multi-Query、RRF、圖譜擴展
三個東西——**你怎麼知道它們不是白加的？**

先講清楚「最好」的誠實定義（三條件缺一不可）：

1. **文獻對齊**：跟官方文件 / 近期文獻的最佳實務不衝突，衝突處有明確理由。
2. **實測勝出**：在你自己的評估集上，數據不輸給所有已測候選。
3. **紀錄在案**：每個被否決的候選都留有否決證據。

缺任何一條，都只是「我覺得不錯」。**這個定義本身就值得一頁投影片。**

### 6-1 建評估集（先於一切，定版後不准改題）

```bash
uv run python scripts/05_evaluate_rag.py --generate source.json --n 10
```

**產出的 `eval_set.json` 必須人工看過**，刪掉爛題再往下。
評估集品質決定整個結論的可信度——用爛題測出來的勝利沒有意義。

### 6-2 A/B 實測

```bash
uv run python scripts/05_evaluate_rag.py --run eval_set.json --api http://localhost:8000
```

比的是：**naive 向量 RAG（top-5 直接生成）vs 現行強 RAG**。
LLM-as-judge 盲評，腳本會**隨機交換 A/B 位置**防位置偏誤，
依 faithfulness / completeness / citation 三維度各給 1–5 分。

預期結尾：

```
===== 勝負 =====
{
  "baseline":   {"faithfulness": 3.8, "completeness": 3.2, "citation": 3.5},
  "strong_rag": {"faithfulness": 4.3, "completeness": 4.1, "citation": 4.2},
  "wins": {"baseline": 2, "strong_rag": 7, "tie": 1}
}
```

> ⚠️ **本課程預設 judge 和受測 pipeline 是同一支模型（都是 Flash）。**
> 這樣最省成本，但 judge 沒有比受測系統更強的判斷力，而且兩邊同源會有
> self-preference bias。**這個設定下的勝負只能當方向性訊號，不能當強證據。**
> 要升級：`export GEMINI_JUDGE_MODEL=<更強的模型>` 再重跑，並在 decision
> record 註明用了哪支 judge。
>
> 把這條限制講出來，本身就是教學重點：
> **知道自己的證據有多強，比證據看起來多漂亮更重要。**

### 6-3 SOTA 對齊迴圈（進階選做）

用 Langchain-docs MCP 查官方當前推薦的 retrieval 技術、用 web search 查近期
RAG/GraphRAG 文獻 → 列出「文獻推薦但我們沒有」的候選（reranker、HyDE、
hybrid BM25、社群偵測式 GraphRAG…）→ **一次只實作一個** → 用同一評估集重跑
6-2 → 勝則併入主線重新受挑戰、敗則寫進 decision record 否決欄 → 直到無候選勝出。

迴圈紀律與 decision record 範本見 `references/method-validation.md`。

> 這段示範的是 **agent 的自我證成能力**——不是讓 LLM 說「我的方法很好」，
> 而是讓它建立評估基礎設施、調研、實測、留紀錄。
> **「有邊界的強結論」比「無邊界的空話」有價值。** 這句話值得寫在白板上。

**✅ 這步成功了嗎**：`eval_report.json` 產出，且 `wins.strong_rag > wins.baseline`。

**❌ 強 RAG 沒贏**：**這不是錯誤，是重要發現。** 依序查三個原因：

1. **語料太小（最常見）**。看總 chunk 數，低於 ~30 就別期待強 RAG 會贏——
   naive 的 `k=5` 已經撈走語料的一大半，兩邊 context 幾乎重疊，
   檢索策略根本沒有發揮空間。**徵兆是兩邊分數一起觸頂**（都 4.5 以上）。
   → 換長一點的影片或多灌幾份文件再重跑。
2. **圖譜空或全是孤島**。回 Step 4 看 Entity 數。
3. **Multi-Query 改寫偏題**。

三個都不是 → 如實回報「在此語料上強 RAG 無顯著增量」。
**評估的價值就在這裡：它會告訴你「你加的東西沒用」，這個結論跟「有用」一樣值錢。**
上課時這是比贏了更好的教材——因為它讓同學看到，方法宣稱是要被檢驗的，
不是講出來就算數。

---

## Step 7：前端圖譜視覺化

```bash
npm create vite@latest frontend -- --template react
cd frontend && npm i react-force-graph-2d
```

把 `references/frontend-graph.md` 裡的完整 `App.jsx` 貼進 `src/App.jsx`，然後：

```bash
npm run dev
```

瀏覽器開 http://localhost:5173。

### 已經幫你處理好的四個坑（講解時要點出來）

1. **react-force-graph 會改寫 links**：渲染後 `link.source` 會從字串變成節點
   物件。合併子圖去重時要寫 `l.source.id ?? l.source`，漏掉會出現重複邊或
   直接 crash。**這是這個套件最經典的坑。**
2. **節點合併去重**：直接 concat 會有重複 id，力導向圖會抖動不停。
3. **CORS**：後端已開 `allow_origins=["*"]`——**僅限教學，正式部署一定要鎖**。
4. **畫布尺寸**：不給 `width`/`height` 就會用整個視窗寬，被左邊 420px 聊天欄
   一擠，圖的右半邊直接被切出畫面外——**投影幕上特別明顯**。

### 課程高潮

問一個問題 → 答案出現、附時間戳連結 → 右側圖譜相關節點同步變橘色
→ 點任一節點 → 鄰居子圖瞬間展開。

**✅ 這步成功了嗎**：左聊天右圖譜都看得到；問一題後有節點變橘；點節點後圖上節點數增加。
**❌ 卡住了**：
- 圖是空白 → 先確認 Step 5 第一條驗證的節點數 > 0，再開 DevTools Console 看
  是不是 CORS 或連線錯誤（後端要還在 8000 埠跑）。
- 節點不會展開 → Console 若報 `l.source.id` 相關錯誤，表示你用了自己改寫的
  合併邏輯而不是 reference 裡的版本。

### 升級路線（選做）

把左側聊天欄換成 CopilotKit（AG-UI 協定），用 `useCopilotAction` 註冊一個
`highlightNodes` 前端動作，讓 agent 回答時**主動呼叫它高亮節點**——
這是「agent 操作前端」的核心賣點。

**寫之前先用 CopilotKit MCP 查當前 API**。前端框架迭代很快，照舊教學抄必踩版本坑。

---

## 附錄 A：帶 agent 跑的說法

裝好 skill 之後，直接對 Claude Code / Cursor / Codex 說：

> 用 yt-graphrag-bot 這個 skill，幫我把 https://youtube.com/watch?v=XXX 做成問答機器人。

或明確叫 slash 指令：`/yt-graphrag-bot`

agent 會照 `SKILL.md` 的 Phase 順序執行，每個 Phase 完成後回報
「Phase N 完成：<成功判準的實際輸出>」。**卡住時它應該把完整錯誤訊息貼給你，
而不是自己亂改腳本**——這是 SKILL.md 硬規則第 4 條刻意設定的。

「教同學建」模式（預設）：每個 Phase 會先講「為什麼」，展示腳本關鍵段落，
執行，然後帶你用 MCP 驗證。
「幫我建」模式：直接跑，每 Phase 回報驗證結果。開頭講清楚你要哪種。

---

## 附錄 B：這個 skill 本身在示範什麼

帶同學回頭看 skill 的結構——**這才是課程真正要教的東西**：

| 元素 | 在本 skill 中 | 通用原則 |
|---|---|---|
| 腳本 | `scripts/` 七支 .py | 確定性、可重跑、**冪等**的步驟寫成腳本 |
| MCP（驗證用） | Chroma / Neo4j | 建完每層立刻互動驗證，不要最後才 debug |
| MCP（判斷依據用） | Langchain-docs / CopilotKit + web search | **易過期的知識即時查**，轉譯成決策依據 |
| 評估迴圈 | Step 6 + eval 腳本 + decision record | 方法宣稱要有「文獻對齊 + 實測數據」雙證據 |
| `SKILL.md` | 主文件 | 流程編排、判斷邏輯、每步的「為什麼」 |
| `references/` | 三份深度文件 | **按需載入**，不塞爆主文件 |
| 跨平台殼 | `.claude` / `.cursor` / `AGENTS.md` | 一份真相 + N 個指路殼，不要複製 N 份 |

**出作業建議**：讓同學把 Step 4 的抽取 prompt 換成自己領域的 schema
（財經影片抽「公司-持有-產品」、醫學影片抽「藥物-治療-疾病」），
親身體會 **schema 設計對圖譜品質的決定性影響**。

---

## 附錄 C：常見卡點速查

| 症狀 | 原因 | 解法 |
|---|---|---|
| `ModuleNotFoundError` | 指令沒加 `uv run`，或不在 skill 根目錄 | 加 `uv run`，`cd` 到有 `pyproject.toml` 那層 |
| 金鑰明明設了卻說沒設 | 寫在 `~/.zshrc`（非互動 shell 不讀），或金鑰在 `.env` 但指令沒加 `--env-file` | 改寫 `~/.zshenv`；或每條指令加 `--env-file .env` |
| `address already in use` (8000) | 埠被別的程式佔用 | 換埠 `--port 8010`，Step 6 記得 `--api http://localhost:8010` |
| `'list' object has no attribute 'strip'` | 舊版腳本用了 `.content`；LangChain 1.x 要用 `.text` | 已修正，確認你的腳本是最新版 |
| Gemini 404 / model not found | 模型改名了 | `uv run python scripts/check_setup.py` 看可用清單 → `export GEMINI_MODEL=...` |
| Gemini 429 / quota exceeded | 免費層每分鐘請求上限 | 等一分鐘重跑，腳本冪等不會重複寫 |
| Chroma dimension mismatch | 換過嵌入模型但沒重建庫 | `rm -rf ./chroma_db` 重跑 Step 3 |
| YouTube 抓不到字幕 / 429 | 被限流 | 等幾分鐘；**課堂請課前預抓 `source.json` 發放** |
| PDF 抽不到字 | 掃描版 | `--engine llamaparse`（需 `LLAMA_CLOUD_API_KEY`） |
| 網頁抽不到正文 | JS 渲染頁 | `--engine tavily`（需 `TAVILY_API_KEY`） |
| 文件來源被切成超大塊 | 誤用 `01` 直出格式跳過 `00` | 一律用 `00_ingest_source.py` 當入口 |
| Chroma MCP 查無資料 | MCP 與腳本路徑/collection 不一致 | 用絕對路徑，見 `references/mcp-setup.md` |
| 圖譜全是孤島節點 | 抽取 prompt 實體正規化不足 | 在 `EXTRACT_PROMPT` 加同義詞正規化規則後重跑 |
| 前端圖重複邊 / 抖動 | 沒處理 `link.source` 被改寫成物件 | 用 `references/frontend-graph.md` 的版本，坑 1 |
| 前端圖右半邊被切掉 | `ForceGraph2D` 沒給 width | 同上，坑 4 |
| 強 RAG 沒贏 naive | **多半是語料太小** | 先查總 chunk 數（< ~30 就是）；再查 Entity 數、Multi-Query 是否偏題 |
| A/B 勝負反覆不穩 | judge 噪音 | 差距 < 0.3 分視為平手；或每題評 3 次取中位數 |
