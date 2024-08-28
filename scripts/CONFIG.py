start_year = 1944
end_year = 2023
engine = "cfgrib" ## "netcdf4" or "cfgrib"
file_name = f"era5-monthly-temp.{'nc' if engine == 'netcdf4' else 'grib'}"