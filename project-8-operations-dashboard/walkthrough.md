# Walkthrough：在 Cursor 上把營運數據儀表板一步一步做出來

> 這份文件帶你從零做出一份**完整的營運數據儀表板**——從生成帶瑕疵的合成資料開始，經過清理管線、指標計算，最後用 Streamlit 做成互動多頁面儀表板。你會學到三件事：怎麼用 Faker 精準控制資料品質、怎麼寫清理邏輯讓每一步都看得見流失、怎麼用 @st.cache_data 搭配 pages 資料夾打造快速的多頁儀表板。
>
> 文中有四種標記，幫你少走彎路：
> - 🔍 **名詞卡**：專有名詞的白話解釋 + 生活比喻
> - ❓ **想一想**：先自己想，再往下看答案
> - ✅ **預期看到**：每個指令跑完的正常畫面長什麼樣
> - 🧯 **卡住的話**：常見翻車點與救援方式

---

## 🚦 開始前檢查清單（先做這三件事，做的當天才不會卡）

1. **產生一次完整的資料流程**——執行 `generate_data.py`、`pipeline.py`、`metrics.py`，確認沒有報錯且輸出合理。先跑過一次就知道「這邊應該印出 8 passed」。
2. **在本機跑一次 `streamlit run app.py`**——重點是確認中文字型正常顯示（不是豆腐方塊）。確認圖表中文字型正常，避免部署後才發現問題。
3. **確認 uv 環境已裝好所有套件**——一個沒裝會很卡。跑 `uv add` 時網速不穩會失敗，先連上好的網路再裝一遍。

## 🗺️ 學習地圖（建議 3 小時）

| 段落 | 時間 | 類型 |
|---|---|---|
| 開場故事 + 第 1 節反模式 | 30 分 | 閱讀理解（開場故事是全課靈魂，慢慢看） |
| 第 2–3 節產生資料與探索 | 25 分 | 動手做（Faker 生成 + Ask Mode 探索） |
| 第 4 節清理管線 | 25 分 | 動手做（每一步都印出列數，這是亮點） |
| 第 5 節指標計算 | 20 分 | 動手做（手算一個小例子 + 跑測試） |
| 第 6 節 Streamlit 儀表板 | 35 分 | 動手做（拉篩選器看圖表變化 ⭐ 一定要親自試） |
| 第 7–8 節快取與字型排錯 | 15 分 | 閱讀理解 + 動手做 |
| 收尾三句話 | 10 分 | 閱讀理解 |

---

## 🎬 課堂放映表（講師用）

> 程式碼在 `./dashboard/`，遙控器是 `./demo.sh`（放在 `project-8-operations-dashboard/` 根目錄，腳本自己會 `cd dashboard`）。
> 整堂課只有兩個指令：`./demo.sh` 列出所有幕，`./demo.sh N` 跑第 N 幕。
> 全程離線、不需要任何 API key；八幕的順序就是下面時間軸的順序。

### 上課前 15 分鐘要先做完

| # | 做什麼 | 為什麼要先做 |
|---|---|---|
| 1 | `cd /Users/kevinluo/cursor-class-2/project-8-operations-dashboard/dashboard && uv sync` | 全課唯一會碰網路的動作。同步過一次之後，當天 `UV_OFFLINE=1` 也跑得動（走 uv cache），教室網路爛掉也不影響 |
| 2 | 回到 `project-8-operations-dashboard/`，依序跑 `./demo.sh 1`、`./demo.sh 4` | 第 5、7、8 幕都需要 `data/*_clean.csv`，沒有的話 demo.sh 會直接擋下來。先跑過也順便確認 seed 固定：連跑兩次 md5 一樣 |
| 3 | `./demo.sh 8` 開一次瀏覽器，切到「地區分析」用肉眼確認中文不是豆腐方塊 ▢▢▢ | 字型 fallback 鏈寫在 `dashboard/data_access.py` 的 `FONT_FAMILY`，macOS／Windows 都正常，但**換一台 Linux 投影機就要重看一次**。確認完 Ctrl+C 關掉，把 8501 讓出來 |
| 4 | `rm -rf dashboard/.demo_broken`，並確認 8501 沒有殘留的 streamlit | 第 6 幕會在 `.demo_broken/` 造一份改壞的複本再刪掉；上一次 Ctrl+C 中斷可能留著。8501 被占用時 streamlit 會自動改 8502，不會 crash，但投影片上的網址會對不上 |
| 5 | 把終端機字體調到投影可讀（建議 18pt 以上），瀏覽器縮放 110–125% | 第 4、5、6 幕的重點全是「終端機上的數字」，後排看不到就等於沒演 |
| 6 | 心裡記住：本文第 0 節寫的路徑是 `project-8-operations-dashboard/`，但 uv 專案實際在 `project-8-operations-dashboard/dashboard/` | 學生照著第 0 節做會在錯的一層建 venv。講到第 0 節時補一句「所有指令請先 `cd dashboard`」 |

### 放映時間軸

