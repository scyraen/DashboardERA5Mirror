from datetime import datetime
from typing import cast

import ee
import folium
import streamlit as st
import streamlit.components.v1 as components
from branca.element import Figure
from folium.plugins import DualMap

from modules.get_data import available_bands, available_months, fetch_month_image, initialize
from modules.variables import VARIABLES

st.set_page_config(page_title="ERA5 Weather Dashboard", layout="wide")


@st.cache_resource(show_spinner=False)
def ensure_ee_initialized() -> bool:
    initialize()
    return True


@st.cache_data(show_spinner=False)
def band_options() -> tuple[list[str], dict[str, str], dict[str, str], list[str]]:
    """
    Return curated variable keys, their labels, and a mapping to the actual band id
    present in the collection. Variables that cannot be resolved are returned in missing.
    """
    ensure_ee_initialized()
    available_set = set(available_bands())

    resolved: dict[str, str] = {}
    missing: list[str] = []

    for key in VARIABLES.keys():
        base = key.removesuffix("_mean").removesuffix("_sum")
        candidates = [
            key,
            base,
            f"{base}_mean",
            f"{base}_sum",
        ]
        seen: set[str] = set()
        deduped = []
        for cand in candidates:
            if cand not in seen:
                seen.add(cand)
                deduped.append(cand)

        band_id = next((cand for cand in deduped if cand in available_set), None)
        if band_id:
            resolved[key] = band_id
        else:
            missing.append(key)

    bands = list(resolved.keys())
    labels = {band: str(VARIABLES[band]["name"]) for band in bands}
    return bands, labels, resolved, missing


@st.cache_data(show_spinner=False)
def month_options() -> list[datetime]:
    ensure_ee_initialized()
    months = available_months()
    return months


def month_slider(months: list[datetime], label: str, default: datetime | None = None) -> datetime:
    latest_idx = max(len(months) - 1, 0)
    if default and default in months:
        default_value = default
    else:
        default_value = months[latest_idx]
    return st.select_slider(
        label,
        options=months,
        value=default_value,
        format_func=lambda d: d.strftime("%Y-%m"),
        help="Scroll through available monthly aggregates (first to last available month).",
    )


def render_map(
    image: ee.Image,  # type: ignore[reportPrivateImportUsage]
    title: str,
    vis_params: dict[str, object],
    height: int = 480,
) -> None:
    if not vis_params:
        vis_params = {
            "min": 0,
            "max": 300,
            "palette": ["#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636", "#f0f921"],
        }
    map_id = ee.Image(image).getMapId(vis_params)  # type: ignore[reportPrivateImportUsage]

    fmap = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
    folium.TileLayer(
        tiles=map_id["tile_fetcher"].url_format,
        attr="Map Data © Google Earth Engine",
        name=title,
        overlay=True,
        control=False,
    ).add_to(fmap)

    html = fmap.get_root().render()
    # Render once per rerun; no explicit key to avoid iframe key issues.
    components.html(html, height=height, scrolling=False)


def render_synced_maps(
    left_image: ee.Image,  # type: ignore[reportPrivateImportUsage]
    right_image: ee.Image,  # type: ignore[reportPrivateImportUsage]
    left_title: str,
    right_title: str,
    left_vis: dict[str, object] | None,
    right_vis: dict[str, object] | None,
    height: int = 480,
) -> None:
    """
    Render two folium maps that stay in sync (pan/zoom) using Leaflet.Sync via DualMap.
    """
    default_vis = {
        "min": 0,
        "max": 300,
        "palette": ["#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636", "#f0f921"],
    }
    left_vis = left_vis or default_vis
    right_vis = right_vis or default_vis

    left_map_id = ee.Image(left_image).getMapId(left_vis)  # type: ignore[reportPrivateImportUsage]
    right_map_id = ee.Image(right_image).getMapId(right_vis)  # type: ignore[reportPrivateImportUsage]

    dual_map = DualMap(location=[20, 0], zoom_start=2, tiles="CartoDB positron", control=False)
    if isinstance(dual_map._parent, Figure):
        dual_map._parent.height = f"{height}px"
        dual_map._parent.width = "100%"

    folium.TileLayer(
        tiles=left_map_id["tile_fetcher"].url_format,
        attr="Map Data © Google Earth Engine",
        name=left_title,
        overlay=True,
        control=False,
    ).add_to(dual_map.m1)
    folium.TileLayer(
        tiles=right_map_id["tile_fetcher"].url_format,
        attr="Map Data © Google Earth Engine",
        name=right_title,
        overlay=True,
        control=False,
    ).add_to(dual_map.m2)

    html = dual_map.get_root().render()
    components.html(html, height=height, scrolling=False)


