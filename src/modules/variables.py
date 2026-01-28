import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


class VisParamGenerator:
    # Standard meteorological palettes
    PALETTES = {
        "temperature": ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"],
        "precipitation": ["#ffffff", "#edf8b1", "#7fcdbb", "#2c7fb8", "#253494"],
        "pressure": ["#ffffff", "#cccccc", "#999999", "#666666", "#333333"],
        "generic": ["#ffffff", "#000000"],
    }

    def get_params(self, var_name, unit):
        v = var_name.lower()

        # Temperature Logic (Kelvin)
        if unit == "K" or "temperature" in v:
            return {"min": 220, "max": 320, "palette": self.PALETTES["temperature"]}

        # Precipitation Logic (Meters)
        if "precipitation" in v or "runoff" in v:
            return {"min": 0, "max": 0.02, "palette": self.PALETTES["precipitation"]}

        # Pressure Logic (Pascals)
        if "pressure" in v or "pa" in unit.lower():
            return {"min": 95000, "max": 105000, "palette": self.PALETTES["pressure"]}

        # Default Fallback
        return {"min": 0, "max": 100, "palette": self.PALETTES["generic"]}


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
