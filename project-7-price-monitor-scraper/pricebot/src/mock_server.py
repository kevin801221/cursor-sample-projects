"""
內建離線 Mock 電商商城
提供合規的 robots.txt 與 4 款具備價格變動的商品 HTML
"""

ROBOTS_TXT = """User-agent: *
Disallow: /admin/
Disallow: /cart/
Allow: /products/
"""

MOCK_PRODUCTS = [
    {
        "id": "prod-001",
        "title": "Logitech MX Master 3S 無線智能滑鼠",
        "price": 3290.0,
        "in_stock": True,
        "category": "周邊設備",
    },
    {
        "id": "prod-002",
        "title": "Keychron Q1 Pro 機械鍵盤 (茶軸)",
        "price": 4980.0,
        "in_stock": True,
        "category": "鍵盤",
    },
    {
        "id": "prod-003",
        "title": "LG 27 吋 4K UHD IPS 專業護眼螢幕",
        "price": 8990.0,
        "in_stock": True,
        "category": "顯示器",
    },
    {
        "id": "prod-004",
        "title": "Sony WH-1000XM5 無線降噪耳罩耳機",
        "price": 10900.0,
        "in_stock": True,
        "category": "耳機",
    },
]

def render_product_page(p: dict) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>{p['title']} - 測試商城</title></head>
    <body>
      <div class="product-detail">
        <h1 id="product-title">{p['title']}</h1>
        <div class="price-box">
          <span class="currency">NT$</span>
          <span class="price-value" data-pid="{p['id']}">{p['price']}</span>
        </div>
        <div class="stock-status">{'庫存充足' if p['in_stock'] else '缺貨中'}</div>
      </div>
    </body>
    </html>
    """
