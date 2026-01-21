import ee
import pandas as pd
import plotly.express as px
import streamlit as st


def render():
    st.header("Time-Series Analysis")

    lon = st.number_input("Longitude", value=13.405, format="%.3f")
    lat = st.number_input("Latitude", value=52.520, format="%.3f")
    point = ee.Geometry.Point([lon, lat])

    if st.button("Fetch Hourly Data"):
        with st.spinner("Extracting data from GEE..."):
            coll = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").filterBounds(point).limit(168)

            def get_val(img):
                val = img.reduceRegion(ee.Reducer.mean(), point, 9000).get("temperature_2m")
                return img.set("date", img.date().format()).set("temp", val)

            data = coll.map(get_val).reduceColumns(ee.Reducer.toList(2), ["date", "temp"]).get("list")
            df = pd.DataFrame(data.getInfo(), columns=["date", "temp"])
            df["date"] = pd.to_datetime(df["date"])

            fig = px.line(df, x="date", y="temp", title="Temperature Trend (Last 7 Days)")
            st.plotly_chart(fig, use_container_width=True)
