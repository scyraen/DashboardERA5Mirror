import folium
import streamlit as st
from folium.plugins import DualMap
from folium.template import Template as FoliumTemplate


def create_vertical_legend(conf, side="left"):
    """Generates the HTML for a vertically centered legend."""
    vis = conf["vis"]
    colors = vis["palette"]
    vmin, vmax = vis["min"], vis["max"]
    name = conf["name"]

    gradient = f"linear-gradient(to top, {', '.join(colors)})"

    side_pos = "left: 10px;" if side == "left" else "right: 10px;"

    return f"""
    <div style="
        position: absolute; z-index: 9999; {side_pos} top: 50%; 
        transform: translateY(-50%);
        background: rgba(255, 255, 255, 0.85);
        padding: 8px; border-radius: 6px; border: 1px solid #999;
        font-family: sans-serif; display: flex; flex-direction: column;
        align-items: center; width: 50px; pointer-events: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    ">
        <div style="writing-mode: vertical-rl; transform: rotate(180deg); 
                    font-weight: bold; font-size: 11px; margin-bottom: 5px; white-space: nowrap;">{name}</div>
        <div style="font-size: 10px; margin-bottom: 2px;">{vmax}</div>
        <div style="width: 12px; height: 150px; background: {gradient}; border: 1px solid #777;"></div>
        <div style="font-size: 10px; margin-top: 2px;">{vmin}</div>
    </div>
    """


def render_dual_map(l_img, r_img, l_conf, r_conf, sync_enabled, height=550):
    l_url = l_img.getMapId(l_conf["vis"])["tile_fetcher"].url_format
    r_url = r_img.getMapId(r_conf["vis"])["tile_fetcher"].url_format

    dm = DualMap(location=[20, 0], zoom_start=3, tiles="CartoDB positron", control=False)

    if not sync_enabled:
        dm._template = FoliumTemplate("{% macro script(this, kwargs) %}{% endmacro %}")
        dm.default_js = []

    folium.TileLayer(tiles=l_url, attr="GEE", name=l_conf["name"], overlay=True).add_to(dm.m1)
    folium.TileLayer(tiles=r_url, attr="GEE", name=r_conf["name"], overlay=True).add_to(dm.m2)

    l_legend = create_vertical_legend(l_conf, side="left")
    r_legend = create_vertical_legend(r_conf, side="right")

    dm.m1.get_root().html.add_child(folium.Element(l_legend))
    dm.m2.get_root().html.add_child(folium.Element(r_legend))

    st.components.v1.html(dm._repr_html_(), height=height)
    st.markdown(
        """
    <style>
        .stMainBlockContainer{
            height: 100vh !important;
            padding-top: 5rem;
            padding-left: 16px;
            padding-right: 16px;    
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
