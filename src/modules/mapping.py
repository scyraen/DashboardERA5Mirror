import folium
import streamlit.components.v1 as components
from folium.plugins import DualMap


def create_vertical_legend(conf, side="left"):
    colors = conf["vis"]["palette"]
    vmin = conf["vis"]["min"]
    vmax = conf["vis"]["max"]
    name = conf["name"]

    gradient = f"linear-gradient(to top, {", ".join(colors)})"

    side_pos = "left: 20px;" if side == "left" else "right: 20px;"

    return f"""
    <div style='
        position: fixed; 
        z-index: 9999; 
        {side_pos}
        top: 50%; 
        transform: translateY(-50%);
        background: rgba(255, 255, 255, 0.9);
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #ddd;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 60px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    '>
        <div style='
            writing-mode: vertical-rl; 
            transform: rotate(180deg); 
            font-weight: bold; 
            font-size: 13px;
            margin-bottom: 10px;
            color: #333;
        '>
            {name}
        </div>
        <div style='font-size: 11px; margin-bottom: 4px; color: #555;'>{vmax}</div>
        <div style='
            width: 18px; 
            height: 180px; 
            background: {gradient}; 
            border: 1px solid #888;
            border-radius: 2px;
        '></div>
        <div style='font-size: 11px; margin-top: 4px; color: #555;'>{vmin}</div>
    </div>
    """


def render_dual_map(l_img, r_img, l_conf, r_conf, height=600):
    """Renders the DualMap with custom-built HTML legends."""
    dm = DualMap(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

    l_url = l_img.getMapId(l_conf["vis"])["tile_fetcher"].url_format
    r_url = r_img.getMapId(r_conf["vis"])["tile_fetcher"].url_format

    folium.TileLayer(tiles=l_url, attr="GEE", name=l_conf["name"], overlay=True).add_to(dm.m1)
    folium.TileLayer(tiles=r_url, attr="GEE", name=r_conf["name"], overlay=True).add_to(dm.m2)

    l_legend_html = create_vertical_legend(l_conf, side="left")
    r_legend_html = create_vertical_legend(r_conf, side="right")

    m_html = dm.get_root().render()

    full_html = l_legend_html + r_legend_html + m_html

    components.html(full_html, height=height)
