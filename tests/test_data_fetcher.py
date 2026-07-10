import pytest
from unittest.mock import patch, MagicMock
from data_fetcher import clean_price, match_laptop, scrape_generic

def test_clean_price():
    """Test cleaning raw price string to integer values."""
    assert clean_price("JD 780.00") == 780
    assert clean_price("650 JOD") == 650
    assert clean_price("1,250.50 JD") == 1250.5
    assert clean_price("JOD 80") == 80
    assert clean_price(None) is None
    assert clean_price("Out of Stock") is None

def test_match_laptop():
    """Test matching scraped titles to database items based on spec similarity scores."""
    laptops = [
        {
            "id": "laptop_01",
            "brand": "ASUS",
            "model": "TUF Gaming A15",
            "cpu": "AMD Ryzen 7 7735HS",
            "gpu": "NVIDIA GeForce RTX 4060 8GB",
            "ram": 16,
            "storage": 512,
            "screen_size": 15.6,
            "price_jod": 780,
            "use_cases": ["gaming"],
            "performance_level": "high",
            "portability": "medium"
        },
        {
            "id": "laptop_02",
            "brand": "Lenovo",
            "model": "ThinkPad E14 Gen 5",
            "cpu": "Intel Core i5-1335U",
            "gpu": "Integrated Intel Iris Xe Graphics",
            "ram": 8,
            "storage": 256,
            "screen_size": 14.0,
            "price_jod": 650,
            "use_cases": ["work"],
            "performance_level": "medium",
            "portability": "high"
        }
    ]

    # Strong match for ASUS TUF
    scraped_title_1 = "ASUS TUF A15 Gaming Laptop Ryzen 7 7735HS RTX 4060 16GB RAM 512GB SSD"
    match_1 = match_laptop(scraped_title_1, 780, "http://buy.com", "img", laptops)
    assert match_1 is not None
    assert match_1["id"] == "laptop_01"

    # Mismatched brand
    scraped_title_2 = "Dell TUF Gaming Laptop Ryzen 7 RTX 4060"
    match_2 = match_laptop(scraped_title_2, 780, "http://buy.com", "img", laptops)
    assert match_2 is None

    # Thinkpad match
    scraped_title_3 = "Lenovo ThinkPad E14 Gen 5 Core i5-1335U 8GB RAM 256GB SSD"
    match_3 = match_laptop(scraped_title_3, 630, "http://buy.com", "img", laptops)
    assert match_3 is not None
    assert match_3["id"] == "laptop_02"

@patch('requests.get')
@patch('data_fetcher.load_laptops')
@patch('data_fetcher.save_laptops')
def test_scrape_generic(mock_save, mock_load, mock_get):
    """Test WooCommerce generic scraping layout logic with mock HTML response."""
    # 1. Setup mock database
    mock_load.return_value = [
        {
            "id": "laptop_01",
            "brand": "ASUS",
            "model": "TUF Gaming A15",
            "cpu": "AMD Ryzen 7 7735HS",
            "gpu": "NVIDIA GeForce RTX 4060 8GB",
            "ram": 16,
            "storage": 512,
            "screen_size": 15.6,
            "price_jod": 780,
            "use_cases": ["gaming"]
        }
    ]
    mock_save.return_value = True

    # 2. Setup mock HTTP response with HTML content
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """
    <html>
        <div class="product-item">
            <h3 class="prod-title">ASUS TUF Gaming A15 Ryzen 7 RTX 4060 16gb</h3>
            <span class="prod-price">JD 760.00</span>
            <a class="prod-link" href="http://shop.com/product/asus-tuf-a15">View Details</a>
            <img class="prod-img" src="http://shop.com/product/asus-tuf-a15.jpg" />
        </div>
    </html>
    """
    mock_get.return_value = mock_response

    # 3. Run scraper
    success, count = scrape_generic(
        url_template="http://shop.com/laptops/page/{page}",
        product_selector=".product-item",
        title_selector=".prod-title",
        price_selector=".prod-price",
        link_selector=".prod-link",
        img_selector=".prod-img",
        pages=1
    )

    assert success is True
    assert count == 1
    
    updated_laptop = mock_load.return_value[0]
    assert updated_laptop["price_jod"] == 760
    assert updated_laptop["purchase_url"] == "http://shop.com/product/asus-tuf-a15"
