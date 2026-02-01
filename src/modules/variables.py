import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


class VisParamGenerator:
    # Standard meteorological palettes
    PALETTES = {
        "temperature": ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"],
        "precipitation": ["#ffffff", "#edf8b1", "#7fcdbb", "#2c7fb8", "#253494"],
        "evaporation": ["#8c510a", "#d8b365", "#f6e8c3", "#c7eae5", "#5ab4ac", "#01665e"],
        "vegetation": ["#f7fcf5", "#e5f5e0", "#a1d99b", "#41ab5d", "#00441b"],
        "snow": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#2171b5"],
        "ice": ["#ffffff", "#e0f3f8", "#abd9e9", "#74add1", "#4575b4"],
        "pressure": ["#ffffff", "#cccccc", "#999999", "#666666", "#333333"],
        "soil_moisture": ["#f5f5f5", "#f6e8c3", "#dfc27d", "#80cdc1", "#35978f", "#01665e"],
        "flux": ["#d73027", "#f46d43", "#fdae61", "#fee090", "#e0f3f8", "#abd9e9", "#74add1", "#4575b4"],
        "solar": ["#ffffcc", "#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#bd0026"],
        "wind": ["#ffffff", "#f0f0f0", "#d9d9d9", "#bdbdbd", "#969696", "#737373", "#525252", "#252525"],
        "generic": ["#ffffff", "#000000"],
    }

    def get_params(self, var_name, unit):
        v = var_name.lower()

        # Temperature (Kelvin)
        if unit == "C" or "temperature" in v:
            return {"min": 220, "max": 320, "palette": self.PALETTES["temperature"]}

        if "volumetric_soil_water" in v:
            return {"min": 0, "max": 0.5, "palette": self.PALETTES["soil_moisture"]}

        # Snow (Cover, Density, Depth)
        if "snow" in v:
            if "cover" in v or "albedo" in v:
                return {"min": 0, "max": 1, "palette": self.PALETTES["snow"]}
            if "density" in v:
                return {"min": 100, "max": 500, "palette": self.PALETTES["snow"]}
            if "depth" in v or "fall" in v or "melt" in v:
                return {"min": 0, "max": 0.5, "palette": self.PALETTES["snow"]}

        # Lake Ice & Reservoir
        if "lake" in v:
            if "depth" in v:
                if "ice" in v:
                    return {"min": 0, "max": 2, "palette": self.PALETTES["ice"]}
                else:
                    return {"min": 0, "max": 50, "palette": self.PALETTES["generic"]}
        if "lake_shape" in v:  # Unitless factor
            return {"min": 0, "max": 1, "palette": self.PALETTES["generic"]}
        if "reservoir" in v:  # Skin reservoir water content
            return {"min": 0, "max": 0.001, "palette": self.PALETTES["precipitation"]}

        if "forecast_albedo" in v:
            return {"min": 0, "max": 1, "palette": self.PALETTES["generic"]}

        # Evaporation & Runoff
        if "evaporation" in v:
            return {"min": -0.01, "max": 0, "palette": self.PALETTES["evaporation"]}

        if "precipitation" in v or "runoff" in v:
            return {"min": 0, "max": 0.02, "palette": self.PALETTES["precipitation"]}

        # Energy Flux
        if "heat_flux" in v:
            return {"min": -10000000, "max": 10000000, "palette": self.PALETTES["flux"]}

        # Solar & Thermal Radiation
        if "radiation" in v:
            if "solar" in v:
                return {"min": 0, "max": 25000000, "palette": self.PALETTES["solar"]}
            else:
                return {"min": -15000000, "max": 0, "palette": self.PALETTES["flux"]}

        # Wind Components (m/s)
        if "component_of_wind" in v:
            return {"min": -15, "max": 15, "palette": self.PALETTES["wind"]}

        # Vegetation (Leaf Area Index)
        if "leaf_area_index" in v:
            return {"min": 0, "max": 8, "palette": self.PALETTES["vegetation"]}

        # Pressure (Pascals)
        if "pressure" in v or "pa" in unit.lower():
            return {"min": 95000, "max": 105000, "palette": self.PALETTES["pressure"]}

        # Default Fallback
        return {"min": 0, "max": 100, "palette": self.PALETTES["generic"]}


def reformulate_description(description):
    description += "."
    description = description.lower().capitalize()

    def fix_var(match):
        # Convert "total_precipitation" to "Total Precipitation"
        return match.group(0).replace("_", " ").title()

    pattern = r"[a-z0-9]+(?:_[a-z0-9]+)+"

    return re.sub(pattern, fix_var, description)


def enrich_catalog(scraped_data):
    generator = VisParamGenerator()
    for var_id, info in scraped_data.items():
        info["vis"] = generator.get_params(var_id, info["unit"])
    return scraped_data


def scrape_catalog(catalog):
    url = "https://developers.google.com/earth-engine/datasets/catalog/" + catalog
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    variables = {}

    # Parse the 'Bands' table for Name, Unit, and Description
    tables = soup.find_all("table")
    for table in tables:
        # Check if this table looks like the bands table
        headers = [th.text.lower() for th in table.find_all("th")]
        if "description" in headers or "units" in headers:
            rows = table.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    var_id = cols[0].get_text(strip=True)
                    unit = cols[1].get_text(strip=True)
                    description = cols[3].get_text(strip=True)

                    if unit == "K":
                        unit = "C"

                    if "_" in description:
                        description = reformulate_description(description)

                    variables[var_id] = {
                        "name": var_id.replace("_", " ").title(),
                        "unit": unit,
                        "description": description,
                        "vis": {},
                    }

    data = enrich_catalog(variables)

    return data


def get_vars(catalog):
    path = Path(__file__).resolve().parents[2] / "docs" / "catalog_vars.json"
    try:
        with open(path, "r") as f:
            current = json.load(f)
    except FileNotFoundError:
        current = {}
        print("File not there yet, starting fresh!")

    if catalog not in current:
        data = scrape_catalog(catalog)
        current[catalog] = data

        with open(path, "w") as f:
            json.dump(current, f, indent=4)

    return current[catalog]


def get_filtered_variables(all_vars):
    """Filters the variables dictionary to remove clutter and technical noise."""
    filtered = {}

    exclude_patterns = [
        "_min",
        "_max",
        "soil_temperature_level_2",
        "soil_temperature_level_3",
        "soil_temperature_level_4",
        "volumetric_soil_water_layer_2",
        "volumetric_soil_water_layer_3",
        "volumetric_soil_water_layer_4",
        "heat_flux",
        "lake_bottom",
        "lake_shape",
        "radiation",
    ]

    problematic_bands = ["evaporation_from_bare_soil_sum", "evaporation_from_open_water_surfaces_sum", "evaporation_from_vegetation_transpiration_sum"]

    for key, info in all_vars.items():
        if any(pat in key for pat in exclude_patterns):
            continue
        if key in problematic_bands:
            continue

        filtered[key] = info

    return filtered


if __name__ == "__main__":
    get_vars("ECMWF_ERA5_LAND_MONTHLY_AGGR")
