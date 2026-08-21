# 評估報告：這個 skill 能不能完美跑？

**評估日期**：2026-08-13 初評 / **2026-08-14 補上真實 Gemini 金鑰後全流程實跑**
**評估方式**：不是讀程式碼推論，是**真的把環境架起來跑**——
uv 裝好全部相依、docker 起真的 Neo4j 5、真的抓 YouTube 字幕、
真的呼叫 Gemini 嵌入與生成、真的寫進 Chroma 與 Neo4j、真的打每一個 API 端點、
真的跑完一輪 LLM-as-judge A/B 評測。

---

## 結論

**打包前的 `files/`：不能跑。** 一個必然阻斷的結構問題，加上四個會在課堂上咬人的缺陷。

**打包後的 `yt-graphrag-bot/`：Phase 0 → 4.5 全流程實跑通過。**

| 範圍 | 狀態 |
|---|---|
| Step 0 安裝（三平台） | ✅ 實測通過 |
| Step 1 環境檢查 | ✅ `ALL CHECKS PASSED` |
| Step 2 來源擷取（YouTube/PDF/DOCX/網頁） | ✅ 四條路線全部實跑通過 |
| Step 3 切塊入向量庫 | ✅ **真實 Gemini 嵌入**，3072 維，語意檢索正常 |
| Step 4 圖譜寫入 Neo4j | ✅ **真實 Gemini 抽取** 53 條關係／76 實體，零解析失敗 |
| Step 5 強 RAG + 三個 API | ✅ `/chat` 回出帶時間戳引用的實質答案 |
| Step 6 方法驗證 | ✅ 8 題評估集 + A/B 跑完並產出 `eval_report.json` |
| Step 7 前端 | ✅ 瀏覽器實跑：初始渲染 / 問答 / 節點高亮 / 點擊展開 全部通過（修掉 2 個版面問題後） |
| 付費路線（LlamaParse / Tavily）、whisper fallback | ⚠️ 未驗證（需額外金鑰／無字幕影片） |

**「完美跑」的誠實答案**：主線可以跑，**但要先修掉 4 個只有真打 API 才會現形的
問題**（都已修，見下方 §一）。剩下未驗證的只有前端與兩條付費支線。

### 但實跑也跑出一個「結果不如預期」的發現

Step 6 的 A/B：**強 RAG 沒有贏過 naive baseline**（1 勝 1 敗 6 平，
三個維度平均分完全相同）。查下去原因不是 bug，是**語料太小**——
測試影片只有 6 分鐘、產出 8 個 chunk，naive 的 `k=5` 一題就撈走 62% 的全部語料，
兩邊 context 幾乎完全重疊，檢索策略根本沒有發揮空間，分數還一起觸頂。

這件事有兩層意義：

1. **SKILL.md 的疑難排解漏了這個原因**（原本只列「圖譜空」和「Multi-Query 偏題」，
   但這次圖譜是滿的）。已補進 SKILL.md、WALKTHROUGH 與選材建議：
   **挑 20 分鐘以上的影片，或一次灌好幾份文件**。
2. **這反而是很好的教材**。同學會親眼看到：加了三個花俏元件，數據說「沒差」。
   方法宣稱是要被檢驗的，不是講出來就算數。

---

## 一、只有真打 Gemini 才現形的缺陷（2026-08-14 補測）

前一輪我用假 LLM 替身驗介面契約，看起來全綠。真接上金鑰後，三個問題立刻現形——
**這就是為什麼「未驗證」那一欄不能當成「大概沒事」**。

### 🔴 A. `.content` 在 LangChain 1.x 是 list，不是字串（阻斷級）

```
AttributeError: 'list' object has no attribute 'strip'
  raw = resp.content.strip().removeprefix("```json")...
