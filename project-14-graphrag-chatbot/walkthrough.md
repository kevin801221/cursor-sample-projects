# Walkthrough：把 GraphRAG 問答機器人一步一步建起來

> 這份文件帶你從零建出一個完整的 RAG 問答機器人——從丟一個 YouTube 連結或 PDF 開始，產出一個會回答問題、會附時間戳引用、還會即時高亮知識圖譜的應用。你會親手證明一件事：**向量資料庫和知識圖譜各司其職，一起比單獨用更厲害。**
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先做這五件事，做的當天才不會卡）

1. **裝好 Docker Desktop，並先跑一次 Neo4j**——第一次拉映像檔可能 5–10 分鐘。Neo4j 啟動要等 20 秒才連得上，提前跑過一次會省麻煩。（公司電腦裝不了 Docker？走 Step 0-3B 的 Neo4j Aura 雲端路線，一樣能上完全課。）
2. **註冊好 Google AI Studio 帳號、拿一把 Gemini API 金鑰**（aistudio.google.com，點 Get API key → Create API key），放在環境變數。跑一次 `check_setup.py`——沒全綠再往下。
3. **選好一支 20 分鐘以上、資訊密度高的影片**。如果要用指令在當下抓字幕，同時跟多人搶同一支影片會被 YouTube 限流（429）；建議自己先抓一遍 `source.json` 確認可行。
4. **看過本文件的每個「✅ 預期看到」**——知道正常畫面長什麼樣，才判斷得出「這是正常的」還是「翻車了」。
5. **有備用素材**：在自己電腦上先完整跑過一遍，確認能生出可用的 source.json、Neo4j 圖譜、答案。如果現場網路或 Docker 出問題，備用步驟能用存好的中間產物繼續往下。

## 🗺️ 學習地圖（建議 3 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 第 1 節概念 | 30 分 | 閱讀理解（這是全課靈魂，慢慢看） |
| Phase 0 起飛前檢查 | 10 分 | 動手做（3 個指令，一遍 check_setup） |
| Phase 1 多來源擷取 | 15 分 | 動手做或閱讀理解（預抓 source.json、講選材建議） |
| Phase 2 向量化 | 15 分 | 動手做（Chroma 裡的 metadata、切塊邏輯） |
| Phase 3 圖譜抽取 | 25 分 | 動手做（抽取 prompt → MERGE 寫入 → 5 條 Cypher 巡圖；Neo4j 視覺化是全程最「哇」的時刻） |
| Phase 4–5 強 RAG + API | 20 分 | 動手做（測 /chat 與 /graph，看時間戳引用） |
| Phase 4.5 方法驗證 | 20 分 | 動手做（A/B 盲評數據出爐——用數據說話） |
| Phase 6 前端視覺化 | 15 分 | 動手做（問題 → 答案 → 節點變橘 → 點節點展開） |
| 收尾 + 誠實條款 | 10 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `./agent-automatic-graphrag-chat-skill/`，遙控器是 `./demo.sh`（位於 `project-14-graphrag-chatbot/` 根目錄）。
> 整堂課只有一個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 支援從轉錄擷取、向量儲存、圖譜抽取到混合多跳推理問答之全管線展示。

