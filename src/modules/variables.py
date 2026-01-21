# src/modules/variables.py
VARIABLES = {
    "Temperature (2m)": {
        "name": "Temp (K)",
        "band": "temperature_2m",
        "vis": {
            "min": 250,
            "max": 310,
            "palette": ["#0000ff", "#00ffff", "#ffff00", "#ff0000"],
        },
    },
    "Total Precipitation": {
        "name": "Precip (m)",
        "band": "total_precipitation_sum",
        "vis": {"min": 0, "max": 0.1, "palette": ["#ffffff", "#00fbff", "#0033ff"]},
    },
    "Soil Moisture (0-7cm)": {
        "name": "Soil Water (m³/m³)",
        "band": "volumetric_soil_water_layer_1",
        "vis": {"min": 0, "max": 0.5, "palette": ["#f7fbff", "#08306b"]},
    },
    "Surface Pressure": {
        "name": "Pressure (Pa)",
        "band": "surface_pressure",
        "vis": {
            "min": 50000,
            "max": 110000,
            "palette": ["#fee5d9", "#fcae91", "#fb6a4a", "#cb181d"],
        },
    },
    "Snow Depth": {
        "name": "Snow Depth (m)",
        "band": "snow_depth",
        "vis": {
            "min": 0,
            "max": 1,
            "palette": ["#ffffff", "#ebf5fb", "#aed6f1", "#2e86c1"],
        },
    },
    "Evaporation": {
        "name": "Evaporation (m)",
        "band": "total_evaporation_sum",
        "vis": {"min": -0.01, "max": 0, "palette": ["#440154", "#21908d", "#fde725"]},
    },
    "Runoff": {
        "name": "Runoff (m)",
        "band": "runoff_sum",
        "vis": {"min": 0, "max": 0.05, "palette": ["#ffffcc", "#41b6c4", "#081d58"]},
    },
    "Solar Radiation": {
        "name": "Radiation (J/m²)",
        "band": "surface_net_solar_radiation_sum",
        "vis": {
            "min": 0,
            "max": 30000000,
            "palette": ["#000000", "#990000", "#ffcc00", "#ffffff"],
        },
    },
}
