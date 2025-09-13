import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path
import yaml

from .schemas import ScoreRequest, ScoreResponse, PriceRequest, PriceResponse
from .routes import router # Import the router from the new routes.py
from .dependencies import load_assets # Import load_assets from dependencies.py

# Load environment variables (needed for API_TOKEN in dependencies.py)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- App Initialization ---
app = FastAPI(
    title="Telematics Risk API",
    description="API for scoring driver risk with dynamic explanations.",
    version="0.3.0-debug"
)

# Include the router with the score and price endpoints
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    load_assets()

# --- API Endpoints ---
@app.get("/test")
def test_endpoint():
    return {"message": "Test endpoint works!"}

@app.get("/", operation_id="read_root_get")
def read_root():
    return {"message": "Welcome to the Telematics Risk API with SHAP explanations"}
