from unittest.mock import MagicMock, patch
from ml_pipeline import LaptopRecommenderPipeline, LaptopScorer, ReasoningGenerator


def _pref():
    return {
        "budget": 800,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "ASUS",
    }


def test_score_laptop_rewards_better_budget_fit():
    scorer = LaptopScorer()
    pref = _pref()

    laptop_near_budget = {
        "brand": "ASUS",
        "price_jod": 760,
        "use_cases": ["gaming"],
        "performance_level": "high",
        "portability": "medium",
        "screen_size": 15.6,
    }
    laptop_too_cheap = {**laptop_near_budget, "price_jod": 300}

    near_score, _ = scorer.score(laptop_near_budget, pref)
    cheap_score, _ = scorer.score(laptop_too_cheap, pref)

    assert near_score > cheap_score


def test_generate_reasoning_includes_specific_matches():
    reasoning_gen = ReasoningGenerator()
    reasoning = reasoning_gen.generate(
        {
            "brand": "ASUS",
            "model": "TUF Gaming A15",
            "cpu": "AMD Ryzen 7 7735HS",
            "gpu": "NVIDIA GeForce RTX 4060 8GB",
            "ram": 16,
            "storage_size": 512,
            "screen_size": 15.6,
            "price_jod": 780,
            "use_cases": ["gaming"],
            "performance_level": "high",
            "portability": "medium",
        },
        _pref()
    )

    assert "under your budget" in reasoning
    assert "RTX 4060 8GB" in reasoning


def test_get_recommendations_returns_ranked_result_shape():
    mock_repo = MagicMock()
    pipeline = LaptopRecommenderPipeline(mock_repo)
    pref = _pref()

    mocked_laptops = [
        {
            "id": "laptop_01",
            "brand": "ASUS",
            "model": "TUF Gaming A15",
            "cpu": "AMD Ryzen 7 7735HS",
            "gpu": "NVIDIA GeForce RTX 4060 8GB",
            "ram": 16,
            "storage_size": 512,
            "screen_size": 15.6,
            "os": "Windows",
            "price_jod": 780,
            "use_cases": ["gaming"],
            "performance_level": "high",
            "portability": "medium",
            "image_url": "http://example.com/image.png",
            "shop_offers": [{"product_url": "http://example.com/buy"}],
        }
    ]

    mock_repo.filter_laptops.return_value = mocked_laptops
    result = pipeline.get_recommendations(pref)

    assert result["winning_model"] == "hard_filter_weighted_score"
    assert len(result["recommendations"]) == 1
    rec = result["recommendations"][0]
    assert rec["brand"] == "ASUS"
    # Purchase URL is now handled differently in the new schema (via shop_offers)
    # The original test checked for rec["purchase_url"], but our new formatter uses shop_offers
    assert rec["shop_offers"][0]["product_url"] == "http://example.com/buy"
