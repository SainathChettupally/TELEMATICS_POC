#!/bin/bash
set -e

echo "--- Starting API Server ---"
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 &

echo "--- Starting Dashboard ---"
streamlit run src/dashboard/app.py --server.port 8501 &

echo "--- Services are running in the background ---"
