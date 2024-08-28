import os
import numpy as np
import xarray as xr
import pandas as pd
from tqdm import tqdm

from CONFIG import end_year, engine, file_name
start_year = 1940

print("Averaging monthly temperatures across the whole grid with corrected hemisphere weighting...")

# Function to convert Kelvin to Fahrenheit
def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * 9/5 + 32

# Function to convert Kelvin to Celsius
def kelvin_to_celsius(kelvin):
    return kelvin - 273.15

# Open the NetCDF file using xarray
dirname = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(dirname, "data", "input", file_name)
ds = xr.open_dataset(file_path, engine=engine)

# Filter the dataset for expver = 1
if (engine == "netcdf4"):
    ds = ds.sel(expver=1)

# Filter the dataset for the required years
ds = ds.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))

# Initialize a list to store monthly mean temperatures
monthly_mean_temps = []

# Loop through each year and each month to calculate the mean temperature
for year in tqdm(range(start_year, end_year + 1), desc="Calculating monthly means"):
    for month in range(1, 13):
        # Select the data for the specific year and month
        monthly_data = ds["t2m"].sel(time=str(year) + f"-{month:02d}")
        
        try:
            # Northern Hemisphere
            monthly_data_north = monthly_data.where(ds.latitude >= 0, drop=True)
            weights_north = np.cos(np.deg2rad(monthly_data_north.latitude))
            weights_north = weights_north / weights_north.sum()
            weighted_mean_north = (monthly_data_north * weights_north).sum(dim="latitude") / weights_north.sum()
            mean_temp_north = weighted_mean_north.mean(dim="time").mean(dim="longitude").item()

            # Append results for north hemisphere
            if not np.isnan(mean_temp_north):
                monthly_mean_temps.append([year, month, "north", mean_temp_north])

            # Southern Hemisphere
            monthly_data_south = monthly_data.where(ds.latitude < 0, drop=True)
            weights_south = np.cos(np.deg2rad(monthly_data_south.latitude))
            weights_south = weights_south / weights_south.sum()
            weighted_mean_south = (monthly_data_south * weights_south).sum(dim="latitude") / weights_south.sum()
            mean_temp_south = weighted_mean_south.mean(dim="time").mean(dim="longitude").item()
            
            # Append results for south hemisphere
            if not np.isnan(mean_temp_south):
                monthly_mean_temps.append([year, month, "south", mean_temp_south])
                
        except Exception as e:
            print(f"Error processing year {year}, month {month}: {e}")
            monthly_mean_temps.append([year, month, "unknown", np.nan])

# Create a DataFrame with the results
monthly_mean_temp_df = pd.DataFrame(monthly_mean_temps, columns=["year", "month", "hemisphere", "temp_k"])

# Add a column for temperature in Fahrenheit
monthly_mean_temp_df["temp_f"] = monthly_mean_temp_df["temp_k"].apply(kelvin_to_fahrenheit)
monthly_mean_temp_df["temp_c"] = monthly_mean_temp_df["temp_k"].apply(kelvin_to_celsius)

# Output the DataFrame to a CSV file
output_dir = os.path.join(dirname, "data", "output")
os.makedirs(output_dir, exist_ok=True)
output_file = "monthly_mean_temperatures.csv"
monthly_mean_temp_df.to_csv(os.path.join(output_dir, output_file), index=False)

print(f"Saved data/output/{output_file}\n\n")
