import altair as alt
import ee
import folium
import pandas as pd
import streamlit as st
from branca.element import MacroElement, Template
from streamlit_folium import st_folium


@st.cache_data(ttl=3600, show_spinner="Computing National KPIs...")
def get_national_kpis(name):
    countries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    roi = countries.filter(ee.Filter.eq("country_na", name))
    if roi.size().getInfo() == 0:
        return {}

    modis_lai = ee.ImageCollection("MODIS/061/MCD15A3H")
    era5 = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")

    # Time Ranges
    baseline_years = ee.Filter.calendarRange(1990, 2020, "year")
    current_years = ee.Filter.calendarRange(2024, 2024, "year")  # Latest full year

    def get_stats_image(temp_col, precip_col, soil_col, lai_col):
        temp = temp_col.select("temperature_2m").mean().subtract(273.15).rename("temp")
        soil = soil_col.select("volumetric_soil_water_layer_1").mean().rename("soil")
        # Precipitation SUM: Total water for the period
        precip = precip_col.select("total_precipitation_sum").sum().multiply(1000).rename("precip")
        # LAI MEAN: Average biomass density
        lai = lai_col.select("Lai").mean().multiply(0.1).rename("lai")
        return ee.Image([temp, precip, soil, lai])

    # Calculate Current (2024)
    current_img = get_stats_image(era5.filter(current_years), era5.filter(current_years), era5.filter(current_years), modis_lai.filter(ee.Filter.calendarRange(2023, 2023, "year")))

    # Calculate Baseline (Average Annual)
    # For precip, we sum the whole 30 years and divide by 31 to get the average annual sum
    base_precip = era5.filter(baseline_years).select("total_precipitation_sum").sum().divide(31).multiply(1000)
    base_others = era5.filter(baseline_years).select(["temperature_2m", "volumetric_soil_water_layer_1"]).mean()
    base_temp = base_others.select("temperature_2m").subtract(273.15)
    base_soil = base_others.select("volumetric_soil_water_layer_1")
    base_lai = modis_lai.filter(ee.Filter.calendarRange(2002, 2010, "year")).select("Lai").mean().multiply(0.1)

    baseline_img = ee.Image([base_temp.rename("temp"), base_precip.rename("precip"), base_soil.rename("soil"), base_lai.rename("lai")])

    def reduce_roi(img):
        return img.reduceRegion(ee.Reducer.mean(), roi.geometry(), 9000, maxPixels=1e9).getInfo()

    curr_stats, b_stats = reduce_roi(current_img), reduce_roi(baseline_img)

    def make_kpi(key, label, unit, exp, src, inv=False, prec=2):
        v, b = curr_stats.get(key, 0), b_stats.get(key, 0)
        return {"name": label, "value": f"{v:.{prec}f}{unit}", "delta": f"{v - b:+.{prec}f}{unit}", "explanation": exp, "source": src, "invert": inv}

    return {
        "temp": make_kpi("temp", "Avg Air Temp", "°C", "Mean annual temp.", "ERA5", True),
        "lai": make_kpi("lai", "Leaf Area Index", "", "Biomass health.", "MODIS", prec=3),
        "precip": make_kpi("precip", "Annual Precip", "mm", "Total yearly rain.", "ERA5"),
        "soil": make_kpi("soil", "Soil Moisture", "m³/m³", "Topsoil water.", "ERA5"),
    }


def get_national_yearly_data(roi, era5_collection, target_year=2025):
    start_year = target_year - 9
    years = ee.List.sequence(start_year, target_year)
    modis_col = ee.ImageCollection("MODIS/061/MCD15A3H")

    # Annual Mean of Totals for Precip
    precip_base_val = (
        era5_collection.filter(ee.Filter.calendarRange(1990, 2020, "year")).select("total_precipitation_sum").sum().divide(31).multiply(1000).reduceRegion(ee.Reducer.mean(), roi.geometry(), 10000).getInfo().get("total_precipitation_sum")
    )

    lai_base_val = modis_col.filter(ee.Filter.calendarRange(2002, 2010, "year")).select("Lai").mean().multiply(0.1).reduceRegion(ee.Reducer.mean(), roi.geometry(), 10000).getInfo().get("Lai")

    def calculate_year_stats(y):
        y = ee.Number(y)
        y_precip = era5_collection.filter(ee.Filter.calendarRange(y, y, "year")).select("total_precipitation_sum").sum().multiply(1000)
        y_lai = modis_col.filter(ee.Filter.calendarRange(y, y, "year")).select("Lai").mean().multiply(0.1).rename("lai_act")

        stats = y_lai.addBands(y_precip).reduceRegion(ee.Reducer.mean(), roi.geometry(), 10000)
        return ee.Feature(None, stats).set("year", y)

    yearly_features = ee.FeatureCollection(years.map(calculate_year_stats)).getInfo()

    rows = []
    for f in yearly_features["features"]:
        p = f["properties"]
        rows.append({"year": p["year"], "precip_act": p.get("total_precipitation_sum", 0), "precip_base": precip_base_val, "lai_act": p.get("lai_act", 0), "lai_base": lai_base_val})
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600, show_spinner="Getting Yearly Data...")
def get_yearly_df(name):
    countries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    roi = countries.filter(ee.Filter.eq("country_na", name))
    era5 = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")

    df = get_national_yearly_data(roi, era5)
    return df


