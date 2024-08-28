// Works with Celsius, Fahrenheight and Kelvin
// Returns degree or increment
module.exports = function convertTemp(value, {
  input = "c",
  output = "f",
  degree = true
} = {}) {
  if (value === null || isNaN(value) || !isFinite(value) || (value !== 0 && !value)) return null;
  
  const io = input + "-" + output;

  switch (io) {
    case "c-c":
    case "f-f":
    case "k-k":
      return value;
    case "c-f":
      return value * 9 / 5 + (degree ? 32 : 0);
    case "c-k":
      return value + (degree ? 273.15 : 0);
    case "f-c":
      return (value + (degree ? -32 : 0)) * 5 / 9;
    case "f-k":
      return (value + (degree ? -32 : 0)) * 5 / 9 + (degree ? 273.15 : 0);
    case "k-c":
      return degree ? value - 273.15 : value;
    case "k-f":
      return (degree ? value - 273.15 : value) * 9 / 5 + (degree ? 32 : 0);
  }
}