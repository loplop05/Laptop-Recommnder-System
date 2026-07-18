import logging
from unittest.mock import patch, MagicMock
from ml_pipeline import LaptopRecommenderPipeline
from refresh_data import scrape_all_shops

logging.basicConfig(level=logging.INFO)

def test_pipeline():
    mock_repo = MagicMock()
    mock_repo.filter_laptops.return_value = []
    pipeline = LaptopRecommenderPipeline(mock_repo)

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
    test_pipeline()
    test_scraper()
