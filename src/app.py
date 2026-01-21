import streamlit as st
from modules.gee_interface import initialize_gee
from modules.views import charts, map_comp, map_evo


def main():
    st.set_page_config(layout="wide", page_title="ERA5 Explorer")
    initialize_gee()

    # 1. Define Pages
    pages = [
        st.Page(
            map_comp.render,
            icon=":material/compare:",
            title="Map Comparison",
            url_path="map-comparison",
        ),
        st.Page(
            charts.render,
            icon=":material/bar_chart:",
            title="Chart Analysis",
            url_path="chart-analysis",
        ),
        st.Page(
            map_evo.render,
            icon=":material/history:",
            title="Map Evolution",
            url_path="map-evolution",
        ),
    ]

    # 2. Setup Headless Navigation
    current_page = st.navigation(pages, position="hidden")

    # 3. Custom Navbar UI
    # Using a container and horizontal dividers for a cleaner look
    with st.container():
        # Adjusting column widths to center the links if desired
        cols = st.columns([1, 2, 2, 2, 1])

        # Link 1
        cols[1].page_link(pages[0], use_container_width=True)
        # Link 2
        cols[2].page_link(pages[1], use_container_width=True)
        # Link 3
        cols[3].page_link(pages[2], use_container_width=True)

        st.divider()

    # 4. Execute the current page logic
    current_page.run()


if __name__ == "__main__":
    main()
