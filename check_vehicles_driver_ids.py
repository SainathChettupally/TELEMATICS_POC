import pandas as pd

file_path = "c:\\Users\\csain\\Downloads\\Telematics AI\\data\\simulated\\vehicles.parquet"
df = pd.read_parquet(file_path)
print("Unique driver_ids from vehicles.parquet:")
for driver_id in df['driver_id'].unique():
    print(driver_id)