| 時間 | 幕 | 指令 | 打開哪個檔案投影 | 📺 螢幕上會出現 | 🎯 這一幕在教 |
|---|---|---|---|---|---|
| 0:00–0:05 | 開場（無幕） | `./demo.sh` | `project-8-operations-dashboard/demo.sh` | 終端機印出「Project 8：營運數據儀表板 — 課堂幕次表」，第 1 幕到第 8 幕各一段標題＋一行 📺 預告 | 先讓學生看到終點：今天會從髒 CSV 一路走到會動的儀表板 |
| 0:05–0:30 | 開場故事 ＋ 第 1 節五個反模式（無指令） | — | `walkthrough.md`（🎬 開場故事 ～ 1.5） | 「教室情景 ↔ 系統層面」對照表、五個反模式的 ✗／✓ 兩欄表、四個指標的定義表 | 洗資料 → 算指標 → 貼成績牆三步驟；五個反模式是後面八幕的骨架 |
| 0:30–0:40 | 第 1 幕：產生「刻意帶瑕疵」的資料 | `./demo.sh 1` | `dashboard/generate_data.py` | 兩張「瑕疵注入清單」表格（customers：email 缺失 150 列 30.0%、region 名稱髒 200 列、完全重複列 15 列；transactions：amount 負值 200 列 10.0%…），最後 `wc -l` 印出 `501 data/customers_raw.csv` 與 `2001 data/transactions_raw.csv` | 瑕疵是「設計」出來的，不是碰運氣；固定 seed 才能讓全班拿到一模一樣的檔案（連跑兩次 md5 相同） |
| 0:40–0:55 | 第 2 幕：先看髒資料長什麼樣 | `./demo.sh 2` | `dashboard/pipeline.py`（`explore` / `quality_report`）、`dashboard/DATA_QUALITY_REPORT.md` | 前 10 列一眼就髒：`2023/10/07`、`2024年10月16日`、`Hsinchu`、`Pro`、空白 email；接著品質報告印出 email 缺失 150 列 30.0%、plan 有 12 種寫法、region 有 31 種寫法、amount 無法轉數字 65 列、負值 200 列 10.0%、min=-573／max=4976／mean=443.7／std=925.9、IQR 離群 173 列、跨表孤立 121 列（6.0%） | 鐵律 1：先探索、再清理。這份報告就是後面每一刀的決策依據 |
| 0:55–1:05 | 第 3 幕：型別陷阱（壞版 vs 修好版）⭐ | `./demo.sh 3` | `dashboard/pipeline.py`（`trap_demo`、`clean_amount_text`） | 上半段 `dtype: object`，`amount.sum()` 吐出 `5345475347148158170135164…` 並補一行「這是一個 5,847 個字元的字串」；下半段 `dtype: float64`、救得回來 50 列、救不回來 25 列、總金額 927,006 | `sum()` 不會報錯，只會給你一個錯得離譜的答案——`pd.to_numeric(errors="coerce")` 是必修不是選修 |
| 1:05–1:20 | 第 4 幕：清理管線，每一步都記帳 | `./demo.sh 4` | `dashboard/pipeline.py`（`clean_data`、`_step`） | 13 個【步驟】區塊，每個都是「清理前 N 列 → 去掉「原因」-M 列 → 清理後 K 列」：步驟 5 -10、步驟 10 -25、步驟 11 -200 且印「金額合計 -46,220 USD——真的要丟嗎？先問業務」、步驟 12 -119、步驟 13 -12；中間有一段【不刪除】離群值（> 1,215 USD）192 列合計 579,332 USD；結尾 500→490（98.0%）、2000→1644（82.2%），`wc -l` 印 491 與 1645 | 鐵律 2：每一步印出丟棄列數，資料流失才看得見；而且不是每個異常都該刪——離群值那 579,332 USD 是真客戶 |
| 1:20–1:40 | 第 5 幕：四個指標與它們的分母 | `./demo.sh 5` | `dashboard/metrics.py` | 先四行中間結果：`[MRR 2024-01] 交易數：111, 總額：81,608.00`、`cohort_size：99, 留下來：68`、`付費客戶：340 / 總客戶：490`、`ARPU … 營收 81,608.00 活躍 99`；接著 2024 全年 12 列總表（活躍客戶 99→152、次月留存率落在 68.7%–82.1%），總轉換率 69.4%，最後一個月留存率 0.0% 並附「沒有下個月可比」的說明 | 鐵律 3：分母定義要統一並寫進 docstring；每個函式都吐中間結果，是為了讓人能自己核對，不是為了好看 |
| 1:40–1:55 | 第 6 幕：pytest 綠 → 紅 → 綠 | `./demo.sh 6` | `dashboard/test_metrics.py`、`dashboard/test_pipeline.py` | 先 `8 passed in 0.21s`（綠色），再 `-v` 印出四行 `PASSED` 與 `4 passed`；改壞版本跑出 `assert 250.0 == pytest.approx(300.0)`、`Obtained: 250.0 / Expected: 300.0`、`1 failed, 3 passed`（紅色）；刪掉複本還原後又是 `8 passed` | 測試要「能變紅」才有意義。250 與 300 的差別一眼看得出來，正是因為測試資料小到能手算（忘了濾負值就會算成 250） |
| 1:55–2:05 | 第 7 幕：快取的威力 | `./demo.sh 7` | `dashboard/data_access.py`（`get_data`／`filter_data`／`_benchmark`） | 準備動作先印一行 `[DEBUG] 檔案讀取` 並註明「計時從這裡才開始」；然後第 1 次約 11 ms、第 2 次約 0.5 ms，印出「快了 22 倍。第 2 次沒有再印 [DEBUG] → 檔案沒有重讀」；手動清快取後第 3 次回到約 6.6 ms，`[DEBUG]` 又印一次 | `@st.cache_data` 只該快取「讀檔」這一層；篩選與排序留在快取外面，否則快取永遠不命中 |
| 2:05–2:30 | 第 8 幕：開儀表板（本幕會開瀏覽器） | `./demo.sh 8` | `dashboard/app.py`、`dashboard/pages/04_地區分析.py` | 先 `smoke_app.py` 五頁全 `✓`（app.py KPI 5 張、01／02 各 2 張圖、03 圖 2＋KPI 3、04 圖 1＋互動 4）且整輪只印一次 `[DEBUG]`；瀏覽器開 `http://localhost:8501`，標題「營運數據儀表板」，KPI 為 總客戶 490／轉換率 69.4%／本月 MRR $100,984／ARPU $664.4／上月留存率 78.8%；切到「地區分析」點 radio「按客戶數」，圖表標題從「地區營收排行」變「地區客戶數排行」、柱子重排成 110／110／99／92／81，回頭看終端機 `[DEBUG] 檔案讀取` 仍然只有一行。結束按 Ctrl+C | 多頁共用同一份快取（`from data_access import get_data`），互動全部發生在快取外面——這就是儀表板不龜速的原因 |
| 2:30–2:40 | 收尾（無幕） | — | `walkthrough.md`（10. 驗收清單、13. 帶走的三句話） | 驗收清單逐條打勾，最後停在三句話那一頁 | 把八幕收回三句話：合成資料可控、先探索再清理、每一步都要看得見 |

累計 2 小時 40 分，對應學習地圖的 30＋25＋25＋20＋50＋10 分；中間安排兩次 10 分鐘休息（建議放在第 4 幕與第 6 幕之後）就剛好三小時。

### ⭐ 全場最值得停下來的一幕

**第 3 幕的型別陷阱**——`amount.sum()` 不但沒報錯，還吐出一個 5,847 個字元的怪物字串，那個畫面比任何投影片都有說服力。跑完先別往下捲，停 3 分鐘，問學生兩個問題：「pandas 為什麼不報錯？」（因為 `+` 對字串是合法的，它做的是串接不是加法）以及「如果這條 sum 直接進了老闆的月報，你要多久才會發現？」。第二名是第 8 幕切 radio 那 30 秒——柱子在眼前重排、終端機 `[DEBUG]` 卻紋風不動，那是快取這堂課唯一能「看見」的瞬間，記得把瀏覽器和終端機並排放。

### 🧯 現場翻車備案

| 翻什麼 | 徵狀 | 30 秒內的救援 |
|---|---|---|
| 第 1 幕裝不了套件 | `uv sync` 卡住或報網路錯誤 | `UV_OFFLINE=1 ./demo.sh 1`——課前同步過就會走 uv cache，完全離線也能跑完八幕 |
| 資料檔不見／被改壞 | 第 5、7、8 幕跳出「還沒有清理後的資料。先跑：./demo.sh 4」 | 照它說的跑；要整組重來就 `rm -rf dashboard/data && ./demo.sh 1 && ./demo.sh 4`，seed 固定，重生出來的數字一模一樣 |
| 第 6 幕被 Ctrl+C 中斷 | `dashboard/.demo_broken/` 殘留 | `rm -rf dashboard/.demo_broken`。（實測 pytest 預設不會遞迴進點開頭的目錄，就算殘留也還是 `8 passed`，不用當著學生的面慌） |
| 第 8 幕網址對不上 | 瀏覽器打不開 8501，或開起來是別人的頁面 | 8501 被占用時 streamlit 會自動改 8502 並在終端機印出真正的 Local URL——**看終端機那一行就好**，或手動 `uv run streamlit run app.py --server.port 8502` |
| 圖表中文變豆腐方塊 ▢▢▢ | 換了投影機／Linux 機器，圖表座標軸全是方框 | **別急著救，這本身就是第 8 節的教材**：先講「本機有字型、伺服器沒有」，再示範 `sudo apt-get install fonts-noto-cjk` 與 `fc-list \| grep Noto`。字型設定集中在 `dashboard/data_access.py` 的 `FONT_FAMILY` 一行 |
| `[DEBUG]` 印超過一次 | 學生喊「老師你的快取沒生效」 | 第 7 幕計時區間**上方**那一行是準備動作印的，腳本自己有註明；儀表板端若真的多印，就是把排序／篩選寫進 `get_data()` 了，打開 `data_access.py` 現場示範搬出去 |
| 儀表板要重新載入資料 | 改了 CSV 但畫面沒變 | 側邊欄最下面有「清除快取並重新載入」按鈕（等同右上角漢堡選單 → Clear cache → Rerun） |

