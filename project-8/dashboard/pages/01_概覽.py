"""概覽：MRR 月度走勢，以及 MRR 與活躍客戶數的對比。"""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from data_access import apply_font, sidebar_filters

st.set_page_config(page_title="概覽 | 營運數據儀表板", page_icon="📈", layout="wide")
st.title("概覽")

customers, transactions = sidebar_filters()

monthly = (
    transactions.groupby("month", as_index=False)
    .agg(MRR=("amount", "sum"), 交易數=("amount", "size"), 活躍客戶=("customer_id", "nunique"))
    .sort_values("month")
)

st.subheader("MRR 月度走勢")
fig_trend = px.line(monthly, x="month", y="MRR", markers=True,
                    labels={"month": "月份", "MRR": "MRR (USD)"})
fig_trend.update_traces(line=dict(width=3))
st.plotly_chart(apply_font(fig_trend, "月度經常性營收（MRR）"), width="stretch")

st.subheader("MRR vs 活躍客戶數")
fig_cmp = make_subplots(specs=[[{"secondary_y": True}]])
fig_cmp.add_trace(go.Bar(x=monthly["month"], y=monthly["MRR"], name="MRR (USD)"), secondary_y=False)
fig_cmp.add_trace(
    go.Scatter(x=monthly["month"], y=monthly["活躍客戶"], name="活躍客戶數",
               mode="lines+markers", line=dict(width=3)),
    secondary_y=True,
)
fig_cmp.update_yaxes(title_text="MRR (USD)", secondary_y=False)
fig_cmp.update_yaxes(title_text="活躍客戶數", secondary_y=True)
fig_cmp.update_xaxes(title_text="月份")
st.plotly_chart(apply_font(fig_cmp, "營收與客戶數要一起看"), width="stretch")

st.caption("營收上升但客戶數沒動 → 是少數大客戶撐的；客戶數上升但營收沒動 → 新客都在最便宜的方案。")

st.dataframe(monthly, width="stretch")
