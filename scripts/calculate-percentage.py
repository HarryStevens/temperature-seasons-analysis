import os
import numpy as np
import xarray as xr
from tqdm import tqdm
import json

from CONFIG import start_year, end_year

# Define file paths
dirname = os.path.dirname(os.path.abspath(__file__))
input_file_name = f"seasonal_slopes_{start_year}_{end_year}.nc"
input_file_path = os.path.join(dirname, "data", "output", input_file_name)
output_file_path = os.path.join(dirname, "data", "output", "percentage-analysis.json")

print(f"Calculating % of Earth's surface where certain conditions are met in {input_file_name}")

# Load the NetCDF file using xarray
ds = xr.open_dataset(input_file_path)

# Extract latitude, summer_slope, and winter_slope
latitudes = ds["latitude"]
winter_slope = ds["winter_slope"]
summer_slope = ds["summer_slope"]

# Create a boolean mask where winter_slope > summer_slope
winter_faster_mask = winter_slope > summer_slope

# Create a boolean mask where both summer_slope and winter_slope are negative
both_negative_mask = (summer_slope < 0) & (winter_slope < 0)
both_positive_mask = (summer_slope > 0) & (winter_slope > 0)
winter_positive_summer_negative_mask = (summer_slope > 0) & (winter_slope < 0)
summer_positive_winter_negative_mask = (summer_slope < 0) & (winter_slope > 0)

# Calculate latitude weights (cosine of latitude)
latitude_weights = np.cos(np.deg2rad(latitudes))

# Initialize variables for calculating areas
earth_area = 0
winter_faster_area = 0
both_negative_area = 0
both_positive_area = 0
winter_positive_summer_negative_area = 0
summer_positive_winter_negative_area = 0

# Iterate over the data with progress logging using tqdm
for lat_idx in tqdm(range(len(latitudes)), desc="Processing latitude bands"):
    lat_weight = latitude_weights[lat_idx].item()
    for lon_idx in range(len(ds["longitude"])):
        if winter_faster_mask.isel(latitude=lat_idx, longitude=lon_idx).item():
            winter_faster_area += lat_weight
        if both_negative_mask.isel(latitude=lat_idx, longitude=lon_idx).item():
            both_negative_area += lat_weight
        if both_positive_mask.isel(latitude=lat_idx, longitude=lon_idx).item():
            both_positive_area += lat_weight
        if winter_positive_summer_negative_mask.isel(latitude=lat_idx, longitude=lon_idx).item():
            winter_positive_summer_negative_area += lat_weight
        if summer_positive_winter_negative_mask.isel(latitude=lat_idx, longitude=lon_idx).item():
            summer_positive_winter_negative_area += lat_weight
        earth_area += lat_weight

# Calculate the percentage of Earth's surface for each condition
winter_faster_percentage = (winter_faster_area / earth_area) * 100
both_negative_percentage = (both_negative_area / earth_area) * 100
both_positive_percentage = (both_positive_area / earth_area) * 100
winter_positive_summer_negative_percentage = (winter_positive_summer_negative_area / earth_area) * 100
summer_positive_winter_negative_percentage = (summer_positive_winter_negative_area / earth_area) * 100

# Prepare the output data
output_data = {
    "earth_area": earth_area,
    "winter_faster_area": winter_faster_area,
    "winter_faster_percentage": winter_faster_percentage,
    "both_negative_area": both_negative_area,
    "both_negative_percentage": both_negative_percentage,
    "both_positive_area": both_positive_area,
    "both_positive_percentage": both_positive_percentage,
    "winter_positive_summer_negative_area": winter_positive_summer_negative_area,
    "winter_positive_summer_negative_percentage": winter_positive_summer_negative_percentage,
    "summer_positive_winter_negative_area": summer_positive_winter_negative_area,
    "summer_positive_winter_negative_percentage": summer_positive_winter_negative_percentage
}

# Save the results to a JSON file
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
with open(output_file_path, "w") as json_file:
    json.dump(output_data, json_file, indent=4)

print(f"Saved results to {output_file_path}")
