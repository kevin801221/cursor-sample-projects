import streamlit as st
import pandas as pd
from src.database import get_all_products, get_product_history, init_db
from src.crawler import PriceCrawler

st.set_page_config(page_title="PriceBot 價格監控儀表板", page_icon="🛒", layout="wide")

init_db()

st.title("🛒 PriceBot 價格監控與歷史趨勢儀表板")
st.caption("合法合規 Python 爬蟲管線 · SQLite 價格歷史庫 · Telegram 降價即時告警")

# Sidebar Controls
st.sidebar.header("🕹️ 爬蟲控制台")
if st.sidebar.button("🚀 執行常規爬取 (抓取最新價格)", use_container_width=True):
    crawler = PriceCrawler()
    crawler.crawl_mock_store(apply_discount=False)
    st.sidebar.success("✓ 爬取完成！已更新資料庫")
    st.rerun()

if st.sidebar.button("💥 模擬商品特價降價 (觸發 Telegram 告警)", use_container_width=True):
    crawler = PriceCrawler()
    crawler.crawl_mock_store(apply_discount=True)
    st.sidebar.success("🚨 已注入特價價格，並觸發降價告警通知！")
    st.rerun()

# KPI Row
products = get_all_products()

if not products:
    st.info("💡 目前資料庫尚無爬取資料，請點擊側邊欄「🚀 執行常規爬取」開始第一輪抓取！")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("監控商品數", f"{len(products)} 件")
    c2.metric("在售庫存率", "100%")
    c3.metric("爬蟲合規狀態", "100% (遵守 robots.txt)")
    c4.metric("通知系統", "Telegram Bot 連線中")

    st.markdown("---")

    # Product Table
    st.subheader("📦 目前監控中商品清單")
    df_prod = pd.DataFrame(products)
    st.dataframe(
        df_prod[["product_id", "title", "current_price", "lowest_price", "highest_price", "currency", "updated_at"]],
        use_container_width=True,
    )

    st.markdown("---")

    # History Chart
    st.subheader("📈 商品價格歷史趨勢分析")
    selected_prod = st.selectbox(
        "選擇要分析的商品：",
        options=[p["product_id"] for p in products],
        format_func=lambda x: f"{x} - {next((p['title'] for p in products if p['product_id'] == x), '')}"
    )

    if selected_prod:
        history = get_product_history(selected_prod)
        if history:
            df_hist = pd.DataFrame(history)
            df_hist["scraped_at"] = pd.to_datetime(df_hist["scraped_at"])
            st.line_chart(df_hist.set_index("scraped_at")["price"])
