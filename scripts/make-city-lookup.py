import os
import json
import numpy as np
import xarray as xr
from scipy.spatial import cKDTree
from tqdm import tqdm

from CONFIG import file_name, engine

# Open the GRIB2 file using xarray
dirname = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(dirname, "data", "input", file_name)
ds = xr.open_dataset(file_path, engine=engine)

# Adjust longitudes to be in the range -180 to 180
ds = ds.assign_coords(longitude=(((ds.longitude + 180) % 360) - 180)).sortby("longitude")

# Extract latitude and longitude arrays
lats = ds["latitude"].values
lons = ds["longitude"].values

# Create a meshgrid of latitude and longitude
lon_grid, lat_grid = np.meshgrid(lons, lats)

# Flatten the latitude and longitude arrays to create points for KDTree
points = np.vstack([lat_grid.ravel(), lon_grid.ravel()]).T

# Build a KDTree for fast spatial indexing
tree = cKDTree(points)

# Function to find the nearest grid cell for a given latitude and longitude
def find_nearest_grid_cell(lat, lon):
    distance, index = tree.query([lat, lon])
    lat_index, lon_index = np.unravel_index(index, lat_grid.shape)
    return distance, index, lat_index, lon_index

# Load cities data from JSON file
cities_file_path = os.path.join(dirname, "data", "input", "cities.json")
with open(cities_file_path, "r") as f:
    cities = json.load(f)

# Find the grid cell for each city with progress indication
city_grid_cells = []
for city in tqdm(cities, desc="Processing cities"):
    lat = float(city["lat"])
    lon = float(city["lon"])
    distance, index, lat_index, lon_index = find_nearest_grid_cell(lat, lon)
    city_grid_cells.append({
        "id": city["id"],
        "lat": lat,
        "lon": lon,
        "grid_distance": distance,
        "grid_index": index,
        "grid_lat_index": int(lat_index),
        "grid_lon_index": int(lon_index)
    })

# Output the results
output_file_path = os.path.join(dirname, "data", "output", "city_grid_cells.json")
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
with open(output_file_path, "w") as f:
    json.dump(city_grid_cells, f, indent=4)

print("Grid cell mapping for cities complete.")
