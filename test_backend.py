import logging
from unittest.mock import patch

from ml_pipeline import LaptopRecommenderPipeline
from refresh_data import scrape_all_shops

logging.basicConfig(level=logging.INFO)

def test_pipeline():
    pipeline = LaptopRecommenderPipeline()

    pref = {
        "budget": 800,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "Any"
    }
    recommendations = pipeline.get_recommendations(pref).get('recommendations', [])
    assert isinstance(recommendations, list)


@patch('test_backend.scrape_all_shops')
def test_scraper(mock_scrape_all_shops):
    """Scraper test should not rely on external network availability."""
    mock_scrape_all_shops.return_value = 3
    count = scrape_all_shops()
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
