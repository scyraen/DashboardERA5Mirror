continents = {
    "africa": {"name": "Africa", "coords": [3, 18], "zoom": 2, "bbox": [-20, -35, 52, 38]},
    "asia": {"name": "Asia", "coords": [44, 87], "zoom": 1, "bbox": [25, -10, 180, 80]},
    "europe": {"name": "Europe", "coords": [54, 25], "zoom": 2, "bbox": [-25, 35, 45, 71]},
    "north_america": {"name": "North America", "coords": [47, -101], "zoom": 2, "bbox": [-170, 7, -50, 84]},
    "oceania": {"name": "Oceania", "coords": [-25, 134], "zoom": 2, "bbox": [110, -48, 180, 0]},
    "south_america": {"name": "South America", "coords": [-14, -56], "zoom": 2, "bbox": [-82, -56, -34, 13]},
}

kpi_config = {
    "global": {"temp": {"dataset": "ECMWF/ERA5_LAND/MONTHLY_AGGR", "band": "mean_2m_air_temperature", "reducer": "mean", "scale": 27830, "label": "Global Temperature", "unit": "°C", "offset": -273.15}},  # ~27km  # Convert Kelvin to Celsius
    "continent": {"forest_loss": {"dataset": "UMD/hansen/global_forest_change_2024_v1_12", "band": "lossyear", "reducer": "sum", "scale": 30, "label": "Forest Loss Area", "unit": "Hectares"}},
    "country": {"precip": {"dataset": "UCSB-CHG/CHIRPS/DAILY", "band": "precipitation", "reducer": "sum", "scale": 5566, "label": "Total Precipitation", "unit": "mm"}},  # ~5.5km
    "city": {"air_quality": {"dataset": "COPERNICUS/S5P/OFFL/L3_NO2", "band": "tropospheric_NO2_column_number_density", "reducer": "mean", "scale": 1113, "label": "Nitrogen Dioxide", "unit": "mol/m²"}},  # ~1.1km
}