def render_national_visuals(name):
    df_yearly = get_yearly_df(name)
    roi = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017").filter(ee.Filter.eq("country_na", name))
    era5 = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")

    baseline_temp = era5.filter(ee.Filter.calendarRange(1990, 2020, "year")).select("temperature_2m").mean()
    current_temp = era5.filter(ee.Filter.calendarRange(2025, 2025, "year")).select("temperature_2m").mean()

    temp_anomaly = current_temp.subtract(baseline_temp).clip(roi)

    st.write("#### Annual Temperature Anomaly (2025 vs. 1990-2020)")

    vis_params = {"min": -1.5, "max": 1.5, "palette": ["#313695", "#74add1", "#ffffbf", "#f46d43", "#a50026"]}

    centroid = roi.geometry().centroid().getInfo()["coordinates"]
    m = folium.Map(location=[centroid[1], centroid[0]], zoom_start=4, tiles="cartodbpositron")

    map_id = temp_anomaly.getMapId(vis_params)

    colors = vis_params["palette"]
    vmin, vmax = vis_params["min"], vis_params["max"]
    unit_name = "Δ °C"
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
            <div style="color: #666; font-size: 9px; margin-top: 5px;">vs Base</div>
    {{% endmacro %}}
    """

    macro = MacroElement()
    macro._template = Template(legend_html)
    m.get_root().add_child(macro)

    folium.TileLayer(tiles=map_id["tile_fetcher"].url_format, attr="Google Earth Engine / ERA5-Land", name="Annual Temp Anomaly", overlay=True).add_to(m)

    folium.TileLayer(tiles="https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png", attr="&copy; OpenStreetMap &copy; CARTO", name="Labels", overlay=True, control=False).add_to(m)

    st_folium(m, width=700, height=450, returned_objects=[])

    col1, col2 = st.columns(2)

    with col1:
        st.write("#### Annual Total Precipitation")
        base = alt.Chart(df_yearly).encode(x=alt.X("year:O", title="Year"))

        bars = base.mark_bar(color="#3498db", opacity=0.7).encode(y=alt.Y("precip_act:Q", title="Total Rainfall (mm)"))

        norm_line = alt.Chart(df_yearly).mark_rule(color="#e74c3c", strokeDash=[5, 5]).encode(y=alt.Y("precip_base:Q", title="Base Rainfall"))
        st.altair_chart(bars + norm_line, width="stretch")

    with col2:
        st.write("#### Annual Leaf Area Index")
        lai_line = alt.Chart(df_yearly).mark_line(color="green", point=True).encode(x=alt.X("year:O", title="Year"), y=alt.Y("lai_act:Q", title="Avg Annual LAI", scale=alt.Scale(zero=False)))
        lai_norm = alt.Chart(df_yearly).mark_rule(color="gray", strokeDash=[2, 2]).encode(y="lai_base:Q")

        st.altair_chart(lai_norm + lai_line, width="stretch")


def render_national(name):
    st.title(f"Dashboard for {name}")

    kpi_info = get_national_kpis(name)
    kpi_cols = st.columns(4)

    for i, (key, kpi) in enumerate(kpi_info.items()):
        kpi_cols[i].metric(label=kpi["name"], value=kpi["value"], delta=kpi["delta"], help=kpi["explanation"], delta_color="inverse" if kpi.get("invert") else "normal")

    render_national_visuals(name)

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
