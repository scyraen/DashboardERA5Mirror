import time

import streamlit as st
from geopy.geocoders import Nominatim
from pycountry_convert import country_alpha2_to_continent_code

from docs.constants import continents
from src.modules.chart_views.city import render_city
from src.modules.chart_views.continent import render_continent
from src.modules.chart_views.country import render_national
from src.modules.chart_views.globe import render_global


@st.cache_data(show_spinner="Searching location...")
def get_locations(_geolocator, query, limit=None, feature_type=None, country_codes=None):
    """
    Function to fetch locations.
    Streamlit caches the result based on the input arguments.
    """
    time.sleep(1)  # Nominatim policy

    try:
        locations = _geolocator.geocode(query, exactly_one=False, limit=limit, featuretype=feature_type, country_codes=country_codes, addressdetails=True, language="en")
        return locations
    except Exception as e:
        st.error(f"Geocoding error: {e}")
        return None


def reset_state(depth=0):
    for v in ["cont_ver", "country_ver", "city_ver"]:
        if v not in st.session_state:
            st.session_state[v] = 0

    # 1. Reset City
    if depth <= 2:
        st.session_state.city = "--"
        st.session_state.city_ver += 1
        st.session_state.last_city_query = ""

    # 2. Reset Country
    if depth <= 1:
        st.session_state.country = "--"
        st.session_state.country_ver += 1
        st.session_state.last_country_query = ""
        if "country_iso" in st.session_state:
            del st.session_state.country_iso

    # 3. Reset Continent
    if depth == 0:
        st.session_state.continent = "--"
        st.session_state.cont_ver += 1


def render():
    if "continent_select" not in st.session_state:
        st.session_state.continent_select = "--"
    if "country_input" not in st.session_state:
        st.session_state.country_input = ""
    if "city_input" not in st.session_state:
        st.session_state.city_input = ""

    # PAGE CONFIG
    st.set_page_config(layout="wide", page_title="Climate Reanalysis Portal")

    # Initialize Geocoder
    geolocator = Nominatim(user_agent="climate_dashboard (ct3828fu@zedat.fu-berlin.de")
    continent_map = {"africa": "AF", "asia": "AS", "europe": "EU", "north_america": "NA", "south_america": "SA", "oceania": "OC", "antarctica": "AN"}

    # SIDEBAR NAVIGATION
    st.sidebar.title("Navigation Control")

    # Level 1: World
    st.sidebar.button("Reset to World View", on_click=reset_state, args=(0,), width="stretch")

    st.sidebar.markdown("---")

    # Level 2: Continent
    st.sidebar.write("Continent")
    continent_options = ["--"] + [c for c in continents.keys()]

    selected_cont = st.sidebar.selectbox(
        "Continent", options=continent_options, format_func=lambda k: k if k == "--" else continents[k]["name"], key=f"cont_select_{st.session_state.get('cont_ver', 0)}", on_change=reset_state, args=(1,), label_visibility="collapsed"
    )
    st.session_state.continent = selected_cont

    # Level 3: Country
    if st.session_state.continent not in ["--", "antarctica"]:
        st.sidebar.write("---")
        st.sidebar.write("Country")
        col_search, col_back = st.sidebar.columns([4, 1])

        with col_search:
            country_query = st.text_input("", placeholder="e.g. Italy", label_visibility="collapsed", key=f"country_input_{st.session_state.get('country_ver', 0)}")

        with col_back:
            st.button("↵", key="back_to_cont", help="Back to Continent Level", on_click=reset_state, args=(1,))

        if country_query and country_query != st.session_state.get("last_country_query", ""):
            st.session_state.last_country_query = country_query
            locations = get_locations(geolocator, country_query, limit=1, feature_type="country")

            if locations:
                loc_obj = locations[0]
                iso_code = loc_obj.raw.get("address", {}).get("country_code", "").upper()

                try:
                    detected_cont_code = country_alpha2_to_continent_code(iso_code)
                    target_cont_code = continent_map.get(st.session_state.continent)

                    if detected_cont_code != target_cont_code:
                        st.sidebar.error(f"'{country_query}' is not in the selected continent.")
                    else:
                        st.session_state.country = loc_obj.address
                        st.session_state.country_coords = (loc_obj.latitude, loc_obj.longitude)
                        st.session_state.country_iso = iso_code.lower()
                        st.rerun()

                except KeyError:
                    st.sidebar.warning(f"Could not verify continent for {country_query}")

        elif not country_query and st.session_state.get("country", "--") != "--":
            reset_state(depth=1)
            st.rerun()

    # Level 4: City Search
    # Level 4: City Search
    if st.session_state.get("country", "--") != "--":
        st.sidebar.write("---")
        st.sidebar.write("City")

        col_city, col_back_city = st.sidebar.columns([4, 1])
        with col_city:
            # Dynamic key to allow resetting the text input
            city_query = st.text_input("", placeholder="e.g. Rome", label_visibility="collapsed", key=f"city_input_{st.session_state.get('city_ver', 0)}")
        with col_back_city:
            st.button("↵", key="back_to_country", on_click=reset_state, args=(2,))

        # 1. TRIGGER SEARCH (Only if query is new)
        if city_query and city_query != st.session_state.get("last_city_query", ""):
            locations = get_locations(geolocator, city_query, feature_type="city", country_codes=st.session_state.get("country_iso"), limit=5)

            if locations:
                st.session_state.last_city_query = city_query
                if len(locations) == 1:
                    # OPTION 1: Automatic selection for single result
                    loc = locations[0]
                    st.session_state.city = loc.address.split(",")[0].strip()
                    st.session_state.city_coords = (loc.latitude, loc.longitude)
                    st.session_state.city_options = None
                    st.rerun()
                else:
                    # MULTIPLE results: Save them to show the selectbox
                    st.session_state.city_options = locations
            else:
                st.sidebar.error(f"No results for '{city_query}'")

        # 2. SELECTION BOX (This renders when multiple cities are found)
        if st.session_state.get("city_options"):
            # We need a placeholder so the first real city can be "changed" to
            opts = {loc.address: loc for loc in st.session_state.city_options}
            display_list = ["-- Select specific location --"] + list(opts.keys())

            def handle_multiselect():
                selection = st.session_state.city_confirm_box
                if selection != "-- Select specific location --":
                    chosen_loc = opts[selection]
                    st.session_state.city = selection.split(",")[0].strip()
                    st.session_state.city_coords = (chosen_loc.latitude, chosen_loc.longitude)
                    st.session_state.city_options = None  # Close the box

            st.sidebar.selectbox("Multiple matches found:", options=display_list, key="city_confirm_box", on_change=handle_multiselect)

        # 3. RESET IF TEXT IS CLEARED
        elif not city_query and st.session_state.get("city", "--") != "--":
            reset_state(depth=2)
            st.rerun()

    # APP LOGIC
    current_city = st.session_state.get("city", "--")
    current_country = st.session_state.get("country", "--")
    current_cont = st.session_state.get("continent", "--")

    if current_city != "--":
        render_city(current_city, st.session_state.get("city_coords"))
    elif current_country != "--":
        render_national(current_country)
    elif current_cont != "--":
        render_continent(current_cont)
    else:
        render_global()


if __name__ == "__main__":
    render()