### 上課前 15 分鐘要先做完（不要當著學生的面做）

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd agent-automatic-graphrag-chat-skill && uv sync` | 同步虛擬環境與 LanceDB / NetworkX / LangChain 依賴 |
| 2 | 跑一次 `./demo.sh 1` | 執行 `check_setup.py` 確認所有依賴健全 |
| 3 | 檢查預載資料庫 | 確認已有 `source.json` 與本機向量庫快取 |

### 放映時間軸

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:30 | 開場故事 + 概念 | — | `walkthrough.md` §開場故事 ～ §1 | 圖書館書架 vs 偵探紅線板比喻、多跳推理原理 | 傳統向量 RAG 的盲點與 GraphRAG 優勢 |
| 0:30–0:40 | 第 1 幕：環境檢查 | `./demo.sh 1` | `agent-.../scripts/check_setup.py` | 向量庫、圖譜演算法套件與 LLM 介面檢查全綠 | 課前環境與相依確認 |
| 0:40–1:00 | 第 2 幕：多來源擷取與轉錄 | `./demo.sh 2` | `agent-.../scripts/00_ingest_source.py` | YouTube 轉錄、字幕清洗與語意切塊格式 | 垃圾進垃圾出——好的 RAG 從乾淨切塊開始 |
| 1:00–1:30 | 第 3 幕：知識圖譜構建 ⭐ | `./demo.sh 3` | `agent-.../scripts/03_build_graph.py` | 實體 (Entity) 與關聯 (Relation) 抽取拓撲圖 | 不只記文字，更記住概念之間的關係網 |
| 1:30–2:10 | 第 4 幕：GraphRAG 混合問答 ⭐ | `./demo.sh 4` | `agent-.../scripts/04_chatbot_server.py` | 向量檢索 + 圖譜多跳推理，附帶時間戳引用來源 | 跨章節跨實體關聯的精準問答能力 |
| 2:10–2:30 | 第 5 幕：評估指標分析 | `./demo.sh 5` | `agent-.../scripts/05_evaluate_rag.py` | 忠實度 (Faithfulness) 與相關性 A/B 評測表 | 沒有評估指標的 RAG 只是玄學 |

---

## 🎬 開場故事：圖書館書架 vs 偵探紅線板

想像我們現在是偵探。有一宗複雜的案件，線索散落在各地。我們要找出『X 誰在背後』——但不只是找到答案，還要指出『我是怎麼推理的』。

**傳統方法（純向量搜尋）**：像一間圖書館。你問『何謂民主制度』，圖書館員按『相似度』排序，從『講民主、共和、投票票』的書架區快速拉出來。但缺點是什麼呢？他只給你『最相似的五本書』。真正回答你問題需要的東西——比如『民主是怎麼從古希臘演變到現代的』——可能散落在五本完全不同的角落，他給不出來。

**我們今天的方法（GraphRAG）**：同時用兩張表。

一張是『快速查詢表』（向量庫）：按主題相近排列，找『講到相似內容的段落』非常快。

一張是『紅線板』（知識圖譜）：密密麻麻的照片、線條、箭頭。『民主』這個中心詞，上面連著『古希臘』『法國大革命』『孟德斯鳩』『三權分立』。你問『民主是什麼』，快速表先給你五段『講民主的話』，然後紅線板說『等等，這五段涉及的人物還牽連到這個和那個』，一併拉進來。

**結果呢？**回答變得更有『文脈』，而且每一個說法都配一個時間戳：『第 3 分 47 秒時說的』『第 12 分 30 秒時說的』——讓你能點進去驗證。

這就是你要自己建出來的東西。

這個比喻會貫穿全課，先把對照表記在心裡：

| 圖書館書架 | 偵探紅線板 | GraphRAG 系統 |
|---|---|---|
| 書按主題相近排列，快速掃描 | 照片串聯起來的關係網 | 向量資料庫 + 知識圖譜 |
| 查詢快，但孤立 | 慢，但看到全貌 | 先快查，再擴展 |
| 「講到類似內容的段落」 | 「牽涉的相關概念」 | Multi-Query + RRF 融合 |
| 借出來的書上有頁碼 | 紅線板上的箭頭 | 時間戳引用 + 圖譜節點高亮 |

---

## 🔍 名詞卡（十八個術語的白話解釋）

### 1. GraphRAG（圖表加強的檢索增強生成）

> 白話：不只用「相似度」查資料，還用「概念關係」找相關的東西。
> 生活比喻：打電話查天氣，接線生不只說「今天 25°C」，還說「根據我們的記錄，類似天氣時通常會發生 X 和 Y」。

### 2. RAG（檢索增強生成）

> 白話：AI 不是只靠記憶回答，而是先從你的文件庫查相關的段落，再根據那些段落生成答案。
> 生活比喻：小孩做功課時，先翻書找相關章節，再根據書上的內容寫答案。

### 3. 向量資料庫（Chroma）

> 白話：把文字轉成「高維空間裡的點」——相似的意思會變成相近的點。用來快速找「意思接近」的段落。
> 生活比喻：一張色票，紅色群聚在一起、藍色群聚在一起，要找「類似的紅」時很快。

### 4. 嵌入（Embedding）

> 白話：把一句話、一個段落變成一串數字。Gemini 把「民主制度」變成 3072 個數字，意思相近的段落會得到相近的數字串。
> 生活比喻：把每個人用「身高、體重、膚色 RGB 值」描述，這樣你就能按「外觀相似度」排序了。

### 5. 知識圖譜（Neo4j）

> 白話：把概念和概念之間的關係畫成網狀圖。「馬克思─創立─共產主義，共產主義─批評者─亞當斯密」。
> 生活比喻：一張人脈圖：誰認識誰、誰跟誰有仇、誰跟誰是朋友。

### 6. 三元組（Entity─Relation─Entity）

> 白話：「主詞─動詞─受詞」的簡潔資訊單位。例：「牛頓─提出─萬有引力」「太陽─繞圈─銀河」。
> 生活比喻：新聞的最小單位：「某人做了什麼事」。

### 7. 實體（Entity）

> 白話：知識圖譜上的「點」——通常是概念、人物、事件。「民主」「孟德斯鳩」「法國大革命」都是實體。
> 生活比喻：人脈圖上的每一個人頭像。

### 8. 切塊（Chunking）

> 白話：把長文本分成「可吃的小塊」。不是隨意切，而是在完整語意段結束的地方切。YouTube 的 2 秒碎片要先聚合成一分鐘再切。
> 生活比喻：把一本書分章節，章節內再分段落，而不是隨意撕頁。

### 9. Multi-Query（多視角改寫）

> 白話：同一個問題，AI 自動改寫成術語版、白話版、背景版三個問法，分別查詢。解決「使用者說『檢查點機制』、文件說『狀態保存』」的詞彙不搭問題。
> 生活比喻：老師同一個數學題目，用「代數」「幾何」「應用情境」三種講法問，確保沒人會因為詞彙理解力卡住。

### 10. RRF 融合（Reciprocal Rank Fusion）

> 白話：三路檢索各有排名，現在要合併結果。不看分數，只看排名，用公式 1/(k+rank) 算綜合得分。
> 生活比喻：三個評審各給十大名單，要找大家都推薦的——計算「被推薦的次數和名次」。

### 11. 圖譜擴展（Graph Expansion）

> 白話：查詢回來五個段落，馬上反查「這五個段落涉及的實體的一階鄰居」，全部塞進 context。
> 生活比喻：我要買手機，評測文推薦了 5 支。但我不只讀這 5 支的內容，還順便看「這 5 支手機常被人跟 X 手機比較」的資訊。

### 12. LLM-as-Judge（用 LLM 當裁判）

> 白話：不是人類評分，而是用一支 AI（通常比受測 AI 更強）來評分「兩個答案誰更好」。加盲評（隨機換位）防止「我總是選第一個」的偏誤。
> 生活比喻：用一位資深老師（第三方、不偏心）評分兩份作業，而且不告訴老師哪份是誰寫的。

### 13. 盲評與位置偏誤（Blind Evaluation & Position Bias）

> 白話：評分時不知道「這是新方法還是舊方法」、不知道「這是第一個選項還是第二個」。否則裁判會下意識偏向第一個或喜歡的那個。
> 生活比喻：品酒師品酒時不看酒的標籤，不然會被「貴酒一定好喝」的心理暗示影響。

### 14. 冪等（Idempotent）

> 白話：同一個動作重跑 100 次，結果都一樣，不會累積重複。像電梯的「停樓層」按鈕：多按不會多來幾台電梯。
> 生活比喻：銀行轉帳。你點「轉帳」，系統確認已轉帳，即使網路不穩重新點一次，也不會轉兩次錢。

### 15. Skill / MCP（Model Context Protocol）

> 白話：Skill 是「給 AI 用的腳本」，MCP 是「讓 AI 能呼叫外部工具」的協議。有 MCP 時，AI 可以自己去查 Neo4j、自己去搜文件。
> 生活比喻：沒有 MCP：AI 像被禁足的小孩，只能根據你口頭描述猜。有 MCP：AI 像有輪子的小孩，能自己去圖書館、自己去看現場。

### 16. FastAPI + React 力導向圖

> 白話：FastAPI 是「提供數據的後端」，React 力導向圖是「畫出會互相推斥又互相吸引的動畫網狀圖」的前端。
> 生活比喻：廚房（後端）烹飪，前廳（前端）用高級擺盤展示。

### 17. Neo4j Aura

> 白話：Neo4j 官方的雲端代管版。你不用裝 Docker，註冊完雲端幫你開一台圖資料庫，改一個連線網址（`neo4j+s://`）就能用。免費層有節點/關係上限，閒置太久會被暫停。
> 生活比喻：地端 Docker 是「自己家的廚房」，Aura 是「租的共享廚房」——不用買設備就能開火，但要遵守營業時間，太久不去攤位會被收走。

### 18. Cypher 與 MERGE

