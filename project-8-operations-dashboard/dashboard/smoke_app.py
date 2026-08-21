"""上課前的保命檢查：用 Streamlit 官方的 AppTest 把五個頁面都跑一遍。

不開瀏覽器，直接在終端機確認「首頁 + 四個分頁」都不會噴例外。
課堂前 30 秒跑這個，比在投影機前面才發現頁面壞掉好得多。

執行：uv run python smoke_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))          # 讓 pages/*.py 裡的 `import data_access` 找得到模組

from streamlit.testing.v1 import AppTest  # noqa: E402

PAGES = [
    "app.py",
    "pages/01_概覽.py",
    "pages/02_客戶.py",
    "pages/03_營收.py",
    "pages/04_地區分析.py",
]


def main() -> int:
    print("=" * 56)
    print("  儀表板頁面自我檢查（不開瀏覽器）")
    print("=" * 56)
    failed = 0
    for page in PAGES:
        app = AppTest.from_file(str(HERE / page), default_timeout=60).run()
        if app.exception:
            failed += 1
            print(f"  ✗ {page:<22} 例外：{app.exception[0].message}")
            continue
        widgets = len(app.multiselect) + len(app.radio) + len(app.select_slider)
        print(f"  ✓ {page:<22} 圖表 {len(app.get('plotly_chart'))} 張、"
              f"KPI 卡片 {len(app.metric)} 張、互動元件 {widgets} 個")
    print("-" * 56)
    if failed:
        print(f"  {failed} 個頁面壞掉了。先修好再上課。")
        return 1
    print("  五個頁面全部正常，可以 streamlit run app.py 了。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
