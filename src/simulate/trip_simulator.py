
import pandas as pd
import numpy as np
import datetime
import uuid
from pathlib import Path

# --- Configuration ---
NUM_DRIVERS = 50
TRIPS_PER_DRIVER = 50
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "simulated"

# Constants for simulation
SECONDS_PER_TRIP_EVENT = 1
AVG_TRIP_DURATION_MINS = 20
START_DATE = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=90)

def generate_drivers_data(num_drivers):
    """Generates a DataFrame of driver information."""
    drivers = {
        "driver_id": [f"driver_{i+1}" for i in range(num_drivers)],
        "age": np.random.randint(18, 70, size=num_drivers),
        "postal_code": [f"{np.random.randint(10000, 99999)}" for _ in range(num_drivers)],
    }
    return pd.DataFrame(drivers)

def generate_vehicles_data(drivers_df):
    """Generates a DataFrame of vehicle information linked to drivers."""
    vehicles = {
        "vehicle_id": [str(uuid.uuid4()) for _ in range(len(drivers_df))],
        "driver_id": drivers_df["driver_id"],
        "year": np.random.randint(2010, 2024, size=len(drivers_df)),
        "make": np.random.choice(["Honda", "Toyota", "Ford", "Chevrolet", "Nissan"], size=len(drivers_df)),
        "model": np.random.choice(["Accord", "Camry", "F-150", "Silverado", "Altima"], size=len(drivers_df)),
    }
    return pd.DataFrame(vehicles)

def simulate_trip_events(trip_id, start_time, duration_seconds):
    """Simulates GPS and accelerometer events for a single trip."""
    num_events = duration_seconds // SECONDS_PER_TRIP_EVENT
    timestamps = pd.to_datetime(np.linspace(start_time.timestamp(), start_time.timestamp() + duration_seconds, num_events), unit='s', utc=True)

    # Simulate speed with some noise and events
    base_speed = np.random.uniform(15, 60, size=num_events)
    speed_noise = np.random.normal(0, 1, size=num_events)
    speed_mph = np.maximum(0, base_speed + speed_noise)
    
    # Add harsh events
    for _ in range(np.random.randint(0, 4)): # This allows 0, 1, 2, or 3 events
        if num_events < 5: continue # Skip if trip is too short for this event
        idx = np.random.randint(0, num_events - 5) # Ensure index is not too close to the end
        event_type = np.random.choice(["brake", "accel"])
        
        # Define the window for the event
        event_slice = slice(idx, idx + 5)
        
        if event_type == "brake":
            speed_mph[event_slice] *= np.linspace(1, 0.5, 5) # Rapidly decrease speed
        else:
            speed_mph[event_slice] *= np.linspace(1, 1.5, 5) # Rapidly increase speed

    # Simulate accelerometer data (simple model)
    accel_x = np.random.normal(0, 0.1, size=num_events) # Lateral
    accel_y = np.diff(speed_mph, prepend=0) * 0.1 # Forward/backward (m/s^2)
    accel_z = np.random.normal(-9.8, 0.05, size=num_events) # Gravity

    # Simulate GPS path (simple random walk)
    lat_start, lon_start = 40.7128, -74.0060 # NYC
    lat_step = speed_mph * SECONDS_PER_TRIP_EVENT / 3600 / 69.0 # Approx conversion
    lon_step = speed_mph * SECONDS_PER_TRIP_EVENT / 3600 / 54.6 # Approx conversion
    latitudes = lat_start + np.cumsum(np.random.normal(0, lat_step))
    longitudes = lon_start + np.cumsum(np.random.normal(0, lon_step))

    events = {
        "trip_id": trip_id,
        "timestamp_utc": timestamps,
        "latitude": latitudes,
        "longitude": longitudes,
        "speed_mph": speed_mph,
        "accelerometer_x": accel_x,
        "accelerometer_y": accel_y,
        "accelerometer_z": accel_z,
    }
    return pd.DataFrame(events)

def generate_all_data(num_drivers, trips_per_driver):
    """Generates and saves all simulated dataframes."""
    print("Generating synthetic data...")
    
    drivers_df = generate_drivers_data(num_drivers)
    vehicles_df = generate_vehicles_data(drivers_df)
    
    all_trips = []
    all_events = []

    for i, vehicle in vehicles_df.iterrows():
        print(f"Simulating for vehicle {i+1}/{len(vehicles_df)}...")
        for _ in range(trips_per_driver):
            trip_id = str(uuid.uuid4())
            
            # Random trip start time in the last 90 days
            random_days = np.random.uniform(0, 90)
            random_seconds = np.random.uniform(0, 24*3600)
            start_time = START_DATE + datetime.timedelta(days=random_days, seconds=random_seconds)
            
            # Random trip duration
            duration_seconds = int(np.random.normal(AVG_TRIP_DURATION_MINS, 10) * 60)
            duration_seconds = max(60, duration_seconds) # Min 1 minute
            end_time = start_time + datetime.timedelta(seconds=duration_seconds)

            all_trips.append({
                "trip_id": trip_id,
                "vehicle_id": vehicle["vehicle_id"],
                "start_time_utc": start_time,
                "end_time_utc": end_time,
            })
            
            trip_events_df = simulate_trip_events(trip_id, start_time, duration_seconds)
            all_events.append(trip_events_df)

    trips_df = pd.DataFrame(all_trips)
    events_df = pd.concat(all_events, ignore_index=True)

    # --- Save Data ---
    print(f"Saving data to {DATA_DIR}...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    drivers_df.to_parquet(DATA_DIR / "drivers.parquet")
    vehicles_df.to_parquet(DATA_DIR / "vehicles.parquet")
    trips_df.to_parquet(DATA_DIR / "trips.parquet")
    events_df.to_parquet(DATA_DIR / "events.parquet")
    
    print("Data simulation complete.")
    print(f"  - {len(drivers_df)} drivers")
    print(f"  - {len(vehicles_df)} vehicles")
    print(f"  - {len(trips_df)} trips")
    print(f"  - {len(events_df)} events")

if __name__ == "__main__":
    generate_all_data(NUM_DRIVERS, TRIPS_PER_DRIVER)