"""四個 SaaS 核心指標：MRR、留存率、轉換率、ARPU。

本課鐵律 3：**四個指標的分母定義要全公司統一**。
所以每個函式的 docstring 第一段就把「分子是什麼、分母是什麼」寫死，
配合 test_metrics.py 用 5–8 列可以手算的小資料驗證——實作改壞了測試會紅。

防禦性編程：就算 pipeline.py 說「負值已經刪掉了」，這裡每個函式還是會
再 pd.to_numeric(errors='coerce') 一次、再過濾一次 amount > 0。不相信上游資料。

執行：uv run python metrics.py   # 印出 2024 全年的指標總表
"""

from __future__ import annotations

import pandas as pd

# 印出中間結果（cohort_size、交易筆數…）方便課堂上核對。
# 反模式是「只看 Agent 給的結論不看過程」，所以預設打開。
VERBOSE = True


def _log(message: str) -> None:
    if VERBOSE:
        print(message)


def _prepare_transactions(transactions_df: pd.DataFrame) -> pd.DataFrame:
    """統一交易資料的型別，並加上 month 欄（YYYY-MM）。

    月份一律用 strftime('%Y-%m') 切，不要自己算月份——這是指標對不起來的頭號原因。
    """
    df = transactions_df.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df = df[df["transaction_date"].notna() & df["amount"].notna()]
    df["month"] = df["transaction_date"].dt.strftime("%Y-%m")
    return df


def _next_month(year_month: str) -> str:
    """'2024-01' → '2024-02'（跨年也對：'2024-12' → '2025-01'）。"""
    return str(pd.Period(year_month, freq="M") + 1)


def monthly_mrr(transactions_df: pd.DataFrame, year_month: str) -> float:
    """計算指定月份的月度經常性營收（MRR）。

    定義：
      分子 = 該月份所有 amount > 0 的交易金額總和（新客 + 續約，退款不算）
      分母 = 無（MRR 是總額，不是平均）

    參數：
      transactions_df：交易 DataFrame，需欄位 [transaction_date, amount]
      year_month：格式 "YYYY-MM"，例如 "2024-01"
    回傳：該月 MRR（USD）
    """
    df = _prepare_transactions(transactions_df)
    rows = df[(df["month"] == year_month) & (df["amount"] > 0)]
    mrr = float(rows["amount"].sum())
    _log(f"[MRR {year_month}] 交易數：{len(rows)}, 總額：{mrr:,.2f}")
    return mrr


def retention_rate(
    customers_df: pd.DataFrame, transactions_df: pd.DataFrame, cohort_month: str
) -> float:
    """計算 cohort_month 這批付費客在「下個月」的留存率。

    定義：
      分母 = cohort_month 當月有付費交易、且存在於客戶主表的客戶數（cohort_size）
      分子 = 這批人之中，下個月（cohort_month + 1）也有付費交易的客戶數
      → 分母是「上個月的付費客」，不是「全部客戶」。這個分母選錯，數字會漂亮很多但是假的。

    回傳：0–1 之間的比率（0.85 代表 85%）；分母為 0 時回傳 0.0
    """
    df = _prepare_transactions(transactions_df)
    paid = df[df["amount"] > 0]
    valid_ids = set(customers_df["id"])

    cohort = set(paid[paid["month"] == cohort_month]["customer_id"]) & valid_ids
    next_month = _next_month(cohort_month)
    next_actives = set(paid[paid["month"] == next_month]["customer_id"])
    retained = cohort & next_actives

    _log(f"[留存率 {cohort_month} → {next_month}] cohort_size：{len(cohort)}, "
         f"留下來：{len(retained)}")
    if not cohort:
        return 0.0
    return len(retained) / len(cohort)


def conversion_rate(customers_df: pd.DataFrame, transactions_df: pd.DataFrame) -> float:
    """計算客戶總轉換率（試用 → 付費）。

    定義：
      分母 = 客戶主表的相異客戶數（所有註冊帳號，含從未付費的）
      分子 = 至少有 1 筆 amount > 0 交易的相異客戶數
      → 分母是「所有註冊客戶」。若分母改用「有交易紀錄的客戶」，轉換率永遠是 100%。

    回傳：0–1 之間的比率；分母為 0 時回傳 0.0
    """
    df = _prepare_transactions(transactions_df)
    total = customers_df["id"].nunique()
    paid_ids = set(df[df["amount"] > 0]["customer_id"]) & set(customers_df["id"])

    _log(f"[轉換率] 付費客戶：{len(paid_ids)} / 總客戶：{total}")
    if total == 0:
        return 0.0
    return len(paid_ids) / total


def arpu(customers_df: pd.DataFrame, transactions_df: pd.DataFrame, year_month: str) -> float:
    """計算該月的平均每客營收（ARPU）。

    定義：
      分子 = 該月 amount > 0 的交易總額（＝ monthly_mrr）
      分母 = 該月有付費交易、且存在於客戶主表的相異客戶數（活躍客戶數）
      → 分母是「當月活躍客戶」，不是「全部客戶」。兩種算法都有人用，
        差異可以到好幾倍，所以定義必須全公司統一。

    回傳：USD／每位活躍客戶；分母為 0 時回傳 0.0
    """
    df = _prepare_transactions(transactions_df)
    rows = df[(df["month"] == year_month) & (df["amount"] > 0)]
    rows = rows[rows["customer_id"].isin(set(customers_df["id"]))]

    revenue = float(rows["amount"].sum())
    active = rows["customer_id"].nunique()
    _log(f"[ARPU {year_month}] 營收：{revenue:,.2f}, 活躍客戶：{active}")
    if active == 0:
        return 0.0
    return revenue / active


def month_list(transactions_df: pd.DataFrame) -> list[str]:
    """資料裡出現過的月份，由小到大（給儀表板的篩選器用）。"""
    return sorted(_prepare_transactions(transactions_df)["month"].unique().tolist())


def main() -> None:
    from pathlib import Path

    data_dir = Path(__file__).resolve().parent / "data"
    customers = pd.read_csv(data_dir / "customers_clean.csv")
    transactions = pd.read_csv(data_dir / "transactions_clean.csv")

    print("=" * 56)
    print("  單一指標的中間結果（課本 5.2 節的手動驗收）")
    print("=" * 56)
    monthly_mrr(transactions, "2024-01")
    retention_rate(customers, transactions, "2024-01")
    conversion_rate(customers, transactions)
    arpu(customers, transactions, "2024-01")

    global VERBOSE
    VERBOSE = False  # 印總表時把中間結果關掉，畫面才乾淨
    print()
    print("=" * 56)
    print("  2024 全年指標總表")
    print("=" * 56)
    print(f"{'月份':<10}{'MRR (USD)':>14}{'ARPU (USD)':>13}{'活躍客戶':>10}{'次月留存率':>12}")
    print("-" * 56)
    prepared = _prepare_transactions(transactions)
    for month in month_list(transactions):
        mrr = monthly_mrr(transactions, month)
        avg = arpu(customers, transactions, month)
        active = prepared[(prepared["month"] == month) & (prepared["amount"] > 0)][
            "customer_id"
        ].nunique()
        ret = retention_rate(customers, transactions, month)
        print(f"{month:<10}{mrr:>14,.0f}{avg:>13,.1f}{active:>10}{ret:>12.1%}")
    print("-" * 56)
    print(f"  總轉換率（付費客戶 / 全部客戶）：{conversion_rate(customers, transactions):.1%}")
    print("  ※ 最後一個月的留存率是 0.0%，因為沒有「下個月」的資料可以比——這不是 bug。")


if __name__ == "__main__":
    main()