> 白話：Cypher 是 Neo4j 的查詢語言，用「畫圖」的方式寫查詢：`(a)-[r]->(b)` 就是「a 指向 b」。`MERGE` 是它最重要的動詞：「有就拿來用，沒有才建」——所以重跑一百次也不會多出重複節點（這就是冪等）。
> 生活比喻：`MERGE` 像通訊錄的「加聯絡人」：已經有這個人就直接開他的名片，沒有才新建，永遠不會出現十張重複的名片。

---

## Step 0：環境準備與起飛前檢查

### 0-1 裝套件（uv 介紹）

Python 的套件管理有個古老的工具叫 pip，但它慢、容易搞壞環境。我們用 uv，一個新工具，快 10 倍，而且 AI 代理用它時每次 shell 都獨立處理，不怕環境污染。

```bash
cd project-14-graphrag-chatbot
uv sync
```

### 0-2 拿 Gemini 金鑰 + 環境變數

Google 有一個免費服務叫 AI Studio，讓你直接申請用 Gemini 模型。去 aistudio.google.com 點『Get API key』，一個金鑰就夠跑完全流程。金鑰怎麼放？有兩種方式：

(a) export 到 `~/.zshenv`（**不是 `~/.zshrc`**，非互動 shell 只讀前者）或 (b) `.env` 檔但每條指令加 `--env-file`。

```bash
export GOOGLE_API_KEY="AIza..."
export NEO4J_PASSWORD="你自訂的"
```

**為什麼要特別強調 zshenv？**因為 AI 代理每次執行指令都開新的非互動 shell。.zshrc 只在你手工打字的互動模式讀。中途漏一次就會『明明設了卻說沒設』。

### 0-3 起 Neo4j：先選路線（地端 Docker vs 雲端 Aura）

Neo4j 是一個圖資料庫。你有兩條路可以把它跑起來，**先看這張表再動手**：

