"""營收：方案別營收組成、交易金額分佈（離群值要看得見）。"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from data_access import apply_font, sidebar_filters

st.set_page_config(page_title="營收 | 營運數據儀表板", page_icon="💰", layout="wide")
st.title("營收")

customers, transactions = sidebar_filters()

# 交易表沒有 plan，用 customer_id 接回客戶表——這種 join 是儀表板最常見的動作
tx = transactions.merge(customers[["id", "plan"]], left_on="customer_id", right_on="id", how="inner")

st.subheader("方案別月營收")
by_plan = tx.groupby(["month", "plan"], as_index=False)["amount"].sum()
fig_plan = px.bar(by_plan, x="month", y="amount", color="plan", barmode="stack",
                  labels={"month": "月份", "amount": "營收 (USD)", "plan": "方案"})
st.plotly_chart(apply_font(fig_plan, "營收是誰貢獻的"), width="stretch")

st.subheader("交易金額分佈")
q1, q3 = transactions["amount"].quantile([0.25, 0.75])
upper = q3 + 1.5 * (q3 - q1)
fig_hist = px.histogram(transactions, x="amount", nbins=50,
                        labels={"amount": "交易金額 (USD)", "count": "交易筆數"})
fig_hist.add_vline(x=upper, line_dash="dash", line_color="crimson",
                   annotation_text=f"離群值界線 ${upper:,.0f}", annotation_position="top")
st.plotly_chart(apply_font(fig_hist, "大部分交易很小，少數大單撐起營收"), width="stretch")

outliers = transactions[transactions["amount"] > upper]
col1, col2, col3 = st.columns(3)
col1.metric("總營收", f"${transactions['amount'].sum():,.0f}")
col2.metric("離群交易筆數", f"{len(outliers):,}",
            help=f"IQR 法：> Q3 + 1.5×IQR = ${upper:,.0f}")
col3.metric("離群交易佔營收",
            f"{outliers['amount'].sum() / max(transactions['amount'].sum(), 1):.1%}")

st.warning("離群值沒有在 pipeline.py 被刪掉，是刻意的："
           f"這 {len(outliers):,} 筆大單佔了 "
           f"{outliers['amount'].sum() / max(transactions['amount'].sum(), 1):.0%} 的營收，"
           "手一滑用 3σ 全刪掉，等於把最重要的客戶從報表上抹掉。")
