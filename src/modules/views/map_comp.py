from datetime import datetime
import textwrap

import pandas as pd
import streamlit as st

from src.modules.gee_interface import (
    fetch_month_image,
    get_available_months,
)
from src.modules.mapping import render_dual_map
from src.modules.variables import get_vars


@st.cache_data(show_spinner=False)
def cached_fetch(date, band):
    return fetch_month_image(date, band)


@st.dialog("Variables Reference", width="large")
def show_variables_dialog(VARIABLES):
    records = [
        {"Variable ID": var_id, "Name": info["name"], "Unit": info["unit"], "Description": info["description"]}
        for var_id, info in VARIABLES.items()
    ]
    df = pd.DataFrame(records)

    # Force wrapping in Streamlit dataframe cells
    st.markdown(
        """
        <style>
        /* Streamlit dataframe (AgGrid) cell wrapping */
        div[data-testid="stDataFrame"] div[role="gridcell"]{
            white-space: normal !important;
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
            line-height: 1.25 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.warning("Click on the cell to see the full content if it's truncated.")
    st.dataframe(
        df,
        height=600,
        width="stretch",
        row_height=100,
        column_config={
            "Variable ID": st.column_config.TextColumn("Variable ID", width="small"),
            "Name": st.column_config.TextColumn("Name", width="small"),
            "Unit": st.column_config.TextColumn("Unit", width="small"),
            "Description": st.column_config.TextColumn("Description", width="large"),
        },
    )

    if st.button("Close"):
        st.rerun()


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
def map_container(l_var, l_date, r_var, r_date, sync_enabled, VARIABLES):
    """Fragment that holds the map. Changing variables in the sidebar triggers this block."""
    try:
        l_img = cached_fetch(l_date, l_var)
        r_img = cached_fetch(r_date, r_var)

        col1, col2 = st.columns(2)
        col1.subheader(f'{VARIABLES[l_var]["name"]} in {l_date.strftime("%B %Y")}')
        col2.subheader(f'{VARIABLES[r_var]["name"]} in {r_date.strftime("%B %Y")}')

        render_dual_map(l_img, r_img, VARIABLES[l_var], VARIABLES[r_var], sync_enabled)
    except Exception as e:
        st.error(f"Render Error: {e}")


def render():
    months = get_available_months()
    VARIABLES = get_vars("ECMWF_ERA5_LAND_MONTHLY_AGGR")
    options = list(VARIABLES.keys())

    with st.sidebar:
        st.subheader("ERA5 Weather Dashboard")
        st.subheader("Map Settings")
        sync_enabled = st.toggle("Sync Pan/Zoom", value=True, help="Enable to synchronize the pan and zoom actions between both maps.")

        with st.expander("Left Map", expanded=True):
            l_var = st.selectbox(
                "Variable", options=options, format_func=lambda k: VARIABLES[k]["name"], key="l_v_select"
            )
            l_date = date_selector(months, "left")

        with st.expander("Right Map", expanded=True):
            r_var = st.selectbox(
                "Variable", options=options, format_func=lambda k: VARIABLES[k]["name"], key="r_v_select"
            )
            r_date = date_selector(months, "right")

        if st.button("Variables Reference", use_container_width=True):
            show_variables_dialog(VARIABLES)

    map_container(l_var, l_date, r_var, r_date, sync_enabled, VARIABLES)