```

`langchain-google-genai` 4.3.3 + LangChain 1.x 下，`.content` 回的是
**content blocks 的 list**（裡面還夾著 `signature` 之類的 metadata），
純文字要走 `.text`。

影響**全部 6 處 LLM 呼叫**——Phase 3 抽取、Phase 4 的 Multi-Query 與生成、
Phase 4.5 的出題／baseline／judge。也就是說：**整個 LLM 層原本一行都跑不動。**

**修正**：6 處 `.content` → `.text`（已實證 `.text` 是真 `str`，
`isinstance(x, str)` 為 True，`.strip()` / `.removeprefix()` 都能用）。

### 🟠 B. `check_setup.py` 擋掉一把其實能用的金鑰

你的金鑰用的是 `GEMINI_API_KEY` 這個名字。實測 `google-genai` 與
`langchain-google-genai` **兩個名字都吃**，但 `check_setup.py` 只認
`GOOGLE_API_KEY`，於是回報「缺金鑰」——一個假的 Phase 0 失敗。

**修正**：兩個名字都認。

### 🟠 C. `.env` 的金鑰不會被 `uv run` 自動載入

金鑰放 `.env` 是最普遍的習慣，但 `uv run` 預設不讀，必須帶 `--env-file`。
而且 `[tool.uv]` **不支援** `env-file` 設定（實測回
`unknown field env-file`），沒辦法一勞永逸。

還有一個更陰的變體：`export` 寫進 `~/.zshrc` 時，**agent 開的非互動 shell
根本不讀它**（zsh 只在互動模式讀 `.zshrc`，非互動讀 `.zshenv`）——
症狀是「我明明設了它卻說沒設」。

**修正**：SKILL.md 與 WALKTHROUGH 把兩種放法寫成明確的二選一，
並標明 `~/.zshenv` vs `~/.zshrc` 的差別；`check_setup.py` 的失敗訊息
直接提示 `--env-file` 用法。

### 🟡 D. 埠 8000 常被佔用

實測時 8000 已被機器上另一個 python 佔住。已在疑難排解加上換埠指引
（含 Phase 4.5 要跟著改 `--api`）。

---

## 一之二、前端實跑才現形的缺陷（2026-08-14）

前端這塊我原本只做靜態檢視。真的 `npm create vite` + 貼上教材程式碼跑起來，
又是兩個問題。

### 🟠 E. Vite React 樣板的 `index.css` 會把版面弄壞

現在的樣板附了一份示範 CSS：

```css
#root { width: 1126px; max-width: 100%; margin: 0 auto;
        border-inline: 1px solid var(--border); text-align: center; }
```

照 `frontend-graph.md` 原樣貼 `App.jsx` 的結果：版面被卡在 1126px、
畫面中間多一條莫名的直線、整頁文字置中、還生出橫向捲軸。

**特別陰的地方**：我第一次嘗試只覆蓋 `max-width` —— 沒用，因為樣板寫的是 `width`。

**修正**：`frontend-graph.md` 最前面加一步
`echo 'body{margin:0}' > src/index.css`，並說明為什麼。
（跟樣板 CSS 打架時，刪掉比覆蓋便宜——這句話本身也值得對同學講。）

### 🟠 F. 沒有 `zoomToFit`，幾百個節點就是畫面中央一小坨

教材裡 `fgRef` 宣告了卻從頭到尾沒用到。力導向圖的初始縮放跟節點數無關，
所以 276 個節點的實跑結果是：中央一團看不清的小點，標籤完全讀不到。
**這個畫面投在教室螢幕上就是災難。**

**修正**：`onEngineStop={() => fgRef.current?.zoomToFit(400, 60)}`——
一行，而且剛好用掉那個原本是死碼的 `fgRef`。掛在 `onEngineStop` 而非
`useEffect`，是因為要等力導向模擬收斂後縮放才有意義。

---

## 二、初評就找到的缺陷（已修正）

### 🔴 1. 目錄結構不對，SKILL.md 每一條指令都會失敗（阻斷級）

`SKILL.md` 全文引用 `scripts/00_ingest_source.py`、`references/mcp-setup.md`，
但原本的 `files/` 是**扁平的**——所有檔案平鋪在同一層。照 SKILL.md 執行的
第一個指令 `python scripts/check_setup.py` 就會 `No such file`。

**修正**：拆成 `scripts/` + `references/`，SKILL.md 放在最上層。
這也是 Claude Code skill 的標準結構，順便讓三平台都能吃。

---

### 🟠 2. 跨來源汙染：問影片的問題，撈到 PDF 的實體（高）

`04_chatbot_server.py` 的 `graph_expand()` 有一段 fallback：

```cypher
WHERE ck.id IN $ids OR ck.start IN $starts
```

問題出在 `start` 這個欄位**在不同來源代表完全不同的東西**：

| 來源 | `start` 的意義 |
|---|---|
| YouTube | 秒數 |
| PDF | 頁碼 |
| DOCX | 段落序號 |
| 網頁 | 段落序號 |

於是 YouTube 的 `start=1`（第 1 秒）會撞上 PDF 的 `start=1`（第 1 頁），
把另一份文件的實體整包撈進 context。

**這不是理論推測，是實測復現的**：

```
拿來擴展的全是 YouTube chunk, starts: [1, 178, 60, 119]
擴展結果節點: ['另一份文件', '完全無關的PDF實體', '概念0', '檢索', ...]
>>> 有沒有混進 PDF 的實體? 有！跨來源汙染
```

**為什麼這特別嚴重**：這個 skill 的頭號賣點就是「一支腳本吃四種來源」。
真正照它宣傳的用法用（課堂上灌第二份資料）就會踩到，而且**答案看起來完全
正常**——只是偷偷混進了不相干的知識。這種 bug 最貴。

**修正**：fallback 連 `video_id` 一起限定。

```cypher
WHERE ck.id IN $ids
   OR (ck.video_id IN $vids AND ck.start IN $starts)
