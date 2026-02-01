from datetime import datetime, timezone

import ee
import streamlit as st
from dateutil.relativedelta import relativedelta  # standard for date math
from google.oauth2 import service_account


# Initialize once at the module level or in main()
def initialize_gee():
    if "gee_initialized" not in st.session_state:
        try:
            credentials_info = st.secrets["GEE_JSON"]
            credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=["https://www.googleapis.com/auth/earthengine"])
            ee.Initialize(credentials, project=credentials_info["project_id"])
            st.session_state["gee_initialized"] = True
        except Exception as e:
            st.error(f"GEE Initialization failed: {e}")


@st.cache_data(show_spinner="Fetching available dates...")
def get_available_months():
    # Fetch min/max once
    coll = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
    stats = coll.reduceColumns(ee.Reducer.minMax(), ["system:time_start"]).getInfo()

    start = datetime.fromtimestamp(stats["min"] / 1000, tz=timezone.utc)
    end = datetime.fromtimestamp(stats["max"] / 1000, tz=timezone.utc)

    months = []
    curr = datetime(start.year, start.month, 1)
    end_bound = datetime(end.year, end.month, 1)

    while curr <= end_bound:
        months.append(curr)
        curr += relativedelta(months=1)
    return months


def fetch_month_image(date_obj, band_id):
    """Fetches a single monthly image. No caching here
    because ee.Image objects are just 'proxies'."""
    start_dt = ee.Date(date_obj.strftime("%Y-%m-%d"))
    end_dt = start_dt.advance(1, "month")

    return ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR").filterDate(start_dt, end_dt).select(band_id).first()
