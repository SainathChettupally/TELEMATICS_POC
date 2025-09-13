from pydantic import BaseModel
from typing import Dict, List

class ScoreRequest(BaseModel):
    """Request model for the /score endpoint."""
    driver_id: int

class PriceRequest(BaseModel):
    """Request model for the /price endpoint."""
    driver_id: int
    base_premium: float

class ScoreResponse(BaseModel):
    """Response model for the /score endpoint."""
    driver_id: int
    risk_score: float
    top_features: List[Dict] # Use a generic list of dictionaries

class PriceResponse(BaseModel):
    """Response model for the /price endpoint."""
    driver_id: int
    premium: float
    delta: float