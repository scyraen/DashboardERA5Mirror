from datetime import datetime, timezone

import ee
import streamlit as st
from google.oauth2 import service_account


def initialize_gee():
    """Initializes Google Earth Engine using Streamlit secrets."""
    if "gee_initialized" not in st.session_state:
        try:
            credentials_info = st.secrets["GEE_JSON"]
            scopes = ["https://www.googleapis.com/auth/earthengine"]
            credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scopes)
            ee.Initialize(credentials, project=credentials_info["project_id"])
            st.session_state["gee_initialized"] = True
            return True
        except Exception as e:
            st.error(f"GEE Initialization failed: {e}")
            return False
    return True


@st.cache_data(show_spinner="Fetching available dates...")
def get_available_months():
    initialize_gee()
    coll = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
    stats = coll.reduceColumns(ee.Reducer.minMax(), ["system:time_start"]).getInfo()

    start = datetime.fromtimestamp(stats["min"] / 1000, tz=timezone.utc)
    end = datetime.fromtimestamp(stats["max"] / 1000, tz=timezone.utc)

    months = []
    curr = datetime(start.year, start.month, 1)
    end_bound = datetime(end.year, end.month, 1)

    while curr <= end_bound:
        months.append(curr)
        if curr.month == 12:
            curr = datetime(curr.year + 1, 1, 1)
        else:
            # FIXED: Passing current year instead of month as year
            curr = datetime(curr.year, curr.month + 1, 1)
    return months


@st.cache_data(show_spinner="Checking GEE bands...")
def get_available_bands():
    initialize_gee()
    try:
        return ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR").first().bandNames().getInfo()
    except Exception:
        return []


@st.cache_data(show_spinner=False)
def get_resolved_variables(VARIABLES_DICT):
    available_set = set(get_available_bands())
    resolved = {}
    missing = []

    for key in VARIABLES_DICT.keys():
        base = key.removesuffix("_mean").removesuffix("_sum")
        candidates = [key, base, f"{base}_mean", f"{base}_sum"]

        band_id = next((c for c in candidates if c in available_set), None)

        if band_id:
            resolved[key] = band_id
        else:
            missing.append(key)

    return resolved, missing


def fetch_month_image(date_obj, band_id):
    initialize_gee()
    start_date = date_obj.strftime("%Y-%m-%d")
    return ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR").filterDate(start_date).select([band_id]).first()