```

回歸測試：同樣的情境，現在輸出 `有沒有混進 PDF 的實體? 沒有`。

---

### 🟠 3. Phase 1 的成功判準永遠對不上 YouTube 的實際輸出（中）

SKILL.md 硬規則第 3 條寫死：「實際輸出符合成功判準才算完成，不符合就往下查、
都沒中就回報卡住」。而 Phase 1 的成功判準是：

```
[✓] <來源類型> 來源 N 段已存至 source.json
```

但 `00_ingest_source.py` 的 YouTube 分支印的是：

```
[✓] YouTube 來源已正規化: source.json
```

pdf / docx / url 三條路線都印對，**只有 YouTube 這條印錯**——偏偏這是整堂課
的主線。照硬規則執行的 agent（尤其是能力較弱的免費模型，這正是硬規則的
服務對象）會判定 Phase 1 失敗然後卡在那裡。

**修正**：讓 YouTube 分支輸出與其他三條一致。實測現在印
`[✓] youtube 來源 60 段已存至 source.json`。

---

### 🟠 4. judge 少給一個維度，整輪評測白做（中）

`05_evaluate_rag.py` 只檢查 judge 的輸出**是不是合法 JSON**，沒檢查**欄位齊不齊**。
LLM 少給一個 `citation` 是很常見的事，而且不會當場報錯——
要跑到最後 `aggregate()` 才 `KeyError` 炸掉。

那時候 10 題已經全部跑完了：20 次 RAG 呼叫 + 10 次 judge 呼叫的成本與時間，
連同 `eval_report.json` 一起蒸發。

**修正**：解析後立刻驗三個維度都在，缺了就跳過該題並印訊息，其餘照跑。

---

### 🟡 5. 重跑換語言時撿到上一次的舊字幕（低）

`01_fetch_transcript.py` 用 `glob(f"{info['id']}*.vtt")` 找剛下載的字幕檔，
取 `[0]`。如果 `subs/` 裡還躺著上次跑 `--lang en` 留下的檔案，
這次跑 `--lang zh-TW` 可能拿到舊的英文字幕，而且**完全不會報錯**。

**修正**：先精確比對本次語言的檔名，找不到才退回萬用比對。

---

### 🟡 6. 前端圖的右半邊會被切出畫面外（低，但在投影幕上很明顯）

`references/frontend-graph.md` 的 `ForceGraph2D` 沒給 `width` / `height`，
套件預設用**整個視窗寬**。左邊還有一個 420px 的聊天欄，於是圖被推出去，
右半邊直接看不到。

**修正**：加 resize 監聽明確餵尺寸，側欄補 `flexShrink: 0`。
並在「已知坑」補上第 4 條。

---

## 三、依你的要求做的改動

| 項目 | 改動 |
|---|---|
| **套件管理** | `pip install` → **uv**。新增 `pyproject.toml`，所有指令改 `uv run` |
| **LLM** | OpenAI → **純 Gemini**（AI Studio 金鑰）。`langchain-openai` → `langchain-google-genai`，`gpt-4o-mini`/`text-embedding-3-small` → `gemini-3.5-flash`/`gemini-embedding-001` |
| **judge 模型** | 依你選的「全部 Flash」。已在 SKILL.md 與 `method-validation.md` 加上誠實條款（見下方限制 1） |
| **跨平台** | 新增 `install.sh`，一鍵掛給 Claude Code / Cursor / Codex |

### 順手加的一個防護：模型改名

Google 每隔一陣子就改模型名（`gemini-1.5` → `2.5` → `3.x`）。任何寫死模型名的
教材都會過期，然後整班在 Step 3 撞上看不懂的 404。

`check_setup.py` 現在會拿你的金鑰**真的去問一次 Google「有哪些模型可用」**，
並確認設定的兩支模型在不在清單裡；不在就直接印出可用清單叫你 export。
模型名同時抽成環境變數（`GEMINI_MODEL` / `GEMINI_EMBED_MODEL`），
**一個 export 就同時改掉所有腳本**。

把一個必然會發生的失敗，從 Step 3 的神秘 404 前移到 Step 1 的一行提示。

---

## 四、沒修的已知限制（留給你決定）

這些我**刻意沒動**——它們在單一來源的教學場景不會咬人，改了反而讓教學版
變複雜。但你該知道它們在。

**1. judge 與受測 pipeline 同一支模型。**
你選了「全部 Flash」。這省成本，但 judge 沒有比受測系統更強的判斷力，
且兩邊同源會有 self-preference bias。**這個設定下的 A/B 勝負只能當方向性訊號，
不能當強證據。** 已寫進 `method-validation.md` 誠實條款，並留了
`GEMINI_JUDGE_MODEL` 給你隨時升級。

**2. `/graph` 端點回傳全圖，沒有 `video_id` 過濾。**
灌了第二份資料之後，前端初始畫面會把兩份資料的圖疊在一起。
單一來源的教學不受影響；要做多來源就得加過濾參數。

**3. 重跑不會清掉舊的 Entity 節點。**
`03_build_graph.py` 只 `DETACH DELETE` 舊 Chunk，Entity 會留下來。
換一支影片重跑，圖裡會累積上一支影片的孤兒實體。
（保留 Entity 是刻意的——跨影片實體合併正是圖譜的價值。但要清空時得手動
`MATCH (n) DETACH DELETE n`。）

**4. Neo4j 沒有建索引。**
`MERGE (a:Entity {name: $subj})` 在沒有 constraint 的情況下是全表掃描。
教學規模（幾百個節點）完全無感；上千 chunk 就會明顯變慢。
一行 `CREATE CONSTRAINT FOR (e:Entity) REQUIRE e.name IS UNIQUE` 可解。

**5. 效能：都是「一次一個」的寫法。**
`03` 每個 chunk 一次 LLM 呼叫、每條三元組一次 auto-commit；
`05` 每題重開一次 Chroma 連線與 embedding client。
實測數字：8 個 chunk 抽 53 條關係花 **68 秒**；8 題 A/B 評測花 **2 分 49 秒**。
一支 20 分鐘影片（約 30~40 chunk）Phase 3 要抓 5 分鐘左右。
**慢，但不錯。** 教學版可讀性優先，這個取捨我認為是對的。

**6. LLM 的 JSON 全靠字串剝殼。**
三支腳本都用 `removeprefix("```json")` 處理輸出，沒用 structured output。
`03` 的註解自己承認了這點（「這就是為什麼正式系統要用 structured output」）
——當教材是合理的。
**實測意外地穩**：8 個 chunk 的三元組抽取、8 題出題、8 輪 judge 評分，
**零解析失敗**，Gemini 完全遵守了「嚴格只輸出 JSON」。
但這是運氣好不是保證，Gemini 支援 `response_schema`，想升級隨時可以。

**7. YouTube 字幕限流是課堂最大實務風險。**
一個班同時抓同一支影片幾乎必被 429。**課前預抓好 `source.json` 發給同學**，
這件事我在 WALKTHROUGH 裡標了兩次，因為它比任何程式碼 bug 都更會毀掉一堂課。

---

## 五、實測覆蓋明細

| 測項 | 方法 | 結果 |
|---|---|---|
| 七支腳本語法 | `py_compile` | ✅ 全過 |
| SKILL.md 宣稱的版本表 | uv 實裝比對 | ✅ 屬實（`langchain-openai` 那格已隨 Gemini 改寫移除） |
| `parse_vtt` ASR 滾動式重複去重 | 手工 VTT 樣本 | ✅ 正確去重、剝除 word-level 標記 |
| `_pack_paragraphs` 段落聚合 | 含空輸入邊界 | ✅ |
| `00` YouTube | 真抓 YouTube | ✅ 60 段 |
| `00` PDF / DOCX / 網頁 | 自製素材 + 本地 HTTP server | ✅ 三條全過 |
| `00` 不支援格式 | `.html` 當檔案餵 | ✅ 正確報錯 exit 1 |
| `02` to_documents 兩種 source_type | youtube vs pdf | ✅ `chunk_index` 全域連續 |
| `02` Chroma 入庫 + 冪等重跑 | 假嵌入 + 真 Chroma | ✅ 第二次印「已清除舊資料 4 筆」 |
| `03` Cypher | 真 Neo4j 5（docker） | ✅ 8 條三元組 MERGE 去重成 5 條關係 |
| `03` 冪等 | 連跑兩次 | ✅ |
| `04` multi_query / rrf_fuse / graph_expand | 假 LLM + 真 Chroma + 真 Neo4j | ✅ |
| `04` `/chat` `/graph` `/graph/{name}` | 直接呼叫函式 | ✅ 三個端點皆回正確結構 |
| **跨來源汙染** | 灌入第二份 PDF 後擴展 | 🔴 復現 → 修正 → ✅ 回歸通過 |
| `05` aggregate / parse_json_loose | 合成資料 + 壞輸入 | ✅ |
| `check_setup` 失敗路徑 | 無金鑰 / 假金鑰 | ✅ 兩種都優雅失敗並給修復指令 |
| `uv sync` | 乾淨環境 | ✅ |
| `install.sh` 三平台 | 空專案 | ✅ 三個 `[✓]` |
| `install.sh` 冪等 | 重跑 | ✅ AGENTS.md 區塊數維持 1 |
| Claude Code 實際載入 | `--global` 安裝後 | ✅ skill 出現在可用清單 |

### 真實金鑰補測（2026-08-14，影片：3Blue1Brown《LLM explained briefly》6 分鐘）

| 測項 | 結果 |
|---|---|
| Skill 從 symlink 載入 + `uv` 穿過 symlink | ✅ base dir 正確解析、`uv sync` 正常 |
| Phase 0 無金鑰時擋住 | ✅ 4 項 ✗、exit=1、拒絕往下 |
| Phase 0 全綠 | ✅ `ALL CHECKS PASSED` |
| **模型名 `gemini-3.5-flash` / `gemini-embedding-001` 真實存在** | ✅ 由 API 模型清單確認（先前只是從套件 docstring 推的） |
| Phase 1 YouTube 中文人工字幕 | ✅ 115 段，輸出格式符合成功判準 |
| Phase 2 真實 Gemini 嵌入 | ✅ 8 chunk、**3072 維**、語意檢索回傳相關片段 |
| Phase 3 真實 Gemini 三元組抽取 | ✅ 76 實體／53 關係、**8/8 chunk 零 JSON 解析失敗**、68 秒 |
| Phase 3 跨 chunk 實體合併 | ✅ 「下一個單詞」被 3 個 chunk 共用 |
| Phase 3 同義詞未合併 | ⚠️ 「大型語言模型」vs「大型语言模型」（繁/簡）各自成節點——**SKILL.md 預言的教學素材真的長出來了** |
| Phase 4+5 `/graph` | ✅ 76 節點 53 邊 |
| Phase 4+5 `/chat` 完整強 RAG | ✅ 帶時間戳引用的實質答案、5 sources、24 graph_nodes、14 秒 |
| Phase 4.5 `--generate` | ✅ 8 題全是具體概念題，無空題 |
| Phase 4.5 `--run` A/B | ✅ 腳本跑通產出報告；**但強 RAG 未勝出**（見結論的「結果不如預期」） |
| `.content` → `.text` 修正後回歸 | ✅ 6 處全部正常 |

### 前端實跑（2026-08-14，27 分鐘 Transformer 影片，28 chunk / 276 節點 / 200 邊）

| 測項 | 結果 |
|---|---|
| `npm create vite` + 貼上教材 App.jsx | ✅ 零 console 錯誤 |
| Vite 樣板 CSS 衝突 | 🟠 復現（1126px 卡死 + 直線 + 橫捲軸）→ 修正 → ✅ |
| 缺 `zoomToFit` | 🟠 復現（276 節點擠成一小坨）→ 修正 → ✅ 填滿畫布 |
| 畫布尺寸（坑 4 的修正是否有效） | ✅ canvas 1020×860 = 1440−420，精準 |
| 提問 → 答案 + 時間戳引用 | ✅ 5 個可點連結（3:54 / 4:51 / 26:17 / 6:46 / 22:26） |
| 引用深連結真的能跳 | ✅ 開出 `youtube.com/watch?v=...&t=291s` |
| 答案相關節點高亮變橘 | ✅ |
| 點節點展開鄰居 | ✅ 觸發 `GET /graph/机器学习入门模型` |
| 答案 markdown 亂炸 | 🟠 **改後端 prompt 解決**（見下）→ ✅ 殘留 `**` 與裸網址皆歸零 |
| 節點太小 / 標籤疊成一團 / 圖看起來靜止 | 🟠 三個都復現 → 修正 → ✅ |
| 圖譜孤島 | ⚠️ 畫面上大半是 2~3 節點碎團——Phase 3 正規化不足，**視覺化讓它無所遁形** |

### 🟠 G. markdown 亂炸的根因在後端，不在前端

前端把答案當純文字印，畫面上就是滿滿的 `**核心地位**` 和裸網址。
一開始我想在前端用正則擦掉——**方向就錯了**。

真正的原因：`04_chatbot_server.py` 把 context 標成 `[片段 1｜{網址}]`，
**LLM 就照抄這個格式進答案**。它模仿的是你給它看的東西。

**修正**（在 prompt 端）：片段標頭不放網址、明確要求純文字不用 markdown、
引用只寫 `[片段 N]`，網址由介面自己補。
實測改完：殘留 `**` = 0、裸網址 = 0、`[片段 N]` 標記 4 個，前端把它們渲染成
可點的琥珀色時間戳。

> 教學重點：**輸出格式的問題，優先在生成端解決，不要在渲染端補救。**

### 🟠 H. 節點太小 / 標籤疊成一團 / 圖看起來是靜止的

三個都是實跑才看得出來的：

- **太小**：`zoomToFit` 之後縮放比例很小，固定的圖座標半徑就變成看不見的點。
  修法是**半徑除以 `scale`**，讓節點維持固定的「螢幕」大小。
- **標籤疊成一團**：24 個高亮節點聚在一起時完全讀不出字。
  標籤改到 `onRenderFramePost` 統一畫（`nodeCanvasObject` 是逐節點呼叫、
  順序由資料決定，做不到），先依「高亮 > 連結數」排序，再用矩形碰撞偵測
  跳過重疊的。**寧可少幾個標籤，也不要疊成一團。**
- **看起來靜止**：`d3AlphaDecay` 預設收斂太快，一載入就不動了。調低 +
  拉長 `cooldownTime`，互動後 `d3ReheatSimulation()`。

### 介面重做（2026-08-14）

原本的保底版只有功能沒有設計，投影出來很難看。重做後仍是**零 UI 套件**
（純 CSS + 設計 tokens），但加了一個簽名元素：**底部的影片時間軸**——
所有 chunk 是暗刻度，本次答案的證據亮成琥珀色，讓「引用可回溯」這個
專案主張變成看得見的畫面。為此在後端新增了 `GET /chunks`（純新增，
不動既有行為）。`references/frontend-graph.md` 已用實跑通過的檔案內容重寫。

### 沒測到的（誠實聲明）
- **付費路線**：LlamaParse、Tavily 都需要金鑰。
- **whisper fallback**：需要一支完全沒字幕的影片。
- **MCP 驗證點**：Chroma / Neo4j MCP 未接。（不影響——每個驗證點都有實測過的
  無 MCP 替代指令。）

---

## 六、重現這次驗證

金鑰放 `.env` 的話（本次驗證就是這樣跑的）：

```bash
cd yt-graphrag-bot
uv sync
docker run -d --name neo4j-teach -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/你的密碼 neo4j:5 && sleep 25

E="--env-file ../.env"          # .env 裡要有 GOOGLE_API_KEY(或 GEMINI_API_KEY) 與 NEO4J_PASSWORD
uv run $E python scripts/check_setup.py
uv run $E python scripts/00_ingest_source.py "<20 分鐘以上的影片網址>" --out source.json
uv run $E python scripts/02_ingest_vectordb.py source.json --persist ./chroma_db
uv run $E python scripts/03_build_graph.py source.json
cp scripts/04_chatbot_server.py chatbot_server.py
uv run $E uvicorn chatbot_server:app --port 8010 &   # 8000 常被佔
uv run $E python scripts/05_evaluate_rag.py --generate source.json --n 10
uv run $E python scripts/05_evaluate_rag.py --run eval_set.json --api http://localhost:8010
```

**影片請挑 20 分鐘以上**——本次用 6 分鐘的影片，就是因此測不出強 RAG 的增量。

全綠就代表上面那塊「未驗證」也補上了。之後照 `WALKTHROUGH.md` 一路走。
