import os
import netCDF4 as nc
import numpy as np

from CONFIG import start_year, end_year

dirname = os.path.dirname(os.path.abspath(__file__))
input_file_name = f"seasonal_slopes_{start_year}_{end_year}.nc"
input_file = os.path.join(dirname, "data", "output", input_file_name)
output_file = os.path.join(dirname, "data", "output", f"seasonal_slopes_{start_year}_{end_year}_v3.nc")
print(f"Converting {input_file_name} from V4 to V3")

def convert_nc4_to_nc3(input_file, output_file):
    # Open the NetCDF-4 file
    src = nc.Dataset(input_file, "r")
    
    # Create a new NetCDF-3 file
    dst = nc.Dataset(output_file, "w", format="NETCDF3_CLASSIC")
    
    # Copy global attributes
    for name in src.ncattrs():
        dst.setncattr(name, src.getncattr(name))
    
    # Copy dimensions
    for name, dimension in src.dimensions.items():
        dst.createDimension(name, len(dimension) if not dimension.isunlimited() else None)
    
    # Copy variables
    for name, variable in src.variables.items():
        # Handle unsupported data types
        datatype = variable.datatype
        if datatype == np.float64:
            datatype = np.float32  # NetCDF-3 does not support float64
        elif datatype == np.int64:
            datatype = np.int32  # NetCDF-3 does not support int64
        
        x = dst.createVariable(name, datatype, variable.dimensions)
        
        # Copy variable attributes
        for attr_name in variable.ncattrs():
            attr_value = variable.getncattr(attr_name)
            try:
                x.setncattr(attr_name, attr_value)
            except Exception as e:
                print(f"Warning: Attribute {attr_name} of variable {name} could not be copied: {e}")
        
        # Copy variable data
        try:
            x[:] = variable[:]
        except Exception as e:
            print(f"Warning: Data of variable {name} could not be copied: {e}")
    
    # Close the files
    src.close()
    dst.close()

# Example usage
convert_nc4_to_nc3(input_file, output_file)
