// Log the start of the calculation process
console.log("Calculating season temperatures and regressions")

// Import necessary modules from d3 for array manipulation and regression
const d3 = Object.assign(
  require("d3-array"),
  require("d3-regression"),
  {}
);
// Import the file system module and the Indian Ocean module for file operations
const fs = require("fs");
const io = require("indian-ocean");

// Import a utility function for temperature conversion
const convertTemp = require("./utils/convertTemp");

// Read the start and end year from the CONFIG.py file
const [ start_year, end_year ] = fs.readFileSync(`${__dirname}/CONFIG.py`, "utf8").split("\n").slice(0, 2).map(d => +d.split("= ")[1]);

// Read the raw temperature data from a CSV file
const raw = io.readDataSync(`${__dirname}/data/output/monthly_mean_temperatures.csv`);
raw.forEach(d => {
  d.year = +d.year;  // Convert year to a number
  d.month = +d.month; // Convert month to a number
  d.temp_f = +d.temp_f; // Convert temperature to a number
  return d;
});

// Group the data by year and hemisphere
const years_hemispheres = d3.groups(raw, d => d.year, d => d.hemisphere)

// Filter and process the data to calculate seasonal temperatures for each year and hemisphere
const years_hemispheres_seasons = years_hemispheres
  .slice(1) // Filter out the first year (1940) because there is no previous year to compare
  .map(([year, hemispheres]) => {
    return {
      year,
      data: hemispheres.map(([hemisphere, entries]) => {
        // Get previous December's data from the correct hemisphere
        const december = years_hemispheres
          .find(d => d[0] === year - 1)[1]
          .find(d => d[0] === hemisphere)[1]
          .find(d => d.month === 12);
        
        // Get the mid and end season data
        const mid = entries.filter(d => [6, 7, 8].includes(d.month));
        const end = [december, ...entries.filter(d => [1, 2].includes(d.month))];
        
        // Assign summer and winter based on hemisphere
        const summer = hemisphere === "north" ? mid : end;
        const winter = hemisphere === "north" ? end : mid;
        
        // Calculate mean temperatures for summer and winter
        return {
          year,
          hemisphere,
          summer,
          winter,
          summer_mean_f: d3.mean(summer, d => d.temp_f),
          winter_mean_f: d3.mean(winter, d => d.temp_f)
        }
      })
    }
  })
  .map(d => d.data)
  .flat() // Flatten the array to make it a single list of objects

// Calculate the seasonal temperatures for each year
const years_seasons = d3
  .groups(years_hemispheres_seasons, d => d.year)
  .map(([year, entries]) => {
    return {
      year,
      summer: d3.mean(entries, d => d.summer_mean_f),
      winter: d3.mean(entries, d => d.winter_mean_f),
    }
  })

// Define the output file name for seasonal mean temperatures
const file = "data/output/seasonal_mean_temperatures.csv";
// Write the seasonal mean temperatures to the output CSV file
io.writeDataSync(`${__dirname}/${file}`, years_seasons);
console.log(`Wrote ${file}`);

// Filter the data to include only years from the start year onward
const filtered = years_seasons.filter(d => d.year >= start_year);

// Calculate linear regression for both summer and winter
const regressions = Array.from(["summer", "winter"]).map(season => {
  const r = d3.regressionLinear().x(d => d.year).y(d => d[`${season}`])(filtered);
  const f = r.a * (start_year - end_year); // Calculate the slope (a) over the time range
  return {
    season,
    f, // Slope in Fahrenheit
    c: convertTemp(f, { input: "f", output: "c", degree: false }), // Convert slope to Celsius
    r
  }
})

// Create an object to store the regression data for the world
const world = {
  data: filtered,
  slopes: {
    summer: regressions[0].r.a, // Slope for summer
    winter: regressions[1].r.a  // Slope for winter
  },
  intercepts: {
    summer: regressions[0].r.b, // Intercept for summer
    winter: regressions[1].r.b  // Intercept for winter
  }
}

// Define the output file name for the world data
const worldFile = "data/output/world.json";
// Write the world regression data to a JSON file
io.writeDataSync(`${__dirname}/${worldFile}`, world);
console.log(`Wrote ${worldFile}\n\n`);
