from fastapi import APIRouter, HTTPException, Depends
import pandas as pd
import numpy as np
import json
import os
import logging
import yaml

from .schemas import ScoreRequest, ScoreResponse, PriceRequest, PriceResponse
from . import dependencies

router = APIRouter()

# --- Security ---
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != dependencies.API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return credentials.credentials

@router.post("/score", response_model=ScoreResponse, operation_id="score_driver_post")
def score_driver(request: ScoreRequest, token: str = Depends(get_current_token)):
    """Scores a driver and provides peer-comparison feedback for top features."""

    if dependencies.driver_features_df is None or dependencies.model is None or dependencies.explainer is None:
        raise HTTPException(status_code=503, detail="Assets not loaded.")

    driver_id = request.driver_id
    
    try:
        # Select all features for the driver and get the latest entry
        driver_data = dependencies.driver_features_df.loc[[driver_id]]
        features = driver_data.sort_values(by='window_end_date', ascending=False).head(1)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Driver ID {driver_id} not found.")

    if features.empty:
        raise HTTPException(status_code=404, detail=f"No feature data found for driver ID {driver_id}.")

    feature_columns = dependencies.explainer.feature_names
    features = features[feature_columns]

    # Calculate portfolio averages
    portfolio_averages = dependencies.driver_features_df[feature_columns].mean().to_dict()

    risk_score = dependencies.model.predict_proba(features)[0][1]
    
    shap_values = dependencies.explainer.shap_values(features)
    shap_values_class_1 = shap_values[0]

    feature_shap_map = dict(zip(feature_columns, shap_values_class_1))
    
    sorted_features = sorted(
        [item for item in feature_shap_map.items() if item[1] > 0],
        key=lambda item: item[1],
        reverse=True
    )

    # Manually build a list of dictionaries for the response
    top_features_response = []
    for feature_name, shap_value in sorted_features[:3]:
        driver_value = features.iloc[0][feature_name]
        avg_value = portfolio_averages[feature_name]
        
        top_features_response.append({
            "feature": feature_name,
            "value": driver_value,
            "average": avg_value,
            "shap_value": shap_value
        })

    dependencies.logger.info(f"Scoring request for driver_id: {driver_id} processed successfully.")

    return ScoreResponse(
        driver_id=driver_id,
        risk_score=float(risk_score),
        top_features=top_features_response
    )

@router.post("/price", response_model=PriceResponse, operation_id="calculate_price_post")
def calculate_price(request: PriceRequest, token: str = Depends(get_current_token)):
    """Calculates the insurance premium based on risk score."""
    try:
        # Select all features for the driver and get the latest entry
        driver_data = dependencies.driver_features_df.loc[[request.driver_id]]
        features = driver_data.sort_values(by='window_end_date', ascending=False).head(1)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Driver ID {request.driver_id} not found.")

    if features.empty:
        raise HTTPException(status_code=404, detail=f"No feature data found for driver ID {request.driver_id}.")

    feature_columns = dependencies.explainer.feature_names
    features = features[feature_columns]
    score = dependencies.model.predict_proba(features)[0][1]

    base_premium = request.base_premium
    dependencies.logger.info(f"Received pricing request for driver_id: {request.driver_id}, base_premium: {base_premium}, score: {score}")

    from pathlib import Path
    BASE_DIR = Path(__file__).parent.parent.parent
    try:
        with open(BASE_DIR / "src" / "config" / "pricing_config.yaml", 'r') as f:
            pricing_config = yaml.safe_load(f)
        pricing_params = pricing_config.get("pricing", {})
        if not all(k in pricing_params for k in ["alpha", "min_cap", "max_cap"]):
            raise ValueError("Missing pricing parameters in config file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading pricing configuration: {e}")

    premium = base_premium * (1 + pricing_params['alpha'] * (score - dependencies.score_stats['holdout_score_mean']) / dependencies.score_stats['holdout_score_std'])
    
    clamped_premium = max(pricing_params['min_cap'], min(premium, pricing_params['max_cap']))
    delta = clamped_premium - base_premium
    dependencies.logger.info(f"Pricing request for driver_id: {request.driver_id} processed. Premium: {clamped_premium}")

    return PriceResponse(
        driver_id=request.driver_id,
        premium=clamped_premium,
        delta=delta
    )