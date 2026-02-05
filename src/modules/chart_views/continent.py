import json
from pathlib import Path

import altair as alt
import ee
import folium
import pandas as pd
import streamlit as st
from branca.element import MacroElement, Template
from streamlit_folium import st_folium


def render_continent_visuals(name):
    path = Path(__file__).resolve().parents[3] / "docs"
    st.write("#### Current Continental Pressure Systems (hPa)")

    continent_geometries = {
        "europe": ee.Geometry.Rectangle([-25, 34, 45, 72]),
        "asia": ee.Geometry.Rectangle([26, -11, 180, 81]),
        "africa": ee.Geometry.Rectangle([-20, -35, 52, 38]),
        "north_america": ee.Geometry.Rectangle([-170, 7, -50, 84]),
        "south_america": ee.Geometry.Rectangle([-94, -56, -28, 13]),
        "oceania": ee.Geometry.Rectangle([110, -48, 180, 25]),
    }

    continent_map_settings = {
        "europe": {"location": [54.5, 15.0], "zoom": 3},
        "asia": {"location": [34.0, 100.0], "zoom": 2},
        "africa": {"location": [0.0, 20.0], "zoom": 2},
        "north_america": {"location": [45.0, -100.0], "zoom": 2},
        "south_america": {"location": [-15.0, -60.0], "zoom": 2},
        "oceania": {"location": [-25.0, 135.0], "zoom": 3},
    }

    map_settings = continent_map_settings.get(name.lower(), {"location": [45, 10], "zoom": 3})
    continent_geom = continent_geometries.get(name.lower(), ee.Geometry.Rectangle([-180, -90, 180, 90]))

    mslp = ee.ImageCollection("ECMWF/ERA5/DAILY").select("mean_sea_level_pressure").first().divide(100)
    mslp_clipped = mslp.clip(continent_geom)

    m = folium.Map(location=map_settings["location"], zoom_start=map_settings["zoom"], tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="CartoDB Positron (No Labels)",
    ).add_to(m)

    mslp_vis = {"min": 980, "max": 1030, "palette": ["#08306b", "#4292c6", "#ffffcc", "#ef3b2c", "#67000d"]}
    colors = mslp_vis["palette"]
    vmin, vmax = mslp_vis["min"], mslp_vis["max"]
    unit_name = "hPa"
    gradient = f"linear-gradient(to top, {', '.join(colors)})"

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
    <div style="writing-mode: vertical-rl; transform: rotate(270deg); color: #333; 
                        font-weight: bold; font-size: 11px; margin-bottom: 5px; white-space: nowrap;">{unit_name}</div>
            <div style="color: #a50026; font-size: 10px; margin-bottom: 2px;">{vmax}</div>
            <div style="width: 12px; height: 35vh; background: {gradient}; border: 1px solid #777;"></div>
            <div style="color: #313695; font-size: 10px; margin-top: 2px;">{vmin}</div>
        </div>
    {{% endmacro %}}
    """

    macro = MacroElement()
    macro._template = Template(legend_html)
    m.get_root().add_child(macro)

    mslp_id = mslp_clipped.getMapId(mslp_vis)
    folium.TileLayer(tiles=mslp_id["tile_fetcher"].url_format, attr="ECMWF ERA5", overlay=True).add_to(m)
    st_folium(m, width=800, height=400)

    col1, col2 = st.columns(2)

    data_df = pd.read_csv(path / f"data_{name}.csv")
    data_df["time"] = pd.to_datetime(data_df["time"])

    with col1:
        st.write("#### Soil Moisture (m³/m³)")
        soil_chart = alt.Chart(data_df).mark_line(color="#3498db", size=2).encode(x=alt.X("time:T", title="Date"), y=alt.Y("soil_moisture:Q", title="Soil Moisture"), tooltip=["time:T", "soil_moisture:Q"]).properties(height=250)
        st.altair_chart(soil_chart, width="stretch")

    with col2:
        st.write("#### Wind Speed at 10m (m/s)")

        wind_min = data_df["wind_10m"].min()
        wind_max = data_df["wind_10m"].max()

        wind_chart = (
            alt.Chart(data_df)
            .mark_area(
                line={"color": "#5dade2", "size": 2}, color=alt.Gradient(gradient="linear", stops=[alt.GradientStop(color="rgba(93, 173, 226, 0.2)", offset=0), alt.GradientStop(color="rgba(93, 173, 226, 0.8)", offset=1)], x1=1, x2=1, y1=1, y2=0)
            )
            .encode(
                x=alt.X("time:T", title="Date"),
                y=alt.Y("wind_10m:Q", title="Wind Speed (m/s)", scale=alt.Scale(domain=[wind_min * 0.95, wind_max * 1.05])),
                tooltip=[alt.Tooltip("time:T", format="%Y-%m-%d %H:%M"), alt.Tooltip("wind_10m:Q", format=".2f", title="Wind Speed")],
            )
            .properties(height=250)
        )
        st.altair_chart(wind_chart, width="stretch")


def render_continent(name):
    path = Path(__file__).resolve().parents[3] / "docs"

    continents = {"africa": "Africa", "europe": "Europe", "north_america": "North America", "south_america": "South America", "oceania": "Oceania", "asia": "Asia"}

    with open(path / "kpi_data.json", "r") as f:
        kpi_info = json.load(f)["continental"][name]
    with open(path / "kpi_gen.json", "r") as f:
        kpi_gen = json.load(f)

    st.title(f"Dashboard for {continents[name]}")

    kpis = st.columns(4)

    for i, (key, kpi) in enumerate(kpi_info.items()):
        gen = kpi_gen.get(key, {})

        kpis[i].metric(label=kpi["name"], value=kpi["value"], delta=kpi["delta"], help=gen.get("explanation", ""), delta_color="inverse" if gen.get("invert") else "normal")

    render_continent_visuals(name)

    _, btn_col = st.columns([8, 2])
    with btn_col:
        if st.button("View Data Sources", width="stretch"):
            show_sources(kpi_info, kpi_gen)


@st.dialog("Data Sources")
def show_sources(kpi_info, kpi_gen):
    st.write("The following datasets were used to generate the climate metrics shown above:")
    table_data = [{"Metric": v["name"], "Source": kpi_gen.get(k, {}).get("source")} for k, v in kpi_info.items()]
    st.table(table_data)
    st.info("Baseline comparisons are calculated against the 1990-2020 climate normal.")


if __name__ == "__main__":
    render_continent("europe")
