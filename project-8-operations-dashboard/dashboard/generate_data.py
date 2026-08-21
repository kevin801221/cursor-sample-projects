"""用 Faker 產生「刻意帶瑕疵」的 SaaS 合成資料。

課堂重點：
1. 固定亂數種子（SEED）＋固定日期區間 → 每次跑出來的 CSV 一模一樣，課堂可重現。
2. 瑕疵是「精準注入」的，不是碰運氣：缺失值、重複列、amount 混進字串、
   離群值、日期格式不一、email 大小寫不一、地區名稱髒——每一種都對應
   pipeline.py 的一個清理步驟。
3. 產出 data/customers_raw.csv（500 列）與 data/transactions_raw.csv（2000 列）。

執行：uv run python generate_data.py
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# 課堂可重現的常數：改了這裡，全班的數字才會一起變
# ---------------------------------------------------------------------------
SEED = 20240101
N_CUSTOMERS = 500          # 總列數（含 10 列重複）
N_TRANSACTIONS = 2000      # 總列數（含 15 列重複）

# 資料區間固定在 2024 全年——walkthrough 裡示範的 monthly_mrr(df, "2024-01")
# 才會真的算得出數字。不要改成 date.today()，那樣課本上的數字會對不起來。
DATA_START = date(2024, 1, 1)
DATA_END = date(2024, 12, 31)
SIGNUP_START = date(2023, 1, 1)

PLANS = ["starter", "pro", "enterprise"]
PLAN_PRICE = {"starter": 49, "pro": 149, "enterprise": 499}   # 月費（USD）
PAYING_RATIO = 0.72        # 只有 72% 的註冊客戶真的付錢 → 轉換率大約落在 70%
MONTHLY_RETENTION = 0.87   # 每個月有 13% 的付費客流失 → 留存率大約落在 80% 上下
REGIONS = ["台北", "台中", "台南", "高雄", "新竹"]

# 同一個地區的「髒寫法」——真實系統裡不同表單、不同年代的資料就長這樣
REGION_DIRTY = {
    "台北": [" 台北", "台北 ", "臺北", "Taipei", "taipei", "台北市"],
    "台中": ["台中 ", "臺中", "Taichung", "taichung ", "台中市"],
    "台南": [" 台南", "臺南", "Tainan", "tainan", "台南市"],
    "高雄": ["高雄 ", "Kaohsiung", "kaohsiung", "高雄市", " 高雄"],
    "新竹": ["新竹 ", "Hsinchu", "hsinchu", "新竹市", " 新竹"],
}

DATA_DIR = Path(__file__).resolve().parent / "data"

fake = Faker()
Faker.seed(SEED)
rnd = fake.random          # Faker 內建的 Random，已被 Faker.seed 固定


def _fmt_date(d: date, style: int) -> str:
    """同一個日期的三種寫法——這就是「日期格式不一」的瑕疵。"""
    if style == 0:
        return d.isoformat()              # 2024-03-05
    if style == 1:
        return d.strftime("%Y/%m/%d")     # 2024/03/05
    return f"{d.year}年{d.month:02d}月{d.day:02d}日"  # 2024年03月05日


def _dirty_email(email: str) -> str:
    """大小寫不一 ＋ 前後空白，兩種最常見的 email 髒法。"""
    return rnd.choice([f"  {email.upper()}", f"{email.title()} ", f" {email} "])


def _sample_index(k: int, pool: list[int]) -> list[int]:
    """從 pool 取 k 個不重複的索引，取完就從 pool 移除（確保各種瑕疵不互相覆蓋）。"""
    picked = rnd.sample(pool, k)
    for i in picked:
        pool.remove(i)
    return picked


def make_customers() -> tuple[pd.DataFrame, pd.DataFrame]:
    """500 列客戶資料，欄位 [id, email, signup_date, plan, region]。

    回傳 (帶瑕疵的 df, 乾淨的 meta)。meta 是「真相」，只給 make_transactions 用，
    不會寫進 CSV——學生拿到的檔案裡只有髒資料。
    """
    # 註冊日期刻意偏向後半段（u ** 0.6），這樣 MRR 走勢才會是成長曲線而不是雜訊
    span = (DATA_END - SIGNUP_START).days
    signup_dates = [
        SIGNUP_START + timedelta(days=int(span * rnd.random() ** 0.6)) for _ in range(N_CUSTOMERS)
    ]
    rows = []
    for i in range(N_CUSTOMERS):
        rows.append(
            {
                "id": i + 1,
                "email": fake.email(),
                "signup_date": _fmt_date(signup_dates[i], 0),
                "plan": rnd.choice(PLANS),
                "region": rnd.choice(REGIONS),
            }
        )
    df = pd.DataFrame(rows)
    meta = df[["id", "plan", "region"]].copy()
    meta["signup_month"] = [d.strftime("%Y-%m") for d in signup_dates]

    pool = list(range(N_CUSTOMERS))
    flaws: dict[str, int] = {}

    # 瑕疵 1：30% 客戶沒有 email（缺失值）
    idx = _sample_index(int(N_CUSTOMERS * 0.30), pool)
    df.loc[idx, "email"] = None
    flaws["email 缺失"] = len(idx)

    # 瑕疵 2：email 大小寫不一 ＋ 前後空白
    idx = _sample_index(60, pool)
    df.loc[idx, "email"] = [_dirty_email(e) for e in df.loc[idx, "email"]]
    flaws["email 大小寫/空白"] = len(idx)

    # 瑕疵 3：plan 大小寫不一
    idx = _sample_index(45, pool)
    df.loc[idx, "plan"] = [rnd.choice([p.upper(), p.title(), f" {p} "]) for p in df.loc[idx, "plan"]]
    flaws["plan 大小寫/空白"] = len(idx)

    # 瑕疵 4：日期格式不一（2024/03/05、2024年03月05日）
    idx = _sample_index(120, pool)
    for i in idx:
        d = signup_dates[i]
        df.loc[i, "signup_date"] = _fmt_date(d, rnd.choice([1, 2]))
    flaws["signup_date 格式不一"] = len(idx)

    # 瑕疵 5：地區名稱髒（Taipei / 臺北 / 台北市 / 前後空白）
    dirty_idx = rnd.sample(range(N_CUSTOMERS), 200)
    for i in dirty_idx:
        df.loc[i, "region"] = rnd.choice(REGION_DIRTY[df.loc[i, "region"]])
    flaws["region 名稱髒"] = len(dirty_idx)

    # 瑕疵 6：10 列完全重複（覆蓋既有列，總列數維持 500）
    src = rnd.sample(range(N_CUSTOMERS), 10)
    dst = rnd.sample([i for i in range(N_CUSTOMERS) if i not in src], 10)
    for s, d_ in zip(src, dst):
        df.loc[d_] = df.loc[s].copy()
    flaws["完全重複列"] = len(dst)

    _print_flaws("customers_raw.csv", len(df), flaws)
    return df, meta


def make_transactions(meta: pd.DataFrame) -> pd.DataFrame:
    """2000 列交易資料，欄位 [customer_id, transaction_date, amount, region]。

    不是亂灑的隨機交易，而是「訂閱制」的形狀：
      - 只有 PAYING_RATIO 的客戶真的付錢（其他人是免費試用 → 轉換率的分母）
      - 付費客從註冊那個月開始，每個月扣一次款，直到某個月流失（MONTHLY_RETENTION）
    這樣 MRR 走勢、留存率、ARPU 才會像真的 SaaS，圖表也才有東西可以講。
    """
    months = [f"{DATA_START.year}-{m:02d}" for m in range(DATA_START.month, DATA_END.month + 1)]
    plan_of = dict(zip(meta["id"], meta["plan"]))
    region_of = dict(zip(meta["id"], meta["region"]))
    start_of = dict(zip(meta["id"], meta["signup_month"]))
    payer_ids = sorted(rnd.sample(meta["id"].tolist(), int(N_CUSTOMERS * PAYING_RATIO)))

    def _charge(cid: int, month: str, amount: int) -> dict:
        year, mon = int(month[:4]), int(month[5:])
        return {
            "customer_id": cid,
            "transaction_date": _fmt_date(date(year, mon, rnd.randint(1, 28)), 0),
            "amount": amount,
            "region": region_of[cid],
        }

    rows: list[dict] = []
    for cid in payer_ids:
        price = PLAN_PRICE[plan_of[cid]]
        first = True
        for month in months:
            if month < start_of[cid]:
                continue
            if not first and rnd.random() > MONTHLY_RETENTION:
                break                      # 這個月流失，之後就不再扣款
            rows.append(_charge(cid, month, round(price * rnd.uniform(0.9, 1.15))))
            first = False

    # 校正到剛好 N_TRANSACTIONS 列：多了就隨機丟、少了就補「加購」交易
    while len(rows) > N_TRANSACTIONS:
        rows.pop(rnd.randrange(len(rows)))
    while len(rows) < N_TRANSACTIONS:
        base = rows[rnd.randrange(len(rows))]
        rows.append(_charge(base["customer_id"], base["transaction_date"][:7],
                            round(base["amount"] * rnd.uniform(0.3, 0.8))))

    df = pd.DataFrame(rows)

    pool = list(range(N_TRANSACTIONS))
    flaws: dict[str, int] = {}

    # 瑕疵 1：10% 離群值（500–5000 USD 的大單）
    idx = _sample_index(int(N_TRANSACTIONS * 0.10), pool)
    df.loc[idx, "amount"] = [rnd.randint(500, 5000) for _ in idx]
    flaws["amount 離群值(500–5000)"] = len(idx)

    # 瑕疵 2：10% 負值（退款？誤輸入？課堂上要討論的就是這個）
    idx = _sample_index(int(N_TRANSACTIONS * 0.10), pool)
    df.loc[idx, "amount"] = [-abs(a) for a in df.loc[idx, "amount"]]
    flaws["amount 負值"] = len(idx)

    # 瑕疵 3：amount 混進字串——有的救得回來（"1,250"、"NT$380"），有的救不回來（"待確認"、空值）
    df["amount"] = df["amount"].astype(object)
    idx = _sample_index(30, pool)
    df.loc[idx, "amount"] = [f"{rnd.randint(1000, 5000):,}" for _ in idx]
    flaws['amount 字串 "1,250"'] = len(idx)

    idx = _sample_index(20, pool)
    df.loc[idx, "amount"] = [f"NT${abs(int(a))}" for a in df.loc[idx, "amount"]]
    flaws['amount 字串 "NT$380"'] = len(idx)

    idx = _sample_index(15, pool)
    df.loc[idx, "amount"] = "待確認"
    flaws['amount 字串 "待確認"'] = len(idx)

    idx = _sample_index(10, pool)
    df.loc[idx, "amount"] = None
    flaws["amount 缺失"] = len(idx)

    # 瑕疵 4：5% 孤立 customer_id（501–510，客戶主表裡根本沒有這些人）
    idx = _sample_index(int(N_TRANSACTIONS * 0.05), pool)
    df.loc[idx, "customer_id"] = [rnd.randint(501, 510) for _ in idx]
    flaws["孤立 customer_id(>500)"] = len(idx)

    # 瑕疵 5：日期格式不一
    idx = _sample_index(300, pool)
    for i in idx:
        d = date.fromisoformat(df.loc[i, "transaction_date"])
        df.loc[i, "transaction_date"] = _fmt_date(d, rnd.choice([1, 2]))
    flaws["transaction_date 格式不一"] = len(idx)

    # 瑕疵 6：地區名稱髒
    dirty_idx = rnd.sample(range(N_TRANSACTIONS), 700)
    for i in dirty_idx:
        clean = df.loc[i, "region"]
        if clean in REGION_DIRTY:
            df.loc[i, "region"] = rnd.choice(REGION_DIRTY[clean])
    flaws["region 名稱髒"] = len(dirty_idx)

    # 瑕疵 7：15 列完全重複（覆蓋既有列，總列數維持 2000）
    src = rnd.sample(range(N_TRANSACTIONS), 15)
    dst = rnd.sample([i for i in range(N_TRANSACTIONS) if i not in src], 15)
    for s, d_ in zip(src, dst):
        df.loc[d_] = df.loc[s].copy()
    flaws["完全重複列"] = len(dst)

    _print_flaws("transactions_raw.csv", len(df), flaws)
    return df


def _print_flaws(name: str, total: int, flaws: dict[str, int]) -> None:
    print(f"\n{'=' * 56}")
    print(f"  {name}：共 {total} 列，故意注入的瑕疵如下")
    print("=" * 56)
    for k, v in flaws.items():
        print(f"  {k:<28} {v:>5} 列 ({v / total:>5.1%})")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    customers, meta = make_customers()
    transactions = make_transactions(meta)

    customers.to_csv(DATA_DIR / "customers_raw.csv", index=False)
    transactions.to_csv(DATA_DIR / "transactions_raw.csv", index=False)

    print(f"\n已寫出 {DATA_DIR / 'customers_raw.csv'}（{len(customers)} 列）")
    print(f"已寫出 {DATA_DIR / 'transactions_raw.csv'}（{len(transactions)} 列）")
    print("下一步：先探索（uv run python pipeline.py --report），再清理（uv run python pipeline.py）")


if __name__ == "__main__":
    main()
