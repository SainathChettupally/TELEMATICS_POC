import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import logging

from src.features.build_features import (
    load_data, calculate_trip_features, aggregate_driver_features,
    validate_features, main
)

# Fixture for mock data
@pytest.fixture
def mock_raw_data():
    events_df = pd.DataFrame({
        'trip_id': ['t1', 't1', 't2'],
        'timestamp_utc': ['2023-01-01 10:00:00', '2023-01-01 10:00:05', '2023-01-01 11:00:00'],
        'speed_mph': [30, 35, 40],
        'accelerometer_y': [0.1, -4.0, 0.5]
    })
    trips_df = pd.DataFrame({
        'trip_id': ['t1', 't2'],
        'vehicle_id': ['v1', 'v2'],
        'start_time_utc': ['2023-01-01 10:00:00', '2023-01-01 11:00:00']
    })
    vehicles_df = pd.DataFrame({
        'vehicle_id': ['v1', 'v2'],
        'driver_id': ['d1', 'd2']
    })
    return events_df, trips_df, vehicles_df

# Test load_data
def test_load_data(mock_raw_data):
    events_df, trips_df, vehicles_df = mock_raw_data
    with patch('pandas.read_parquet') as mock_read_parquet:
        mock_read_parquet.side_effect = [events_df, trips_df, vehicles_df]
        data = load_data()
        assert not data.empty
        assert 'driver_id' in data.columns

# Test calculate_trip_features
def test_calculate_trip_features(mock_raw_data):
    events_df, trips_df, vehicles_df = mock_raw_data
    data = pd.merge(events_df, trips_df, on="trip_id")
    data = pd.merge(data, vehicles_df[['vehicle_id', 'driver_id']], on="vehicle_id")
    trip_features_df = calculate_trip_features(data)
    assert 'miles_driven' in trip_features_df.columns
    assert 'harsh_brakes' in trip_features_df.columns

# Test aggregate_driver_features
def test_aggregate_driver_features(mock_raw_data):
    events_df, trips_df, vehicles_df = mock_raw_data
    data = pd.merge(events_df, trips_df, on="trip_id")
    data = pd.merge(data, vehicles_df[['vehicle_id', 'driver_id']], on="vehicle_id")
    trip_features_df = calculate_trip_features(data)
    driver_features_df = aggregate_driver_features(trip_features_df, trips_df, vehicles_df)
    assert 'driver_id' in driver_features_df.columns
    assert 'miles_driven' in driver_features_df.columns

# Test validate_features
def test_validate_features_success():
    df = pd.DataFrame({
        'miles_driven': [100, 200],
        'night_driving_percentage': [0.1, 0.5],
        'harsh_brakes_per_100mi': [1, 5],
        'rapid_accels_per_100mi': [2, 6],
        'speeding_percentage': [0.05, 0.1],
        'stop_go_events': [10, 20],
        'mean_speed': [30, 40],
        'p50_speed': [35, 45]
    })
    validated_df = validate_features(df)
    pd.testing.assert_frame_equal(df, validated_df)

def test_validate_features_failure():
    df = pd.DataFrame({
        'miles_driven': [100, 12000], # Out of range
        'night_driving_percentage': [0.1, 0.5],
        'harsh_brakes_per_100mi': [1, 5],
        'rapid_accels_per_100mi': [2, 6],
        'speeding_percentage': [0.05, 0.1],
        'stop_go_events': [10, 20],
        'mean_speed': [30, 40],
        'p50_speed': [35, 45]
    })
    with pytest.raises(ValueError, match="Feature 'miles_driven' has values outside expected range"):
        validate_features(df)

# Test logging of null rates and label incidence
def test_logging_in_main(mock_raw_data, caplog):
    events_df, trips_df, vehicles_df = mock_raw_data
    with patch('pandas.read_parquet') as mock_read_parquet:
        with patch('src.features.build_features.validate_features') as mock_validate_features:
            with patch('src.features.build_features.Path.mkdir'):
                with patch('src.features.build_features.pd.DataFrame.to_parquet'):

                    mock_read_parquet.side_effect = [events_df, trips_df, vehicles_df, pd.DataFrame({'driver_id': ['d1', 'd2'], 'claim_in_30d': [0, 1]})] # Mock labels_df read
                    mock_validate_features.side_effect = lambda x: x # Pass through validation

                    with caplog.at_level(logging.INFO):
                        main()
                        assert "Logging null rates for driver features:" in caplog.text
                        assert "Logging label incidence:" in caplog.text
