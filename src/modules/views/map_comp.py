from datetime import datetime

import streamlit as st

from src.modules.gee_interface import (
    fetch_month_image,
    get_available_months,
)
from src.modules.mapping import render_dual_map
from src.modules.variables import get_filtered_variables, get_vars


@st.cache_data(show_spinner=False)
def cached_fetch(date, band):
    return fetch_month_image(date, band)


def copy_right_to_left():
    st.session_state.l_v_select = st.session_state.r_v_select


def copy_left_to_right():
    st.session_state.r_v_select = st.session_state.l_v_select


def date_selector(months: list[datetime], key_prefix: str) -> datetime:
    years = sorted(list(set(m.year for m in months)), reverse=True)
    col_y, col_m = st.columns(2)
    with col_y:
        year = st.selectbox("Year", years, key=f"{key_prefix}_year")
    with col_m:
        available_in_year = sorted([m.month for m in months if m.year == year])
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month = st.selectbox("Month", available_in_year, format_func=lambda x: month_names[x - 1], key=f"{key_prefix}_month")
    return datetime(year, month, 1)


@st.fragment
def map_container(l_var, l_date, r_var, r_date, sync_enabled, VARIABLES):
    """Fragment that holds the map. Changing variables in the sidebar triggers this block."""
    try:
        l_img = cached_fetch(l_date, l_var)
        r_img = cached_fetch(r_date, r_var)

        col1, col2 = st.columns(2)
        col1.subheader(f'{VARIABLES[l_var]["name"]} ({l_date.strftime("%b %Y")})')
        col2.subheader(f'{VARIABLES[r_var]["name"]} ({r_date.strftime("%b %Y")})')

        render_dual_map(l_img, r_img, VARIABLES[l_var], VARIABLES[r_var], sync_enabled)
    except Exception as e:
        st.error(f"Render Error: {e}")


def render():
    months = get_available_months()
    all_vars = get_vars("ECMWF_ERA5_LAND_MONTHLY_AGGR")
    VARIABLES = get_filtered_variables(all_vars)
    options = list(VARIABLES.keys())

    if "l_v_select" not in st.session_state:
        st.session_state.l_v_select = options[0]
    if "r_v_select" not in st.session_state:
        st.session_state.r_v_select = options[0]

    with st.sidebar:
        st.title("Map Settings")

        with st.expander("Left Map", expanded=True):
            l_var = st.selectbox("Variable", options=options, format_func=lambda k: VARIABLES[k]["name"], help=VARIABLES[st.session_state.get("l_v_select", options[0])]["description"], key="l_v_select")
            st.button("Copy Right Map Variable", on_click=copy_right_to_left)
            l_date = date_selector(months, "left")

        if "sync_enabled" not in st.session_state:
            st.session_state.sync_enabled = True

        def toggle_sync():
            st.session_state.sync_enabled = not st.session_state.sync_enabled

        icon = "🔗" if st.session_state.sync_enabled else "⛓️‍💥"
        help = f"Click to {'unlink' if st.session_state.sync_enabled else 'link'} map views"

        st.button(icon, on_click=toggle_sync, help=help, use_container_width=True)

        sync_enabled = st.session_state.sync_enabled

        with st.expander("Right Map", expanded=True):
            r_var = st.selectbox("Variable", options=options, format_func=lambda k: VARIABLES[k]["name"], help=VARIABLES[st.session_state.get("r_v_select", options[0])]["description"], key="r_v_select")
            st.button("Copy Left Map Variable", on_click=copy_left_to_right)
            r_date = date_selector(months, "right")

    map_container(l_var, l_date, r_var, r_date, sync_enabled, VARIABLES)
