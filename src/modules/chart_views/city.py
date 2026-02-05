from datetime import datetime

import altair as alt
import ee
import folium
import pandas as pd
import requests
import streamlit as st
from branca.element import MacroElement, Template
from streamlit_folium import st_folium


def render_city_map(lat, lon):
    st.write("#### Thermal Footprint")

    point = ee.Geometry.Point([lon, lat])
    roi = point.buffer(10**4)

    landsat_col = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(roi).filter(ee.Filter.lt("CLOUD_COVER", 20)).select("ST_B10")

    def thermal_calc(img):
        temp = img.multiply(0.00341802).add(149.0).subtract(273.15)
        return temp.clip(roi).rename("temp_c")

    city_thermal = landsat_col.map(thermal_calc).median()

    vis = {"min": -10, "max": 55, "palette": ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"]}

    colors = vis["palette"]
    vmin, vmax = vis["min"], vis["max"]
    unit_name = "°C"

    gradient = f"linear-gradient(to top, {', '.join(colors)})"

    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="cartodbpositron")

    legend_html = f"""
        {{% macro html(this, kwargs) %}}
        <div style="
            position: absolute; z-index: 9999; left: 10px; top: 50%; 
            transform: translateY(-50%);
            background: rgba(255, 255, 255, 0.85);
            padding: 8px; border-radius: 6px; border: 1px solid #999;
            font-family: sans-serif; display: flex; flex-direction: column;
            align-items: center; width: 50px; pointer-events: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        ">
            <div style="writing-mode: vertical-rl; transform: rotate(270deg); color: black; 
                        font-weight: bold; font-size: 11px; margin-bottom: 5px; white-space: nowrap;">{unit_name}</div>
            <div style="color: black; font-size: 10px; margin-bottom: 2px;">{vmax}</div>
            <div style="width: 12px; height: 35vh; background: {gradient}; border: 1px solid #777;"></div>
            <div style="color: black; font-size: 10px; margin-top: 2px;">{vmin}</div>
        </div>
        {{% endmacro %}}
        """

    macro = MacroElement()
    macro._template = Template(legend_html)
    m.get_root().add_child(macro)

    try:
        map_id = city_thermal.getMapId(vis)
        folium.TileLayer(tiles=map_id["tile_fetcher"].url_format, attr="NASA/USGS Landsat 9", name="30m Thermal Detail", overlay=True, opacity=0.7).add_to(m)
    except Exception:
        st.error("No clear satellite passes found for this city recently.")

    folium.TileLayer("cartodb light_only_labels", attr="CartoDB", overlay=True).add_to(m)

    st_folium(m, width=700, height=450, returned_objects=[])
    st.caption("30m Resolution")


def render_city_visuals(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "hourly": ["apparent_temperature", "precipitation_probability", "wind_speed_10m", "wind_gusts_10m"], "timezone": "auto", "forecast_days": 2}
    res = requests.get(url, params=params).json()

    df = pd.DataFrame(
        {
            "Time": pd.to_datetime(res["hourly"]["time"]),
            "Feels Like (°C)": res["hourly"]["apparent_temperature"],
            "Rain Risk (%)": res["hourly"]["precipitation_probability"],
            "Sustained": res["hourly"]["wind_speed_10m"],
            "Gusts": res["hourly"]["wind_gusts_10m"],
        }
    ).head(24)

    render_city_map(lat, lon)

    st.write("#### 24-Hour Meteogram")

    base = alt.Chart(df).encode(x=alt.X("Time:T", axis=alt.Axis(title="Time", format="%H:%M")))

    temp_line = base.mark_line(color="#ff4b4b", size=3).encode(y=alt.Y("Feels Like (°C):Q", title="Temperature (°C)", scale=alt.Scale(zero=False)))

    rain_bars = base.mark_bar(color="#1c83e1", opacity=0.3).encode(y=alt.Y("Rain Risk (%):Q", title="Rain Risk (%)", scale=alt.Scale(domain=[0, 100])))

    meteogram = alt.layer(rain_bars, temp_line).resolve_scale(y="independent")
    st.altair_chart(meteogram, width="stretch")

    st.write("#### Wind Speed & Gust Profile")

    base = alt.Chart(df).encode(x=alt.X("Time:T", axis=alt.Axis(title="Hour", format="%H:%M")))

    area = base.mark_area(opacity=0.3, color="#51b7f5").encode(y=alt.Y("Sustained:Q", title="Wind Speed (km/h)"))

    line = base.mark_line(color="#1c83e1", strokeWidth=2).encode(y="Gusts:Q")

    points = base.mark_point(color="#1c83e1").encode(y="Gusts:Q", tooltip=["Time", "Gusts", "Sustained"])

    st.altair_chart(area + line + points, width="stretch")
    st.caption("The line represents sudden gusts; the shaded area is the steady wind. A large gap indicates high turbulence.")


