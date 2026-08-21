# GraphRAG 問答機器人：從影片到知識圖譜

> Cursor 課程 Project 14：丟一個 YouTube 連結／PDF／DOCX／網頁，建出一個會回答內容、會附時間戳引用、還會即時高亮知識圖譜的問答機器人。

一句話：**向量資料庫 + 知識圖譜，各司其職；引用必須可回溯；方法宣稱要有數據證明。**

## 專案規格

| | |
|---|---|
| **最終成果** | 左邊聊天、右邊知識圖譜的完整 RAG 問答應用。問一個問題 → 答案出現、附可點的時間戳引用 → 右側圖譜相關節點同步變橘色 → 點任一節點 → 鄰居子圖瞬間展開 → 底部時間軸亮出證據分布 |
| **技術棧** | Python 3.12 + uv、Gemini API（免費）、Chroma（向量資料庫）、Neo4j 5（知識圖譜）、FastAPI、React 力導向圖 |
| **預估時間** | 第一次完整跑約 60–90 分鐘（含環境）；之後 30 分鐘內 |
| **前置需求** | Docker Desktop、Node.js 18+、免費 Google AI Studio 金鑰（aistudio.google.com） |
| **來源支援** | YouTube（含無 CC 影片的字幕 fallback）、PDF（含掃描版）、DOCX、任意網頁 |

## 這個 App 做什麼

收一個資訊來源（影片 / 文件），建出三個互相同步的視圖：

1. **對話**：問「這個內容說了什麼」，得到一個認真的答案 + 時間戳引用（點了能直接跳到影片）
2. **圖譜**：同時出現相關的知識節點，拖動探索更多連結
3. **時間軸**：底部柱狀圖顯示「答案的證據分布在影片的哪些位置」

三個視圖是**同一次檢索的三種投影**：對話說「答案是什麼」，圖譜說「牽涉哪些概念、怎麼連」，時間軸說「這些話出現在哪裡」。

## 三層架構

```
資訊來源
  ↓ [Phase 1] 統一入口擷取（免費地端 + 付費雲端可選）
source.json （標準化格式，帶可回溯 ref：時間戳／頁碼／網址）
  ↓ [Phase 2] LangChain 切塊 + Gemini 嵌入
Chroma VectorDB （向量檢索：「講到類似主題的段落」）
  ↓ [Phase 3] Gemini 抽取三元組 Entity─REL─Entity
Neo4j 知識圖譜 （圖譜擴展：「相關的其他概念」）
  ↓ [Phase 4] 強 RAG（Multi-Query + RRF + 圖譜擴展）
  ↓ [Phase 5] FastAPI 後端 + React 前端
完整問答應用
  ↓ [Phase 4.5] 方法驗證（naive vs 強 RAG 的盲評）
證據報告 + decision record（「為什麼這個設計有效」）
```

**關鍵洞察**：VectorDB 和 GraphDB **不是二選一**。
- VectorDB 的工作：快速找出「講法相似」的語料段落
- GraphDB 的工作：把「同一概念在影片別處的其他講法」也帶進來
- 精確對齊：用 chunk_index 把兩者綁在一起，沒有 mismatch

## 三個值得偷走的設計

**1. 把必然會發生的失敗前移。**
Google 經常改模型名。我們不寫死模型名，反而在 Phase 0 直接**用你的金鑰真的問一次 Google 有哪些模型可用**，確認設定的模型在清單裡——把 Phase 3 的神秘 404，變成 Phase 0 的一行提示。

**2. 引用必須可回溯，而且要看得見。**
影片時間戳和 PDF 頁碼是同一件事的不同外衣。做 RAG 最容易被信任的不是答案本身，是「我可以點過去自己確認」。前端的時間軸就是把這件事變成畫面。

**3. 方法宣稱要有雙證據。**
Phase 4.5 做的是 naive 向量 RAG vs 強 RAG 的 LLM-as-judge 盲評（隨機換位防位置偏誤）。一個方法可以宣稱「目前最好」，若且唯若：與文獻對齐 + 在自己的評估集上數據不輸 + 每個被否決的候選都留有紀錄。缺任何一條都只是「我覺得不錯」。

## 這是什麼課程

**跑完能得到**：一個能用的 RAG 機器人。

**更重要的是學到**：
- 多層 RAG 架構如何組合（不是堆積）
- 邊建邊驗的工程心態（不是最後才 debug）
- 科學態度：方法宣稱要附數據、要寫誠實條款
- 技術取捨：免費 vs 付費、本地 vs 雲端、精度 vs 速度

## 知識圖譜的視覺化

整堂課最「哇」的一幕：Neo4j 的圖長出來時，同學親眼看到「文字變成了連結」。

