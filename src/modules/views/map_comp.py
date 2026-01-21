from datetime import datetime

import streamlit as st

from src.modules.gee_interface import (
    fetch_month_image,
    get_available_months,
    get_resolved_variables,
)
from src.modules.mapping import render_dual_map
from src.modules.variables import VARIABLES


@st.cache_data(show_spinner=False)
def cached_fetch(date, band):
    return fetch_month_image(date, band)


def date_selector(months: list[datetime], key_prefix: str) -> datetime:
    years = sorted(list(set(m.year for m in months)), reverse=True)
    col_y, col_m = st.columns(2)
    with col_y:
        year = st.selectbox("Year", years, key=f"{key_prefix}_year")
    with col_m:
        available_in_year = sorted([m.month for m in months if m.year == year])
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month = st.selectbox(
            "Month", available_in_year, format_func=lambda x: month_names[x - 1], key=f"{key_prefix}_month"
        )
    return datetime(year, month, 1)


@st.fragment
def map_container(l_var, l_date, r_var, r_date, sync_enabled, resolved_map):
    """Fragment that holds the map. Changing variables in the sidebar triggers this block."""
    l_band = resolved_map[l_var]
    r_band = resolved_map[r_var]

    try:
        l_img = cached_fetch(l_date, l_band)
        r_img = cached_fetch(r_date, r_band)

        st.info(f"Comparing {VARIABLES[l_var]['name']} vs {VARIABLES[r_var]['name']}")

        render_dual_map(l_img, r_img, VARIABLES[l_var], VARIABLES[r_var], sync_enabled)
    except Exception as e:
        st.error(f"Render Error: {e}")


def render():
    months = get_available_months()
    resolved_map, _ = get_resolved_variables(VARIABLES)
    resolved_options = list(resolved_map.keys())

    with st.sidebar:
        st.subheader("Map Settings")
        sync_enabled = st.toggle("Sync Pan/Zoom", value=True)

        with st.expander("Left Map", expanded=True):
            l_var = st.selectbox(
                "Variable", options=resolved_options, format_func=lambda k: VARIABLES[k]["name"], key="l_v_select"
            )
            l_date = date_selector(months, "left")

        with st.expander("Right Map", expanded=True):
            r_var = st.selectbox(
                "Variable", options=resolved_options, format_func=lambda k: VARIABLES[k]["name"], key="r_v_select"
            )
            r_date = date_selector(months, "right")

    map_container(l_var, l_date, r_var, r_date, sync_enabled, resolved_map)
