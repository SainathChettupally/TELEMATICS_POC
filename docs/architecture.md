# Architecture

## System Overview

The system is designed as a modular pipeline that flows from data simulation to a user-facing dashboard.

1.  **Data Simulation**: Generates raw trip data.
2.  **Feature Engineering**: Cleans and transforms raw data into meaningful features.
3.  **Model Training**: Trains a GBDT model on the engineered features.
4.  **API Server**: Exposes a `/score` endpoint to provide real-time risk scores.
5.  **Dashboard**: A Streamlit application for visualizing scores and driver behavior.

## Mermaid Diagram

```mermaid
graph TD
    A[Data Simulator] --> B(Raw Data *.parquet);
    B --> C{Feature Engineering};
    C --> D[Feature Store *.parquet];
    D --> E{Model Training};
    E --> F[Trained Model *.pkl];
    G[Driver ID] --> H{API Server};
    F --> H;
    D --> H;
    H --> I(Risk Score JSON);
    J[User] --> K{Dashboard};
    H --> K;
    K --> J;
```
