import ee
import streamlit as st
from google.oauth2 import service_account


def initialize_gee():
    """Initializes Google Earth Engine using Streamlit secrets."""
    try:
        credentials_info = st.secrets["GEE_JSON"]
        scopes = ["https://www.googleapis.com/auth/earthengine"]
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=scopes
        )
        ee.Initialize(credentials, project=credentials_info["project_id"])
        return True

    except Exception as e:
        st.error(f"GEE Initialization failed: {e}")
        return False


def test_connection():
    """Simple test to fetch ERA5 metadata."""
    try:
        era5_test = ee.ImageCollection("ECMWF/ERA5/DAILY").first()
        info = era5_test.getInfo()
        msg = f"Successfully connected! First ERA5 image info: {info}"
        return msg
    except Exception as e:
        return f"Connection test failed: {e}"
