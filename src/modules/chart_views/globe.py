import json
from pathlib import Path

import altair as alt
import ee
import folium
import pandas as pd
import streamlit as st
from branca.element import MacroElement, Template
from streamlit_folium import st_folium


def render_global_visuals():

    st.write("#### Global Yearly Temperature Anomaly")
    era5 = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")

    baseline = era5.filter(ee.Filter.calendarRange(1990, 2020, "year")).mean()
    current = era5.filter(ee.Filter.calendarRange(2025, 2025, "year")).mean()
    anomaly = current.select("temperature_2m").subtract(baseline.select("temperature_2m"))

    vis = {"min": -2, "max": 2, "palette": ["#313695", "#74add1", "#ffffbf", "#f46d43", "#a50026"]}
    colors = vis["palette"]
    vmin, vmax = vis["min"], vis["max"]
    unit_name = "Δ °C"
    gradient = f"linear-gradient(to top, {', '.join(colors)})"

    m = folium.Map(location=[20, 0], zoom_start=2, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="CartoDB Positron (No Labels)",
    ).add_to(m)

    vis = {"min": -2, "max": 2, "palette": ["#313695", "#74add1", "#ffffbf", "#f46d43", "#a50026"]}
    map_id = anomaly.getMapId(vis)

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
            <div style="color: #666; font-size: 9px; margin-top: 5px;">vs Base</div>
        </div>
    {{% endmacro %}}
    """

    macro = MacroElement()
    macro._template = Template(legend_html)
    m.get_root().add_child(macro)

    folium.TileLayer(tiles=map_id["tile_fetcher"].url_format, attr="GEE/ERA5", overlay=True).add_to(m)
    st_folium(m, width=800, height=400)
    st.caption("Shows deviations from the 30-year average. Red indicates warming; Blue indicates cooling.")

    st.write("#### Global Warming Stripes (150-Year History)")
    stripes_df = pd.read_csv("docs/global_stripes_data.csv")
    stripes = (
        alt.Chart(stripes_df)
        .mark_rect()
        .encode(x=alt.X("Year:O", axis=None), color=alt.Color("Anomaly:Q", scale=alt.Scale(scheme="redblue", reverse=True, domain=[-1.5, 1.5]), legend=None), tooltip=["Year", "Anomaly"])
        .properties(width=800, height=120)
    )
    st.altair_chart(stripes)

    st.write("#### Atmospheric CO2 Concentration (ppm)")
    co2_df = pd.read_csv("docs/co2_daily_2026.csv")

    co2_df["Date"] = pd.to_datetime(co2_df[["Year", "Month", "Day"]])

    co2_chart = alt.Chart(co2_df).mark_line(color="#ff4b4b", size=3).encode(x="Date:T", y=alt.Y("PPM:Q", scale=alt.Scale(domain=[400, 435]), title="CO2 ppm"), tooltip=["Date", "PPM"]).properties(width=800, height=300)
    st.altair_chart(co2_chart)


def render_global():
    path = Path(__file__).resolve().parents[3] / "docs" / "kpi_data.json"

    with open(path, "r") as f:
        kpi_info = json.load(f)["global"]["global"]

    st.title("Global Dashboard")

    kpis = st.columns(4)
    for i, (key, kpi) in enumerate(kpi_info.items()):
        kpis[i].metric(label=kpi["name"], value=kpi["value"], delta=kpi["delta"], help=kpi["explanation"], delta_color="inverse" if kpi.get("invert") else "normal")

    render_global_visuals()

    _, btn_col = st.columns([8, 2])
    with btn_col:
        if st.button("View Data Sources", width="stretch"):
            show_sources(kpi_info)


@st.dialog("Data Sources")
def show_sources(kpi_info):
    st.write("The following datasets were used to generate the climate metrics shown above:")
    source_df = pd.DataFrame([{"Metric": v["name"], "Source": v["source"]} for v in kpi_info.values()])
    st.table(source_df)
    st.info("Baseline comparisons are calculated against the 1990-2020 climate normal.")


if __name__ == "__main__":
    render_global()
