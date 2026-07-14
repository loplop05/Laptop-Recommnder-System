from unittest.mock import patch
from ml_pipeline import LaptopRecommenderPipeline

def test_weighted_score_prefers_better_match():
    """Test weighted score gives better fit a higher score."""
    pipeline = LaptopRecommenderPipeline()
    pref = {
        "budget": 800,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "ASUS"
    }
    laptop_good_match = {
        "brand": "ASUS",
        "price_jod": 750,
        "use_cases": ["gaming"],
        "performance_level": "high",
        "portability": "medium",
        "screen_size": 15.6
    }

    laptop_bad_match = {
        "brand": "Apple",
        "price_jod": 1500, # over budget
        "use_cases": ["work"], # wrong use case
        "performance_level": "entry", # low performance
        "portability": "high",
        "screen_size": 13.3
    }

    score_good, _ = pipeline._score_laptop(laptop_good_match, pref)
    score_bad, _ = pipeline._score_laptop(laptop_bad_match, pref)

    assert score_good > score_bad
    assert 0 <= score_good <= 100
    assert 0 <= score_bad <= 100

@patch("ml_pipeline.filter_laptops")
@patch("ml_pipeline.get_connection")
def test_get_recommendations_with_weighted_scoring(mock_get_connection, mock_filter_laptops):
    """Test recommendation engine query handler with deterministic DB mocks."""
    pipeline = LaptopRecommenderPipeline()
    pipeline._db_ready = True

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
        "image_url": "http://example.com/image.png",
        "shop_offers": [{"product_url": "http://example.com/buy"}],
    }
    mock_filter_laptops.return_value = [laptop]

    class _Cursor:
        def fetchone(self):
            return {"c": 1}

    class _Conn:
        def execute(self, *_args, **_kwargs):
            return _Cursor()

        def close(self):
            return None

    mock_get_connection.return_value = _Conn()

    pref = {
        "budget": 800,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "Any"
    }

    result = pipeline.get_recommendations(pref)
    assert result["winning_model"] == "hard_filter_weighted_score"
    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0]["brand"] == "ASUS"
    assert result["recommendations"][0]["purchase_url"] == "http://example.com/buy"
