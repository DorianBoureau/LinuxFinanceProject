import time
import streamlit as st
from quantA.single_asset import run_single_asset_module
from quantB.dashboard import run_quantB

# Page configuration
st.set_page_config(
    page_title="Financial Engineering Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------
# Auto-Refresh Logic (5 minutes)
# -------------------------------------------------------------------

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

current_time = time.time()

# Check if 300 seconds (5 min) have passed since the last reload
if current_time - st.session_state.last_refresh > 300:
    st.session_state.last_refresh = current_time
    st.rerun()

# -------------------------------------------------------------------
# Main Layout
# -------------------------------------------------------------------

st.title("Financial Engineering — Market Dashboard")

# Navigation Tabs
tab1, tab2 = st.tabs(["Quant A — Single Asset Analysis", "Quant B — Multi-Asset Portfolio"])

with tab1:
    run_single_asset_module()

with tab2:
    run_quantB()