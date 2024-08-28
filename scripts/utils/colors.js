// Import the unit configuration from the config file
const { unit } = require("./config");


// Define the heat and cold value thresholds based on the selected unit
// If the unit is "change", use larger increments for values; otherwise, use smaller increments
const heatValues = unit === "change" ? 
  [0.667, 1.333, 2, 2.667, 3.333, 4, 4.667, 5.333, 6, 6.667, 7.333, 8, 8.667, 9.333, 10, 10.667, 11.333, 12] : 
  [0.083, 0.167, 0.25, 0.333, 0.417, 0.5, 0.583, 0.667, 0.75, 0.833, 0.917, 1, 1.083, 1.167, 1.25, 1.333, 1.417, 1.5];

const coldValues = unit === "change" ? 
  [-0.667, -1.333, -2, -2.667, -3.333, -4, -4.667, -5.333, -6, -6.667, -7.333, -8] : 
  [-0.083, -0.167, -0.25, -0.333, -0.417, -0.5, -0.583, -0.667, -0.75, -0.833, -0.917, -1];

// Define color scales corresponding to heat values (positive) 
const heatColors = [
  "#f8f4e2", "#f9e9ce", "#fadfbb", "#fad5a7", "#f9ca94", "#f7c081", // Light yellow to light orange shades
  "#fd9c63", "#f69259", "#ee8850", "#e77d47", "#df733e", "#d76935", // Darker orange to red shades
  "#cc0000", "#bf0018", "#b20124", "#a5042b", "#980730", "#8b0a34"  // Deep red shades
];

// Define color scales corresponding to cold values (negative)
const coldColors = [
  "#eff4e9", "#e0ede6", "#d2e5e1", "#c4deda", "#b6d7d2", "#a9d0ca", // Light green to light blue-green shades
  "#9fc4d7", "#95bed3", "#8cb7ce", "#82b1ca", "#78aac6", "#6ea4c1"  // Darker blue-green to blue shades
];

// Function to determine the color scale for a given value based on temperature change (value is slope * (end_year - start_year))
function colorScale(value, {
  cv = coldValues, // Defaults for cold values
  cc = coldColors, // Defaults for cold colors
  hv = heatValues, // Defaults for heat values
  hc = heatColors  // Defaults for heat colors
} = {}){
  // Check if the value is negative (cold)
  if (value < 0) {
    let index = -1; // Initialize index to indicate no match found

    // Loop through cold values to find the appropriate color index
    for (let i = 0, l = cv.length; i < l; i++) {
      const v = cv[i];
      if (value > v) {
        index = i;
        break; // Exit loop once the correct index is found
      }
    }
    
    // Return the corresponding cold color or the last color if no match is found
    return index === -1 ? cc[cc.length - 1] : cc[index];
  } 
  else { // If the value is positive (heat)
    let index = -1; // Initialize index to indicate no match found
    
    // Loop through heat values to find the appropriate color index
    for (let i = 0, l = hv.length; i < l; i++){
      const v = hv[i];
      if (value < v) {
        index = i;
        break; // Exit loop once the correct index is found
      }
    }
    
    // Return the corresponding heat color or the last color if no match is found
    return index === -1 ? hc[hc.length - 1] : hc[index]
  }
}

// Export the modules to be used in other parts of the program
module.exports = {
  coldColors,   // Cold color scale
  coldValues,   // Cold value thresholds
  heatColors,   // Heat color scale
  heatValues,   // Heat value thresholds
  colorScale    // Function to determine the color based on value
}
