"""營運數據儀表板：首頁（KPI 卡片）。

啟動：uv run streamlit run app.py   →   http://localhost:8501
左側「篩選器」會同時影響所有頁面；左上角可以切換 pages/ 裡的四個分頁。
"""

from __future__ import annotations

import streamlit as st

from data_access import get_data, sidebar_filters  # noqa: F401  (get_data 供其他頁面沿用)
from metrics import arpu, conversion_rate, monthly_mrr, retention_rate

st.set_page_config(page_title="營運數據儀表板", page_icon="📊", layout="wide")

st.title("營運數據儀表板")
st.caption("資料流程：Faker 產生髒資料 → pipeline.py 清理（每步記帳）→ metrics.py 算指標 → 這面牆")

customers, transactions = sidebar_filters()
latest_month = transactions["month"].max()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("總客戶", f"{len(customers):,}")
with col2:
    st.metric("轉換率", f"{conversion_rate(customers, transactions):.1%}")
with col3:
    st.metric(f"本月 MRR（{latest_month}）", f"${monthly_mrr(transactions, latest_month):,.0f}")

st.divider()

col4, col5 = st.columns(2)
with col4:
    st.metric(f"本月 ARPU（{latest_month}）", f"${arpu(customers, transactions, latest_month):,.1f}")
with col5:
    prev_month = sorted(transactions["month"].unique())[-2] if transactions["month"].nunique() > 1 else latest_month
    st.metric(f"上月留存率（{prev_month} → {latest_month}）",
              f"{retention_rate(customers, transactions, prev_month):.1%}")

with st.expander("四個指標的分母定義（全公司要用同一套，不然永遠對不起來）"):
    st.markdown(
        """
| 指標 | 分子 | 分母 |
|---|---|---|
| **MRR** | 該月 `amount > 0` 的交易總額 | 無（是總額不是平均） |
| **留存率** | 該月付費客中，下個月還有交易的人數 | 該月的付費客數（不是全部客戶） |
| **轉換率** | 至少有 1 筆付費交易的客戶數 | 客戶主表的相異客戶數（含從未付費的） |
| **ARPU** | 該月交易總額 | 該月的活躍客戶數（不是全部客戶） |

定義寫在 `metrics.py` 每個函式的 docstring，並用 `test_metrics.py` 的手算小資料鎖住。
        """
    )

st.subheader("清理後的資料長什麼樣")
tab1, tab2 = st.tabs(["客戶", "交易"])
with tab1:
    st.dataframe(customers.head(20), width="stretch")
with tab2:
    st.dataframe(transactions.head(20), width="stretch")

st.info("左側選單切換到「概覽 / 客戶 / 營收 / 地區分析」四個分頁；"
        "切換頁面時看終端機，`[DEBUG] 檔案讀取` 只會印一次，代表快取生效。")
