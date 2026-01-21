from datetime import datetime

import ee
import streamlit as st
from google.oauth2 import service_account


def initialize_gee():
    """Initializes Google Earth Engine using Streamlit secrets."""
    try:
        credentials_info = st.secrets["GEE_JSON"]
        scopes = ["https://www.googleapis.com/auth/earthengine"]
        credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scopes)
        ee.Initialize(credentials, project=credentials_info["project_id"])
        return True

    except Exception as e:
        st.error(f"GEE Initialization failed: {e}")
        return False


@st.cache_data(show_spinner="Fetching available months...")
def get_available_months():
    initialize_gee()
    coll = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
    stats = coll.reduceColumns(ee.Reducer.minMax(), ["system:time_start"]).getInfo()

    start = datetime.fromtimestamp(stats["min"] / 1000)
    end = datetime.fromtimestamp(stats["max"] / 1000)

    # Generate list of months (YYYY-MM-01)
    dates = []
    curr = datetime(start.year, start.month, 1)
    while curr <= end:
        dates.append(curr)
        if curr.month == 12:
            curr = datetime(curr.year + 1, 1, 1)
        else:
            curr = datetime(curr.year, curr.month + 1, 1)
    return dates


def get_era5_image(date_obj, band_name):
    """Fetches a single band image for a specific month."""
    initialize_gee()
    start_date = date_obj.strftime("%Y-%m-01")
    end_date = date_obj.replace(day=28)  # Safety for next month calc

    img = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR").filterDate(start_date, end_date).select(band_name).first()
    return img


def test_connection():
    """Simple test to fetch ERA5 metadata."""
    try:
        era5_test = ee.ImageCollection("ECMWF/ERA5/DAILY").first()
        info = era5_test.getInfo()
        msg = f"Successfully connected! First ERA5 image info: {info}"
        return msg
    except Exception as e:
        return f"Connection test failed: {e}"
