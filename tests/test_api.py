import json
import pytest
from unittest.mock import patch, MagicMock

def test_security_headers(client):
    """Test that strict security headers are attached to every response."""
    response = client.get('/')
    assert 'Content-Security-Policy' in response.headers
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    # The updated Referrer-Policy is 'strict-origin-when-cross-origin'
    assert response.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'

def test_get_laptops_api(client):
    """Test retrieving laptop database with safe fields."""
    response = client.get('/api/laptops')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'laptops' in data
    assert 'count' in data
    assert isinstance(data['laptops'], list)
    
    if len(data['laptops']) > 0:
        laptop = data['laptops'][0]
        assert 'brand' in laptop
        assert 'model' in laptop
        assert 'price_jod' in laptop
        assert 'id' not in laptop

def test_recommendation_input_validation(client):
    """Test request parameter boundary checks and input validation."""
    
    # 1. Invalid Content-Type
    res = client.post('/api/recommend', data="not-json")
    assert res.status_code == 400
    
    # 2. Too low budget (limit is 100)
    invalid_payload = {
        "budget": 50,
        "use_case": "gaming",
        "performance": "medium",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "Any"
    }
    res = client.post('/api/recommend', json=invalid_payload)
    assert res.status_code == 400
    # Updated error message in refactored code
    assert b"Budget must be between 100 and 10000 JOD" in res.data

    # 3. Too high budget (limit is 10000)
    invalid_payload["budget"] = 20000
    res = client.post('/api/recommend', json=invalid_payload)
    assert res.status_code == 400

    # 4. Non-integer budget
    invalid_payload["budget"] = "cheap"
    res = client.post('/api/recommend', json=invalid_payload)
    assert res.status_code == 400

    # 5. Invalid use case value
    invalid_payload["budget"] = 800
    invalid_payload["use_case"] = "mining"
    res = client.post('/api/recommend', json=invalid_payload)
    assert res.status_code == 400
    assert b"Invalid use_case value" in res.data

    # 6. Invalid performance value
    invalid_payload["use_case"] = "gaming"
    invalid_payload["performance"] = "ultra-extreme"
    res = client.post('/api/recommend', json=invalid_payload)
    assert res.status_code == 400
    assert b"Invalid performance value" in res.data

    # 7. Invalid screen size
    invalid_payload["performance"] = "high"
    invalid_payload["screen_size"] = "huge"
    res = client.post('/api/recommend', json=invalid_payload)
    assert res.status_code == 400
    assert b"Invalid screen_size value" in res.data

    # 8. Invalid brand
    invalid_payload["screen_size"] = "15-16"
    invalid_payload["brand"] = "Samsung" # not in allow-list
    res = client.post('/api/recommend', json=invalid_payload)
    assert res.status_code == 400
    assert b"Invalid brand value" in res.data

def test_recommendation_successful(client):
    """Test successful recommendation requests."""
    # We no longer use LLM, so we don't need to mock it.
    # The pipeline is deterministic and will return recommendations from the seeded DB.
    payload = {
        "budget": 800,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "ASUS"
    }
    
    res = client.post('/api/recommend', json=payload)
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "winning_model" in data
    assert "recommendations" in data

@patch('refresh_data.scrape_all_shops')
def test_refresh_prices_api(mock_scrape, client):
    """Test refresh prices API route behavior."""
    mock_scrape.return_value = 5
    res = client.post('/api/refresh-prices')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "updated" in data
    assert data["updated"] == 5
    assert "refreshed" in data["message"]
