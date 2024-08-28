import os
import numpy as np
import xarray as xr
import pandas as pd
from tqdm import tqdm

from CONFIG import end_year, engine, file_name
start_year = 1940

print("Averaging annual temperatures for the Arctic and Antarctic regions...")

# Function to convert Kelvin to Fahrenheit
def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * 9/5 + 32

# Function to convert Kelvin to Celsius
def kelvin_to_celsius(kelvin):
    return kelvin - 273.15

# Open the gridded file using xarray
dirname = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(dirname, "data", "input", file_name)
ds = xr.open_dataset(file_path, engine=engine)

# Filter the dataset for expver = 1 if using netcdf4
if engine == "netcdf4":
    ds = ds.sel(expver=1)

# Filter the dataset for the required years
ds = ds.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))

# Define latitude ranges for Arctic and Antarctic
arctic_ds = ds.sel(latitude=slice(90, 66 + 34/60))
antarctic_ds = ds.sel(latitude=slice(-(66 + 34/60), -90))

# Function to calculate weighted mean temperature for a region
def calculate_weighted_mean_temp(region_ds, year):
    yearly_data = region_ds["t2m"].sel(time=str(year))

    try:
        # Check if yearly_data has the expected dimensions
        if len(yearly_data.dims) >= 3 and all(dim in yearly_data.dims for dim in ["time", "latitude", "longitude"]):
            # Calculate latitude weights (cosine of latitude)
            weights = np.cos(np.deg2rad(yearly_data["latitude"]))
            # Normalize the weights so they sum to 1 over the latitude dimension
            weights = weights / weights.sum()
            # Apply latitude weights and calculate the weighted mean temperature
            weighted_mean = (yearly_data * weights).sum(dim="latitude") / weights.sum()
            annual_mean_temp = weighted_mean.mean(dim="time").mean(dim="longitude")
            if annual_mean_temp.size == 1:
                return annual_mean_temp.item()
            else:
                print(f"Warning: Mean temperature for year {year} did not reduce to a single value.")
                return np.nan
        else:
            print(f"Warning: Unexpected dimensions for year {year}.")
            return np.nan
    except Exception as e:
        print(f"Error processing year {year} in region: {e}")
        return np.nan

# Initialize a list to store results
results = []

# Loop through each year and calculate the mean temperature for each region
for year in tqdm(range(start_year, end_year + 1), desc="Calculating annual means"):
    arctic_temp = calculate_weighted_mean_temp(arctic_ds, year)
    antarctic_temp = calculate_weighted_mean_temp(antarctic_ds, year)
    
    results.append([year, "arctic", arctic_temp, kelvin_to_fahrenheit(arctic_temp), kelvin_to_celsius(arctic_temp)])
    results.append([year, "antarctic", antarctic_temp, kelvin_to_fahrenheit(antarctic_temp), kelvin_to_celsius(antarctic_temp)])

# Create a DataFrame with the results
results_df = pd.DataFrame(results, columns=["year", "region", "temp_k", "temp_f", "temp_c"])

# Output the DataFrame to a CSV file
output_dir = os.path.join(dirname, "data", "output")
os.makedirs(output_dir, exist_ok=True)
output_file = "annual_mean_temperatures_poles.csv"
results_df.to_csv(os.path.join(output_dir, output_file), index=False)

print(f"Saved data/output/{output_file}\n\n")
