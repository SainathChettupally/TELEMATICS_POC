```markdown
# Telematics UBI Proof of Concept Submission

## Project Overview
This submission presents a comprehensive Proof of Concept (POC) for a Usage-Based Insurance (UBI) platform, leveraging telematics data to demonstrate an end-to-end solution. MY goal was to design and develop a system that accurately captures driving behavior and vehicle usage data, integrating this data into a dynamic insurance pricing model. I aimed to improve premium accuracy, encourage safer driving, enhance customer transparency, and ensure compliance with data security and privacy regulations.

## Public Repository
https://github.com/SainathChettupally/TELEMATICS_POC.git

## Setup and Installation
Setting up and running this project locally is straightforward. The steps are as follows:

1.  **Cloning the repository (if applicable):**
    ```bash
    git clone <my-repo-link-here>
    cd Telematics AI
    ```
2.  **Creating and activating a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```
3.  **Installing dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Setting up environment variables:**
    We provide an `.env.example` file. Copy it to `.env` and populate necessary values, such as `API_TOKEN`.
    ```bash
    cp .env.example .env
    ```

## Running the Application

### 1. Seeding Demo Data
To generate synthetic telematics data, train our models, and prepare all necessary artifacts, I  execute the seeding script:
```bash
bash bin/seed_demo.sh
```
This script performs the following actions:
-   Simulates driver and trip data using `src/simulate/trip_simulator.py`.
-   Generates features and labels using `src/features/build_features.py`.
-   Trains the risk scoring model using `src/model/train.py`.
-   Saves all required artifacts for the application.

### 2. Launching API & Dashboard
To launch both the FastAPI service and the Streamlit dashboard concurrently, I'll use our `run_all.sh` script:
```bash
bash bin/run_all.sh
```
This script initiates:
-   The FastAPI server (typically accessible at `http://127.0.0.1:8000`).
-   The Streamlit dashboard (typically accessible at `http://localhost:8501`).

### Individual Service Commands:
For individual service control, we use:
-   **FastAPI Service:**
    ```bash
    uvicorn src.api.app:app --host 0.0.0.0 --port 8000
    ```
    API documentation is available at `http://127.0.0.1:8000/docs`.
-   **Streamlit Dashboard:**
    ```bash
    streamlit run src/dashboard/app.py
    ```

## Evaluation Steps
I ensure the robustness and accuracy of our solution through the following evaluation steps:

1.  **Running Unit and Integration Tests:**
    ```bash
    pytest -q tests
    ```
2.  **Generating Evaluation Metrics and Plots:**
    My `bin/seed_demo.sh` script automatically generates comprehensive evaluation artifacts, which are stored in the `/docs/evaluation` directory. These include ROC curves, PR curves, calibration plots, decile lift tables (`decile_lift_table.csv`), and pricing sensitivity plots (`pricing_sensitivity_plot.png`). Key performance metrics are also consolidated in `docs/metrics.json`.

## Project Structure
My project is meticulously organized into the following main directories to ensure clarity and maintainability:

-   `/bin`: Contains essential shell scripts for project setup and execution.
-   `/data`: Stores all simulated and processed data, including features and labels.
-   `/docs`: Houses comprehensive documentation, evaluation metrics, architectural decisions (`decisions.md`), and visual plots.
-   `/models`: Dedicated to persisting my machine learning models (`risk_model_calibrated.pkl`) and explainers (`shap_explainer.pkl`).
-   `/src`: Contains all source code, logically separated into:
    -   `/src/api`: MY FastAPI application for risk scoring and pricing.
    -   `/src/config`: Configuration files, such as pricing parameters (`pricing_config.yaml`).
    -   `/src/dashboard`: The Streamlit application for data visualization and user interaction.
    -   `/src/features`: Logic for my feature engineering pipeline (`build_features.py`, `feature_config.yaml`).
    -   `/src/model`: Components for machine learning model training and evaluation (`train.py`).
    -   `/src/simulate`: Scripts for generating my synthetic telematics data (`trip_simulator.py`).
-   `/tests`: Contains all unit and integration tests for various project components.

## Key Features and Achievements
My solution successfully implements the following key features, directly addressing the project objectives:

