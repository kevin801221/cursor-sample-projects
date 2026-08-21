import pytest
from src.compliance import RobotsChecker
from src.models import ProductPrice
from src.database import save_price_record, init_db, get_all_products

def test_robots_compliance():
    checker = RobotsChecker()
    mock_robots = """User-agent: *
Disallow: /admin/
Allow: /products/
"""
    checker.load_from_text(mock_robots)
    assert checker.can_fetch("https://mock-shop.internal/products/prod-001") is True
    assert checker.can_fetch("https://mock-shop.internal/admin/settings") is False

def test_pydantic_product_model():
    item = ProductPrice(
        product_id="prod-test",
        title="  無線機械鍵盤  ",
        price=2999.0,
        currency="TWD",
        in_stock=True,
        url="https://shop.com/test",
    )
    assert item.title == "無線機械鍵盤"
    assert item.price == 2999.0

def test_price_history_and_drop_alert():
    init_db()

    # 1. Normal price
    item1 = ProductPrice(
        product_id="prod-test-alert",
        title="電競耳機",
        price=5000.0,
        currency="TWD",
        in_stock=True,
        url="https://shop.com/prod-test",
    )
    alert1 = save_price_record(item1)
    assert alert1 is None # First time no alert

    # 2. Price drop (-20%)
    item2 = ProductPrice(
        product_id="prod-test-alert",
        title="電競耳機",
        price=4000.0,
        currency="TWD",
        in_stock=True,
        url="https://shop.com/prod-test",
    )
    alert2 = save_price_record(item2)
    assert alert2 is not None
    assert alert2.old_price == 5000.0
    assert alert2.new_price == 4000.0
    assert alert2.drop_percentage == 20.0
