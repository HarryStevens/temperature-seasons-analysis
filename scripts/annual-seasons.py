import os
import numpy as np
import xarray as xr
from tqdm import tqdm  # Import tqdm for progress bars

from CONFIG import start_year, end_year, engine, file_name

# Function to determine hemisphere
def get_hemisphere(latitude):
    return "north" if latitude >= 0 else "south"

# Function to convert Kelvin to Fahrenheit
def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * 9/5 + 32

# Function to get the season based on month and hemisphere
def get_season(month, hemisphere):
    if hemisphere == "north":
        if month in [6, 7, 8]:
            return "summer"
        if month in [12, 1, 2]:
            return "winter"
    elif hemisphere == "south":
        if month in [6, 7, 8]:
            return "winter"
        if month in [12, 1, 2]:
            return "summer"
    return None  # For months not included in summer or winter

# Define the file path
dirname = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(dirname, "data", "input", file_name)
output_dir = os.path.join(dirname, "data", "output", "year")

# Open the gridded file from Copernicus using xarray
ds = xr.open_dataset(file_path, engine=engine)

# Filter the dataset for expver = 1
if engine == "netcdf4":
    ds = ds.sel(expver=1)

# Filter the dataset for the required years
print("Filtering the dataset for the required years")
ds = ds.sel(time=slice(f"{start_year-1}-01-01", f"{end_year}-12-31"))

# Adjust longitudes to be in the range -180 to 180
ds = ds.assign_coords(longitude=(((ds.longitude + 180) % 360) - 180)).sortby('longitude')

# Loop through each year to calculate seasonal temperatures
for year in tqdm(range(start_year, end_year + 1), desc="Processing years"):

    # Filter data for the current and previous year (for winter calculations)
    yearly_data = ds["t2m"].sel(time=slice(f"{year-1}-12-01", f"{year}-08-31"))

    # Determine the latitude and longitude values
    lats = yearly_data.latitude.values
    lons = yearly_data.longitude.values
    
    # Initialize arrays to store seasonal temperature values
    seasonal_temps = {
        "summer": np.full((len(lats), len(lons)), np.nan),
        "winter": np.full((len(lats), len(lons)), np.nan)
    }
    
    # Iterate over each month to calculate seasonal temperatures
    for month in range(1, 13):
        # Determine the hemisphere for each grid cell
        hemisphere = np.vectorize(get_hemisphere)(lats)
        
        # Determine the season for each grid cell
        season = np.vectorize(get_season)(month, hemisphere)
        
        # Filter the data for the current month
        monthly_data = yearly_data.sel(time=yearly_data.time.dt.month == month)
        
        if monthly_data.time.size > 0:
            # Calculate the mean temperature for the month
            mean_temp = monthly_data.mean(dim="time")
            mean_temp_f = kelvin_to_fahrenheit(mean_temp)
            
            # Update the seasonal temperatures
            for s in seasonal_temps:
                mask = (season == s)
                if np.any(mask):
                    seasonal_temps[s][mask] = mean_temp_f.values[mask]
    
    # Create a new dataset with seasonal temperatures
    seasonal_ds = xr.Dataset(
        {season: (["latitude", "longitude"], seasonal_temps[season]) for season in seasonal_temps},
        coords={
            "latitude": lats,
            "longitude": lons
        }
    )
    
    # Define output file path
    output_file = os.path.join(output_dir, f"seasonal_temps_{year}.nc")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save to NetCDF file
    seasonal_ds.to_netcdf(output_file, engine="netcdf4")

print("All seasonal temperatures files have been saved to the data/output/year folder.")