---

## 🎬 開場故事：數據之旅的三個步驟

想像一下你是導師，班上 40 個學生交回數學作業。大家翻一翻——有人在卷子上寫『87 分』、有人寫『八十七分』、有人用 Excel 寫了『87.0』、有人交了兩份……再翻翻，有五個人根本沒交，格子空著。

現在你要算全班平均。怎麼算？你不能直接加起來，因為有人寫字、有人寫數字，加法都算不了。所以第一步是什麼？**洗資料**——把『八十七分』改成 87、把重複交的刪掉、空的格子標記成『未交』。

第二步才是算平均。你終於拿著乾淨的 40 個數字，可以 87 + 95 + 72 + … = 平均 82 分。

第三步呢？老師拿著這個 82，貼在教室後面的成績牆，還加上別的資訊——班級排名、進步最多的同學、不及格人數。這面牆就叫儀表板。

今天整份教學就是這三步：**第一，清理亂七八糟的作業（資料清理）；第二，算對你要的指標（平均、進步率、排名）；第三，用有顏色、會動的圖表貼在牆上（互動儀表板）。一家 SaaS 公司的執行長每天看的儀表板，不過就是這個邏輯。大規模而已。

這個比喻會貫穿全課，重點對應關係先記起來：

| 教室情景 | 系統層面 |
|---|---|
| 學生交回的亂作業 | CSV 檔裡的髒資料（型態不統一、缺值、重複、虛假記錄） |
| 老師洗資料 | Pandas DataFrame 清理（dropna、drop_duplicates、型態轉換） |
| 40 個乾淨數字 | 清理後的表格（customers_clean.csv、transactions_clean.csv） |
| 算平均 87 分 | 指標計算（MRR、留存率、轉換率、ARPU） |
| 成績牆有顏色 | Streamlit 儀表板的圖表與卡片 |
| 拉卡片看排名變化 | @st.cache_data 快取 + 篩選器互動 |
| 卡片被風吹掉了 | 中文字型缺失變豆腐方塊 |

---

## 0. 課前準備

- Python 3.12、Cursor Pro、uv 套件管理
- 在 `/Users/kevinluo/cursor-class-2/project-8-operations-dashboard` 建立專案資料夾
- 初始化 uv 環境：

```bash
cd /Users/kevinluo/cursor-class-2/project-8-operations-dashboard
uv venv
source .venv/bin/activate
uv add pandas numpy faker streamlit plotly openpyxl loguru

# 補充：若要用 pip，等價於：
# pip install pandas numpy faker streamlit plotly openpyxl loguru
```

確認安裝成功：`python -c "import pandas, streamlit; print('OK')"` 應無報錯。

> 🔍 **名詞卡：Python**
> 白話：一套「寫資料處理指令」的語言。跟 Excel 不同，你沒有滑鼠和選單，只有「打字下指令」——但好處是速度快、可以處理幾百萬列資料，Excel 會當機。
>
> 🔍 **名詞卡：uv 套件管理**
> 白話：Python 的「應用商店」。需要什麼工具（pandas、Streamlit）就打 `uv add`，它幫你下載、自動解決相依性。就像 App Store 一鍵裝 App。

---

## 1. 先懂概念：資料清理與指標計算的五個反模式

### 1.1 反模式一：看資料前就開始清理

常見做法：讀進 CSV，直接 dropna()、刪離群值、轉型別——假設資料的問題。

正確做法：**先用 Ask Mode 做一輪探索式分析**。看清缺失值分佈、型別錯誤、離群值有多少，再決定怎麼清。有時候「缺失」只是待審核、不是真缺失；有時候離群值裡有重要客戶。

**你這章學到的**：Ask Mode 讀 CSV 產出品質報告（缺失值統計、型別檢查、異常值偵測），成為清理的決策依據。

### 1.2 反模式二：清理管線悶著頭幹，不知道丟了什麼

常見做法：寫一堆 filter、dropna、drop_duplicates，執行完看不到前後列數差異。

正確做法：**每一步都印出丟棄列數**。

```python
# 反模式
df = df[df['amount'] > 0]
df = df.dropna(subset=['email'])

# 正確做法
print(f"原始列數：{len(df)}")
df = df[df['amount'] > 0]
print(f"去掉負值後：{len(df)}")
df = df.dropna(subset=['email'])
print(f"去掉無 email 後：{len(df)}")
```

這樣每清理一步，你和整個公司都能看到流失了多少資料，有問題立刻發現。

> 🔍 **名詞卡：髒資料**
> 白話：跟成績簿裡那筆「八十七」一樣——型態搞錯了、有空白、有重複、甚至有完全虛假的數字（客戶 ID 根本不存在）。現實的資料幾乎全是髒的。
>
> 🔍 **名詞卡：缺值（missing value）/ NaN**
> 白話：成績表的「空格」——有個學生根本沒交，那個格子就是缺的。資料庫裡叫 NULL 或 NaN（Not a Number），代表「沒有值」。
>
> 🔍 **名詞卡：重複值**
> 白話：同學不小心交了兩份一樣的作業。資料表裡，同樣的一列出現兩次。

### 1.3 反模式三：指標算法沒有定義，各自為政

常見做法：工程師算一套、BI 算一套、執行算一套，MRR 永遠對不起來。

正確做法：**四個指標的分母定義全公司統一，寫進註解，配合 pytest 驗證**。

| 指標 | 定義 | 生活比喻 |
|---|---|---|
| MRR | 月度經常性營收，包括新客+續約客，不含退款 | 訂閱制飲料店：每月固定從會員卡扣錢，那個數字就是 MRR。新辦卡+舊客繼續喝都算。 |
| 留存率 | 上個月末付費客，本月末還在的百分比 | 100 個會員上月辦卡，這月還剩 85 個在用——留存率 85%。中間有人退卡。 |
| 轉換率 | 試用客轉成付費客的百分比 | 1000 個免費試用帳號，最後只有 720 個付費——轉換率 72%。 |
| ARPU | 月均每客營收 | 500 位客戶本月共付 \$10,000→ ARPU = \$20/客。老闆可以看出每個客戶平均值錢多少。 |

