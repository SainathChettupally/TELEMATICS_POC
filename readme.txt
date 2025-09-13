Telematics UBI POC - readme.txt

PROJECT OVERVIEW
This project is a Proof of Concept (POC) for a Usage-Based Insurance (UBI) platform using telematics data. It simulates driver data, scores driver risk using a GBDT model, and provides a dashboard to visualize the results.

Repository Link: https://github.com/SainathChettupally/Telematics-POC.git

SETUP

1.  Create a virtual environment:
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

2.  Install dependencies:
    pip install -r requirements.txt

3.  Configure Environment:
    Create a .env file in the root directory by copying the .env.example file. This file is used to manage environment variables.
    cp .env.example .env
    You must add a secure API_TOKEN to your .env file. For example:
    API_TOKEN="your_secret_token_here"

RUNNING SHELL SCRIPTS ON WINDOWS

This project uses shell scripts (.sh) for automated setup and execution. On Windows, you can run these scripts using:

*   Git Bash: Install Git for Windows, which includes Git Bash. You can then run .sh scripts directly from the Git Bash terminal.
*   Windows Subsystem for Linux (WSL): Install WSL and a Linux distribution (e.g., Ubuntu). You can then run .sh scripts within the WSL environment.

AUTOMATED RUN

This project includes scripts to automate the setup and execution process.

-   bin/seed_demo.sh: This script runs the full data pipeline, including data simulation, feature engineering, and model training. It prepares all the necessary assets for the API and dashboard to run.
-   bin/run_all.sh: This script starts all the services, including the API server and the Streamlit dashboard.

To run the entire project automatically, execute the following commands from the root directory:

bash bin/seed_demo.sh
bash bin/run_all.sh

MANUAL EXECUTION

If you prefer to run each step manually, follow the instructions below.

1.  Generate Simulated Data:
    python -m src.simulate.trip_simulator

2.  Build Features:
    python -m src.features.build_features

3.  Train Model:
    Note: Model evaluation is performed as part of src/model/train.py. The evaluation results and plots are saved to:
    *   docs/metrics.json (for AUC, PR-AUC, Brier, ECE)
    *   docs/evaluation/evaluation_plots.png (for ROC, PR, Calibration plots)
    *   docs/evaluation/decile_lift_table.csv (for decile lift table)

4.  Run API Server:
    Make sure your API_TOKEN is set in the .env file.
    uvicorn src.api.app:app --host 0.0.0.0 --port 8000

5.  Run Dashboard:
    streamlit run src.dashboard/app.py

Evaluation Steps

Model evaluation metrics and plots are generated during the model training process (src/model/train.py) and saved to the following locations:

-   Model Metrics: docs/metrics.json (AUC, PR-AUC, Brier score, ECE).
-   Decile Lift Table: docs/evaluation/decile_lift_table.csv (predicted vs. observed loss rates across risk deciles).
-   Evaluation Plots: docs/evaluation/evaluation_plots.png (ROC, PR, and Calibration plots).
-   Pricing Sensitivity: docs/evaluation/pricing_sensitivity_plot.png (illustrates the pricing engine's behavior).

Data Validation Tests

To verify the simulated data adheres to expected ranges (e.g., speed, acceleration), run the dedicated data simulation tests:

pytest tests/test_data_simulation.py

Notes on Models, Data, and Services

Models

-   Risk Scoring Model: A calibrated tree-based model (e.g., HistGradientBoosting) is used for predicting risk.
-   Pricing Engine: A formula-based engine with guardrails (clamping, EMA smoothing) ensures stable and fair pricing.

Data

-   Simulated Telematics Data: Located in data/simulated (drivers, trips, events).
-   Processed Features: 30-day rolling features per driver are in data/features.
-   Labels: labels.parquet contains the target variable (e.g., claim_in_30d).

Services

-   FastAPI: Provides secure API endpoints for risk scoring and premium calculation.
-   Streamlit Dashboard: Offers a user interface to visualize KPIs, driver trends, and perform what-if premium analysis.

API ENDPOINTS

The API is protected and requires an API_TOKEN to be passed in the Authorization header as a Bearer token.

Score Driver
- URL: /score
- Method: POST
- Body:
  {
    "driver_id": "some_driver_id"
  }
- cURL Example:
  curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer your_secret_token_here" -d '{"driver_id": "driver_123"}' http://localhost:8000/score

Calculate Price
- URL: /price
- Method: POST
- Body:
  {
    "driver_id": "some_driver_id",
    "base_premium": 100.0
  }
- cURL Example:
  curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer your_secret_token_here" -d '{"driver_id": "driver_123", "base_premium": 100.0}' http://localhost:8000/price

DATA RETENTION POLICY

This policy outlines data retention for a production environment. All raw telematics data and derived features will be retained for a period of 7 years for auditing and regulatory compliance purposes. After this period, data will be securely archived or purged.