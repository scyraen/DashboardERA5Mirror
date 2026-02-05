import streamlit as st

from src.modules.gee_interface import initialize_gee
from src.modules.views import charts, info, map_comp, map_evo


def main():
    st.set_page_config(layout="wide", page_title="ERA5 Explorer")
    initialize_gee()

    pages = [
        st.Page(map_comp.render, icon=":material/compare:", title="Map Comparison", url_path="map-comparison"),
        st.Page(charts.render, icon=":material/bar_chart:", title="Dashboard Levels", url_path="dashboard-levels"),
        st.Page(map_evo.render, icon=":material/history:", title="Map Evolution", url_path="map-evolution"),
        st.Page(info.render, icon=":material/info:", title="Info", url_path="info"),
    ]

    current_page = st.navigation(pages, position="hidden")

    with st.container():
        cols = st.columns([1, 1, 1, 1, 1, 1])
        cols[1].page_link(pages[0], use_container_width=True)
        cols[2].page_link(pages[1], use_container_width=True)
        cols[3].page_link(pages[2], use_container_width=True)
        cols[4].page_link(pages[3], use_container_width=True)
        st.divider()

    current_page.run()


if __name__ == "__main__":
    main()