| | 🟢 地端 Docker（首選） | ☁️ Neo4j Aura Free（替代） |
|---|---|---|
| **成本** | 免費，無節點/關係上限 | 免費層：20 萬節點、40 萬關係、每帳號 1 個 instance（[官方 FAQ](https://neo4j.com/cloud/platform/aura-graph-database/faq/)） |
| **資料隱私** | 資料不出你的機器 | 語料會上傳到 Neo4j 的雲端 |
| **速度** | localhost 直連，最快 | 每個查詢都走網路，有延遲 |
| **斷網可用** | 完全離線可用 | 沒網路就全掛 |
| **清庫重來的自由** | `docker rm -f` 再 run 一次，10 秒重生 | 只能 `MATCH (n) DETACH DELETE n` 清資料，instance 砍了要重建重抄密碼 |
| **課堂投影可靠性** | 教室網路再爛也不影響 | 依賴外網；閒置 72 小時會被暫停，上課前要先 resume |

**裁決很明確：有 Docker 就用地端。** 資料不出機器、免費無上限、翻車了 `docker rm` 就能砍掉重練、教室網路不穩也不怕。Aura 是給「公司電腦鎖權限裝不了 Docker」或「機器太弱跑不動容器」的同學的逃生門——不是升級版，是替代路線。

> 程式碼兩條路線通吃：repo 讀 `NEO4J_URI`（預設 `bolt://localhost:7687`）、`NEO4J_USER`（預設 `neo4j`）、`NEO4J_PASSWORD`（必填）。走地端只要設密碼；走 Aura 多 export 一個 `NEO4J_URI` 就好，**腳本一行都不用改**。

#### 0-3A 地端 Docker 路線（首選）

一行啟動。要等 20 秒才連得上——這 20 秒的原因我等下會講。

```bash
docker run -d --name neo4j-teach -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD neo4j:5 && sleep 25
```

（`-p 7474/-p 7687` 和 `NEO4J_AUTH=使用者/密碼` 就是 [Neo4j Docker 官方文件](https://neo4j.com/docs/operations-manual/current/docker/introduction/)的現行寫法。注意：官方要求密碼至少 8 個字元，太短容器會起不來。）

#### 0-3B Aura 雲端路線（裝不了 Docker 才走）

1. **註冊**：到 [console.neo4j.io](https://console.neo4j.io) 用 Google 帳號或 email 註冊，免信用卡。
2. **建 instance**：選 **AuraDB Free**，按 Create。每個帳號只能有 1 個 Free instance（[官方文件](https://neo4j.com/docs/aura/getting-started/create-instance/)）。
3. **抄密碼（最重要的一步）**：建立當下畫面會顯示一次自動產生的密碼，**點 Download 或複製存好——關掉就再也拿不回來**，只能 reset。
4. **抄連線 URI**：instance 卡片上有一串 `neo4j+s://xxxxxxxx.databases.neo4j.io`。注意 scheme 是 **`neo4j+s://`**（TLS 加密，[官方連線文件](https://neo4j.com/docs/aura/getting-started/connect-instance/)），不是地端用的 `bolt://`。
5. **設環境變數**（一樣寫進 `~/.zshenv`）：

```bash
export NEO4J_URI="neo4j+s://xxxxxxxx.databases.neo4j.io"   # 換成你的
export NEO4J_PASSWORD="Aura 給你的密碼"
# NEO4J_USER 不用設，預設就是 neo4j
```

Aura 的兩個脾氣要先知道：**閒置 72 小時會自動暫停**（上課前記得到 console 按 Play resume），**暫停超過 30 天 instance 會被刪除、資料全失**（[官方 instance actions 文件](https://neo4j.com/docs/aura/managing-instances/instance-actions/)）。額度與政策以官網當日顯示為準。

#### 0-3C 兩條路線在這裡會合

不管走哪條，都用同一個指令驗證——`check_setup.py` 拿同一組環境變數連線，全綠就代表你的路線通了：

```bash
uv run python scripts/check_setup.py
```

✅ **預期看到**：最後一行 `ALL CHECKS PASSED — 可以開始 Phase 1`。腳本會檢四類東西：
1. Python 套件齊全
2. 環境變數有值（支援 `GOOGLE_API_KEY` 和 `GEMINI_API_KEY` 兩個名字）
3. Gemini 模型真的能用（實打 API 確認）
4. Neo4j 連線正常

🧯 **卡住的話**：
- `ModuleNotFoundError` → 沒跑 `uv sync`
- 金鑰報缺 → 確認寫進 `~/.zshenv`（在 Terminal 重開或 source 一下）；或檢查是否用了 (b) `.env` 方案但沒帶 `--env-file`
- Gemini 404 → 金鑰失效或用完免費額度；或模型改名了（腳本會直接印可用清單，`export GEMINI_MODEL=<清單裡的>` 即可）
- Neo4j 連線失敗（地端）→ 等 20 秒再試；或 docker 沒啟動，檢查 `docker ps`
- Neo4j 連線失敗（Aura）→ 三查：URI 是不是 `neo4j+s://` 開頭（用 `bolt://` 連 Aura 必失敗）；instance 是不是閒置被暫停了（console 按 Play）；公司防火牆有沒有擋 7687 埠（換手機熱點試一次就知道）

---

## Step 1：多來源統一入口（Phase 1 來源擷取）

現在進到第一個『各司其職』的示範。四種來源——YouTube、PDF、DOCX、網頁——都會被一支腳本吃進去、正規化成同一個 source.json。下游完全不用改。怎麼做到？答案就在選項設計上。

講「免費 vs 付費」決策：

| 來源 | 免費（預設） | 付費（可選） | 何時值得 |
|---|---|---|---|
| YouTube | yt-dlp（人工 CC → 自動字幕 → whisper fallback） | ——無 | 不需要 |
| PDF | pymupdf | LlamaParse | 掃描件、複雜表格 |
| 網頁 | trafilatura | Tavily | JS 渲染頁、反爬 |
| DOCX | python-docx | ——無 | 邊際效益為零 |

> ❓ **想一想**：為什麼沒有『YouTube 的付費版』？因為什麼工作是免費地端就能做，不值得花錢的？
>
> **答案**：yt-dlp 下載字幕一分鐘就搞定，沒有額外價值，花錢沒意義。即使完全沒字幕，用 whisper 轉錄也只是等 5 分鐘。

### 1-1 課前預抓 source.json（最重要）

如果多人同時抓同一支 YouTube 影片，YouTube 的伺服器會以為你在攻擊，直接返回『429 Too Many Requests』。課前預先抓好這個 JSON 檔會很穩定。如果多人同時做實驗，建議先一個人抓一遍 source.json，再分給大家用。

自己跑一遍：
```bash
uv run python scripts/00_ingest_source.py "https://youtu.be/..." --out source.json
```

課前發放預抓的 source.json 給大家。

✅ **預期看到**：
```
[✓] youtube 來源 60 段已存至 source.json
```

並能用這行驗證：
```bash
uv run python -c "import json; d=json.load(open('source.json')); print(d['source_type'], len(d['segments']))"
# 印出：youtube 60
```

### 1-2 打開 source.json 講三件事

注意 source.json 的結構。每一段有四個欄位：

```json
{
  "source_type": "youtube",
  "segments": [
    {
      "text": "今天我想講機器學習的……",
      "start": 12,
      "duration": 3,
      "ref": "https://youtu.be/xxx?t=12"
    }
  ]
}
```

**三件重點**：

1. **source_type**：下游的腳本會用這個自動決定「我該怎麼處理」——YouTube 要聚合時間窗、PDF 已經聚合過。同一份程式碼、不同邏輯。
2. **ref**：『引用必須可回溯』。每一段都帶著「出自第幾秒」的資訊，回答時點了能直接跳。
3. **start**：一個坑點。這個欄位在 YouTube 是秒數、在 PDF 是頁碼。等等講到圖譜擴展時會看到為什麼要小心。

🧯 **卡住的話**：
- 字幕是英文 → 正常，這支影片沒有中文字幕。AI 也能理解英文。
- 全是自動字幕、質量糟糕 → 正常，YouTube 自動字幕就是這樣。但如果完全沒字幕，`check_setup` 會提示 whisper 指令。

---

## Step 2：向量化入庫（Phase 2 切塊 + 嵌入）

source.json 只是『原始素材』。要拿來查詢，得先變成向量。但直接嵌入 2 秒一個碎片品質很差——想像把一本書斯成 2 秒的紙條，每一張都嵌入一個向量。這樣沒有意義。所以我們先聚合。

關鍵概念：
- **先聚後切**：YouTube 聚合成 ~60 秒自然段、PDF 已聚合（≥200 字）
- **metadata 完整**：chunk_index 讓 Phase 3 反查、url_at_time 讓引用可點
- **冪等**：重跑會刪掉同 video_id 的舊資料，不會累積重複

```bash
uv run python scripts/02_ingest_vectordb.py source.json --persist ./chroma_db
```

✅ **預期看到**：
```
[✓] 已寫入 collection='yt_rag' at ./chroma_db
```

驗證（原樣複製，效果等價）：
```bash
uv run python -c "
import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
emb = GoogleGenerativeAIEmbeddings(model=os.environ.get('GEMINI_EMBED_MODEL','gemini-embedding-001'))
db = Chroma(collection_name='yt_rag', embedding_function=emb, persist_directory='./chroma_db')
print('chunks 總數:', db._collection.count())
print('第一筆 metadata:', db.get(limit=1)['metadatas'][0] if db.get(limit=1)['metadatas'] else '空')
"
```

如果 chunk 數是『空』，就是路徑對不上。Chroma 是存在本地的 SQLite，檔案位置要一致。

🧯 **卡住的話**：
- metadata 是空 → 檢查 persist 路徑一致性（`./chroma_db` vs `./chroma_db`）
- dimension mismatch → 換過嵌入模型沒重建庫，`rm -rf ./chroma_db` 重來

---

## Step 3：知識圖譜抽取（Phase 3 三元組 → Neo4j）

現在到最視覺化的一步。我們用 Gemini 看每一個段落，問『這段落講了什麼三元組』。比如『馬克思提出了共產主義思想』，抽成『馬克思─提出─共產主義』。每個 chunk 可能有 5–10 個三元組，全部塞進 Neo4j。接下來打開瀏覽器，你會親眼看到『文字變成了網』的一刻。

```bash
uv run python scripts/03_build_graph.py source.json
```

預期輸出每個 chunk 一行（見 WALKTHROUGH.md Step 4），結尾：
```
[✓] 圖譜完成: 213 條關係
```

跑的時候讀下面三小節，把「文字怎麼變成網」的三個環節看清楚——抽取、寫入、檢索。全部對照 `scripts/03_build_graph.py` 和 `scripts/04_chatbot_server.py` 的真實程式碼，不是示意圖。

### 3-1 三元組是怎麼從 chunk 抽出來的

打開 `scripts/03_build_graph.py`，最上面就是整個抽取的靈魂——`EXTRACT_PROMPT`：

```python
EXTRACT_PROMPT = """你是知識圖譜抽取器。從以下影片逐字稿片段抽取三元組。
規則:
- entity 用正式名稱（如 "LangGraph"、"檢查點機制"），同義詞正規化為同一名稱
- relation 用簡短動詞片語（如 "包含"、"用於"、"解決"）
- 只抽取片段中明確陳述的關係，不要腦補
- 最多 8 個三元組
- 嚴格只輸出 JSON，不要 markdown 圍欄，格式:
{"triples": [{"subject": "...", "relation": "...", "object": "..."}]}

片段:
"""
```

五條規則各有存在的理由，一條一條看：

1. **「正式名稱 + 同義詞正規化」**——這是圖譜品質的第一道防線。同一個概念如果一下叫「LLM」一下叫「大型語言模型」，圖上就會裂成兩個節點，後面的圖譜擴展就接不起來。（它防不住 100%，等下 3-5 會看到漏網之魚——那是故意留給你的作業。）
2. **「簡短動詞片語」**——關係名太長會讓圖上的邊標籤糊成一團，也讓後續查詢難以聚合。
3. **「不要腦補」**——LLM 最愛把自己的常識混進來。抽取器只准搬運原文明確說過的關係，這是「引用可回溯」在圖譜層的版本。
4. **「最多 8 個」**——限制產出、控制成本，也逼模型挑重要的講。
5. **「嚴格只輸出 JSON」**——但 LLM 不一定聽話。所以 `extract_triples()` 裡有兩層防禦：先用 `removeprefix`/`removesuffix` 剝掉模型愛加的 markdown 圍欄，再用 try/except 接 `json.JSONDecodeError`——**解析失敗就印一行警告、跳過這個 chunk，絕不讓一個 chunk 炸掉整條管線**。腳本還在這裡留了一句話給你：「這就是為什麼正式系統要用 structured output」。

另外注意每個三元組會被掛上 `chunk_id`（`t["chunk_id"] = chunk["chunk_id"]`）——這一行就是圖譜和向量庫能「精確對齊」的祕密，Step 4 的圖譜擴展全靠它。

> ❓ **想一想**：去重（同一個實體在 10 個 chunk 出現，只留一個節點）是在 Python 裡做的嗎？在 `03_build_graph.py` 裡找找看有沒有去重的程式碼。
>
> **答案**：沒有——Python 這邊完全不去重，去重直接交給 Neo4j 的 `MERGE`。往下看。

### 3-2 寫進 Neo4j 的 Cypher 長什麼樣（MERGE = 冪等）

`write_neo4j()` 做三件事，順序有講究。

**第一件：先清掉同一支影片的舊圖**（冪等的關鍵）：

```cypher
MATCH (c:Chunk {video_id: $vid}) DETACH DELETE c
```

重跑腳本 100 次，圖都長一樣，不會累積重複——因為每次都先把「這支影片」的舊 Chunk 連根拔掉（`DETACH DELETE` = 連同掛在上面的關係一起刪）。注意它只刪這支影片的，別支影片的圖不受波及——這就是 EVALUATION.md 裡「cross-source 汙染」修掉之後的樣子。

**第二件：建 Video 和 Chunk 節點**，用 `PART_OF` 掛回影片。

**第三件：每個三元組跑這段**（真實程式碼，一字不差）：

```cypher
MERGE (a:Entity {name: $subj})
MERGE (b:Entity {name: $obj})
MERGE (a)-[r:REL {type: $rel}]->(b)
WITH a, b MATCH (ck:Chunk {id: $cid})
MERGE (a)-[:MENTIONED_IN]->(ck)
MERGE (b)-[:MENTIONED_IN]->(ck)
```

逐行拆：

- **`MERGE` 不是 `CREATE`**。`MERGE` 的語意是「有就拿來用，沒有才建」。「馬克思」在 30 個 chunk 出現，`CREATE` 會做出 30 個馬克思節點；`MERGE` 只有一個——**實體合併就發生在這一行**，比對的 key 就是 `name`（寫入前有 `.strip()` 掉頭尾空白）。這也是為什麼 3-1 的 prompt 拚命要求「正式名稱」：`MERGE` 只認完全相同的字串。
- **`MENTIONED_IN` 是 GraphRAG 的命脈**。實體不只連實體，還連回它出現的 Chunk。圖譜負責「找到相關概念」，Chunk 負責「提供原文證據（帶時間戳）」——少了這條邊，圖譜再漂亮也接不回原文。
- **關係為什麼是 `[:REL {type: "提出"}]` 而不是 `[:提出]`**？Cypher 的關係型別不能直接用變數塞，要動態型別得裝 APOC 外掛。教學版把關係名存成屬性 `type`，通用又免外掛——這是一個「上課環境的可攜性 > 查詢的優雅度」的取捨，原始碼註解裡就寫著。

所以整個 Step 3 的資料模型是：

```
(Video) <-[:PART_OF]- (Chunk) <-[:MENTIONED_IN]- (Entity) -[:REL {type}]-> (Entity)
```

### 3-3 檢索時圖譜擴展跑的是什麼查詢

快轉看一眼 Step 4 會用到的查詢（`04_chatbot_server.py` 的 `graph_expand()`），你就明白剛剛建的邊是怎麼被用的：

```cypher
MATCH (e:Entity)-[:MENTIONED_IN]->(ck:Chunk)
WHERE ck.id IN $ids
   OR (ck.video_id IN $vids AND ck.start IN $starts)
MATCH (e)-[r:REL]-(nb:Entity)
RETURN DISTINCT e.name AS a, r.type AS rel, nb.name AS b LIMIT 30
```

讀法：向量檢索命中了幾個 chunk（`$ids`）→ 反查「這些 chunk 裡提過哪些實體」（走 `MENTIONED_IN` 逆向）→ 再往外跳一步拿「這些實體的一階鄰居」（`(e)-[r:REL]-(nb)`，注意沒有箭頭方向，兩個方向都要）→ 最多 30 條餵進 context。這就是名詞卡裡「圖譜擴展」的完整實作——兩個 `MATCH`，一次多跳。

（`WHERE` 裡那條 `OR` 是 fallback：chunk_id 對不上時改用 `video_id + start` 比對。為什麼一定要連 `video_id` 一起限定？因為 `start` 在 YouTube 是秒、在 PDF 是頁碼，光比 start 會讓「影片第 1 秒」撞上「PDF 第 1 頁」，撈進別份文件的實體——Step 1 埋的那個坑，在這裡爆。）

前端點節點展開子圖用的是另一條（`/graph/{name}`），邏輯同款：從一個實體出發拿一階鄰居 + 出處。

### 3-4 投影時刻：Neo4j 瀏覽器視覺化

打開 http://localhost:7474，用帳號 neo4j 和你的密碼登入。（走 Aura 路線的同學：在 [console.neo4j.io](https://console.neo4j.io) 的 instance 卡片按 **Query**/**Open**，下面每一條 Cypher 都一樣能貼。）

以下 5 條 Cypher 按順序貼，每條講一件事：

**① 看全圖**

```cypher
MATCH (n) RETURN n LIMIT 100
```

你會看到：一張會動的網——圓是節點（Entity / Chunk / Video），線是關係。這就是『偵探紅線板』本人。這說明什麼：文字真的變成結構了，接下來每一條查詢都在這張網上走路。

**② 數節點和關係（圖的體檢報告）**

```cypher
MATCH (n) RETURN labels(n)[0] AS 類型, count(*) AS 數量
```

```cypher
MATCH ()-[r]->() RETURN type(r) AS 關係, count(*) AS 數量
```

你會看到：一張小表——Entity 幾個、Chunk 幾個、Video 1 個；REL、MENTIONED_IN、PART_OF 各幾條。這說明什麼：這是驗收清單的數字來源。Entity = 0 代表抽取全掛，REL 遠少於 Entity 代表圖是一盤散沙。

**③ 找 degree 最高的實體（誰是主角）**

```cypher
MATCH (e:Entity)-[r:REL]-()
RETURN e.name AS 實體, count(r) AS 連接數
ORDER BY 連接數 DESC LIMIT 10
```

你會看到：一張排行榜，第一名通常就是影片的核心主題。這說明什麼：不用看影片，光看圖的拓撲就能猜出「這支影片在講什麼」——連接數就是重要性的代理指標。

**④ 看某實體的兩跳鄰居（多跳推理的手動版）**

```cypher
MATCH p = (e:Entity {name: "把③的第一名貼進來"})-[:REL*1..2]-(nb:Entity)
RETURN p LIMIT 50
```

你會看到：以那個實體為中心炸開的一朵花——第一圈是直接相關的概念，第二圈是「相關的相關」。這說明什麼：`*1..2` 就是「跳 1 到 2 步」，這是純向量檢索永遠做不到的事——向量只會找「講法相似」，不會找「隔了一層的關聯」。GraphRAG 的差異化價值就在這一朵花裡。

**⑤ 從實體走回原文證據（引用可回溯的圖譜版）**

```cypher
MATCH (e:Entity {name: "同上"})-[:MENTIONED_IN]->(ck:Chunk)
RETURN e.name AS 實體, ck.start AS 秒數, ck.url_at_time AS 可點網址
```

你會看到：這個概念在影片裡每一次出現的秒數和可點連結。這說明什麼：圖譜不是脫離原文的抽象畫——每個節點都拉得回「影片第幾秒說的」。這條 `MENTIONED_IN` 邊就是 3-2 寫入的，也是 Step 4 時間戳引用的源頭。

看 5 分鐘，想想這個問題：

> ❓ **想一想**：這個圖上，誰被連接最多？（就是中心詞。）這代表什麼意思？
>
> **答案**：這個概念在影片裡最常被提及、涉及最多其他東西。用③的查詢可以直接驗證你的目測。

#### 🎤 講師提示：圖螢幕怎麼投影最壯觀

- **先跑①再講話**。力導向布局需要 3–5 秒「自己長開」，這段開花動畫就是全課最「哇」的瞬間——別浪費在你低頭敲鍵盤的時候。投影前先深呼吸，貼上、按執行、退後一步。
- **調暗色主題 + 全螢幕**。Neo4j Browser 右下角齒輪可切深色背景，投影機上深底亮點的對比遠勝白底；按 Esc 進全螢幕藏掉側欄。
- **LIMIT 是效果旋鈕**。節點太多會糊成毛球，太少不壯觀。100 是好起點；如果你的圖很密，降到 50；很稀就升到 200。
- **點一個節點再講②③**。單擊節點會高亮它的鄰居——先讓學生「看見」degree，再用③的排行榜印證，比直接丟數字有感十倍。
- **順序就是劇本**：①哇（全圖）→ ②多少（體檢）→ ③誰重要（排行）→ ④怎麼連（兩跳開花）→ ⑤回原文（時間戳）。從震撼到證據，五條查詢就是一段完整的敘事。

### 3-5 同義詞的故意不處理

你會發現『大型語言模型』和『大型语言模型』變成兩個節點——前面是繁體、後面是簡體。這叫『同義詞未合併』。有人會想『為什麼不直接改 prompt 讓它合併』？答案是：我故意留著。為什麼？因為這是最好的教學素材。回頭看 prompt，加一條正規化規則，重跑，然後看圖變了——這個『自己迭代』的過程，比直接給你完美圖譜更值得。

✅ **預期看到**：Neo4j 圖視覺化，Entity 數 > 0、REL 關係數 > 0，圖看起來有一定的「連結密度」（不是全是孤立點）。

🧯 **卡住的話**：
- Entity = 0 → 抽取全失敗。檢查 GOOGLE_API_KEY 有效、免費額度（Gemini 免費層每分鐘有 req 上限）
- 連線失敗 → Neo4j 還沒起來或密碼錯，回 Step 0 重檢
- 全是孤島（每個三元組是獨立的三個節點）→ 抽取 prompt 缺同義詞正規化，但功能上沒錯，可以先往下走

---

## Step 4+5：強 RAG 後端 + 三個 API（Phase 4 檢索擴展 + Phase 5 服務化）

現在來看『圖書館快速查詢 + 紅線板擴展』的完整流程。你問一個問題，後端要做四件事：

講解強 RAG 四步（簡要版，不要展示程式碼內部）：

1. **Multi-Query**：一個問題 → 術語版、白話版、背景版三個檢索視角
2. **RRF 融合**：三路檢索結果按排名（不按分數）融合
3. **圖譜擴展**：撈到的 chunks 的相關實體鄰居一起帶進來
4. **防脆弱**：Multi-Query 失敗時退回原問題（加強元件不能讓系統變脆）

```bash
cp scripts/04_chatbot_server.py chatbot_server.py
uv run uvicorn chatbot_server:app --reload --port 8000
```

為什麼要 cp 一遍？因為 Python 模組名不能數字開頭。一行 cp 搞定。接著 uvicorn 啟動 server。

### 4-1 現場打 API 驗證

保持 server 運行，另開終端機執行：

```bash
curl -s localhost:8000/graph | python3 -c "import json,sys; d=json.load(sys.stdin); print('圖節點:', len(d['nodes']), '邊:', len(d['links']))"
```

```bash
curl -s -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"question":"這個內容主要在講什麼"}' | python3 -c "import json,sys; d=json.load(sys.stdin); print('answer 前80字:', d['answer'][:80]); print('sources 數:', len(d['sources']))"
```

✅ **預期看到**：
- 第一條：節點和邊的數字都 > 0
- 第二條：answer 是非空文字（不是「我不知道」）、sources ≥ 1（帶時間戳的引用）

投影或展示 `/chat` 的完整返回，看看時間戳引用：
```json
{
  "answer": "...",
  "sources": [
    {"timestamp": 123, "url": "https://youtu.be/xxx?t=123", "text": "..."}
  ],
  "graph_nodes": [...]
}
```

看，每一個引用都帶時間戳和可點的網址。『最容易被信任的不是答案本身，是我可以點過去自己確認』。

🧯 **卡住的話**：
- Connection refused → server 沒起或埠被佔，改埠 `--port 8010`
- answer 說「我不知道」→ 正常（代表誠實），換一個更相關的問題重試
- sources 或 graph_nodes 是空 → 向量檢索有回，但圖譜擴展沒撈到。回 Step 3 檢查 Entity 數

---

## Step 4.5：方法驗證與 A/B 盲評（Phase 4.5 這是全課方法論核心）

現在到最重要的一步——『用數據證明我們加的東西有用』。我們加了三件花俏的東西：Multi-Query、RRF、圖譜擴展。但沒有數據就是空話。要跑一個盲評，對比『簡單的向量 RAG』和『複雜的強 RAG』。

### 4.5-1 建評估集（先於一切）

```bash
uv run python scripts/05_evaluate_rag.py --generate source.json --n 10
```

腳本會自動出 10 題。但出完之後要自己逐題看一遍，問『這題合理嗎』『能從影片答到嗎』。評估集品質決定整個結論的可信度。爛題測出來的勝利沒有意義。

打開 `eval_set.json` 逐題檢查——為什麼某些題很好、某些題可能要刪掉。

### 4.5-2 A/B 盲評

```bash
uv run python scripts/05_evaluate_rag.py --run eval_set.json --api http://localhost:8000
```

這會跑 10 題 × 2 個方法 = 20 次檢索、10 次 judge 評分。預期 3–5 分鐘。

預期結尾：
```
===== 勝負 =====
{
  "baseline": {"faithfulness": 3.8, "completeness": 3.2},
  "strong_rag": {"faithfulness": 4.3, "completeness": 4.1},
  "wins": {"baseline": 2, "strong_rag": 7, "tie": 1}
}
```

看這個數字。強 RAG 贏了 7 題、平了 1 題、輸了 2 題。這就是用『數據』而不是『我覺得』在講話。

### 4.5-3 誠實條款

但要講誠實的部分。我們的 judge 和受測 pipeline 是同一支模型（都是 Gemini Flash）。這省錢，但代表 judge 沒有比受測系統更強的判斷力。這個 A/B 結果只能當『方向性訊號』。要升級結論的強度，就得用更強的 judge 模型。無論如何，『誠實地說明自己方法的邊界』比『宣稱完美無缺』更值錢。

> ❓ **想一想**：為什麼一定要『盲評』？為什麼 judge 要不知道『這是新方法還是舊方法』？
>
> **答案**：否則 judge 會有心理暗示（「新的一定好」）、或習慣性選第一個。

✅ **預期看到**：eval_report.json + 勝負統計清楚呈現。

🧯 **卡住的話**：
- 強 RAG 沒贏 → 不是錯誤，是重要發現。依序查：
  1. 語料太小嗎？（chunk 數 < 30 就別期待）
  2. 圖譜是空或孤島嗎？
  3. Multi-Query 改寫偏題嗎？
  
  三個都不是 → 如實回報「此語料上無顯著增量」，這個結論本身就有價值。

### 4.5-4 一定要親自試的一幕（候選 1）

看這份數據。我們加了三個花俏的東西，結果在真實語料上測試，確實比簡單方法好 7 比 2。

這不是因為『我覺得』，而是因為『機器評審這樣說』。而且評審過程是盲的。誰看，都是同樣的結論。這就是科學。不是『我設計的東西一定好』，而是『我用標準方式測，數據會說話』。

---

## Step 6：前端視覺化（Phase 6 三視圖同步）

現在到最後一步——讓剛剛的答案、圖譜、引用都在一個漂亮的畫面上動起來。左邊是對話，右邊是動畫圖譜，底部是時間軸。

```bash
npm create vite@latest frontend -- --template react
cd frontend && npm i react-force-graph-2d
```

把 `references/frontend-graph.md` 裡的完整 `App.jsx` 貼進 `src/App.jsx`：

```bash
npm run dev
```

瀏覽器開 http://localhost:5173。

### 6-1 一定要親自試的一幕（候選 2）

自己試試看：

1. 提問：「這個內容主要講什麼？」
2. **答案出現**，附可點的時間戳引用（如「3:47」「12:30」）
3. **右側圖譜節點同步變橘色**——相關的概念被高亮
4. **點其中一個節點**（如「Multi-Query」）
5. **鄰居子圖瞬間展開**——該概念的相關實體、關係全部浮出
6. **底部時間軸亮出琥珀色的柱子**——證據在影片的分布位置

三個視圖是同一次檢索的三種投影。對話說『答案是什麼』，圖譜說『牽涉哪些概念、怎麼連』，時間軸說『這些話出現在哪裡』。一個問題，三種角度看，每一個角度都可以互動。這就是『強 RAG 的全貌』。

✅ **預期看到**：
- 瀏覽器無 console 錯誤
- 提問後有節點變橘
- 點節點後圖上節點數增加

🧯 **卡住的話**：
- 圖是空白 → 後端沒起或 CORS 問題，看瀏覽器 DevTools
- 節點不變橘 → 問題沒打到後端，或後端 /chat 返回空的 graph_nodes
- 右半邊被切掉 → Canvas 沒給寬度，見 frontend-graph.md 坑 4

---

## 誠實的工程：EVALUATION.md 裡的故事

我要跟你講一個不太漂亮的故事。當初做這個 skill 時，用了假 LLM 替身測的，畫面看起來全綠。但真的接上 Gemini 金鑰，一跑程式直接炸。

EVALUATION.md 裡記了四個缺陷（已修）：

| 缺陷 | 症狀 | 教學意義 |
|---|---|---|
| `.content` 是 list | 六處 LLM 呼叫全部 AttributeError | 即使測試用假替身，也要真的打一遍真 API |
| 金鑰兩個名字 | check_setup 擋掉其實能用的金鑰 | 邊界條件要完整，不要假設「肯定只有一種名字」 |
| `.env` 不自動載 | 每條指令都要 `--env-file`，用戶超容易漏 | 放在文件裡當紅線，遠比寄希望於「用戶不會漏」便宜 |
| 埠 8000 常被佔 | 現場一啟動 server 就 connection refused | 預設要改埠，要帶 fallback 指令 |

這些不是『程式有 bug』的故事，而是『測試要夠真實』的故事。一開始偷懶用假的，結果真的 API 就爆。所以現在在 EVALUATION.md 裡把這些都寫著——不是『隱瞞問題』，而是『把發現過程透明化』。

### 選材的故事

第一次測的時候，用了一支 6 分鐘的影片。A/B 跑完，強 RAG 沒贏。一度想『是不是方法爛』。但查下去才發現——影片太短了。只產出 8 個 chunk，naive 的 top-5 就撈走 62% 的全部語料。兩邊 context 幾乎完全重疊，檢索策略根本沒有發揮空間。

後來換 20 分鐘的影片，就贏了。這就是為什麼 README 裡強調『選 20 分鐘以上的影片』。不是『我推薦』，是『實測的結論』。

---

## 驗收清單

- [ ] `uv run python scripts/check_setup.py` 全綠
- [ ] `source.json` 有 ≥ 30 個 segments（來自預抓或現場抓）
- [ ] Chroma collection 內 chunks 總數 > 0，metadata 含 chunk_index、url_at_time
- [ ] Neo4j 圖視覺化：Entity 與 REL 數都 > 0；圖看得出連結結構
- [ ] `/graph` 與 `/chat` API 都有回傳；answer 非空、sources ≥ 1
- [ ] eval_set.json 產出、答案人工檢查合理
- [ ] eval_report.json 產出、wins.strong_rag > wins.baseline（或等於時記錄原因）
- [ ] 前端瀏覽器開啟、提問後節點變橘、點節點後圖展開

## 常見坑排錯速查

| 症狀 | 最可能的原因 | 快速修法 |
|---|---|---|
| 「明明設了金鑰卻說沒設」 | 寫在 `~/.zshrc` 而非 `~/.zshenv` | `export` 寫進 `~/.zshenv`，或用 `.env` + `--env-file` |
| ModuleNotFoundError | 沒跑 `uv sync`，或不在 pyproject.toml 那層 | `uv sync` + `cd` 到有 pyproject.toml 的資料夾 |
| Gemini 404 / model not found | 模型改名或免費額度用完 | `uv run python scripts/check_setup.py` 看可用清單 |
| Neo4j 連線失敗（地端） | Docker 沒起、還沒起好、或密碼錯 | `docker ps` 看 neo4j-teach；等 20 秒後重試 |
| Aura 連線失敗：`Unable to retrieve routing information` 或 SSL 錯 | URI scheme 用錯：拿地端的 `bolt://` 去連 Aura | `NEO4J_URI` 改成 instance 卡片上的 `neo4j+s://xxxx.databases.neo4j.io` |
| Aura 昨天還能連、今天突然連不上 | 閒置 72 小時被自動暫停了 | 到 console.neo4j.io 按 Play resume（要等幾分鐘）；上課日早上先 resume |
| Aura 在公司/學校網路連不上、換家裡網路就好 | 防火牆擋了 7687 埠（Bolt 走這個埠） | 換手機熱點驗證；確定是防火牆就請 IT 開 7687，或改用地端 Docker |
| Aura 密碼忘了抄 | 建 instance 時的密碼只顯示一次 | console 裡對 instance 做 reset password，重新 export `NEO4J_PASSWORD` |
| 地端 Neo4j 容器一直起不來 | `NEO4J_AUTH` 的密碼少於 8 個字元 | 換至少 8 字元的密碼，`docker rm -f neo4j-teach` 後重跑 docker run |
| Chroma metadata 是空 | persist 路徑對不上 | 檢查指令的 `--persist ./chroma_db` 和驗證指令的 persist_directory 一致 |
| 圖是全孤島 | 三元組抽取有實體但沒連結 | 正常（早期階段），逐步迭代 prompt |
| 前端圖右半邊被切掉 | Canvas 沒給寬度 | 用 references/frontend-graph.md 的版本，已修坑 4 |
| 強 RAG 沒贏 naive | 語料太小（chunk < 30） | 換 20 分鐘以上的影片，或多灌幾份文件 |
| 埠 8000 被佔 | 機器上另一個程式用著 | 改埠 `--port 8010`，Phase 4.5 記得 `--api http://localhost:8010` |

## 帶走的三句話

如果整份專案只能記住三件事，就這三句：

1. **多層檢索各司其職，不是疊加**——向量資料庫快速找相似講法，知識圖譜找牽涉的概念，用 chunk_index 精確綁定。一個快但窄，一個慢但廣，一起用才威力大。

2. **引用可回溯比答案漂亮更值錢**——一個能點進去驗證的時間戳，讓接收者從「信你」變成「自己確認」。這就是為什麼前端的時間軸這麼重要。

3. **方法宣稱要有邊界與數據**——「最好」的意思是「在此評估集、已測候選、誠實限制內最好」。缺任何一個都只是意見。知道自己的證據有多強，比證據看起來多漂亮更重要。

---

## 課外讀物：進階路線

有時間或想深入理解，可以查看：

- **MCP 應用**：references/mcp-setup.md——讓 AI agent 自己查 Neo4j、自己調參
- **方法論完整版**：references/method-validation.md——如何建立 SOTA 對齐迴圈
- **付費路線決策**：SKILL.md Phase 0 的 API Key 總表——每個選擇的成本效益
- **來源支援**：SKILL.md Phase 1 的 fallback 設計——為什麼要有 whisper、為什麼 PDF 有兩條路線
- **效能調優**：EVALUATION.md 限制 5——為什麼現在是「一次一個」、升級路線是什麼

---

## 教學工具提示

1. **投影 Neo4j 時**：改背景色、隱藏工具欄，讓圖視覺效果最大化
2. **示範前端時**：關掉瀏覽器其他分頁，降低噪音
3. **時間不夠時**：Phase 4.5 可縮短（或課後補），前端可用預錄影片秀
4. **進度快時**：試著自己調 `EXTRACT_PROMPT` 的實體正規化規則，重跑 Phase 3、對比圖的改變
5. **進度慢時**：Phase 2–3 先看概念、看別人的成果圖，Phase 1 用預抓 source.json，重點放在「概念理解」而不是「敲指令」

---

## 最後一句話

這份教學的目標不是教你『怎麼敲指令把 RAG 跑起來』。敲指令很簡單，3 個月後會變。真正的目標是學『工程思維』——邊建邊驗、用數據講話、誠實地說明邊界。這個思維，比任何一個框架都值錢。回去之後，不只複製這些指令，而是複製『先測後吹』的態度。
