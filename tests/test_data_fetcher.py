import pytest
from unittest.mock import patch, MagicMock
from data_fetcher import clean_price, scrape_generic

def test_clean_price():
    """Test cleaning raw price string to integer values."""
    assert clean_price("JD 780.00") == 780
    assert clean_price("650 JOD") == 650
    assert clean_price("1,250.50 JD") == 1250.5
    assert clean_price("JOD 80") == 80
    assert clean_price(None) is None
    assert clean_price("Out of Stock") is None

@patch('requests.get')
def test_scrape_generic(mock_get):
    """Test WooCommerce generic scraping layout logic with mock HTML response."""
    # Setup mock HTTP response with HTML content
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

    # Run scraper
    results = scrape_generic(
        url_template="http://shop.com/laptops/page/{page}",
        product_selector=".product-item",
        title_selector=".prod-title",
        price_selector=".prod-price",
        link_selector=".prod-link",
        img_selector=".prod-img",
        shop_id=1,
        pages=1
    )

    assert len(results) == 1
    
    scraped = results[0]
    assert scraped["price_jod"] == 760
    assert scraped["purchase_url"] == "http://shop.com/product/asus-tuf-a15"
    assert scraped["title"] == "ASUS TUF Gaming A15 Ryzen 7 RTX 4060 16gb"
    assert scraped["shop_id"] == 1

def laptopSurveyTest():
    
        def check_laptop(ram, storage, processor_score, min_price, max_price):
                laptops = ["Lenovo IdeaPad 3 - 15.6 inch FHD, AMD Ryzen 7 5700U, 8GB RAM, 512GB SSD, Windows 11",
                        "Dell XPS 13 - 13.4 inch FHD, Intel Core i7-1255U, 16GB RAM, 1TB SSD, Windows 11",
                       "MacBook Air M1 - 13.3 inch Retina, 8GB RAM, 256GB SSD, macOS Big Sur",
                       "HP Pavilion 15 - 15.6 inch FHD, AMD Ryzen 5 5500U, 8GB RAM, 256GB SSD, Windows 11",
                       "Acer Aspire 5 - 15.6 inch FHD, Intel Core i5-1135G7, 8GB RAM, 512GB SSD, Windows 11"]

        for laptop in laptops:
            features = parse_features(laptop)
            ram_ok = features["ram"] >= ram
            storage_ok = features["storage_gb"] >= storage
            processor_ok = features["processor_score"] >= processor_score
            price_ok = features["price_jod"] >= min_price and features["price_jod"] <= max_price

            status = "✓ PASS" if (ram_ok and storage_ok and processor_ok and price_ok) else "✗ FAIL"
            print(f"{status} | {laptop}")

    # Test case from video
        print("--- Testing Lenovo IdeaPad 3 requirement (8GB RAM, 512GB SSD, Ryzen 7, 600-900 JOD) ---")
        check_laptop(8, 512, 21000, 600, 900)

    