from unittest.mock import MagicMock, patch
from ml_pipeline import LaptopRecommenderPipeline


def test_score_laptop_rewards_better_match():
    """A better-aligned laptop should score higher."""
    pipeline = LaptopRecommenderPipeline()
    pref = {
        "budget": 900,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "ASUS",
    }

    strong_match = {
        "brand": "ASUS",
        "price_jod": 850,
        "use_cases": ["gaming"],
        "performance_level": "high",
        "portability": "medium",
        "screen_size": 15.6,
    }
    weak_match = {
        "brand": "Lenovo",
        "price_jod": 500,
        "use_cases": ["gaming", "work", "general"],
        "performance_level": "medium",
        "portability": "high",
        "screen_size": 13.3,
    }

    strong_score, _ = pipeline._score_laptop(strong_match, pref)
    weak_score, _ = pipeline._score_laptop(weak_match, pref)
    assert strong_score > weak_score


@patch("ml_pipeline.get_connection")
@patch("ml_pipeline.filter_laptops")
def test_get_recommendations_returns_ranked_results(mock_filter_laptops, mock_get_connection):
    """Recommendation output should contain ranked deterministic results."""
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = {"c": 2}
    mock_get_connection.return_value = conn

    mock_filter_laptops.return_value = [
        {
            "id": "laptop_01",
            "brand": "ASUS",
            "model": "TUF Gaming A15",
            "cpu": "AMD Ryzen 7 7735HS",
            "gpu": "NVIDIA GeForce RTX 4060",
            "ram": 16,
            "storage_size": 512,
            "storage_type": "SSD",
            "screen_size": 15.6,
            "os": "Windows 11",
            "price_jod": 850,
            "use_cases": ["gaming"],
            "performance_level": "high",
            "portability": "medium",
            "image_url": "http://example.com/asus.png",
            "shop_offers": [{"product_url": "http://example.com/asus-buy"}],
        },
        {
            "id": "laptop_02",
            "brand": "Lenovo",
            "model": "Legion 5",
            "cpu": "Intel Core i7",
            "gpu": "NVIDIA GeForce RTX 4060",
            "ram": 16,
            "storage_size": 1024,
            "storage_type": "SSD",
            "screen_size": 16.0,
            "os": "Windows 11",
            "price_jod": 900,
            "use_cases": ["gaming", "work"],
            "performance_level": "high",
            "portability": "medium",
            "image_url": "http://example.com/lenovo.png",
            "shop_offers": [{"product_url": "http://example.com/lenovo-buy"}],
        },
    ]

    pipeline = LaptopRecommenderPipeline()
    pipeline._db_ready = True
    pref = {
        "budget": 900,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "Any",
    }

    result = pipeline.get_recommendations(pref)
    assert result["winning_model"] == "hard_filter_weighted_score"
    assert result["winning_model_label"] == "Smart Filter + Weighted Scoring"
    assert len(result["recommendations"]) == 2
    assert result["recommendations"][0]["rank"] == 1
    assert result["recommendations"][0]["purchase_url"] == "http://example.com/asus-buy"
    assert result["filter_stats"]["after_filter"] == 2
    conn.close.assert_called_once()