-   **Data Collection (Simulation):** I have implemented a robust data simulator (`src/simulate/trip_simulator.py`) that generates synthetic telematics data, including speed, acceleration, braking events, mileage, and time-of-day, all with anonymized IDs to ensure privacy. Data validation ranges are enforced during feature engineering.
-   **Data Processing:** My pipeline (`src/features/build_features.py`) builds 30-day rolling features per driver, such as miles driven, night-time driving percentage, urban driving percentage, p50/p95 speed, harsh braking/rapid acceleration rates per 100 miles, speeding percentage, stop-go metrics, and a composite safety rating. I also produce binary labels for `claim_in_30d`.
-   **Risk Scoring Model:** I  developed a tree-based learner (XGBoost Classifier) for driver risk prediction (`src/model/train.py`), which is then calibrated using Isotonic Regression (`CalibratedClassifierCV`) to ensure well-calibrated probabilities. The model achieves an ROC AUC of approximately 0.745 and an ECE of 0.0086. SHAP values are used for feature explanations.
-   **Pricing Engine:** My dynamic pricing engine (`src/api/routes.py`) calculates premiums using a formula `premium = base * (1 + α*(score−μ)/σ)`, incorporating configurable parameters (`alpha`, `min_cap`, `max_cap`) from `src/config/pricing_config.yaml`. It loads `μ` and `σ` from `docs/metrics.json` to ensure dynamic adjustment based on the model's score distribution.
-   **Secure APIs:** I built FastAPI endpoints (`src/api/app.py`, `src/api/routes.py`) for `POST /score` (returning score and top-k feature reasons) and `POST /price` (returning premium, band, and deltas), secured with Bearer token authentication (`src/api/dependencies.py`).
-   **User Dashboard:** My Streamlit application (`src/dashboard/app.py`) provides an intuitive user interface displaying key performance indicators (KPIs), the latest score and premium, trend analysis, "why it changed" explanations (based on top features from SHAP), and a premium what-if slider. It also includes gamification elements like badges.

## Dashboard Overview

![Dashboard Screenshot](docs/dashboard.png)

## Notes on Models, Data, and External Services

-   **Models:** My risk scoring model is an XGBoost Classifier, trained on engineered telematics features and calibrated using Isotonic Regression. The trained model, calibrator, and SHAP explainer are persisted in the `/models` directory.
-   **Data:** All telematics data utilized in this project is simulated (`src/simulate/trip_simulator.py`) to ensure privacy, reproducibility, and to provide a controlled environment for development and testing. Anonymized driver and trip IDs are consistently used. Processed data artifacts are stored in the `/data` directory.
-   **External Services:** For this Proof of Concept, I have not integrated any live external APIs or services. All data is generated and processed locally. However, our API design allows for straightforward integration with real telematics providers or other external data sources in a production environment.

## Cloud & Performance Note
My architecture is designed with scalability in mind. For future deployment, I envision transitioning from local file-based data storage to cloud-native solutions. Micro-batch processing could leverage services like AWS S3/Lambda for data ingestion and processing, or Kafka/Kinesis for real-time streaming. 

## Privacy, Security, Compliance
i have prioritized privacy, security, and compliance throughout the project:
-   **PII:** No Personally Identifiable Information (PII) is used; all driver IDs are synthetic and anonymized.
-   **Retention:** As documented in `docs/decisions.md`, a 7-year data retention policy is in place for aggregated data, with raw GPS data (if applicable in a real-world scenario) retained for a shorter period.
-   **Access:** API access is secured with Bearer token authentication, and all access attempts are logged for auditing purposes.
-   Further details and decisions regarding these aspects are documented in `/docs/decisions.md`.

## Evidence & Documentation
I provided comprehensive documentation and evaluation evidence:
-   `/docs/architecture.md`: Contains a Mermaid diagram illustrating our system architecture.
-   `/docs/decisions.md`: Documents key architectural and model-related decisions, including justifications for tree-based models, calibration choices, pricing guardrails, and privacy considerations.
-   `/docs/roi_note.md`: Provides a Return on Investment (ROI) sketch, including a tiny sensitivity table.
-   **Saved Plots (located in `docs/evaluation`):**
    -   `roc_curve.png`
    -   `pr_curve.png`
    -   `calibration_plot.png`
    -   `decile_lift_table.csv`
    -   `pricing_sensitivity_plot.png`
-   `docs/metrics.json`: Stores key evaluation metrics such as AUC, PR-AUC, Brier score, ECE, label prevalence, and the mean (μ) and standard deviation (σ) of MY score distribution.

## Opportunities for Enhancement and Future Work
The Streamlit dashboard already includes an **Achievements section** and a **Peer Driving Analysis** module, allowing users to see how their driving compares to peers (e.g., harsh braking, rapid acceleration rates) and earn badges for safe driving habits. 

While this POC demonstrates a robust foundation, I have identified several opportunities to further enhance and optimize the system for production readiness:

- **Expanded Data Sources:** Currently, the system uses only simulated telematics data. In the future, I plan to incorporate real-time telematics feeds, historical driving records, crime and accident data, and live traffic and weather conditions into the pricing model for more dynamic and context-aware premium calculations.
- **Refined Label Generation:** I plan to improve the label generation process in `src/features/build_features.py` to ensure a strict temporal split, preventing any potential data leakage and enhancing predictive performance.
- **Advanced Pricing Guardrails:** Although the current pricing engine has min/max caps, future versions will introduce Exponential Moving Average (EMA) smoothing and minimum-change thresholds to stabilize premium adjustments and deliver a smoother customer experience.


## Nice-to-Have (Stretch Goals)
Beyond the current functionality, I would like to explore:
- Real-time trip-end feedback delivered via websockets or micro-batch processing.
- Contextual enrichment with live traffic, weather, and road condition data for even more accurate risk scoring and pricing.
- More gamification features such as streak tracking, leaderboards, and competitive benchmarking to further engage drivers and encourage safer driving behavior.

> **Note:** For details on how AI was used during the development of this project, please refer to [`docs/ai_assisted_development.md`](docs/ai_assisted_development.md).
```
