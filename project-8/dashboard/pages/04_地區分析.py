"""地區分析：排序切換示範——排序邏輯放在快取之外，切換不會重新讀檔。"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from data_access import apply_font, sidebar_filters

st.set_page_config(page_title="地區分析 | 營運數據儀表板", page_icon="🗺️", layout="wide")
st.title("地區分析")

customers, transactions = sidebar_filters()

# 這兩行都在快取之外：資料本身（get_data）被快取，聚合與排序每次重算，很便宜
region_revenue = transactions.groupby("region", as_index=False)["amount"].sum()
region_customer = customers.groupby("region").size().reset_index(name="客戶數")
region = region_revenue.merge(region_customer, on="region", how="outer").fillna(0)
region["每客營收"] = region["amount"] / region["客戶數"].replace(0, 1)

sort_option = st.radio("排序方式", ["按營收", "按客戶數"], horizontal=True)

if sort_option == "按營收":
    region = region.sort_values("amount", ascending=False)
    y_col, y_label = "amount", "營收 (USD)"
else:
    region = region.sort_values("客戶數", ascending=False)
    y_col, y_label = "客戶數", "客戶數"

fig = px.bar(region, x="region", y=y_col, color="region", text_auto=".2s",
             labels={"region": "地區", y_col: y_label})
fig.update_layout(showlegend=False)
# 關掉 plotly 的自動排序，不然你在上面排好的順序會被它重排回去
fig.update_xaxes(categoryorder="array", categoryarray=region["region"].tolist())
st.plotly_chart(apply_font(fig, f"地區{sort_option[1:]}排行"), width="stretch")

st.dataframe(
    region.rename(columns={"region": "地區", "amount": "營收 (USD)"}),
    width="stretch",
)

st.download_button(
    "匯出地區彙總 CSV",
    data=region.to_csv(index=False).encode("utf-8-sig"),
    file_name="region_summary.csv",
    mime="text/csv",
)

st.success("⭐ 現在切換上面的「排序方式」，柱子會重新排列——"
           "但去看終端機，`[DEBUG] 檔案讀取` 還是只印過一次。"
           "因為排序寫在 @st.cache_data 外面，只有排序重算，檔案沒有重讀。")