**你這章學到的**：在 metrics.py 裡四個函式都有清楚的註解與參數名稱；用小到能手算驗證的資料集寫 pytest，證明實作符合定義。

> 🔍 **名詞卡：MRR（月度經常性營收）**
> 白話：SaaS 公司最在乎的數字。比起「賣出 100 套軟體賺 \$10000」，公司更需要「每月穩定從訂閱客手上拿 \$8000」——前者是一次性，後者是持續的。
>
> 🔍 **名詞卡：留存率（retention rate）**
> 白話：「上個月的客還在不在」。跳槽客會掉留存率。想像 Netflix：新客簽約、用了幾集就退了，留存率就是 X%。
>
> 🔍 **名詞卡：轉換率（conversion rate）**
> 白話：免費轉付費的成功率。試用 app 的人那麼多，真正付錢的才那幾個——那個比例就是轉換率。
>
> 🔍 **名詞卡：ARPU（平均每客營收）**
> 白話：把這個月全部營收除以這個月的客戶數。$10000 / 100 客 = $100/客。客戶都很有錢嗎？看 ARPU 就知道。

### 1.4 反模式四：拿 AI 的結果當聖經

常見做法：問 Agent「幫我算轉換率」，看到結論就信了，不看過程。

正確做法：**永遠留一個你能自己核對的錨點**。

| ✗ 容易出包 | ✓ 安全做法 |
|---|---|
| 直接問「幫我算轉換率」不先看資料 | 先用 Ask Mode 做一輪探索式分析 |
| 只看 Agent 給的結論不看過程 | 要求印出中間結果，如 cohort_size |
| 拿全量資料的斷言當測試依據 | 用能心算驗證的小資料寫 pytest |

**你這章學到的**：每次跟 Agent 要指標計算，都要求它「印出中間結果」；寫測試時用 5–8 列能手算的資料，不用全量。

### 1.5 反模式五：Streamlit 每次互動都重跑整個腳本

常見做法：頁面切換、篩選器調整就重新讀檔、清理、算指標——5 秒等待時間。

正確做法：**@st.cache_data 搭配 pages 資料夾是多頁互動儀表板的標準做法**。

```python
# 反模式：頁面一切換就重算
def load_and_clean():
    df = pd.read_csv("data.csv")
    # ... 清理邏輯
    return df

# 正確做法：同名同參數的函式在所有頁面共用快取
@st.cache_data
def get_data():
    return load_and_clean()

customers, transactions = get_data()
```

快取的 key 是「函式簽章 + 參數」。不同頁面定義同名同參數的 `get_data()`，快取就會命中——篩選器調整不會重新讀檔。

> 🔍 **名詞卡：pandas**
> 白話：Python 的「超強 Excel」。可以讀 CSV、清理資料、算統計、畫圖，全用程式碼搞定。像是 Excel 的 VBA 但強一百倍。
>
> 🔍 **名詞卡：DataFrame**
> 白話：pandas 裡的「表格」。把 CSV 讀進 Python，就變成一個叫 DataFrame 的物件——有列、有欄、可以過濾、排序、計算。
>
> 🔍 **名詞卡：Streamlit**
> 白話：讓你用 Python 寫互動網頁的工具。不用學 HTML/CSS/JavaScript，只要 Python，就能做出有滑桿、篩選器、圖表的儀表板。
>
> 🔍 **名詞卡：@st.cache_data（快取裝飾器）**
> 白話：在函式前面加一行魔法咒語。第一次呼叫函式，Streamlit 算出結果並「存起來」；第二次呼叫同名同參數函式，直接還快取結果，不重算。像你上次看過的 Netflix 推薦，不用每次都重新算。
>
> 🔍 **名詞卡：字型豆腐方塊**
> 白話：圖表上的中文字全變成「▢▢▢」——因為伺服器沒裝中文字型。本機有微軟新細明體所以正常，但放到 Linux 伺服器就掛了。

---

## 2. 階段一：產生帶瑕疵的合成資料

### 2.1 用 Faker 產生 SaaS 資料

我們現在來『造假資料』——但這個『假』不是騙人，是『刻意帶瑕疵的模擬資料』。好處是我們能精確控制缺失值比例、型別錯誤的位置、離群值的數量，而不用等真實資料經歷各種意外。

對 Agent 說：

> 寫 generate_data.py：用 Faker 生成 500 個客戶（每個客戶有 signup_date、plan、email）與 2000 筆交易（customer_id、transaction_date、amount）。
> 故意加瑕疵：30% 客戶缺 email、10% 交易 amount 為負、5% 交易 customer_id 是虛假（不存在的客戶）。
> 最後存成 data/customers_raw.csv 和 data/transactions_raw.csv。

**PROMPT 引用**

```
用 Faker 生成帶瑕疵的 SaaS 資料：
- customers：500 列，欄位 [id, email, signup_date, plan]
  - email：30% 是 NaN
  - plan：uniform 分佈在 ['starter', 'pro', 'enterprise']
- transactions：2000 列，欄位 [customer_id, transaction_date, amount]
  - amount：10% 是負數，80% 是 10–500 USD，10% 是 500–5000 USD
  - customer_id：5% 指向不存在的客戶（id > 500）
  - transaction_date：隨機分佈在過去 12 個月
存成 data/customers_raw.csv 和 data/transactions_raw.csv。
```

**預期產出**

```python
# generate_data.py 片段
from faker import Faker
import pandas as pd

fake = Faker()
customers = []
for i in range(500):
    customers.append({
        'id': i + 1,
        'email': fake.email() if fake.random.random() > 0.3 else None,
        'signup_date': fake.date_between(start_date='-12m'),
        'plan': fake.random.choice(['starter', 'pro', 'enterprise'])
    })
df_customers = pd.DataFrame(customers)
df_customers.to_csv('data/customers_raw.csv', index=False)

transactions = []
for i in range(2000):
    amount = fake.random.randint(10, 500)
    if fake.random.random() < 0.1:
        amount = -amount
    customer_id = fake.random.randint(1, 505)  # 5% 會超過 500
    transactions.append({
        'customer_id': customer_id,
        'transaction_date': fake.date_between(start_date='-12m'),
        'amount': amount
    })
df_transactions = pd.DataFrame(transactions)
df_transactions.to_csv('data/transactions_raw.csv', index=False)
```

### 2.2 驗收這個階段

執行後確認：

```bash
python generate_data.py
ls -la data/
head data/customers_raw.csv
wc -l data/customers_raw.csv  # 應該 501 行（含表頭）
```

✅ **預期看到**：終端機列出 `501 data/customers_raw.csv` 與 `2001 data/transactions_raw.csv`，代表檔案產生成功。打開 VS Code 的 CSV viewer，眼睛掃一下看到有些欄位真的是空的（缺值的比喻）、有些金額是負數、有些客戶 ID 是 999（虛假的）。

🧯 **卡住的話**：Faker 報 `ModuleNotFoundError`——代表套件沒裝。重新跑 `uv add faker`。第二次失敗多半是網路問題，改用預先備好的 CSV 檔，流程照走。

---

## 3. 階段二：探索式分析（Ask Mode）

### 3.1 用 Ask Mode 看清資料品質

