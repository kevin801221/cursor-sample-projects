import time
from bs4 import BeautifulSoup
from loguru import logger
from src.compliance import RobotsChecker
from src.models import ProductPrice
from src.database import save_price_record, init_db
from src.notifier import TelegramNotifier
from src.mock_server import MOCK_PRODUCTS, render_product_page, ROBOTS_TXT

class PriceCrawler:
    def __init__(self):
        self.robots = RobotsChecker()
        self.robots.load_from_text(ROBOTS_TXT)
        self.notifier = TelegramNotifier()
        init_db()

    def crawl_mock_store(self, apply_discount: bool = False):
        logger.info("🚀 開始執行 PriceBot 批次商品爬取任務...")

        for p in MOCK_PRODUCTS:
            url = f"https://mock-shop.internal/products/{p['id']}"

            # 1. Compliance Check
            if not self.robots.can_fetch(url):
                continue

            # 2. Simulate fluctuating price
            current_p = p.copy()
            if apply_discount and p["id"] == "prod-002":
                current_p["price"] = 3980.0 # dropped from 4980 to 3980 (-20.1%)

            # 3. HTML Parse
            html = render_product_page(current_p)
            soup = BeautifulSoup(html, "html.parser")

            title_elem = soup.find(id="product-title")
            price_elem = soup.find(class_="price-value")
            stock_elem = soup.find(class_="stock-status")

            if not title_elem or not price_elem:
                logger.error(f"解析失敗：{url}")
                continue

            title = title_elem.get_text(strip=True)
            price = float(price_elem.get_text(strip=True))
            in_stock = "庫存充足" in stock_elem.get_text(strip=True)

            # 4. Pydantic Validation
            item = ProductPrice(
                product_id=p["id"],
                title=title,
                price=price,
                currency="TWD",
                in_stock=in_stock,
                url=url
            )

            # 5. Database Save & Price Drop Trigger
            alert = save_price_record(item)
            logger.info(f"📦 [紀錄完成] {item.title} -> NT$ {item.price}")

            if alert:
                self.notifier.send_price_drop_alert(alert)

            time.sleep(0.05) # Polite delay

        logger.success("✨ 爬取任務順利完成！")