@st.cache_data(ttl=600, show_spinner="Searching KPIs...")
def get_city_kpis(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "current": ["apparent_temperature", "surface_pressure", "wind_gusts_10m"], "hourly": ["precipitation_probability", "apparent_temperature"], "past_days": 1, "timezone": "auto"}

    data = requests.get(url, params=params).json()

    current_hour = datetime.now().hour
    idx_now = 24 + current_hour
    idx_past = current_hour
    idx_3h_ago = idx_now - 3

    curr_temp = data["current"]["apparent_temperature"]
    past_temp = data["hourly"]["apparent_temperature"][idx_past]
    curr_pressure = data["current"]["surface_pressure"]
    curr_pop = data["hourly"]["precipitation_probability"][idx_now]
    prev_pop = data["hourly"]["precipitation_probability"][idx_3h_ago]
    curr_gust = data["current"]["wind_gusts_10m"]

    weather_source = "Open-Meteo Global Forecasting API"

    return {
        "feels_like": {
            "name": "Feels Like",
            "value": f"{curr_temp:.1f}°C",
            "delta": f"{curr_temp - past_temp:+.1f}°C",
            "explanation": "Temperature as perceived by humans. Delta compares today to this time yesterday.",
            "source": weather_source,
            "invert": True,
        },
        "pressure": {
            "name": "Surface Pressure",
            "value": f"{curr_pressure:.0f} hPa",
            "delta": "Falling" if curr_pressure < 1013 else "Rising",
            "explanation": "Barometric pressure. Sharp drops indicate incoming storm systems.",
            "source": weather_source,
            "invert": False,
        },
        "pop": {
            "name": "Precipitation Risk",
            "value": f"{curr_pop}%",
            "delta": f"{curr_pop - prev_pop:+.0f}%",
            "explanation": "Chance of rain/snow in the next hour. Delta shows change over the last 3 hours.",
            "source": weather_source,
            "invert": True,
        },
        "gusts": {
            "name": "Wind Gusts",
            "value": f"{curr_gust:.1f} km/h",
            "delta": "High" if curr_gust > 40 else "Low",
            "explanation": "Sudden peaks in wind speed. Above 40 km/h can affect high-rise urban safety.",
            "source": weather_source,
            "invert": True,
        },
    }


def render_city(name, coords):
    st.title(f"Dashboard for {name}")

    kpi_info = get_city_kpis(coords[0], coords[1])
    kpis_cols = st.columns(4)

    for i, (key, kpi) in enumerate(kpi_info.items()):
        kpis_cols[i].metric(label=kpi["name"], value=kpi["value"], delta=kpi["delta"], help=kpi["explanation"], delta_color="inverse" if kpi.get("invert") else "normal")

    render_city_visuals(coords[0], coords[1])

    _, btn_col = st.columns([8, 2])
    with btn_col:
        if st.button("View Data Sources", width="stretch"):
            show_sources(kpi_info)


@st.dialog("City Data Sources")
def show_sources(kpi_info):
    st.write("Real-time meteorological and satellite data providers:")

    source_data = [{"Metric": kpi["name"], "Source": kpi["source"]} for kpi in kpi_info.values()]
    source_data.append({"Metric": "High-Res Thermal Map", "Source": "NASA/USGS Landsat 9 (C02/T1_L2)"})

    st.table(pd.DataFrame(source_data))
    st.info("Satellite imagery is filtered for <20% cloud cover to ensure thermal accuracy.")
