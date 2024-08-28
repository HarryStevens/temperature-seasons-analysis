import os
import numpy as np
import xarray as xr
import pandas as pd
from tqdm import tqdm

from CONFIG import end_year, engine, file_name
start_year = 1940

print("Averaging annual temperatures across the whole grid with corrected latitude weighting...")

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

# Filter the dataset for expver = 1
if (engine == "netcdf4"):
    ds = ds.sel(expver=1)

# Filter the dataset for the required years
ds = ds.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))

# Calculate the latitude weights (cosine of latitude)
weights = np.cos(np.deg2rad(ds["latitude"]))

# Normalize the weights so they sum to 1 over the latitude dimension
weights = weights / weights.sum()

# Initialize a list to store annual mean temperatures
annual_mean_temps = []

# Loop through each year and calculate the mean temperature
for year in tqdm(range(start_year, end_year + 1), desc="Calculating annual means"):
    yearly_data = ds["t2m"].sel(time=str(year))

    try:
        # Check if yearly_data has the expected dimensions
        if len(yearly_data.dims) >= 3 and all(dim in yearly_data.dims for dim in ["time", "latitude", "longitude"]):
            # Apply latitude weights and calculate the weighted mean temperature
            weighted_mean = (yearly_data * weights).sum(dim="latitude") / weights.sum()
            annual_mean_temp = weighted_mean.mean(dim="time").mean(dim="longitude")

            if annual_mean_temp.size == 1:
                annual_mean_temp_value = annual_mean_temp.item()
            else:
                print(f"Warning: Mean temperature for year {year} did not reduce to a single value.")
                annual_mean_temp_value = np.nan
        else:
            print(f"Warning: Unexpected dimensions for year {year}.")
            annual_mean_temp_value = np.nan
    except Exception as e:
        print(f"Error processing year {year}: {e}")
        annual_mean_temp_value = np.nan
    
    annual_mean_temps.append([year, annual_mean_temp_value])

# Create a DataFrame with the results
annual_mean_temp_df = pd.DataFrame(annual_mean_temps, columns=["year", "temp_k"])

# Add a column for temperature in Fahrenheit
annual_mean_temp_df["temp_f"] = annual_mean_temp_df["temp_k"].apply(kelvin_to_fahrenheit)
annual_mean_temp_df["temp_c"] = annual_mean_temp_df["temp_k"].apply(kelvin_to_celsius)

# Output the DataFrame to a CSV file
output_dir = os.path.join(dirname, "data", "output")
os.makedirs(output_dir, exist_ok=True)
output_file = "annual_mean_temperatures.csv"
annual_mean_temp_df.to_csv(os.path.join(output_dir, output_file), index=False)

print(f"Saved data/output/{output_file}\n\n")
