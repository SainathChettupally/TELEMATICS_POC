import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.api.app import app

@pytest.fixture(scope="module")
def client_with_auth():
    with patch('src.api.app.API_TOKEN', 'test_token'):
        test_client = TestClient(app)
        yield test_client

def test_calculate_price_basic(client_with_auth):
    # This test will require the app to be initialized with loaded assets
    # For a proper unit test, you might mock dependencies or use a test database
    # For now, we'll assume assets are loaded (e.g., by running the app once)
    # or we'll need to add a fixture to load them.
    
    # Example: Test with a score that should result in a premium within caps
    response = client_with_auth.post(
        "/price",
        headers={
                "Authorization": "Bearer test_token"
            },
        json={
            "driver_id": "test_driver",
            "base_premium": 100.0,
            "score": 0.5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "premium" in data
    assert "delta" in data
    assert data["premium"] > 0

# Add more tests for min_cap, max_cap, and error handling
