import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def render_world_view():
    st.markdown("### Global Climate Pulse")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("**Global Temperature Anomaly (Relative to 1991-2020)**")
        lons, lats = np.meshgrid(np.linspace(-180, 180, 50), np.linspace(-90, 90, 25))
        z = np.sin(lats / 20) + np.random.randn(25, 50) * 0.5
        fig = go.Figure(data=go.Heatmap(z=z, x=np.linspace(-180, 180, 50), y=np.linspace(-90, 90, 25), colorscale="RdBu_r"))
        fig.update_layout(height=450, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, width="stretch")
    with col2:
        st.metric("Global Mean Temp", "+1.2°C", "0.02°C")
        st.write("**Zonal Mean Trend**")
        df = pd.DataFrame({"Lat": np.linspace(-90, 90, 50), "Val": np.random.normal(0, 1, 50)})
        st.plotly_chart(px.line(df, x="Lat", y="Val", height=250), width="stretch")


def render_country_view(loc):
    st.markdown(f"### National/Regional Resource: {loc['name']}")
    k1, k2, k3 = st.columns(3)
    k1.metric("Solar Potential", "185 W/m²", "5%")
    k2.metric("Soil Water Content", "24%", "-2%")
    k3.metric("Heating Degree Days", "142", "-10")
    st.info(f"Analyzing regional ERA5-Land data for {loc['full_address']}")


def render_city_view(loc):
    st.markdown(f"### City-Scale Analysis: {loc['name']}")
    df = pd.DataFrame({"Time": pd.date_range(start="2026-01-21", periods=48, freq="h"), "Temp": np.random.normal(8, 2, 48), "Rain": np.random.exponential(0.2, 48)})
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df.Time, y=df.Temp, name="Temp (°C)"), secondary_y=False)
    fig.add_trace(go.Bar(x=df.Time, y=df.Rain, name="Rain (mm)"), secondary_y=True)
    fig.update_layout(height=350, title="48-Hour Local Reanalysis")
    st.plotly_chart(fig, width="stretch")


def get_depth_category(location):
    addr = location.raw.get("address", {})
    osm_type = location.raw.get("type", "")
    if osm_type in ["continent", "ocean"] or "continent" in addr:
        return "world"
    elif "country" in addr and (osm_type == "administrative" or "country" in location.raw.get("class", "")):
        return "country"
    return "city"


def reset_global():
    st.session_state.loc = {"type": "world", "name": "Global", "breadcrumbs": "World"}
    st.session_state.search_input = ""


def render():
    import numpy as np
    import pandas as pd
    import streamlit as st
    from geopy.geocoders import Nominatim

    # --- PAGE CONFIG ---
    st.set_page_config(layout="wide", page_title="Climate Reanalysis Portal")

    # Initialize Geocoder
    geolocator = Nominatim(user_agent="climate_reanalysis_dash_v2")

    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title("Navigation Control")

    # Level 1: World View (The ultimate reset)
    if st.sidebar.button("Reset to World View", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.sidebar.markdown("---")

    # Level 2: Continent
    selected_cont = st.sidebar.selectbox("1. Continent", options=["--", "Africa", "Antarctica", "Asia", "Europe", "North America", "Oceania", "South America"], index=0 if "continent" not in st.session_state else 1)  # Simple logic to keep state

    # Level 3: Country Search
    selected_country = st.session_state.get("country", "--")

    if selected_cont != "--":
        st.sidebar.write("---")
        # Use columns to put the search and the back button side-by-side
        col_search, col_back = st.sidebar.columns([4, 1])

        with col_search:
            country_query = st.text_input("2. Search Country", placeholder="e.g. Italy")

        with col_back:
            st.write(" ")  # Padding
            if st.button("↩", key="back_to_cont", help="Back to Continent Level"):
                st.session_state.country = "--"
                st.session_state.city = "--"
                st.rerun()

        if country_query:
            locations = geolocator.geocode(country_query, exactly_one=False, limit=3, featuretype="country")
            if locations:
                options = {loc.address: loc for loc in locations}
                selected_country = st.sidebar.selectbox("Confirm Country:", options.keys())
                st.session_state.country = selected_country
                st.session_state.country_coords = (options[selected_country].latitude, options[selected_country].longitude)

    # Level 4: City Search
    selected_city = st.session_state.get("city", "--")

    if selected_country != "--":
        st.sidebar.write("---")
        col_search_city, col_back_city = st.sidebar.columns([4, 1])

        with col_search_city:
            city_query = st.text_input("3. Search City", placeholder="e.g. Rome")

        with col_back_city:
            st.write(" ")  # Padding
            if st.button("↩", key="back_to_country", help="Back to Country Level"):
                st.session_state.city = "--"
                st.rerun()

        if city_query:
            full_query = f"{city_query}, {selected_country}"
            locations = geolocator.geocode(full_query, exactly_one=False, limit=3, language="en")
            if locations:
                options = {loc.address: loc for loc in locations}
                selected_city = st.sidebar.selectbox("Confirm City:", options.keys())
                st.session_state.city = selected_city
                st.session_state.city_coords = (options[selected_city].latitude, options[selected_city].longitude)

    # --- APP LOGIC ---
    # Determine level for the Title and Map
    if selected_city != "--":
        title, level, coords, zoom = selected_city.split(",")[0], "Citywide", st.session_state.city_coords, 10
        st.title(f"Insights: {title}")
        st.caption(f"Depth: {level}")
    elif selected_country != "--":
        title, level, coords, zoom = selected_country.split(",")[0], "National", st.session_state.country_coords, 4
        st.title(f"Insights: {title}")
        st.caption(f"Depth: {level}")
    elif selected_cont != "--":
        title, level, coords, zoom = selected_cont, "Continental", [20, 0], 2
        st.title(f"Insights: {title}")
        st.caption(f"Depth: {level}")
    else:
        title, level, coords, zoom = "Worldwide", "Global", [20, 0], 1
        st.title(f"Insights: {title}")
        st.caption(f"Depth: {level}")

    # --- MAIN DASHBOARD ---
    st.title(f"Insights: {title}")
    st.caption(f"Depth: {level}")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Temp Anomaly", "+1.2°C")
    k2.metric("Precipitation", "92%")
    k3.metric("Soil Moisture", "0.24")
    k4.metric("Alert Status", "Normal")

    st.markdown("---")
    c_map, c_chart = st.columns([2, 1])

    with c_map:
        if coords:
            st.map(pd.DataFrame({"lat": [coords[0]], "lon": [coords[1]]}), zoom=zoom)

    with c_chart:
        st.line_chart(np.random.randn(20))
        st.bar_chart(np.random.randn(10))


if __name__ == "__main__":
    render()