現在我們不是馬上清理，而是『看清楚』資料有什麼問題。就像老師拿到這疊亂作業，先數數『有多少人漏交？有多少人寫成字而不是數字？』——先做個『資料品質診斷書』，再決定怎麼下手。

對 Agent 說（Ask Mode）：

> 讀 data/customers_raw.csv 與 data/transactions_raw.csv，產出詳細的資料品質報告。要求包括：
> 1. 各欄位的缺失值百分比
> 2. 各欄位的資料型別
> 3. amount 的統計摘要（min、max、mean、std、負數比例）
> 4. 重複列數量
> 5. transactions 中 customer_id 指向不存在客戶的列數

不要對話多輪，要求 Agent 一次產完整的分析報告。

✅ **預期看到**

Agent 會回傳：

```
客戶資料品質報告：
- email 缺失率 31%
- signup_date 缺失率 0%
- plan 缺失率 0%

交易資料品質報告：
- amount 負數比例 9.8%
- amount 統計：min=-4500, max=4800, mean=250, std=380
- customer_id 孤立（不存在主表）：103 列（5.2%）
```

**為什麼要這一步**：這個報告成為你的清理決策依據。例如發現 email 缺失 31%，你就知道直接 dropna(subset=['email']) 會丟掉三分之一的客戶，需要謹慎決策或補充其他欄位。

> ❓ **想一想**：如果發現有 31% 的資料缺少某欄位，直接全部刪掉，行不行？
>
> **答案**：不行，會失去三分之一的資料。可以考慮『標記為未交』或『補充其他欄位推測』，而不是直接刪掉。

### 3.2 記錄發現

在專案根目錄建一個 `DATA_QUALITY_REPORT.md`，貼上 Agent 的分析結果，後續清理時回頭參考。

---

## 4. 階段三：寫清理管線

### 4.1 對 Agent 說

> 寫 pipeline.py：
> - 讀進 data/customers_raw.csv 和 data/transactions_raw.csv
> - 定義一個 `clean_data(df_customers, df_transactions)` 函式
> - 清理邏輯（每一步都印出「清理前列數」與「清理後列數」、「丟棄列數」）：
>   1. 去掉 customers 的缺失 email（用其他欄位補充或標記）
>   2. 去掉 transactions 負值 amount
>   3. 去掉 transactions 孤立 customer_id（不存在 customers 裡）
>   4. 去掉重複列
> - 最後存成 data/customers_clean.csv 和 data/transactions_clean.csv
> 關鍵要求：每一步都打日誌，用 loguru 或 print 清楚地秀出流失數據。

**PROMPT 引用**

```
寫 pipeline.py 清理函式，逐步清理客戶與交易資料。
要求每一步都印出：
  清理前：1000 列
  去掉 [原因]：-100 列
  清理後：900 列

清理邏輯：
1. customers 缺 email 的列：填充成 'unknown' 或 dropna（根據業務決定）
2. transactions amount <= 0 的列：刪除
3. transactions customer_id 不存在 customers 的列：刪除
4. 全表重複列：刪除

最後存成 data/customers_clean.csv 和 data/transactions_clean.csv。
用 loguru 記 log。
```

**預期產出**

```python
# pipeline.py 片段
import pandas as pd
from loguru import logger

logger.add("pipeline.log")

def clean_data(df_customers, df_transactions):
    print("=" * 50)
    print("清理客戶資料")
    print("=" * 50)
    
    logger.info(f"客戶資料原始列數：{len(df_customers)}")
    
    # 步驟 1：缺 email 處理
    before = len(df_customers)
    df_customers['email'] = df_customers['email'].fillna('unknown@company.com')
    after = len(df_customers)
    logger.info(f"填充 email 缺失值：{before} → {after}")
    
    # 步驟 2：重複列
    before = len(df_customers)
    df_customers = df_customers.drop_duplicates()
    after = len(df_customers)
    logger.info(f"刪除重複列：-{before - after} 列，剩 {after} 列")
    
    print("\n" + "=" * 50)
    print("清理交易資料")
    print("=" * 50)
    
    logger.info(f"交易資料原始列數：{len(df_transactions)}")
    
    # 步驟 3：負值 amount
    before = len(df_transactions)
    df_transactions = df_transactions[df_transactions['amount'] > 0]
    after = len(df_transactions)
    logger.info(f"去掉負值 amount：-{before - after} 列，剩 {after} 列")
    
    # 步驟 4：孤立 customer_id
    before = len(df_transactions)
    valid_ids = set(df_customers['id'])
    df_transactions = df_transactions[df_transactions['customer_id'].isin(valid_ids)]
    after = len(df_transactions)
    logger.info(f"去掉孤立 customer_id：-{before - after} 列，剩 {after} 列")
    
    return df_customers, df_transactions

if __name__ == "__main__":
    df_customers = pd.read_csv('data/customers_raw.csv')
    df_transactions = pd.read_csv('data/transactions_raw.csv')
    df_customers, df_transactions = clean_data(df_customers, df_transactions)
    df_customers.to_csv('data/customers_clean.csv', index=False)
    df_transactions.to_csv('data/transactions_clean.csv', index=False)
    print("清理完成！")
```

### 4.2 驗收

執行並檢查日誌輸出：

```bash
uv run python pipeline.py 
# 應該看到每一步的列數變化與 pipeline.log
```

確認：

```bash
wc -l data/customers_clean.csv data/transactions_clean.csv
# 應該比原始檔少（因為丟了瑕疵資料）
```

✅ **預期看到**：終端機印出四個「清理前 → 清理後」的大標題與列數，最後看到 `清理完成！`。wc -l 的輸出應該是「496」與「1897」之類——少於原始的 500 與 2000。

🧯 **卡住的話**：如果某一步列數沒變（例如「去掉孤立 customer_id：-0 列」），代表其實沒有孤立記錄。這代表 Faker 這次生成的資料很乾淨，或者虛假 customer_id 恰好都不在交易表裡。現實的資料通常都會有——失敗本身也是教材。

重點是看那邊終端機——『清理前 2000 列，去掉負值後 1800 列，丟了 200 筆交易』。200 筆是多少錢？算一下……假設平均一筆 $100，那就是 $20,000 直接丟掉。看到數字，老闆才會認真考慮『我要不要真的刪掉這些負值交易，還是先檢查是退款還是誤輸入』。這就是為什麼要印出列數差異。

---

## 5. 階段四：算指標

### 5.1 對 Agent 說

> 寫 metrics.py，實作四個函式，計算 SaaS 核心指標。每個函式都要：
> - 清楚的註解解釋計算邏輯
> - 參數型態與回傳值型態清楚標記
> - 印出中間結果（如 cohort_size）方便驗證
>
> 四個函式：
>
> 1. `monthly_mrr(transactions_df, year_month: str)` → float
>    定義：該月所有交易總和（新增 + 續約），不含退款（amount > 0）。
>    例：monthly_mrr(transactions_clean, "2024-01") → 12500.0
>
> 2. `retention_rate(customers_df, transactions_df, cohort_month: str)` → float
>    定義：cohort_month 末付費客在下一個月末還有交易的百分比。
>    例：retention_rate(customers_clean, transactions_clean, "2024-01") → 0.85（85%）
>
> 3. `conversion_rate(customers_df, transactions_df)` → float
>    定義：至少有一筆交易的客戶數 / 總客戶數。
>    例：conversion_rate(customers_clean, transactions_clean) → 0.72（72%）
>
> 4. `arpu(customers_df, transactions_df, year_month: str)` → float
>    定義：該月交易額 / 該月末活躍客數。
>    例：arpu(customers_clean, transactions_clean, "2024-01") → 250.0
>
> 所有函式都用 pd.to_numeric(errors=coerce) 確保型別正確。

