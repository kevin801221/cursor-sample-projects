"""metrics.py 的四個指標測試——資料小到可以用心算驗證。

反模式：拿 data/transactions_clean.csv 的當下結果當斷言依據。
那不是測試，那是把今天的答案抄下來。

執行：uv run pytest test_metrics.py -v
"""

import pandas as pd
import pytest

from metrics import arpu, conversion_rate, monthly_mrr, retention_rate


def test_monthly_mrr():
    """手算驗證：
    2024-01 交易：[100, 200, -50]，2024-02 有一筆 999（不該被算進來）
    MRR = 100 + 200 = 300（負值濾掉、別的月份不算）
    """
    transactions = pd.DataFrame({
        "customer_id": [1, 2, 3, 4],
        "transaction_date": ["2024-01-15", "2024-01-20", "2024-01-25", "2024-02-01"],
        "amount": [100, 200, -50, 999],
    })
    assert monthly_mrr(transactions, "2024-01") == pytest.approx(300.0)


def test_retention_rate():
    """手算驗證：
    2024-01 有付費的客戶（分母）：1, 2, 3 → cohort_size = 3
      （客戶 4 在 2024-01 只有負值交易，不算付費客）
    這三人在 2024-02 還有交易的（分子）：1, 2 → 2 人
      （客戶 5 在 2024-02 有交易，但不在 cohort 裡，不能加進分子）
    留存率 = 2 / 3 = 0.6667
    """
    customers = pd.DataFrame({"id": [1, 2, 3, 4, 5]})
    transactions = pd.DataFrame({
        "customer_id": [1, 2, 3, 4, 1, 2, 5],
        "transaction_date": [
            "2024-01-05", "2024-01-06", "2024-01-07", "2024-01-08",
            "2024-02-05", "2024-02-06", "2024-02-07",
        ],
        "amount": [100, 100, 100, -100, 50, 50, 50],
    })
    assert retention_rate(customers, transactions, "2024-01") == pytest.approx(2 / 3)


def test_conversion_rate():
    """手算驗證：
    客戶主表 5 人（分母 = 5，包含從來沒付過錢的）
    有付費交易的相異客戶：1, 2（分子 = 2）
      （客戶 3 只有一筆 -30 的退款，不算付費）
    轉換率 = 2 / 5 = 0.4
    """
    customers = pd.DataFrame({"id": [1, 2, 3, 4, 5]})
    transactions = pd.DataFrame({
        "customer_id": [1, 1, 2, 3],
        "transaction_date": ["2024-01-01", "2024-02-01", "2024-01-02", "2024-01-03"],
        "amount": [100, 100, 200, -30],
    })
    assert conversion_rate(customers, transactions) == pytest.approx(0.4)


def test_arpu():
    """手算驗證：
    2024-01 營收（分子）= 100 + 200 + 300 = 600
    2024-01 活躍客戶（分母）= 客戶 1 與客戶 2 = 2 人（客戶 1 有兩筆，只算一個人）
    ARPU = 600 / 2 = 300.0
    注意分母不是「全部 4 位客戶」——那樣會算成 150，差一倍。
    """
    customers = pd.DataFrame({"id": [1, 2, 3, 4]})
    transactions = pd.DataFrame({
        "customer_id": [1, 1, 2, 3],
        "transaction_date": ["2024-01-10", "2024-01-11", "2024-01-12", "2024-02-01"],
        "amount": [100, 200, 300, 999],
    })
    assert arpu(customers, transactions, "2024-01") == pytest.approx(300.0)
