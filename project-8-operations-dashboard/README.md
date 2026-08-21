# 營運數據儀表板 — pandas + Streamlit

> Cursor 課程 Project 8（第 29 章）：pandas + Streamlit。
> 一句話：**把髒資料清乾淨、算對指標，做成能互動的儀表板**——用 pandas 清理，Streamlit 多頁秀數據，@st.cache_data 避免重算。

## 專案規格

| | |
|---|---|
| **最終成果** | 含篩選器、四種圖表、匯出功能的營運數據儀表板 |
| **技術棧** | Python 3.12、pandas、plotly、Streamlit、st.cache_data |
| **預估時間** | 6–8 小時，含資料生成到部署的全部流程 |
| **前置需求** | 具備基本 pandas 操作經驗，已安裝 Cursor 與 uv |

## 這個儀表板做什麼

- 用 Faker 產生帶瑕疵的 SaaS 客戶與交易資料（CSV）
- 寫一條清理管線，每一步印出丟棄列數，確保資料品質
- 算出 MRR、留存率、轉換率、ARPU 四個關鍵指標
- Streamlit 多頁面儀表板：首頁數值卡片、客戶頁、營收頁、地區分析
- 篩選器驅動圖表重繪，快取確保切換不重新讀檔

## 資料流程

```
用 Faker 產生髒資料 (customers_raw.csv, transactions_raw.csv)
    ↓ Ask Mode 探索式分析：看缺失值與離群值統計
    ↓ 清理管線 (pipeline.py)：逐步過濾、標準化、驗證
    ↓ 乾淨 DataFrame (customers_clean.csv, transactions_clean.csv)
    ↓ 指標計算 (metrics.py)：MRR、留存率、轉換率、ARPU
    ↓ Streamlit 多頁面 (@st.cache_data 快取)
    → localhost:8501 可互動儀表板
```

## 四階段開發流程（先探索再清理，順序不能顛倒）

| 階段 | 做什麼 | 驗收 |
|---|---|---|
| 1. 產生資料 | Faker 生成帶瑕疵的 SaaS 資料 | 得到 customers_raw.csv 等檔案 |
| 2. 探索分析 | Ask Mode 讀 CSV 產出資料品質報告 | 看到缺失值與離群值統計 |
| 3. 清理管線 | 寫 pipeline.py 印出每步丟棄列數 | 得到乾淨的 DataFrame |
| 4. 算指標 | 實作 MRR、留存率、轉換率、ARPU | metrics.py 四個函式 |
| 5. 建儀表板 | Streamlit 多頁面加篩選器與圖表 | localhost:8501 可互動 |

## 專案結構

```
dashboard/
├── data/
│   ├── customers_raw.csv        # Faker 生成的原始客戶資料（帶瑕疵）
│   ├── transactions_raw.csv      # 原始交易資料
│   ├── customers_clean.csv       # 清理後的客戶資料
│   └── transactions_clean.csv    # 清理後的交易資料
├── generate_data.py              # 用 Faker 產生帶瑕疵資料
├── pipeline.py                   # 清理管線，每步印出丟棄列數
├── metrics.py                    # MRR、留存率、轉換率、ARPU
├── pages/
│   ├── 01_概覽.py                # 首頁：KPI 卡片與趨勢
│   ├── 02_客戶.py                # 客戶細節、分佈
│   ├── 03_營收.py                # 營收趨勢、分類
│   └── 04_地區分析.py            # 地區排序切換、長條圖
├── app.py                        # Streamlit 主頁面
├── pyproject.toml               # uv 專案配置
└── walkthrough.md               # 完整逐步教學
```

## 三條鐵律（本課核心）

1. **先探索、再清理、再算指標**——順序不能顛倒。Ask Mode 一輪探索式分析，看清資料問題後才動手寫清理與指標程式碼，不要盲目清理。
2. **清理管線每一步都該印出丟棄列數**——確認前後對得起來。數據審計靠這一招，不要默默丟掉一堆列。
3. **四個指標定義要全公司統一**——MRR、留存率、轉換率、ARPU 的分母不同會永遠對不起來。寫進註解，配合 pytest 驗證。

## 快速開始

```bash
# 用 uv 建環境與安裝套件
uv venv
source .venv/bin/activate
uv add pandas numpy faker streamlit plotly openpyxl loguru

# 產生資料
python generate_data.py

# 探索資料（Ask Mode）
# 對 Cursor 說：讀 data/customers_raw.csv 與 data/transactions_raw.csv，產出資料品質報告，包括缺失值、型別、離群值

# 清理資料
python pipeline.py

# 運行儀表板
streamlit run app.py
# 開啟 http://localhost:8501
```

> **補充**（uv 指令）：若原文範例用 `pip install`，改成 `uv add`；若用 `requirements.txt`，改成 `uv pip freeze > requirements.txt` 或直接 `uv sync`。

## 常見坑排錯速查

| 問題 | 常見原因 | 解法 |
|---|---|---|
| 圖表中文變方框 | 伺服器缺中文字型 | 安裝 fonts-noto-cjk 並在 plotly 指定字型 |
| 快取沒更新 | cache_data 沒偵測到檔案變更 | 手動 Clear cache 或在檔案路徑加時間戳 |
| amount 全變字串 | CSV 讀取時型別推斷錯誤 | 用 pd.to_numeric(errors=coerce) |
| 部署後套件報錯 | requirements.txt 沒鎖版本 | 用 uv pip list 對齊版本號 |

完整建置步驟、指標計算邏輯、快取設定與中文字型排錯，見 **[walkthrough.md](./walkthrough.md)**。
