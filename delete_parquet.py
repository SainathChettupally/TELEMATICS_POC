import os

file_path = "c:\\Users\\csain\\Downloads\\Telematics AI\\data\\features\\driver_features.parquet"
os.remove(file_path)
print(f"Successfully removed {file_path}")