def layout_sidebar(
    bands: list[str],
    labels: dict[str, str],
    months: list[datetime],
    missing: list[str] | None = None,
) -> tuple[str, datetime, str, datetime]:
    with st.sidebar:
        st.header("Controls")
        ensure_ee_initialized()

        if missing:
            with st.expander("Unavailable variables", expanded=False):
                st.write("These variables are in variables.py but not in the dataset:")
                st.write(", ".join(missing))

        default_var = "temperature_2m"
        temp_idx = bands.index(default_var) if default_var in bands else 0
        left_idx = temp_idx
        right_idx = temp_idx

        left_month_default = months[-1] if months else None  # most recent
        right_month_default = months[0] if months else None  # earliest

        with st.expander("Map left", expanded=True):
            left_var = st.selectbox(
                "Variable", options=bands, index=left_idx, format_func=lambda k: labels[k], key="left_var"
            )
            left_ts = month_slider(months, label="Month (left)", default=left_month_default)

        with st.expander("Map right", expanded=True):
            right_var = st.selectbox(
                "Variable", options=bands, index=right_idx, format_func=lambda k: labels[k], key="right_var"
            )
            right_ts = month_slider(months, label="Month (right)", default=right_month_default)

    return left_var, left_ts, right_var, right_ts


def main() -> None:
    st.title("ERA5 Weather Dashboard")
    st.caption("Compare two ERA5-Land variables side-by-side across monthly aggregates.")

    bands, labels, resolved, missing = band_options()
    months = month_options()
    if not bands:
        st.error(
            "No curated variables are available in the ERA5-Land monthly aggregate collection. " "Check variable names."
        )
        return
    if not months:
        st.error("Could not determine available months in the ERA5-Land monthly aggregate collection.")
        return

    left_var, left_ts, right_var, right_ts = layout_sidebar(bands, labels, months, missing)

    left_image = right_image = None
    left_band = right_band = None
    try:
        left_band = resolved.get(left_var)
        right_band = resolved.get(right_var)

        if left_band:
            left_image = fetch_month_image(left_ts, left_band)
        else:
            st.warning(f"{left_var} not available in collection; select another variable.", icon="⚠️")

        if right_band:
            right_image = fetch_month_image(right_ts, right_band)
        else:
            st.warning(f"{right_var} not available in collection; select another variable.", icon="⚠️")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load data: {exc}")
        return

    left_vis = cast(dict[str, object], VARIABLES.get(left_var, {}).get("vis", {}))
    right_vis = cast(dict[str, object], VARIABLES.get(right_var, {}).get("vis", {}))

    col1, col2 = st.columns(2)
    with col1:
        st.text(f"{labels[left_var]} — {left_ts:%m.%Y}")
    with col2:
        st.text(f"{labels[right_var]} — {right_ts:%m.%Y}")

    if left_image and right_image:
        render_synced_maps(left_image, right_image, labels[left_var], labels[right_var], left_vis, right_vis)
    else:
        with col1:
            if left_image:
                render_map(left_image, labels[left_var], vis_params=left_vis)
            else:
                st.info("Select an available variable to view the left map.")

        with col2:
            if right_image:
                render_map(right_image, labels[right_var], vis_params=right_vis)
            else:
                st.info("Select an available variable to view the right map.")


if __name__ == "__main__":
    main()
