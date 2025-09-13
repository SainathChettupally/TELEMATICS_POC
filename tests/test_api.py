import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
from src.api.app import app, get_current_token, load_assets

# Manually call load_assets to populate global variables for tests
load_assets()

# Override the token dependency for all tests
app.dependency_overrides[get_current_token] = lambda: "test_token"

client = TestClient(app)

# Mock assets for testing
@pytest.fixture(scope="module", autouse=True)
def mock_assets():
    with patch('joblib.load') as mock_joblib_load:
        with patch('pickle.load') as mock_pickle_load:
            with patch('pandas.read_parquet') as mock_read_parquet:
                with patch('json.load') as mock_json_load:
                    with patch('builtins.open', new_callable=MagicMock) as mock_open:
                        with patch('yaml.safe_load') as mock_yaml_safe_load:

                            # Mock model and explainer
                            mock_model = MagicMock()
                            mock_model.predict_proba.return_value = [[0.1, 0.9]] # Example risk score
                            mock_joblib_load.return_value = mock_model

                            mock_explainer = MagicMock()
                            mock_explainer.feature_names = ['feat1', 'feat2']
                            mock_explainer.shap_values.return_value = [np.array([0.0, 0.0]), np.array([0.1, 0.2])]
                            mock_pickle_load.return_value = mock_explainer

                            # Mock driver features
                            mock_df = pd.DataFrame({'driver_id': ['driver_1'], 'feat1': [10], 'feat2': [20]}).set_index('driver_id')
                            mock_read_parquet.return_value = mock_df

                            # Mock metrics.json
                            mock_json_load.return_value = {"holdout_score_mean": 0.5, "holdout_score_std": 0.1}

                            # Mock pricing config
                            mock_yaml_safe_load.return_value = {"pricing": {"alpha": 1.5, "min_cap": 80.0, "max_cap": 500.0}}

                            
                            import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
from src.api.app import app, get_current_token
import src.api.app as app_module # Import the module to patch its attributes

# Override the token dependency for all tests
app.dependency_overrides[get_current_token] = lambda: "test_token"

# Mock global assets directly using patch.object
with (patch.object(app_module, 'model', new=MagicMock()) as mock_model,
     patch.object(app_module, 'explainer', new=MagicMock()) as mock_explainer,
     patch.object(app_module, 'driver_features_df', new=pd.DataFrame({'driver_id': ['driver_1'], 'feat1': [10], 'feat2': [20]}).set_index('driver_id')) as mock_driver_features_df,
     patch.object(app_module, 'score_stats', new={"mu": 0.5, "sigma": 0.1}) as mock_score_stats):

    # Configure mocks
    mock_model.predict_proba.return_value = [[0.1, 0.9]]
    mock_explainer.feature_names = ['feat1', 'feat2']
    mock_explainer.shap_values.return_value = [np.array([0.0, 0.0]), np.array([0.1, 0.2])]

    client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Telematics Risk API with SHAP explanations"}

def test_score_driver_success():
    response = client.post(
        "/score",
        headers={"Authorization": "Bearer test_token"},
        json={"driver_id": "driver_1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["driver_id"] == "driver_1"
    assert "risk_score" in data
    assert "top_features" in data

def test_score_driver_not_found():
    response = client.post(
        "/score",
        headers={"Authorization": "Bearer test_token"},
        json={"driver_id": "non_existent_driver"}
    )
    assert response.status_code == 404
    assert "Driver ID non_existent_driver not found." in response.json()["detail"]

def test_score_driver_unauthorized():
    response = client.post(
        "/score",
        headers={"Authorization": "Bearer wrong_token"},
        json={"driver_id": "driver_1"}
    )
    assert response.status_code == 401
    assert "Invalid or missing token" in response.json()["detail"]

def test_calculate_price_success():
    response = client.post(
        "/price",
        headers={"Authorization": "Bearer test_token"},
        json={
            "driver_id": "driver_1",
            "base_premium": 100.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["driver_id"] == "driver_1"
    assert "premium" in data
    assert "delta" in data
    assert data["premium"] > 0

def test_calculate_price_driver_not_found():
    response = client.post(
        "/price",
        headers={"Authorization": "Bearer test_token"},
        json={
            "driver_id": "non_existent_driver",
            "base_premium": 100.0
        }
    )
    assert response.status_code == 404
    assert "Driver ID non_existent_driver not found." in response.json()["detail"]


def test_calculate_price_unauthorized():
    response = client.post(
        "/price",
        headers={"Authorization": "Bearer wrong_token"},
        json={
            "driver_id": "driver_1",
            "base_premium": 100.0,
            "score": 0.5
        }
    )
    assert response.status_code == 401
    assert "Invalid or missing token" in response.json()["detail"]
