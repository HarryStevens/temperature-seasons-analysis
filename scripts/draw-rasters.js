// Import necessary modules
const { createCanvas } = require("canvas"); // For creating and manipulating canvas elements
const d3 = Object.assign({}, require("d3-array"), require("d3-geo"), require("d3-geo-projection")); // D3 modules for array manipulation and geographic projections
const fs = require("fs"); // File system module for reading and writing files
const logpct = require("logpct"); // Module for logging progress percentage
const netcdf = require("netcdfjs").NetCDFReader; // NetCDF reader module
const topojson = require("topojson-client"); // TopoJSON client for working with geographic data

// Import custom utility functions
const convertTemp = require("./utils/convertTemp"); // Function to convert temperatures
const { unit } = require("./utils/config"); // Config file that specifies the unit (e.g., "change")

// Read the start and end years from CONFIG.py file
const [ start_year, end_year ] = fs.readFileSync(`${__dirname}/CONFIG.py`, "utf8").split("\n").slice(0, 2).map(d => +d.split("= ")[1]);

// Set dimensions for the output image
const width = 1024;

// Import the color scale function
const { colorScale } = require("./utils/colors");

// Load TopoJSON data for the world map
const topo = JSON.parse(fs.readFileSync(`${__dirname}/data/geo/topo_110m.topo.json`, "utf8"));
const countriesGeoInner = topojson.mesh(topo, topo.objects.countries, (a, b) => a !== b); // Inner country borders
const countriesGeoOuter = topojson.mesh(topo, topo.objects.countries, (a, b) => a === b); // Outer country borders

// Define the NetCDF file containing seasonal slope data
const filename = `data/output/seasonal_slopes_${start_year}_${end_year}_v3.nc`;
console.log(`\n\nDrawing raster from ${filename}`);
const nc = new netcdf(fs.readFileSync(`${__dirname}/${filename}`));

// Extract seasonal slope data for winter and summer
const winter = nc.getDataVariable("winter_slope");
const summer = nc.getDataVariable("summer_slope");
const values = { winter, summer };

// Extract longitude and latitude data from the NetCDF file
const X = nc.getDataVariable("longitude");
const Y = nc.getDataVariable("latitude");

// Calculate the resolution of the grid cells based on longitude values
const cell_res = d3.median(d3.pairs(X), ([a, b]) => Math.abs(a - b));

// Define the seasons of interest
const seasons = ["winter", "summer"];

console.log("Creating data");
// Create GeoJSON features for each grid cell with associated seasonal data
const geo = {
  type: "FeatureCollection",
  features: winter
    .map((_, i) => {
      const lon = X[i % X.length]; // Calculate longitude for the current grid cell
      const lat = Y[i / X.length | 0]; // Calculate latitude for the current grid cell
      const properties = { lon, lat }; // Store the coordinates as properties

      // Calculate temperature changes for each season and store them in properties
      seasons.forEach(s => {
        properties[`${s}_decadal`] = values[s][i] * 10;
        properties[`${s}_change`] = values[s][i] * (end_year - start_year);
        properties[`${s}_change_c`] = convertTemp(properties[`${s}_change`], { input: "f", output: "c", degree: false });
      });

      // Define the bounding box for the current grid cell
      let w = Math.max(-180, lon - cell_res);
      let e = Math.min(180, lon + cell_res);
      let n = Math.min(90, lat + cell_res);
      let s = Math.max(-90, lat - cell_res);
  
      // Adjust the bounding box if the grid cell crosses the equator or prime meridian
      if (n > 0 && s < 0) {
        if (lon > 0) s = 0;
        if (lon < 0) n = 0;
      }

      // Log the progress percentage
      logpct((i + 1) / winter.length * 100);

      // Return the GeoJSON feature for the current grid cell
      return {
        type: "Feature",
        properties,
        geometry: {
          type: "Polygon",
          // Define the polygon using the bounding box coordinates
          coordinates: [
            [[w, n], [e, n], [e, s], [w, s], [w, n]]
          ]
        }
      }
    })
}

// Define geographic projections for the world, North America, and the Arctic
const projectionWorld = d3.geoInterrupt(
  d3.geoAzimuthalEquidistantRaw,
    [[ // northern hemisphere
      [[-180,   0], [ -90,  90], [   0,   0]],
      [[   0,   0], [  90,  90], [ 180,   0]]
    ], [ // southern hemisphere
      [[-180,   0], [ -90, -90], [   0,   0]],
      [[   0,   0], [  90, -90], [ 180,   0]]
    ]]
  )
  .rotate([-20, 0, 90])
  .angle(-90);

const projectionNA = d3.geoSatellite().rotate([95, -40, 3]); // Projection for North America
const projectionArctic = d3.geoSatellite().rotate([0, -90, 0]); // Projection for the Arctic

// Define the maps to be drawn with associated projections and dimensions
const maps = [
  {
    id: "world",
    projection: projectionWorld,
    width: width,
    height: width * 2,
    outer: countriesGeoOuter,
    inner: countriesGeoInner
  },
  {
    id: "na",
    projection: projectionNA,
    width: width,
    height: width,
    outer: countriesGeoOuter,
    inner: countriesGeoInner
  },
  {
    id: "arctic",
    projection: projectionArctic,
    width: width,
    height: width,
    outer: countriesGeoOuter,
    inner: countriesGeoInner
  }
]

// Draw each map using the drawMap function
maps.forEach(drawMap);

// Function to draw the map with a specific projection and dimensions
function drawMap({ id, projection, width, height, outer, inner, outerLineWidth }) {
  console.log(`\n\nDrawing rasters for ${id}`)
  projection.fitSize([width, height], { type: "Sphere" }); // Fit the projection to the specified size
  seasons.forEach(season => draw({ season, projection, id, width, height, outer, inner, outerLineWidth })); // Draw the map for each season
}

// Function to draw a specific season on the map
function draw({ season, projection, id, width, height, outer, inner, outerLineWidth }){
  console.log(`\nDrawing ${season}`);

  const canvas = createCanvas(width, height); // Create a new canvas with specified width and height
  const context = canvas.getContext("2d"); // Get the 2D drawing context
  const path = d3.geoPath(projection, context); // Create a geographic path generator using the projection

  context.save();
  context.beginPath();
  path({ type: "Sphere" }); // Draw the outer boundary of the map
  context.clip(); // Clip the drawing area to the map boundary

  // Draw each GeoJSON feature (grid cell) on the map
  geo.features.forEach((feature, i) => {
    context.beginPath();
    path(feature); // Draw the grid cell
    const c = colorScale(feature.properties[`${season}_${unit}`]); // Determine the color based on the temperature change
    context.fillStyle = c;
    context.fill();
    context.strokeStyle = c;
    context.stroke(); // Fill and stroke the grid cell with the corresponding color

    // Log the progress percentage
    logpct((i + 1) / geo.features.length * 100);
  });

  context.fillStyle = "none";
  
  // Draw inner country borders if available
  if (inner) {
    context.beginPath();
    path(inner);
    context.lineWidth = outerLineWidth || 1;
    context.strokeStyle = "#494949";
    context.stroke();  
  }

  // Draw outer country borders if available
  if (outer) {
    context.beginPath();
    path(outer);
    context.lineWidth = outerLineWidth || 1;
    context.strokeStyle = "#2a2a2a";
    context.stroke();  
  }

  // Write the drawn map to a PNG file
  const outputFile = `data/output/${season}_${id}.png`;
  fs.writeFileSync(`${__dirname}/${outputFile}`, canvas.toBuffer());
  console.log(`\nWrote ${outputFile}`);
}