```
原本（平面）：
  「政治經濟學」、「馬克思主義」、「勞動剝餘價值」
  
變成（圖）：
  政治經濟學─創立者─馬克思
             ├─ 核心概念 ─ 勞動剝餘價值 
             └─ 批評者 ─ 亞當斯密
  
(縮小到 Neo4j 網頁介面上實時動畫，投影在教室螢幕上)
```

## 掛給編輯器用

```bash
./install.sh                    # 裝到目前目錄的專案
./install.sh --global           # Claude Code / Codex 裝到使用者層
```

裝好之後，在 Claude Code / Cursor / Codex 裡講「我想拿這支影片做問答機器人」，就會自動觸發。

## 快速開始（完整步驟見 walkthrough.md）

```bash
cd project-14
uv sync

export GOOGLE_API_KEY="AIza..."           # 從 aistudio.google.com
export NEO4J_PASSWORD="你自訂的密碼"

docker run -d --name neo4j-teach -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD neo4j:5 && sleep 25

uv run python scripts/check_setup.py       # 沒全綠不要往下
```

全綠之後照 WALKTHROUGH.md 逐步建置。

## 核心教學重點

| 階段 | 重點 | 驗證方式 |
|---|---|---|
| Phase 0 | API key 管理：環境變數、金鑰輪換、模型名過期 | check_setup.py 全綠 |
| Phase 1 | 多來源統一入口：同一支腳本 4 種格式、cost vs quality | source.json 有 segments |
| Phase 2 | 語意單位設計：切塊前先聚合成完整句子 | Chroma metadata 齊全 |
| Phase 3 | 三元組抽取與去重：Entity 合併、圖譜價值展現 | Neo4j 圖視覺化長出來 |
| Phase 4 | 強 RAG 四件事：Multi-Query + RRF + 圖譜擴展 + graceful degradation | 答案同時帶時間戳+圖節點 |
| Phase 4.5 | **方法論**：文獻對齐 + 實測數據 + 誠實條款 | A/B 盲評有勝負分明的數據 |
| Phase 6 | 交互設計：三視圖同步、節點點擊展開、時間軸亮點 | 投影效果壯觀 |

## 誠實的限制

這個 repo 的完整評估報告在 EVALUATION.md 裡，記錄了：
- **已修的缺陷**：LangChain `.content` 是 list 的坑、Neo4j cross-source 汙染
- **刻意沒修的**：judge 與受測 pipeline 同級模型（成本考量）、無索引（教學規模夠）、效能「一次一個」（可讀性優先）
- **尚未驗證**：付費解析路線（LlamaParse / Tavily）、whisper fallback

> 知道自己的證據有多強，比證據看起來多漂亮更重要。

---

## 檔案結構

```
project-14/
├── README.md                      # 這份（規格卡）
├── walkthrough.md                 # 完整教學文件與步驟
├── scripts/
│   ├── 00_ingest_source.py       # 多來源統一入口
│   ├── 01_fetch_transcript.py    # YouTube 字幕提取（內含 fallback）
│   ├── 02_ingest_vectordb.py     # 切塊 + 嵌入 → Chroma
│   ├── 03_build_graph.py         # 三元組抽取 → Neo4j
│   ├── 04_chatbot_server.py      # FastAPI 強 RAG 後端
│   ├── 05_evaluate_rag.py        # A/B 評測 + decision record
│   └── check_setup.py            # 起飛前檢查（Phase 0 必跑）
├── references/
│   ├── mcp-setup.md              # Chroma / Neo4j / Langchain-docs MCP 設定
│   ├── frontend-graph.md         # React 完整程式碼 + 已知坑與修正
│   └── method-validation.md      # 評估迴圈的紀律與 decision record 範本
├── install.sh                    # Claude Code / Cursor / Codex 跨平台安裝
├── pyproject.toml                # uv 套件管理（Python 3.12）
└── SKILL.md                      # Agent 執行用（硬規則 7 條 + 流程編排）
```

## 帶走的三句話

1. **多層檢索不是堆積**——VectorDB 找相似講法，GraphDB 找概念連結，兩者各司其職，用 chunk_index 精確對齐。
2. **引用可回溯比答案漂亮更值錢**——一個能點進去驗證的時間戳，比十個沒來源的機智回答更有說服力。
3. **方法宣稱要有邊界與數據**——「最好」的意思是「在此語料、已測候選、誠實界限內最好」，缺任何一個都只是意見。

---

## 選材建議（會直接影響 Phase 4.5 的結論）

挑 **20 分鐘以上、資訊密度高**的影片，或一次灌好幾份文件。

語料太小（總 chunk < ~30）時，naive baseline 的 `k=5` 就撈走大半語料，強 RAG 再厲害也沒有發揮空間。實測：一支 6 分鐘影片只產出 8 個 chunk，A/B 有 6 題評分完全相同。

## 授權

MIT
