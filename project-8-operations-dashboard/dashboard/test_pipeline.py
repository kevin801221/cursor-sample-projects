"""pipeline.py 的清理邏輯測試——每個標準化函式一個，加上一個端到端的列數審計。

執行：uv run pytest test_pipeline.py -v
（跑 `uv run pytest` 會連 test_metrics.py 一起跑，共 8 個測試）
"""

import pandas as pd

from pipeline import clean_amount_text, clean_data, normalize_date, normalize_region


def test_normalize_region():
    """五種髒寫法都要收斂成同一個標準名稱。"""
    for dirty in [" 台北", "台北 ", "臺北", "Taipei", "taipei", "台北市"]:
        assert normalize_region(dirty) == "台北"
    assert normalize_region(None) == "未知"


def test_normalize_date():
    """三種日期寫法統一成 ISO 格式，pd.to_datetime 才吃得下。"""
    assert normalize_date("2024-03-05") == "2024-03-05"
    assert normalize_date("2024/03/05") == "2024-03-05"
    assert normalize_date("2024年03月05日") == "2024-03-05"
    assert normalize_date("2024年3月5日") == "2024-03-05"


def test_clean_amount_text():
    """救得回來的字串要救回來，救不回來的原封不動交給 to_numeric 變 NaN。"""
    assert clean_amount_text("NT$380") == "380"
    assert clean_amount_text("1,250") == "1250"
    assert clean_amount_text(" 420 ") == "420"
    assert clean_amount_text("待確認") == "待確認"          # 救不回來
    assert pd.to_numeric(clean_amount_text("待確認"), errors="coerce") != pd.to_numeric("380")


def test_clean_data_drops_expected_rows():
    """端到端的列數審計（手算）：

    客戶 3 列：id 1, 2, 2（第 3 列跟第 2 列完全重複）→ 清完剩 2 列
    交易 6 列：
      1. id=1  400      → 留
      2. id=1  "NT$100" → 留（字串救得回來 = 100）
      3. id=2  -50      → 丟（負值）
      4. id=99 300      → 丟（孤立 customer_id）
      5. id=2  "待確認" → 丟（金額不是數字）
      6. id=1  400      → 丟（跟第 1 列完全重複）
    → 清完剩 2 列，總金額 400 + 100 = 500
    """
    customers = pd.DataFrame({
        "id": [1, 2, 2],
        "email": ["A@X.com ", None, None],
        "signup_date": ["2024-01-01", "2024/02/01", "2024/02/01"],
        "plan": ["PRO", " starter ", " starter "],
        "region": ["Taipei", "臺中", "臺中"],
    })
    transactions = pd.DataFrame({
        "customer_id": [1, 1, 2, 99, 2, 1],
        "transaction_date": ["2024-01-05", "2024-01-06", "2024-01-07",
                             "2024-01-08", "2024年01月09日", "2024-01-05"],
        "amount": [400, "NT$100", -50, 300, "待確認", 400],
        "region": ["台北市", "台北 ", "台中", "高雄", "臺中", "台北市"],
    })

    clean_customers, clean_transactions = clean_data(customers, transactions)

    assert len(clean_customers) == 2
    assert clean_customers["plan"].tolist() == ["pro", "starter"]
    assert clean_customers["region"].tolist() == ["台北", "台中"]
    assert clean_customers["email"].tolist() == ["a@x.com", "unknown@company.com"]

    assert len(clean_transactions) == 2
    assert clean_transactions["amount"].sum() == 500
