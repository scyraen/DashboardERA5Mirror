import streamlit as st
from modules.gee_interface import initialize_gee, test_connection

st.title("ERA 5 Weather Dashboard")

# Initialize GEE
if initialize_gee():
    st.success("GEE API Initialized")

    # Run the test
    with st.spinner("Testing connection..."):
        result = test_connection()
        st.write(result)
else:
    st.error("Could not connect to Google Earth Engine.")

st.write("---")
st.write("Works!")
