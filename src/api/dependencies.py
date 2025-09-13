import joblib
import pandas as pd
import pickle
import numpy as np
import os
import json
import logging
from dotenv import load_dotenv
from fastapi import HTTPException
from pathlib import Path

from src.model.train import FEATURES # Import FEATURES

load_dotenv()
# --- Configuration ---
BASE_DIR = Path(__file__).parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "risk_model_calibrated.pkl"
EXPLAINER_PATH = BASE_DIR / "models" / "shap_explainer.pkl"
FEATURES_PATH = BASE_DIR / "data" / "features" / "driver_features.parquet"
METRICS_PATH = BASE_DIR / "docs" / "metrics.json"

# --- Shared Assets ---
model = None
explainer = None
driver_features_df = None
score_stats = None
API_TOKEN = os.getenv("API_TOKEN")
print(f"DEBUG: API_TOKEN loaded: {API_TOKEN}")

# Configure logging (if not already configured in app.py)
logger = logging.getLogger(__name__)

def load_assets():
    """Load the ML model, SHAP explainer, feature data, and metrics."""
    global model, explainer, driver_features_df, score_stats, API_TOKEN

    logger.info("Loading assets...")
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        logger.info(f"Model loaded from {MODEL_PATH}")

        with open(EXPLAINER_PATH, "rb") as f:
            explainer = pickle.load(f)
        logger.info(f"Explainer loaded from {EXPLAINER_PATH}")
        explainer.feature_names = FEATURES # Set feature_names explicitly
        print(f"DEBUG: explainer.feature_names: {explainer.feature_names}") # Added debug print

        driver_features_df = pd.read_parquet(FEATURES_PATH)
        logger.info(f"Driver features loaded from {FEATURES_PATH}")

        with open(METRICS_PATH, "r") as f:
            score_stats = json.load(f)
        logger.info(f"Score statistics loaded from {METRICS_PATH}")

    except Exception as e:
        logger.error(f"Error loading assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load assets: {e}")