#!/bin/bash
set -e

echo "--- Running Data Simulation ---"
python src/simulate/trip_simulator.py

echo "--- Running Feature Engineering ---"
python src/features/build_features.py

echo "--- Running Model Training ---"
python src/model/train.py

echo "--- Seed Demo Pipeline Complete ---"