**PROMPT 引用**

```
為 metrics.py 實作四個指標計算函式：

def monthly_mrr(transactions_df: pd.DataFrame, year_month: str) -> float:
    """
    計算指定月份的月度經常性營收 (MRR)。
    定義：該月份所有交易總和（amount > 0 只計正值）。
    參數：
      transactions_df：已清理的交易 DataFrame，需欄位 [transaction_date, amount]
      year_month：格式 "YYYY-MM"，e.g. "2024-01"
    回傳：該月 MRR（單位 USD）
    """
    
def retention_rate(customers_df: pd.DataFrame, transactions_df: pd.DataFrame, cohort_month: str) -> float:
    """
    計算 cohort_month 月份的客戶在下個月的留存率。
    定義：(cohort_month 末曾付費且 next_month 末仍有交易的客戶) / (cohort_month 末付費客)
    回傳：0–1 之間的百分比
    """
    
def conversion_rate(customers_df: pd.DataFrame, transactions_df: pd.DataFrame) -> float:
    """
    計算客戶總轉換率。
    定義：(至少有 1 筆交易的客戶數) / (總客戶數)
    回傳：0–1 之間的百分比
    """
    
def arpu(customers_df: pd.DataFrame, transactions_df: pd.DataFrame, year_month: str) -> float:
    """
    計算該月平均每客營收 (ARPU)。
    定義：該月交易額 / 該月末活躍客數
    回傳：USD
    """

確保所有欄位型別都用 pd.to_numeric(errors=coerce) 轉換，並在函式內印出中間結果。
用 pytest 寫小資料集測試（見後文）。
```

**預期產出**

```python
# metrics.py 片段
import pandas as pd
from datetime import datetime

def monthly_mrr(transactions_df: pd.DataFrame, year_month: str) -> float:
    """
    計算該月 MRR。
    """
    transactions_df = transactions_df.copy()
    transactions_df['amount'] = pd.to_numeric(transactions_df['amount'], errors='coerce')
    transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
    
    mask = transactions_df['transaction_date'].dt.strftime('%Y-%m') == year_month
    mrr = transactions_df[mask]['amount'].sum()
    
    # 印出中間結果
    cohort_size = mask.sum()
    print(f"[MRR {year_month}] 交易數：{cohort_size}, 總額：{mrr}")
    
    return float(mrr)

# 其他三個函式類似...
```

### 5.2 驗收

先手動測試一個指標，確認邏輯對：

```bash
python -c "
import pandas as pd
from metrics import monthly_mrr

df = pd.read_csv('data/transactions_clean.csv')
mrr_jan = monthly_mrr(df, '2024-01')
print(f'2024-01 MRR: {mrr_jan}')
"
```

✅ **預期看到**：終端機印出 `[MRR 2024-01] 交易數：123, 總額：24560.5` 這種行。數字是虛的（Faker 生成），但格式對就代表函式有跑。

> ❓ **想一想**：MRR 用 amount > 0 過濾，但原始資料早就丟掉負值了（在 pipeline.py），為什麼還要再過濾一次？
>
> **答案**：防禦性編程——不相信上游的資料。就算 pipeline.py 說『已刪除負值』，指標函式也應該再檢查一次。二重防線。

---

## 6. 階段五：Streamlit 多頁面儀表板

### 6.1 檔案結構與快取設定

現在到最後一關——把這些乾淨資料和計算好的指標，用彩色圖表貼在『虛擬成績牆』上。這個牆會動：你拉篩選器，圖表即時跟著變。

對 Agent 說：

> 用 Streamlit 多頁面架構建儀表板（pages 資料夾）。
> 重點：
> - app.py 是首頁，引入 @st.cache_data
> - pages/ 資料夾建四個頁面
> - 所有頁面都定義同名同參數的 get_data()，這樣快取會共用
> - 不要在被 cache 的函式裡做排序或篩選，那樣會破壞快取
> - 所有中文字型用 plotly 的 font 設定，避免豆腐方塊

**PROMPT 引用**

```
用 Streamlit 多頁面建儀表板：

1. app.py（首頁）：
   - @st.cache_data def get_data() 讀客戶與交易資料
   - 顯示三張 KPI 卡片：總客戶、轉換率、本月 MRR
   - 可選：加一張「上月 vs 本月 MRR 成長率」卡片

2. pages/01_概覽.py：
   - 趨勢線圖（MRR 月度走勢）
   - MRR vs 客戶數對比

3. pages/02_客戶.py：
   - 客戶分佈（按 plan 的長條圖）
   - 註冊日期時間序列

4. pages/03_營收.py：
   - 營收分類（plan 別營收）
   - 交易金額分佈（直方圖）

5. pages/04_地區分析.py：
   - 地區營收排序切換（st.radio「按營收」vs「按客戶數」）
   - 確保切換時不重新讀檔（排序邏輯在快取外）

所有頁面都 import get_data from app 或重新定義，確保 @st.cache_data 生效。
所有 plotly 圖表都加中文字型設定：fig.update_layout(font=dict(family="Noto Sans TC, Microsoft JhengHei, sans-serif"))
```

**預期產出**

```python
# app.py
import streamlit as st
import pandas as pd
from metrics import monthly_mrr, conversion_rate

@st.cache_data
def get_data():
    customers = pd.read_csv('data/customers_clean.csv')
    transactions = pd.read_csv('data/transactions_clean.csv')
    st.write("[DEBUG] get_data() called - 只印一次代表快取生效")
    return customers, transactions

st.set_page_config(page_title="營運數據儀表板", layout="wide")
st.title("營運數據儀表板")

customers, transactions = get_data()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("總客戶", len(customers))
with col2:
    conv_rate = conversion_rate(customers, transactions)
    st.metric("轉換率", f"{conv_rate:.1%}")
with col3:
    # 取最近一個月 MRR（範例）
    st.metric("本月 MRR", "$12,500")

# pages/04_地區分析.py（示例排序快取外）
import streamlit as st
from app import get_data

customers, transactions = get_data()

# 假設有 region 欄位，按 region 聚合營收
region_revenue = transactions.groupby('region')['amount'].sum().reset_index()

sort_option = st.radio("排序方式", ["按營收", "按客戶數"])

if sort_option == "按營收":
    region_revenue = region_revenue.sort_values('amount', ascending=False)
else:
    # 按客戶數排序
    region_customer = customers.groupby('region').size().reset_index(name='count')
    region_revenue = region_revenue.merge(region_customer)
    region_revenue = region_revenue.sort_values('count', ascending=False)

# 圖表
import plotly.express as px
fig = px.bar(region_revenue, x='region', y='amount', title="地區營收")
fig.update_layout(font=dict(family="Noto Sans TC, Microsoft JhengHei, sans-serif"))
st.plotly_chart(fig, use_container_width=True)
```

