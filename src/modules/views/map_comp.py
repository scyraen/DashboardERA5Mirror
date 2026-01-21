from datetime import datetime
from pathlib import Path

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


@st.cache_data(show_spinner=False)
def load_variables_html():
    path = Path(__file__).resolve().parents[3] / "docs" / "variables.html"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        return """
        <style>
            .variables-ref, .variables-ref * {
                color: white !important;
            }
            .variables-ref {
                font-family: inherit;
                background: #1f2937;
                padding: 0;
                margin: 0;
                border-radius: 8px;
                font-size: 13px;
                line-height: 1.4;
                width: 100%;
                overflow-x: hidden;
                overflow-y: auto;
            }
            .variables-ref table {
                width: 100%;
                table-layout: fixed;
                border-collapse: collapse;
            }
            .variables-ref th,
            .variables-ref td {
                padding: 6px 8px;
                word-break: break-word;
                vertical-align: top;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
            .variables-ref thead th {
                position: sticky;
                top: 0;
                background: rgba(31, 41, 55, 0.9);
                font-weight: 600;
            }
            .variables-ref tbody tr:nth-child(odd) {
                background: rgba(255, 255, 255, 0.03);
            }
            .variables-ref tbody tr:nth-child(even) {
                background: rgba(255, 255, 255, 0.05);
            }
            .variables-ref .markdown-wrapper p {
                margin: 0 0 4px 0;
            }
        </style>
        <div class="variables-ref">
        """ + content + "</div>"
    return '<p style="color: white;">Variables reference file not found.</p>'


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
        st.subheader("ERA5 Weather Dashboard")
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

        with st.expander("Variables Reference", expanded=False):
            st.components.v1.html(load_variables_html(), height=600, scrolling=True)

    map_container(l_var, l_date, r_var, r_date, sync_enabled, resolved_map)
