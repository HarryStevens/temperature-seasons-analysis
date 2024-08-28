import os
import json
import numpy as np
import xarray as xr
from tqdm import tqdm
from scipy.stats import linregress

from CONFIG import start_year, end_year
# list of years
year_list = list(range(start_year, end_year + 1))

# Define the path to the directory with annual temperature files
annual_temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output", "year")

# Load city grid cells data
city_grid_cells_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output", "city_grid_cells.json")
with open(city_grid_cells_file, "r") as f:
    city_grid_cells = json.load(f)

# Load the original cities data
cities_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "input", "cities.json")
with open(cities_file_path, "r") as f:
    cities = {city["id"]: city for city in json.load(f)}

# Create the output directory if it doesn't exist
city_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output", "city")
os.makedirs(city_output_dir, exist_ok=True)

# Function to calculate linear regression slope and intercept
def calculate_slope_intercept(years, data):
    if np.all(np.isnan(data)):
        return np.nan, np.nan
    slope, intercept, _, _, _ = linregress(years, data)
    return slope, intercept

# Dictionary to hold data for all cities
city_data = {city["id"]: {"years": [], "summer": [], "winter": []} for city in city_grid_cells}

# Create a combined dataset for all years
all_years_data = []

for year in tqdm(range(start_year, end_year + 1), desc="Loading year files"):
    year_file = os.path.join(annual_temp_dir, f"seasonal_temps_{year}.nc")
    if not os.path.exists(year_file):
        print(f"File for year {year} not found, skipping.")
        continue

    ds = xr.open_dataset(year_file)
    all_years_data.append(ds)

# Combine all datasets into one
combined_ds = xr.concat(all_years_data, dim='year')

# Iterate over each city and extract the seasonal temperatures
for city in tqdm(city_grid_cells, desc="Processing cities"):
    city_id = city["id"]
    
    lat_index = city["grid_lat_index"]
    lon_index = city["grid_lon_index"]
    lat = city["lat"]
    lon = city["lon"]

    # Extract all season data at once for the given latitude and longitude
    seasonal_data = combined_ds[['summer', 'winter']].isel(latitude=lat_index, longitude=lon_index)
    
    # Convert to numpy arrays, then to python float
    summer_temps = seasonal_data['summer'].values.astype(float)
    winter_temps = seasonal_data['winter'].values.astype(float)

    # Calculate slopes and intercepts for each season
    summer_slope, summer_intercept = calculate_slope_intercept(year_list, summer_temps)
    winter_slope, winter_intercept = calculate_slope_intercept(year_list, winter_temps)

    # Structure the output data for the city
    city_output_data = {
        "id": city_id,
        "name": cities[city_id]["name"],
        "lat": lat,
        "lon": lon,
        "lat_index": lat_index,
        "lon_index": lon_index,
        "data": [{"year": y, "summer": s, "winter": w} for y, s, w in zip(year_list, summer_temps, winter_temps)],
        "slopes": {
            "summer": summer_slope,
            "winter": winter_slope
        },
        "intercepts": {
            "summer": summer_intercept,
            "winter": winter_intercept
        }
    }

    # Output the results to a JSON file for the city
    output_file_path = os.path.join(city_output_dir, f"{city_id}.json")
    with open(output_file_path, "w") as f:
        json.dump(city_output_data, f, indent=4)

print("City seasonal temperatures extraction and slope/intercept calculation complete.\n\n")
