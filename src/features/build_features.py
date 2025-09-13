import pandas as pd
import numpy as np
import yaml
import logging
from pathlib import Path

# --- Configuration ---
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "simulated"
FEATURES_DIR = BASE_DIR / "data" / "features"
CONFIG_PATH = Path(__file__).parent / "feature_config.yaml"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Feature Engineering Constants ---
HARSH_BRAKE_THRESHOLD = -5.0  # m/s^2
RAPID_ACCEL_THRESHOLD = 5.0   # m/s^2
SPEEDING_THRESHOLD_MPH = 70.0
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 5
STOP_GO_SPEED_THRESHOLD = 5 # Speed below which is considered 'stopped'

def load_data():
    """Loads the simulated data from parquet files."""
    print("Loading data...")
    events_df = pd.read_parquet(DATA_DIR / "events.parquet")
    trips_df = pd.read_parquet(DATA_DIR / "trips.parquet")
    vehicles_df = pd.read_parquet(DATA_DIR / "vehicles.parquet")
    
    # Merge to get driver_id on each event
    data = pd.merge(events_df, trips_df, on="trip_id")
    data = pd.merge(data, vehicles_df[['vehicle_id', 'driver_id']], on="vehicle_id")
    return data

def calculate_trip_features(df):
    """Calculates features for each individual trip."""
    print("Calculating trip-level features...")
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
    df = df.sort_values(by=['trip_id', 'timestamp_utc'])

    trip_features = {}
    
    # Time-based features
    df['hour'] = df['timestamp_utc'].dt.hour
    df['is_night'] = (df['hour'] >= NIGHT_START_HOUR) | (df['hour'] < NIGHT_END_HOUR)
    
    # Distance
    # Approximate distance covered in one event interval (in miles)
    df['distance_miles'] = df['speed_mph'] * (df.groupby('trip_id')['timestamp_utc'].diff().dt.total_seconds().fillna(0) / 3600.0)

    # Event-based features
    df['harsh_brake'] = df['accelerometer_y'] < HARSH_BRAKE_THRESHOLD
    df['rapid_accel'] = df['accelerometer_y'] > RAPID_ACCEL_THRESHOLD
    df['is_speeding'] = df['speed_mph'] > SPEEDING_THRESHOLD_MPH
    
    # Stop-and-go
    df['is_stopped'] = df['speed_mph'] < STOP_GO_SPEED_THRESHOLD
    df['stop_go_event'] = (df['is_stopped'].diff() == -1) & (df['is_stopped'] == False)

    # Aggregate by trip
    agg_funcs = {
        'distance_miles': 'sum',
        'is_night': 'mean',
        'harsh_brake': 'sum',
        'rapid_accel': 'sum',
        'is_speeding': 'mean',
        'stop_go_event': 'sum',
        'speed_mph': ['mean', 'median', lambda x: x.quantile(0.95)]
    }
    
    trip_df = df.groupby('trip_id').agg(agg_funcs).reset_index()
    
    # Flatten multi-index columns
    trip_df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in trip_df.columns.values]
    trip_df = trip_df.rename(columns={
        'distance_miles_sum': 'miles_driven',
        'is_night_mean': 'night_driving_percentage',
        'harsh_brake_sum': 'harsh_brakes',
        'rapid_accel_sum': 'rapid_accels',
        'is_speeding_mean': 'speeding_percentage',
        'stop_go_event_sum': 'stop_go_events',
        'speed_mph_mean': 'mean_speed',
        'speed_mph_median': 'p50_speed',
        'speed_mph_<lambda_0>': 'p95_speed',
        'trip_id_': 'trip_id'
    })
    
    return trip_df

def aggregate_driver_features(trip_df, trips_df, vehicles_master_df):
    """Aggregates trip features to the driver level using a 30-day rolling window."""
    print("Aggregating features at driver level with a 30-day rolling window...")
    
    # Add driver_id and start_time_utc to trip features
    merged_df = pd.merge(trip_df, trips_df[['trip_id', 'vehicle_id', 'start_time_utc']], on='trip_id')
    merged_df = pd.merge(merged_df, vehicles_master_df[['vehicle_id', 'driver_id']], on='vehicle_id')
    
    # Convert start_time_utc to datetime
    merged_df['start_time_utc'] = pd.to_datetime(merged_df['start_time_utc'])
    
    # Sort by start_time_utc
    merged_df = merged_df.sort_values('start_time_utc')
    
    # Set start_time_utc as index
    merged_df = merged_df.set_index('start_time_utc')

    # Normalize features by distance
    merged_df['harsh_brakes_per_100mi'] = (merged_df['harsh_brakes'] / merged_df['miles_driven']) * 100
    merged_df['rapid_accels_per_100mi'] = (merged_df['rapid_accels'] / merged_df['miles_driven']) * 100
    merged_df.replace([np.inf, -np.inf], 0, inplace=True) # Handle trips with 0 distance
    merged_df.fillna(0, inplace=True)

    # Cap features to handle extreme outliers
    merged_df['harsh_brakes_per_100mi'] = merged_df['harsh_brakes_per_100mi'].clip(upper=500)
    merged_df['rapid_accels_per_100mi'] = merged_df['rapid_accels_per_100mi'].clip(upper=500)

    # Define aggregation functions
    driver_agg_funcs = {
        'miles_driven': 'sum',
        'night_driving_percentage': 'mean',
        'harsh_brakes_per_100mi': 'mean',
        'rapid_accels_per_100mi': 'mean',
        'speeding_percentage': 'mean',
        'stop_go_events': 'sum',
        'mean_speed': 'mean',
        'p50_speed': 'mean',
        'p95_speed': 'mean',
    }

    # Group by driver_id and apply rolling window aggregation
    driver_features = merged_df.groupby('driver_id').rolling('30D').agg(driver_agg_funcs).reset_index()
    
    # Rename columns
    driver_features = driver_features.rename(columns={'start_time_utc': 'window_end_date'})

    return driver_features

