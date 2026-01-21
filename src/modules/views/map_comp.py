from datetime import datetime

import streamlit as st

from src.modules.gee_interface import get_available_months, get_era5_image
from src.modules.mapping import render_dual_map
from src.modules.variables import VARIABLES

st.set_page_config(layout="wide", page_title="ERA5 Dashboard")


def date_selector(months, key_prefix):
    """Helper to render Year and Month dropdowns."""
    years = sorted(list(set(m.year for m in months)), reverse=True)

    col_y, col_m = st.columns(2)
    with col_y:
        year = st.selectbox("Year", years, key=f"{key_prefix}_year")
    with col_m:
        # Filter available months for the selected year
        available_in_year = [m.month for m in months if m.year == year]
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        month = st.selectbox(
            "Month",
            available_in_year,
            format_func=lambda x: month_names[x - 1],
            key=f"{key_prefix}_month",
        )
    return datetime(year, month, 1)


def render():
    st.title("🌍 ERA5-Land Comparison")

    months = get_available_months()
    var_options = list(VARIABLES.keys())

    with st.sidebar:
        st.header("Left Map")
        l_v = st.selectbox("Variable", var_options, key="l_v")
        l_d = date_selector(months, "left")

        st.divider()

        st.header("Right Map")
        r_v = st.selectbox("Variable", var_options, key="r_v")
        r_d = date_selector(months, "right")

    # Data Fetching
    try:
        # Pass the whole config to mapping for the legend name
        l_config = VARIABLES[l_v]
        r_config = VARIABLES[r_v]

        left_img = get_era5_image(l_d, l_config["band"])
        right_img = get_era5_image(r_d, r_config["band"])

        st.subheader(f"Comparing {l_v} ({l_d:%B %Y}) vs {r_v} ({r_d:%B %Y})")

        render_dual_map(left_img, right_img, l_config, r_config)

    except Exception as e:
        st.error(f"Error: {e}")


if __name__ == "__main__":
    render()
