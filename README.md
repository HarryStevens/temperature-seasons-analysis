# temperature-seasons-analysis

Scripts for calculating seasonal temperature change using ERA5 monthly data.

Table of contents:

- [Installation](#installation)
- [Setup](#setup)
  - [Get the data](#get-the-data)
  - [Install dependencies](#install-dependencies)
- [Scripts](#scripts)
  - [Averaging the grid](#averaging-the-grid)
  - [Calculating the seasonal temperature across the grid in each year](#calculating-the-seasonal-temperature-across-the-grid-in-each-year)
  - [Calculating the regression](#calculating-the-regression)
  - [Drawing the maps](#drawing-the-maps)
  - [Calculating city data](#calculating-city-data)

## Installation

```bash
git clone git@github.com:HarryStevens/temperature-seasons-analysis.git
cd temperature-seasons-analysis
```

## Setup

### Get the data

Download "ERA5 monthly averaged data on single levels from 1940 to present" from the [Copernicus Climate Data Store](https://cds-beta.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=download). 
- Navigate to the Download tab
- From "Product type", select "Monthly averaged reanalysis"
- From "Variable", select "2m temperature"
- From "Year", click "Select all"
- From "Month", click "Select all"
- From "Time", select "00:00"
- From "Geographical area", select "Whole available region"
- From "Format", select "GRIB"
- From "Download format", select "Unarchived (not zipped if single file)"
- You may have to create an account and agree to the terms of use. Otherwise, click "Submit form"
- You will be redirected to a page with a link to download the data. You may have to wait until the "Status" column says "Complete". Then you can download the data.
- The file name will be {some string of characters}.grib and will be around 2GB in size. Rename it to "era5-monthly-temp.grib" and move it to the `scripts/data/input` folder.

### Install dependencies

This project uses node and python, so you will need to install the dependencies for both.

First, install the node modules.

```bash
npm i # Install the node modules
```

If you get an error installing node-canvas, you may need to install its dependencies.

```bash 
brew install pkg-config cairo pango libpng jpeg giflib librsvg 
```

Then, create and activate a python virtual environment, and install the python dependencies.

``` bash
python -m venv myenv # Create a Python Virtual Environment
source myenv/bin/activate # Activate the Virtual Environment
pip install -r requirements.txt # Install python dependencies
```

## Scripts

Below are the scripts that are run in order. You can set the start_year and end_year in scripts/CONFIG.py.

### Averaging the grid

```bash
python scripts/average-grid-annual.py # Averages the grid by year
python scripts/average-grid-monthly.py # Averages the grid by year, month & hemisphere
node scripts/average-grid-seasonal.js # Averages the monthly data by year and season
```

### Calculating the seasonal temperature across the grid in each year

```bash
python scripts/annual-seasons.py # Calculate the seasonal temperature in each year
```

### Calculating the regression

```bash
python scripts/make-regression-netcdf.py # Calculate the linear regression of year vs. temperature in each season (takes ~12 minutes)
python scripts/calculate-percentage.py # Calculate the percentage of the grid that fulfills certain criteria
```

### Drawing the maps

```bash
python scripts/convert-to-v3.py # To use the scripts/data/output/seasonal_slopes.nc file with netcdfjs, you will need to convert it from V4 to V3
node scripts/draw-rasters.js # Draw the rasters for map displays
```

### Calculating city data

To get data for a particular search, you will need to create a file called "cities.json" in the `scripts/data/input` folder. This file should contain a list of cities with an id, name, latitude, and longitude. For example:

```json
[
  {
    "id": "1",
    "name": "New York",
    "lat": 40.7128,
    "lon": -74.0060
  }
]
```

Then, run the following scripts:

```bash
python scripts/make-city-lookup.py # Find the grid cell that contains each city's coordinates
python scripts/make-city-files.py # Get the annual season temps for each city
```

The files will be created in the `scripts/data/output/city` folder with the name of the city id. For example, the file for New York will be `scripts/data/output/city/1.json`.