### 6.2 快取驗證

在快取函式內加一行 debug log：

```python
@st.cache_data
def get_data():
    customers = pd.read_csv('data/customers_clean.csv')
    transactions = pd.read_csv('data/transactions_clean.csv')
    print("[DEBUG] 檔案讀取 - 如果你調整篩選器只印一次，代表快取生效")
    return customers, transactions
```

運行儀表板，切換頁面與篩選器，檢查 terminal 是否只印一次。

✅ **預期看到**：
```bash
streamlit run app.py
# 瀏覽器自動開 http://localhost:8501
# 首頁三個 KPI 卡片顯示數字
# 切換 pages/ 的頁面，terminal 看 [DEBUG] 訊息只印一次
# 拉篩選器，圖表順序改變但 [DEBUG] 還是只印一次
```

⭐ **一定要親自試的一幕**：開啟 localhost:8501，然後拉 pages/04 的「排序方式」radio button——看著圖表從「按營收排序」變「按客戶數排序」，柱子在眼前重新排列。同時檢查終端機「看，[DEBUG] 還是只印一次——代表檔案沒重讀」。

🧯 **卡住的話**：
- **Streamlit 找不到 pages 資料夾**：檔名是 `01_概覽.py` 嗎？有沒有底線？Streamlit 的 pages 資料夾很挑。重新檢查資料夾位置與命名。
- **[DEBUG] 印超過一次**：排序邏輯寫進 get_data() 裡了。移出去，放在 get_data() 外面。
- **中文字變豆腐方塊**：這時候別急著救。先秀預先準備的截圖，說「這是部署到雲端常見的問題」，然後解釋「為什麼本機正常但伺服器是方塊」、「怎麼在 Dockerfile 裡裝字型」——**這本身就是課程**。

### 6.3 中文字型排錯

若在本機測試正常但部署到 Linux 伺服器後圖表中文變豆腐方塊：

```bash
# 伺服器上
sudo apt-get install fonts-noto-cjk

# 確認安裝
fc-list | grep Noto
```

在所有 plotly 圖表都加一行：

```python
fig.update_layout(font=dict(family="Noto Sans TC, Microsoft JhengHei, sans-serif"))
```

---

## 7. 階段六：為指標寫 pytest

### 7.1 對 Agent 說

> 寫 test_metrics.py，為 metrics.py 的四個函式各寫一個 pytest。
> 要求：
> - 測試資料自己造，控制在 5–8 列以內（能心算驗證）
> - 每個測試的預期值都在註解裡寫出計算過程
> - 浮點數用 pytest.approx() 比較
> - 不要用實際資料集當斷言依據
>
> 例如 MRR 測試：
> 造 2024-01 有 3 筆交易（100, 200, -50），預期 MRR = 250（100+200）
> （-50 被濾掉）

**PROMPT 引用**

```
為 metrics.py 四個函式各寫一個 pytest。

要求格式：
```python
def test_monthly_mrr():
    """
    手算驗證：
    2024-01 交易：[100, 200, -50]
    MRR = 100 + 200 = 300 (負值濾掉)
    """
    transactions = pd.DataFrame({
        'transaction_date': ['2024-01-15', '2024-01-20', '2024-01-25'],
        'amount': [100, 200, -50]
    })
    result = monthly_mrr(transactions, '2024-01')
    assert result == pytest.approx(300.0)

# 其他三個測試類似
# 用 pytest.approx 比較浮點數
# 測試資料要能手算驗證
```

不要用 data/transactions_clean.csv 當測試依據，那不是測試，那是把當下結果抄下來。
```

### 7.2 驗收

```bash
uv run pytest test_metrics.py -v
# 應該全綠
```

修改一個指標的實作讓測試變紅，確認測試真的有效，再改回來。

✅ **預期看到**：
```
test_metrics.py::test_monthly_mrr PASSED
test_metrics.py::test_retention_rate PASSED
test_metrics.py::test_conversion_rate PASSED
test_metrics.py::test_arpu PASSED

====== 4 passed in 0.12s ======
```

看到 4 passed 了嗎？這四條綠線代表『你寫的指標計算函式，如果有人改壞了，測試會馬上告訴你』。一家正經的公司都這樣做——改程式碼前寫測試，改完了測試全綠，才敢上線。

---

## 8. 排錯情況：中文字全變豆腐方塊

### 發生的情況

部署到 Linux 伺服器（例如 Heroku、Render、自架伺服器）後，折線圖與長條圖的座標軸中文字全變成一格一格的方框。

### 怎麼處理

| 順序 | 動作 | 會看到什麼 |
|---|---|---|
| 1 | 先在本機確認顯示正常，鎖定是伺服器環境缺字型 | ✓ 本機 localhost:8501 中文正常 |
| 2 | 在伺服器或 Docker 安裝 fonts-noto-cjk 套件 | ✓ 字型裝完確認 fc-list \| grep Noto 有輸出 |
| 3 | 在每張圖表明確指定字型家族（不靠 matplotlib 默認） | ✓ 圖表更新後字型恢復 |

### 關鍵程式碼

```python
# 所有 plotly 圖表都要加這一行
fig.update_layout(
    font=dict(family="Noto Sans TC, Microsoft JhengHei, sans-serif"),
    title_font_size=20
)

st.plotly_chart(fig, use_container_width=True)
```

不要靠本機有微軟字體就不寫，部署環境沒有。**本機開發沒問題不代表部署環境也沒問題。**

> 🔍 **名詞卡：部署（deployment）**
> 白話：把你電腦上跑得好好的程式，搬到「雲端伺服器」或「別人的電腦」上。問題經常出現在這個時刻——你本機有字體，雲端伺服器沒有。

---

## 9. 情境演練：快取沒更新

### 情境

資料檔改了（customers_clean.csv 重新產生），但儀表板還是秀舊資料。

### 原因

@st.cache_data 的 key 是「函式簽章 + 參數」，不偵測檔案變更。第一次呼叫 get_data() 就被快取住，除非手動清快取或改參數。

### 解法

#### A. 開發時手動清快取

右上角漢堡選單 → Clear cache → Rerun

#### B. 生產部署用時間戳

```python
from datetime import datetime

@st.cache_data
def get_data(_version=datetime.now().strftime("%Y%m%d")):
    # _version 前綴底線代表 Streamlit 不把它當快取 key 的一部分
    # 但可以用它來強制重載
    return pd.read_csv('data/customers_clean.csv'), ...
```

每次部署重新啟動 Streamlit，`datetime.now()` 改變，快取自動失效。

---

## 10. 驗收清單

