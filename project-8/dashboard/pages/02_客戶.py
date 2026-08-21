"""客戶：方案分佈、註冊時間序列、客戶明細（可匯出 CSV）。"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from data_access import apply_font, sidebar_filters

st.set_page_config(page_title="客戶 | 營運數據儀表板", page_icon="🧑‍💼", layout="wide")
st.title("客戶")

customers, transactions = sidebar_filters()

col1, col2 = st.columns(2)

with col1:
    st.subheader("方案分佈")
    plan_counts = customers.groupby("plan", as_index=False).size().rename(columns={"size": "客戶數"})
    fig_plan = px.bar(plan_counts.sort_values("客戶數", ascending=False),
                      x="plan", y="客戶數", color="plan", text="客戶數",
                      labels={"plan": "方案"})
    fig_plan.update_layout(showlegend=False)
    st.plotly_chart(apply_font(fig_plan, "各方案客戶數"), width="stretch")

with col2:
    st.subheader("累積註冊客戶數")
    signups = customers.groupby("signup_month", as_index=False).size().rename(columns={"size": "新增客戶"})
    signups = signups.sort_values("signup_month")
    signups["累積客戶"] = signups["新增客戶"].cumsum()
    fig_signup = px.area(signups, x="signup_month", y="累積客戶",
                         labels={"signup_month": "註冊月份"})
    st.plotly_chart(apply_font(fig_signup, "客戶是怎麼長起來的"), width="stretch")

st.subheader("客戶明細（含累計消費）")
revenue = (
    transactions.groupby("customer_id", as_index=False)
    .agg(累計消費=("amount", "sum"), 交易數=("amount", "size"))
)
detail = (
    customers.merge(revenue, left_on="id", right_on="customer_id", how="left")
    .drop(columns=["customer_id"])
    .fillna({"累計消費": 0, "交易數": 0})
    .sort_values("累計消費", ascending=False)
)
st.dataframe(detail, width="stretch", height=360)

st.download_button(
    "匯出客戶明細 CSV",
    data=detail.to_csv(index=False).encode("utf-8-sig"),  # utf-8-sig：Excel 打開才不會亂碼
    file_name="customers_detail.csv",
    mime="text/csv",
)
st.caption(f"目前篩選條件下有 {len(detail):,} 位客戶，其中 {(detail['交易數'] == 0).sum():,} 位從未付費——"
           "這些人就是轉換率的分母裡拉低數字的那群。")
