import streamlit as st


def render():
    """Display helpful project information."""
    st.title("Info")
    st.markdown(
        """

        ERA5 Hourly Weather Data Dashboard is a collaborative university project to visualize global weather patterns using the ERA5 dataset via Google Earth Engine (GEE), built with Streamlit and Plotly.

        ## Data Source

        - Website: https://dashboard-era5.streamlit.app/
        - Dataset: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=overview/

        ## Contact Information

        Students involved:
        - Eren Kocadag (eren.kocadag@fu-berlin.de)
        - Constantin Tomei (ct3828fu@fu-berlin.de)
        - Ayse Yasemin Mutlugil (yasemin.mutlugil@fu-berlin.de)
        """
    )