def validate_features(df):
    """
    Enforces data validation ranges for key features.
    Raises ValueError if data is outside expected ranges.
    """
    logger.info("Enforcing data validation ranges...")
    # Define expected ranges for features
    validation_ranges = {
        'miles_driven': (0, 10000),
        'night_driving_percentage': (0, 1),
        'harsh_brakes_per_100mi': (0, 500),
        'rapid_accels_per_100mi': (0, 500),
        'speeding_percentage': (0, 1),
        'stop_go_events': (0, 1000),
        'mean_speed': (0, 100),
        'p50_speed': (0, 100),
    }

    for feature, (min_val, max_val) in validation_ranges.items():
        if feature in df.columns:
            if not ((df[feature] >= min_val) & (df[feature] <= max_val)).all():
                raise ValueError(f"Feature '{feature}' has values outside expected range [{min_val}, {max_val}]")
            logger.info(f"  Feature '{feature}' validated successfully.")
        else:
            logger.warning(f"  Feature '{feature}' not found in DataFrame for validation.")
    logger.info("Data validation complete.")
    return df

def main():
    """Main function to run the feature engineering pipeline."""
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
        print("Feature config loaded:", config)

    # Load raw data
    events_df = pd.read_parquet(DATA_DIR / "events.parquet")
    trips_df = pd.read_parquet(DATA_DIR / "trips.parquet")
    vehicles_df = pd.read_parquet(DATA_DIR / "vehicles.parquet")

    # Merge dataframes
    full_data = pd.merge(events_df, trips_df, on="trip_id")
    full_data = pd.merge(full_data, vehicles_df[['vehicle_id', 'driver_id']], on="vehicle_id")
    # Convert driver_id from string to integer
    full_data['driver_id'] = full_data['driver_id'].str.replace('driver_', '').astype(int)
    vehicles_df['driver_id'] = vehicles_df['driver_id'].str.replace('driver_', '').astype(int)

    # Calculate trip-level features
    trip_features_df = calculate_trip_features(full_data)

    # Aggregate to driver-level features
    driver_features_df = aggregate_driver_features(trip_features_df, trips_df, vehicles_df)

    # Validate features
    driver_features_df = validate_features(driver_features_df)

    # Log null rates
    logger.info("Logging null rates for driver features:")
    null_rates = driver_features_df.isnull().sum() / len(driver_features_df)
    for col, rate in null_rates.items():
        if rate > 0:
            logger.warning(f"  {col}: {rate:.2%}")
        else:
            logger.info(f"  {col}: {rate:.2%}")

    # --- Create and Save Labels ---
    print("Creating labels...")
    high_risk_threshold = driver_features_df['p95_speed'].quantile(0.8)
    labels = (driver_features_df['p95_speed'] > high_risk_threshold).astype(int)
    labels_df = pd.DataFrame({'driver_id': driver_features_df['driver_id'], 'claim_in_30d': labels})
    
    # Log label incidence
    logger.info("Logging label incidence:")
    label_incidence = labels_df['claim_in_30d'].value_counts(normalize=True)
    for label, incidence in label_incidence.items():
        logger.info(f"  Label {label}: {incidence:.2%}")
    
    labels_path = BASE_DIR / "data" / "labels.parquet"
    labels_df.to_parquet(labels_path)
    print(f"Labels created and saved to {labels_path}")

    # --- Save Features (without label-related columns) ---
    print(f"Saving driver features to {FEATURES_DIR}...")
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    # Exclude the column used to create the label to prevent leakage
    features_to_save = driver_features_df.drop(columns=['p95_speed'])
    features_to_save.to_parquet(FEATURES_DIR / "driver_features.parquet")

    print("Feature engineering complete.")
    print(f"  - {len(driver_features_df)} drivers with features")
    print("  - Features: ", features_to_save.columns.tolist())

if __name__ == "__main__":
    main()