"""清理管線：把 data/*_raw.csv 洗成 data/*_clean.csv。

本課鐵律 2：**每一步都印出丟棄列數**。
所以這裡每個清理步驟都會印出「清理前 → 去掉幾列（為什麼）→ 清理後」，
終端機輸出可以直接投影給全班看——200 筆交易被丟掉是多少錢，看到數字才有感覺。

用法：
    uv run python pipeline.py            # 執行清理，寫出 *_clean.csv
    uv run python pipeline.py --report   # 只做探索（前 10 列 + 資料品質報告），不清理
    uv run python pipeline.py --trap     # 示範 amount 型別陷阱：壞掉的版本 vs 修好的版本
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

DATA_DIR = Path(__file__).resolve().parent / "data"
LOG_FILE = Path(__file__).resolve().parent / "pipeline.log"

# 地區別名對照表：左邊那些髒寫法，通通收斂成右邊的標準名稱
REGION_ALIASES = {
    "台北": "台北", "臺北": "台北", "台北市": "台北", "taipei": "台北",
    "台中": "台中", "臺中": "台中", "台中市": "台中", "taichung": "台中",
    "台南": "台南", "臺南": "台南", "台南市": "台南", "tainan": "台南",
    "高雄": "高雄", "高雄市": "高雄", "kaohsiung": "高雄",
    "新竹": "新竹", "新竹市": "新竹", "hsinchu": "新竹",
}

# 中文日期 2024年03月05日 / 2024/03/05 → 2024-03-05
_DATE_CN = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")

logger.remove()
logger.add(sys.stdout, format="{message}", level="INFO")
logger.add(LOG_FILE, format="{time:YYYY-MM-DD HH:mm:ss} | {message}", level="INFO", mode="w")


# ---------------------------------------------------------------------------
# 標準化小工具
# ---------------------------------------------------------------------------
def normalize_region(value) -> str:
    """把髒地區名（' 台北 '、'Taipei'、'臺北'、'台北市'）收斂成標準名稱。"""
    if pd.isna(value):
        return "未知"
    key = str(value).strip()
    return REGION_ALIASES.get(key.lower(), REGION_ALIASES.get(key, key))


def normalize_date(value) -> str:
    """統一日期字串格式：2024/03/05、2024年03月05日 → 2024-03-05。"""
    if pd.isna(value):
        return value
    text = str(value).strip()
    text = _DATE_CN.sub(lambda m: f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", text)
    return text.replace("/", "-")


def clean_amount_text(value):
    """把 'NT$380'、'1,250'、' 420 ' 這種還救得回來的字串洗成純數字字串。

    洗不動的（'待確認'、空值）原封不動回傳，交給 pd.to_numeric(errors='coerce') 變 NaN。
    """
    if pd.isna(value):
        return value
    text = str(value).strip().replace(",", "").replace("NT$", "").replace("$", "")
    return text


# ---------------------------------------------------------------------------
# 每一步都要看得見的列數審計
# ---------------------------------------------------------------------------
_step_no = 0


def _step(title: str, before: int, after: int, reason: str, drops: bool = True) -> None:
    """鐵律 2 的具體長相：清理前 → 去掉幾列（為什麼）→ 清理後。

    drops=False 代表這一步是「標準化」，本來就不該丟列——但列數還是要印，
    因為「以為不會丟卻丟了」正是最該被抓到的意外。
    """
    global _step_no
    _step_no += 1
    dropped = before - after
    logger.info(f"  【步驟 {_step_no}】{title}")
    logger.info(f"     清理前：{before} 列")
    if drops:
        logger.info(f"     去掉「{reason}」：-{dropped} 列")
    else:
        logger.info(f"     沒有丟列：{reason}")
    logger.info(f"     清理後：{after} 列")
    logger.info("")


def _banner(text: str) -> None:
    logger.info("=" * 56)
    logger.info(f"  {text}")
    logger.info("=" * 56)


# ---------------------------------------------------------------------------
# 探索階段：資料品質報告（先看清楚，再決定怎麼清）
# ---------------------------------------------------------------------------
def quality_report(df: pd.DataFrame, name: str) -> None:
    """印出一張資料品質診斷書：缺失值、型別、重複列、離群值。"""
    _banner(f"{name} 資料品質報告（{len(df)} 列 × {len(df.columns)} 欄）")
    logger.info(f"{'欄位':<20}{'型別':<12}{'缺失值':>8}{'缺失率':>9}{'相異值':>8}")
    logger.info("-" * 56)
    for col in df.columns:
        missing = int(df[col].isna().sum())
        logger.info(
            f"{col:<20}{str(df[col].dtype):<12}{missing:>8}{missing / len(df):>9.1%}{df[col].nunique():>8}"
        )
    logger.info("")
    logger.info(f"  完全重複列：{int(df.duplicated().sum())} 列")

    if "amount" in df.columns:
        numeric = pd.to_numeric(df["amount"], errors="coerce")
        bad = int(numeric.isna().sum() - df["amount"].isna().sum())
        q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
        upper = q3 + 1.5 * (q3 - q1)
        logger.info(f"  amount 無法轉成數字（混進字串）：{bad} 列")
        logger.info(f"  amount 負值：{int((numeric < 0).sum())} 列（{(numeric < 0).mean():.1%}）")
        logger.info(
            f"  amount 統計：min={numeric.min():.0f} max={numeric.max():.0f} "
            f"mean={numeric.mean():.1f} std={numeric.std():.1f}"
        )
        logger.info(f"  amount 離群值（IQR 法，> {upper:.0f}）：{int((numeric > upper).sum())} 列")

    if "region" in df.columns:
        logger.info(f"  region 相異寫法：{df['region'].nunique()} 種 → 標準化後會剩 "
                    f"{df['region'].map(normalize_region).nunique()} 種")
    logger.info("")


def explore() -> None:
    """--report：課堂第一幕「先看髒資料長什麼樣」。"""
    customers = pd.read_csv(DATA_DIR / "customers_raw.csv")
    transactions = pd.read_csv(DATA_DIR / "transactions_raw.csv")

    _banner("customers_raw.csv 前 10 列（原汁原味的髒資料）")
    logger.info(customers.head(10).to_string())
    logger.info("")
    _banner("transactions_raw.csv 前 10 列")
    logger.info(transactions.head(10).to_string())
    logger.info("")

    quality_report(customers, "客戶")
    quality_report(transactions, "交易")

    orphan = ~transactions["customer_id"].isin(set(customers["id"]))
    _banner("跨表檢查")
    logger.info(f"  transactions.customer_id 在客戶主表找不到的：{int(orphan.sum())} 列 "
                f"（{orphan.mean():.1%}）")
    logger.info("")
    logger.info("→ 看清楚問題了，才開始寫清理邏輯：uv run python pipeline.py")


# ---------------------------------------------------------------------------
# 型別陷阱示範：壞掉的版本 vs 修好的版本
# ---------------------------------------------------------------------------
def trap_demo() -> None:
    """--trap：amount 混進字串時，直接 sum() 會發生什麼事。"""
    transactions = pd.read_csv(DATA_DIR / "transactions_raw.csv")

    _banner("反模式：不看型別就直接加總")
    logger.info("  程式碼：transactions['amount'].sum()")
    logger.info(f"  amount 欄位的 dtype：{transactions['amount'].dtype}"
                "（不是 float64！整欄被當成字串處理了）")
    try:
        total = transactions["amount"].sum()
        preview = str(total)
        logger.info(f"  結果：{preview[:80]}…")
        logger.info(f"  ↑ 沒報錯，但這是一個 {len(preview):,} 個字元的字串——"
                    "字串被『相加』串起來了，不是金額")
    except TypeError as exc:
        logger.info(f"  結果：TypeError: {exc}")
        logger.info("  ↑ 整條管線在這裡當掉。老闆的儀表板打不開。")
    logger.info("")

    _banner("正確做法：先洗字串，再 pd.to_numeric(errors='coerce')")
    logger.info("  程式碼：pd.to_numeric(amount.map(clean_amount_text), errors='coerce')")
    numeric = pd.to_numeric(transactions["amount"].map(clean_amount_text), errors="coerce")
    logger.info(f"  轉換後 dtype：{numeric.dtype}")
    logger.info(f"  救得回來的字串：{int(numeric.notna().sum() - pd.to_numeric(transactions['amount'], errors='coerce').notna().sum())} 列")
    logger.info(f"  救不回來變 NaN：{int(numeric.isna().sum())} 列（等一下會在管線裡被丟掉並記帳）")
    logger.info(f"  總金額（含負值）：{numeric.sum():,.0f}")
    logger.info("")
    logger.info("→ 這就是為什麼 metrics.py 裡每個函式都再 to_numeric 一次：不相信上游資料。")


# ---------------------------------------------------------------------------
# 清理管線本體
# ---------------------------------------------------------------------------
def clean_data(df_customers: pd.DataFrame, df_transactions: pd.DataFrame):
    """清理客戶與交易資料，每一步都印出列數變化。

    回傳：(乾淨的客戶 DataFrame, 乾淨的交易 DataFrame)
    """
    global _step_no
    _step_no = 0
    df_customers = df_customers.copy()      # 不動到呼叫端的原始 DataFrame
    df_transactions = df_transactions.copy()

    _banner("清理客戶資料")
    logger.info(f"  客戶資料原始列數：{len(df_customers)}")
    logger.info("")

    # 步驟 1：email 標準化 + 缺失值填充（不丟列，但要講清楚填了幾列）
    before = len(df_customers)
    missing_email = int(df_customers["email"].isna().sum())
    df_customers["email"] = (
        df_customers["email"].astype("string").str.strip().str.lower()
        .fillna("unknown@company.com")
    )
    _step("email 標準化（去空白、轉小寫）+ 缺失值填成 unknown@company.com",
          before, len(df_customers), f"改成填充 {missing_email} 列缺失 email", drops=False)

    # 步驟 2：plan 標準化
    before = len(df_customers)
    df_customers["plan"] = df_customers["plan"].astype("string").str.strip().str.lower()
    _step("plan 標準化（' Pro ' / 'STARTER' → 'pro' / 'starter'）",
          before, len(df_customers), f"收斂成 {df_customers['plan'].nunique()} 種方案", drops=False)

    # 步驟 3：region 標準化
    before_variants = df_customers["region"].nunique()
    df_customers["region"] = df_customers["region"].map(normalize_region)
    _step("region 標準化（Taipei / 臺北 / 台北市 → 台北）",
          len(df_customers), len(df_customers),
          f"{before_variants} 種寫法收斂成 {df_customers['region'].nunique()} 種", drops=False)

    # 步驟 4：日期格式統一 + 無法解析的丟棄
    before = len(df_customers)
    df_customers["signup_date"] = pd.to_datetime(
        df_customers["signup_date"].map(normalize_date), errors="coerce"
    )
    df_customers = df_customers[df_customers["signup_date"].notna()]
    _step("signup_date 格式統一（2024/03/05、2024年03月05日 → 2024-03-05）",
          before, len(df_customers), "日期無法解析")

    # 步驟 5：完全重複列
    before = len(df_customers)
    df_customers = df_customers.drop_duplicates()
    _step("刪除完全重複列", before, len(df_customers), "整列一模一樣")

    # 步驟 6：同一個 id 出現多次（保留第一筆）
    before = len(df_customers)
    df_customers = df_customers.drop_duplicates(subset=["id"], keep="first")
    _step("刪除重複 id（保留第一筆）", before, len(df_customers), "id 重複")

    logger.info(f"  客戶資料：{len(df_customers)} 列（原始 500 列）")
    logger.info("")

    _banner("清理交易資料")
    logger.info(f"  交易資料原始列數：{len(df_transactions)}")
    logger.info("")

    # 步驟 7：region 標準化
    before_variants = df_transactions["region"].nunique()
    df_transactions["region"] = df_transactions["region"].map(normalize_region)
    _step("region 標準化", len(df_transactions), len(df_transactions),
          f"{before_variants} 種寫法收斂成 {df_transactions['region'].nunique()} 種", drops=False)

    # 步驟 8：日期格式統一
    before = len(df_transactions)
    df_transactions["transaction_date"] = pd.to_datetime(
        df_transactions["transaction_date"].map(normalize_date), errors="coerce"
    )
    df_transactions = df_transactions[df_transactions["transaction_date"].notna()]
    _step("transaction_date 格式統一", before, len(df_transactions), "日期無法解析")

    # 步驟 9：amount 字串救援（"NT$380"、"1,250" → 380、1250）
    before_numeric = pd.to_numeric(df_transactions["amount"], errors="coerce").notna().sum()
    df_transactions["amount"] = pd.to_numeric(
        df_transactions["amount"].map(clean_amount_text), errors="coerce"
    )
    rescued = int(df_transactions["amount"].notna().sum() - before_numeric)
    _step("amount 字串救援（去掉 NT$ 與千分位逗號）",
          len(df_transactions), len(df_transactions), f"救回 {rescued} 列本來會變 NaN 的金額", drops=False)

    # 步驟 10：amount 無法轉成數字的丟棄
    before = len(df_transactions)
    df_transactions = df_transactions[df_transactions["amount"].notna()]
    _step("刪除 amount 無法轉成數字的列（'待確認'、空值）",
          before, len(df_transactions), "amount 不是數字")

    # 步驟 11：負值 amount
    before = len(df_transactions)
    dropped_money = float(df_transactions.loc[df_transactions["amount"] <= 0, "amount"].sum())
    df_transactions = df_transactions[df_transactions["amount"] > 0]
    _step("刪除 amount <= 0 的列（退款或誤輸入）",
          before, len(df_transactions),
          f"金額非正數，金額合計 {dropped_money:,.0f} USD——真的要丟嗎？先問業務")

    # 步驟 12：孤立 customer_id
    before = len(df_transactions)
    valid_ids = set(df_customers["id"])
    df_transactions = df_transactions[df_transactions["customer_id"].isin(valid_ids)]
    _step("刪除孤立 customer_id（客戶主表查無此人）",
          before, len(df_transactions), "customer_id 不存在 customers")

    # 步驟 13：完全重複列
    before = len(df_transactions)
    df_transactions = df_transactions.drop_duplicates()
    _step("刪除完全重複列", before, len(df_transactions), "整列一模一樣")

    # 離群值：只報告、不刪除——離群值裡常常是最重要的大客戶
    q1, q3 = df_transactions["amount"].quantile([0.25, 0.75])
    upper = q3 + 1.5 * (q3 - q1)
    outliers = df_transactions[df_transactions["amount"] > upper]
    logger.info(f"  【不刪除】離群值（> {upper:,.0f} USD）：{len(outliers)} 列，"
                f"合計 {outliers['amount'].sum():,.0f} USD")
    logger.info("     離群值裡面常常是最重要的大客戶，刪掉就等於刪掉營收——只標記不刪除。")
    logger.info("")
    logger.info(f"  交易資料：{len(df_transactions)} 列（原始 2000 列）")
    logger.info("")

    return df_customers, df_transactions


def main() -> None:
    customers = pd.read_csv(DATA_DIR / "customers_raw.csv")
    transactions = pd.read_csv(DATA_DIR / "transactions_raw.csv")

    raw_customers, raw_transactions = len(customers), len(transactions)
    customers, transactions = clean_data(customers, transactions)

    customers.to_csv(DATA_DIR / "customers_clean.csv", index=False)
    transactions.to_csv(DATA_DIR / "transactions_clean.csv", index=False)

    _banner("清理完成！")
    logger.info(f"  客戶：{raw_customers} → {len(customers)} 列 "
                f"（保留 {len(customers) / raw_customers:.1%}）")
    logger.info(f"  交易：{raw_transactions} → {len(transactions)} 列 "
                f"（保留 {len(transactions) / raw_transactions:.1%}）")
    logger.info(f"  寫出：{DATA_DIR / 'customers_clean.csv'}")
    logger.info(f"  寫出：{DATA_DIR / 'transactions_clean.csv'}")
    logger.info(f"  完整日誌：{LOG_FILE}")


if __name__ == "__main__":
    if "--report" in sys.argv:
        explore()
    elif "--trap" in sys.argv:
        trap_demo()
    else:
        main()
