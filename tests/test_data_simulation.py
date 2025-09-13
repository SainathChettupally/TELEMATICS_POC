import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch
from src.simulate.trip_simulator import generate_all_data, validate_simulated_data

# Define a temporary data directory for testing
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "test_simulated"

@pytest.fixture(scope="module", autouse=True)
def setup_teardown_test_data_dir():
    """Ensures a clean test data directory for simulation outputs."""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Clean up after tests
    for f in TEST_DATA_DIR.glob("*"):
        f.unlink()
    TEST_DATA_DIR.rmdir()

def test_simulated_data_ranges():
    """
    Tests that the generated simulated data falls within expected ranges.
    This implicitly runs generate_all_data and then validates its output.
    """
    with patch('src.simulate.trip_simulator.DATA_DIR', TEST_DATA_DIR):
        generate_all_data(num_drivers=2, trips_per_driver=2) # Generate a small dataset for testing

        events_df = pd.read_parquet(TEST_DATA_DIR / "events.parquet")
        validate_simulated_data(events_df) # This should not raise an error
        
        # Assert specific ranges for sanity check, though validate_simulated_data does this
        assert (events_df['speed_mph'] >= 0).all()
        assert (events_df['speed_mph'] <= 120).all()
        assert (events_df['accelerometer_x'] >= -5).all()
        assert (events_df['accelerometer_x'] <= 5).all()
        # Add more specific assertions if needed for other columns

def test_validate_simulated_data_out_of_range_speed():
    """Tests that validate_simulated_data raises ValueError for out-of-range speed."""
    events_df = pd.DataFrame({
        'trip_id': ['t1'],
        'timestamp_utc': [pd.Timestamp.now()],
        'latitude': [0], 'longitude': [0],
        'speed_mph': [150], # Out of range
        'accelerometer_x': [0], 'accelerometer_y': [0], 'accelerometer_z': [0]
    })
    with pytest.raises(ValueError, match="Simulated speed_mph out of range"):
        validate_simulated_data(events_df)

def test_validate_simulated_data_out_of_range_accel():
    """Tests that validate_simulated_data raises ValueError for out-of-range accelerometer."""
    events_df = pd.DataFrame({
        'trip_id': ['t1'],
        'timestamp_utc': [pd.Timestamp.now()],
        'latitude': [0], 'longitude': [0],
        'speed_mph': [50],
        'accelerometer_x': [100], # Out of range
        'accelerometer_y': [0], 'accelerometer_z': [0]
    })
    with pytest.raises(ValueError, match="Simulated accelerometer_x out of range"):
        validate_simulated_data(events_df)
