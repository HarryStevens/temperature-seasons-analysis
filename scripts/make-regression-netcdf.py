import os
import numpy as np
import xarray as xr
from tqdm import tqdm
from scipy.stats import linregress

from CONFIG import start_year, end_year

print("Calculating the linear regression slopes of year vs. temperature for summer and winter in each grid cell.")

# Define the directory for the yearly files
dirname = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(dirname, "data", "output", "year")
output_file_name = f"seasonal_slopes_{start_year}_{end_year}.nc"
output_file = os.path.join(dirname, "data", "output", output_file_name)

# Create a years range
years = range(start_year, end_year + 1)

# Create a combined dataset for all years
all_years_data = []

for year in tqdm(years, desc="Loading year files"):
    year_file = os.path.join(input_dir, f"seasonal_temps_{year}.nc")
    if not os.path.exists(year_file):
        print(f"File for year {year} not found, skipping.")
        continue

    ds = xr.open_dataset(year_file, engine="netcdf4")
    all_years_data.append(ds)

# Combine all datasets into one
combined_ds = xr.concat(all_years_data, dim='year')

# Initialize arrays to store slopes for summer and winter
lats = combined_ds.latitude.values
lons = combined_ds.longitude.values

summer_slopes = np.full((len(lats), len(lons)), np.nan)
winter_slopes = np.full((len(lats), len(lons)), np.nan)

# A function for calculating the regression
def calculate_regression(temps, array, i, j):
    if np.count_nonzero(~np.isnan(temps)) >= 2:
        slope, _, _, _, _ = linregress(years, temps)
        array[i, j] = slope

# Loop through each grid cell to calculate the linear regression slopes
for i in tqdm(range(len(lats)), desc="Processing cells", unit="cell"):
    for j in range(len(lons)):
        # Extract all season data at once for the given latitude and longitude
        seasonal_data = combined_ds[['summer', 'winter']].isel(latitude=i, longitude=j)
        
        # Convert to numpy arrays, then to python float
        summer_temps = seasonal_data['summer'].values.astype(float)
        winter_temps = seasonal_data['winter'].values.astype(float)

        # Perform linear regression if there are enough valid data points
        calculate_regression(summer_temps, summer_slopes, i, j)
        calculate_regression(winter_temps, winter_slopes, i, j)

# Create a new dataset with the calculated slopes
slope_ds = xr.Dataset(
    {
        "summer_slope": (["latitude", "longitude"], summer_slopes),
        "winter_slope": (["latitude", "longitude"], winter_slopes),
    },
    coords={
        "latitude": lats,
        "longitude": lons
    }
)

# Save the slope data to a NetCDF file
os.makedirs(os.path.dirname(output_file), exist_ok=True)
slope_ds.to_netcdf(output_file, engine="netcdf4")

# Print confirmation message
print(f"Saved {output_file_name}\n\n")