- [ ] `python generate_data.py` 產生 data/customers_raw.csv 與 data/transactions_raw.csv
- [ ] Ask Mode 看清資料品質（缺失值、型別、離群值統計）記在 DATA_QUALITY_REPORT.md
- [ ] `python pipeline.py` 清理完成，每一步都印出列數變化
- [ ] data/customers_clean.csv 與 data/transactions_clean.csv 列數比原始檔少（證明有清理）
- [ ] `python metrics.py` 或 `uv run pytest test_metrics.py -v` 四個指標測試全綠
- [ ] 手動驗證一個指標：用 10 列小資料自己算一遍，與函式結果一致
- [ ] `streamlit run app.py` 啟動儀表板，http://localhost:8501 開啟
- [ ] 首頁三個 KPI 卡片正常顯示
- [ ] 切換到 pages/ 的四個頁面都能載入，不報錯
- [ ] 調整篩選器時，terminal 看 `[DEBUG]` 只印一次（快取生效）
- [ ] 所有圖表都有中文字型設定（不怕豆腐方塊）
- [ ] 手機寬度查看儀表板，單欄佈局不跑版

---

## 11. 常見坑排錯速查表

| 問題 | 常見原因 | 解法 |
|---|---|---|
| 圖表中文變方框 | 伺服器缺中文字型 | 安裝 fonts-noto-cjk 並指定 font family |
| 快取沒更新 | cache_data 沒偵測到檔案變更 | 手動 Clear cache 或加時間戳 |
| amount 全變字串 | CSV 讀取時型別推斷錯誤 | 用 pd.to_numeric(errors=coerce) |
| 部署後套件報錯 | requirements.txt 沒鎖版本 | 用 `uv pip freeze > requirements.txt` 鎖版本 |
| Streamlit 找不到 pages | pages 資料夾命名不對 | 資料夾必須叫 `pages`，檔名 `01_*.py` 格式 |
| 指標數字對不上 | MRR 的「月份」切分標準不一致 | 統一用 strftime('%Y-%m')，不要自己算月 |
| pytest 浮點數斷言失敗 | 用 == 比較浮點數 | 改用 pytest.approx(result, rel=1e-5) |
| 頁面切換時重新讀檔 | 排序邏輯寫在被 cache 的函式內 | 排序要在快取外做，參數別加進 cache key |

---

## 12. 動手練習

### 練習 1：加一張「上月 vs 本月 MRR 成長率」卡片（約 20 分，入門）

**練的是**：用既有指標函式組出新指標，而不是另外寫一套算法。

**怎麼做**

1. 先用 metrics.py 的 monthly_mrr 取兩個月的值 → 拿得到兩個數字
2. 計算成長率並處理上月為 0 的情況 → 不會出現除以零
3. 用 st.metric 顯示數值與 delta → 漲跌方向自動上色
4. 手動抽一個月的資料自己算一次核對 → 兩邊數字一致

**完成標準**

- ✓ 百分比顯示正確，上月為 0 有處理
- ✓ 手算結果對得上

**常見卡點與怎麼救**

- 上月 MRR 為 0 時成長率是無限大，要顯示「—」或「新增」而不是報錯
- 月份切分用字串比對容易錯，統一轉成 period 或年月數字
- st.metric 的 delta 預設漲是綠、跌是紅，反向指標記得用 delta_color 反轉

**PROMPT**

```
在首頁加一張「MRR 月成長率」指標卡：用 metrics.py 既有的 monthly_mrr 取得上月與本月數值，
算出成長率並用 st.metric 顯示（含 delta）。上月為 0 時不要除以零，改顯示「—」。
另外印出上月與本月的原始數值，方便我手動核對。
```

### 練習 2：幫地區長條圖加上排序切換功能（約 20 分，入門）

**練的是**：Streamlit 的互動元件怎麼驅動圖表重繪，順便驗證快取有沒有被打壞。

**怎麼做**

1. 用 st.radio 提供依營收／依客戶數兩種排序 → 選項出現在圖表上方
2. 依選擇對 DataFrame 排序後再畫圖 → 順序即時改變
3. 確認切換時沒有重新讀檔清理 → cache 仍然命中
4. 在 get_data 裡加一行 log 驗證只印一次 → 證明快取生效

**完成標準**

- ✓ 兩種排序都正確，切換不需重整頁面
- ✓ log 只印一次（快取生效）

**常見卡點與怎麼救**

- 把排序寫進被 cache 的函式裡，會讓每次切換都重算，失去快取意義
- 排序後圖表順序沒變，多半是 plotly 自己又排了一次，要關掉自動排序
- log 印很多次代表 cache 沒命中，檢查函式簽章與參數是否一致

**PROMPT**

```
幫地區營收長條圖加上 st.radio 排序切換（依營收／依客戶數）。注意：排序要在快取函式之外做，
不要把排序邏輯放進被 @st.cache_data 裝飾的函式裡。另外在 get_data 內加一行 log ，
讓我可以確認切換排序時沒有重新讀檔清理資料。
```

### 練習 3：為四個指標函式各寫一個 pytest（約 30 分，中級）

**練的是**：用小到能心算的資料集寫測試，是防止 AI 統計幻覺最有效的方法。

**怎麼做**

1. 自己造 5–8 列的小資料，答案能手算 → 預期值先寫在註解裡
2. 為 MRR、留存率、轉換率、ARPU 各寫一個測試 → 四個測試都有明確斷言
3. 刻意改一個指標的實作讓測試變紅 → 確認測試真的有效
4. 改回來跑 `uv run pytest` 全綠 → 四個測試都通過

**完成標準**

- ✓ 四個指標各有測試，預期值有計算依據
- ✓ 改壞實作測試會紅

**常見卡點與怎麼救**

- 用全量資料寫斷言：那不是測試，那是把當下的結果抄下來
- 留存率的分母定義沒統一，測試和實作各算各的，永遠對不起來
- 浮點數直接用 == 比較會失敗，用 pytest.approx

**PROMPT**

```
為 metrics.py 的四個指標函式各寫一個 pytest。要求：測試資料自己造，控制在 8 列以內，
而且要在註解裡寫出手算的計算過程與預期值。浮點數比較用 pytest.approx。
不要用專案裡的實際資料集當斷言依據。
```

---

> 🎬 **要上台放映了？** 回頭看文件最前面的 [🎬 課堂放映表（講師用）](#-課堂放映表講師用)：課前 15 分鐘的六件事、八幕的時間軸與每一幕螢幕上該出現的數字、以及現場翻車的救援表，都在那一節。上課當天只要開一個終端機，跑 `./demo.sh` 就好。

---

## 13. 帶走的三句話

如果今天只能記住三件事，就這三句。

1. **用 Cursor 產生刻意帶瑕疵的合成資料，是練習清理管線最安全的方式**——Faker 可以精準控制缺失值、型別錯誤、離群值的比例，比用真實資料邊緣案例少但更可控。先在合成資料上驗證清理邏輯，再上真實資料。

2. **探索式分析要在 Ask Mode 先做一輪，才動手寫清理與指標程式碼**——看清資料的問題分佈（缺失率、離群值比例），決定策略後再清。盲目 dropna() 可能丟掉業務重要資料；盲目填充可能引入偏誤。

3. **清理管線每一步都該印出丟棄列數，四個指標的定義要全公司統一，@st.cache_data 搭配 pages 資料夾是多頁互動儀表板的標準做法**——前兩個是數據審計的基本功，第三個是避免 Streamlit 儀表板因重複讀檔變成龜速的必修。
