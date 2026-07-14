import logging
from unittest.mock import patch
from ml_pipeline import LaptopRecommenderPipeline
from data_fetcher import scrape_all_shops

logging.basicConfig(level=logging.INFO)


@patch("ml_pipeline.filter_laptops")
@patch("ml_pipeline.get_connection")
def test_pipeline(mock_get_connection, mock_filter_laptops):
    print("--- Testing ML Pipeline ---")
    pref = {
        "budget": 800,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "Any"
    }
    laptop = {
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
        "portability": "medium",
        "shop_offers": [{"product_url": "http://example.com/buy"}],
    }

    class _Cursor:
        def fetchone(self):
            return {"c": 1}

    class _Conn:
        def execute(self, *_args, **_kwargs):
            return _Cursor()

        def close(self):
            return None

    mock_filter_laptops.return_value = [laptop]
    mock_get_connection.return_value = _Conn()

    pipeline = LaptopRecommenderPipeline()
    pipeline._db_ready = True
    recommendations = pipeline.get_recommendations(pref)
    print(f"Recommendations for gaming (800 JOD): {len(recommendations.get('recommendations', []))} laptops found.")
    assert recommendations["winning_model"] == "hard_filter_weighted_score"
    assert len(recommendations.get("recommendations", [])) == 1
    top = recommendations['recommendations'][0]
    print(f"Top Pick: {top['brand']} {top['model']} - {top['price_jod']} JOD")
    assert top["brand"] == "ASUS"


@patch("data_fetcher.scrape_generic")
def test_scraper(mock_scrape_generic):
    print("\n--- Testing Scraper ---")
    mock_scrape_generic.side_effect = [(True, 2), (False, 0), (True, 1)]
    success, count = scrape_all_shops()
    print(f"Scraper Success: {success}, Updated: {count}")
    assert success is True
    assert count == 3

if __name__ == "__main__":
    try:
        test_pipeline()
    except Exception as e:
        print(f"Pipeline Test Failed: {e}")
        
    try:
        test_scraper()
    except Exception as e:
        print(f"Scraper Test Failed: {e}")
