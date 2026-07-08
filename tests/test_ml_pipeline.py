import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from ml_pipeline import LaptopRecommenderPipeline, NumpyKNNClassifier

def test_knn_classifier():
    """Test pure NumPy KNN Classifier."""
    classifier = NumpyKNNClassifier(k=3)
    X_train = np.array([
        [1.0, 2.0],
        [1.5, 1.8],
        [5.0, 5.0],
        [5.2, 4.8]
    ])
    y_train = np.array([0, 0, 1, 1])
    classifier.fit(X_train, y_train, num_classes=2)
    
    # Test prediction probability
    test_pt = np.array([[1.1, 1.9]])
    probs = classifier.predict_proba(test_pt)
    assert probs.shape == (1, 2)
    assert probs[0][0] > probs[0][1]  # Should be closer to class 0

def test_preference_encoding():
    """Test encoding user preference vectors."""
    pipeline = LaptopRecommenderPipeline()
    pref = {
        "budget": 800,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "ASUS"
    }
    vector = pipeline.encode_user_preferences(pref)
    assert isinstance(vector, np.ndarray)
    assert len(vector) == 19
    # Check normalization range
    assert all(0.0 <= val <= 1.0 for val in vector)

def test_laptop_encoding():
    """Test encoding laptop properties."""
    pipeline = LaptopRecommenderPipeline()
    laptop = {
        "brand": "Lenovo",
        "model": "Legion 5",
        "cpu": "Ryzen 7",
        "gpu": "RTX 4060",
        "ram": 16,
        "storage": 512,
        "screen_size": 15.6,
        "price_jod": 900,
        "use_cases": ["gaming", "work"],
        "performance_level": "high",
        "portability": "medium"
    }
    vector = pipeline.encode_laptop(laptop)
    assert isinstance(vector, np.ndarray)
    assert len(vector) == 18
    assert all(0.0 <= val <= 1.0 for val in vector)

def test_synthetic_rating():
    """Test calculating compatibility score between preferences and laptop."""
    pipeline = LaptopRecommenderPipeline()
    pref = {
        "budget": 800,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "ASUS"
    }
    laptop_matching = {
        "brand": "ASUS",
        "price_jod": 750,
        "use_cases": ["gaming"],
        "performance_level": "high",
        "portability": "medium",
        "screen_size": 15.6
    }
    rating_match = pipeline.calculate_synthetic_rating(pref, laptop_matching)
    
    laptop_mismatch = {
        "brand": "Apple",
        "price_jod": 1500, # over budget
        "use_cases": ["work"], # wrong use case
        "performance_level": "entry", # low performance
        "portability": "high",
        "screen_size": 13.3
    }
    rating_mismatch = pipeline.calculate_synthetic_rating(pref, laptop_mismatch)
    
    assert 1.0 <= rating_match <= 5.0
    assert 1.0 <= rating_mismatch <= 5.0
    assert rating_match > rating_mismatch

@patch('openai.resources.chat.completions.Completions.create')
def test_get_recommendations_with_openai(mock_create):
    """Test recommendation engine query handler by mocking OpenAI client response."""
    # Set up mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='''
        {
          "recommendations": [
            {"index": 0, "reasoning": "Fits your gaming demands and matches budget."}
          ],
          "winning_model": "Deep Learning Reasoning",
          "winning_model_label": "Deep Learning Reasoning"
        }
        '''))
    ]
    mock_create.return_value = mock_response

    pipeline = LaptopRecommenderPipeline()
    # Mock laptop database
    pipeline.laptops = [
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
            "portability": "medium",
            "image_url": "http://example.com/image.png",
            "purchase_url": "http://example.com/buy"
        }
    ]

    pref = {
        "budget": 800,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "Any"
    }

    result = pipeline.get_recommendations(pref)
    assert result["winning_model"] == "deep_learning"
    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0]["brand"] == "ASUS"
    assert "gaming demands" in result["recommendations"][0]["reasoning"]
