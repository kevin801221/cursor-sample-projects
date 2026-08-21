"""儀表板的共用資料層：@st.cache_data 快取 + 側邊欄篩選器 + 中文字型設定。

為什麼要有這支檔案（課堂重點）：
  @st.cache_data 的 key 是「函式所在模組 + 函式名 + 參數」。
  五個頁面如果各自定義一份 get_data()，就是五份快取、讀五次檔。
  把 get_data() 放在這裡讓所有頁面 import，全站共用同一份快取——
  這就是「切換頁面、拉篩選器，[DEBUG] 只印一次」的原因。

  另一個鐵則：**不要把排序／篩選寫進 get_data() 裡面**。
  讀檔（慢、結果固定）跟篩選（快、每次都不同）要分開快取，否則快取永遠不命中。

自我檢查（快取的威力，不用開瀏覽器）：
    uv run python data_access.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / "data"
CUSTOMERS_CSV = DATA_DIR / "customers_clean.csv"
TRANSACTIONS_CSV = DATA_DIR / "transactions_clean.csv"

# 中文字型 fallback 鏈：Linux 伺服器用 Noto、Windows 用微軟正黑、macOS 用蘋方／黑體。
# 少了這一行，部署到 Linux 之後圖表中文就是一排豆腐方塊 ▢▢▢。
FONT_FAMILY = "Noto Sans TC, Microsoft JhengHei, PingFang TC, Heiti TC, sans-serif"

PLAN_LABELS = {"starter": "starter（入門）", "pro": "pro（專業）", "enterprise": "enterprise（企業）"}


def apply_font(fig, title: str | None = None):
    """所有 plotly 圖表都要經過這一關：指定中文字型，順便統一標題大小。"""
    fig.update_layout(
        font=dict(family=FONT_FAMILY),
        title_font_size=20,
        margin=dict(t=60, l=10, r=10, b=10),
    )
    if title:
        fig.update_layout(title=title)
    return fig


@st.cache_data
def get_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """讀取清理後的資料（只做讀檔與型別轉換，不做任何篩選或排序）。"""
    print("[DEBUG] 檔案讀取 - 如果你調整篩選器只印一次，代表快取生效")

    if not CUSTOMERS_CSV.exists() or not TRANSACTIONS_CSV.exists():
        st.error("找不到清理後的資料。請先執行：uv run python generate_data.py && uv run python pipeline.py")
        st.stop()

    customers = pd.read_csv(CUSTOMERS_CSV, parse_dates=["signup_date"])
    transactions = pd.read_csv(TRANSACTIONS_CSV, parse_dates=["transaction_date"])
    transactions["amount"] = pd.to_numeric(transactions["amount"], errors="coerce")
    transactions["month"] = transactions["transaction_date"].dt.strftime("%Y-%m")
    customers["signup_month"] = customers["signup_date"].dt.strftime("%Y-%m")
    return customers, transactions


@st.cache_data
def filter_data(
    plans: tuple[str, ...], regions: tuple[str, ...], month_range: tuple[str, str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """依篩選條件切資料。參數都是 tuple（可雜湊）才進得了快取 key。"""
    customers, transactions = get_data()
    customers = customers[customers["plan"].isin(plans) & customers["region"].isin(regions)]
    start, end = month_range
    transactions = transactions[
        transactions["customer_id"].isin(set(customers["id"]))
        & transactions["month"].between(start, end)
    ]
    return customers, transactions


def all_months() -> list[str]:
    """資料裡出現過的所有月份（給篩選器當選項）。"""
    _, transactions = get_data()
    return sorted(transactions["month"].unique().tolist())


def sidebar_filters() -> tuple[pd.DataFrame, pd.DataFrame]:
    """每個頁面共用的側邊欄篩選器，回傳篩選後的 (customers, transactions)。"""
    customers, _ = get_data()
    months = all_months()

    with st.sidebar:
        st.header("篩選器")
        plan_options = sorted(customers["plan"].unique())
        plans = st.multiselect(
            "方案", plan_options, default=plan_options,
            format_func=lambda p: PLAN_LABELS.get(p, p),
        )
        region_options = sorted(customers["region"].unique())
        regions = st.multiselect("地區", region_options, default=region_options)
        month_range = st.select_slider(
            "月份區間", options=months, value=(months[0], months[-1]),
        )
        st.caption("篩選器只影響「篩選」這一層，讀檔那一層被 @st.cache_data 擋住了。")
        if st.button("清除快取並重新載入"):
            st.cache_data.clear()
            st.rerun()

    if not plans or not regions:
        st.warning("請至少選一個方案與一個地區。")
        st.stop()

    filtered = filter_data(tuple(plans), tuple(regions), tuple(month_range))
    if filtered[1].empty:
        st.warning("這組篩選條件沒有任何交易資料，請放寬條件。")
        st.stop()
    return filtered


def _benchmark() -> None:
    """課堂第 7 幕：同一個篩選切兩次，比較耗時，證明快取真的有用。"""
    import logging
    import time

    for name in list(logging.Logger.manager.loggerDict):       # 關掉 bare mode 的雜訊
        if name.startswith("streamlit"):
            logging.getLogger(name).setLevel(logging.ERROR)

    def timed(label: str) -> float:
        start = time.perf_counter()
        customers, transactions = filter_data(*args)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{label:<34}{elapsed:>8.2f} ms   （{len(customers)} 客戶 / {len(transactions)} 筆交易）")
        return elapsed

    print("=" * 66)
    print("  快取的威力：同一個篩選條件，連續切兩次")
    print("=" * 66)
    print("  準備動作：先讀一次資料抓出月份範圍，再把快取清空（下面才開始計時）")
    months = all_months()
    args = (("starter", "pro", "enterprise"), ("台北", "台中", "台南", "高雄", "新竹"),
            (months[0], months[-1]))
    get_data.clear()
    filter_data.clear()
    print("  （↑ 上面那行 [DEBUG] 是準備動作印的，快取已清空，計時從這裡才開始）")
    print()
    first = timed("第 1 次（讀檔 + 型別轉換 + 篩選）")
    second = timed("第 2 次（快取命中）")
    print("-" * 66)
    print(f"  快了 {first / max(second, 1e-6):.0f} 倍。第 2 次沒有再印 [DEBUG] → 檔案沒有重讀。")
    print()
    print("  現在手動清掉快取（等同儀表板右上角 Clear cache）再切一次：")
    get_data.clear()
    filter_data.clear()
    third = timed("第 3 次（快取清掉後）")
    print("-" * 66)
    print(f"  又變回 {third:.2f} ms，而且 [DEBUG] 又印了一次——證明剛剛的快就是快取的功勞。")


if __name__ == "__main__":
    _benchmark()
