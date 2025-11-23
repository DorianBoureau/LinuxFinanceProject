import streamlit as st
from single_asset import run_single_asset_module
from quantB.dashboard import run_quantB

st.set_page_config(layout="wide")

tab1, tab2 = st.tabs(["Quant A — Single Asset", "Quant B — Portfolio"])

with tab1:
    run_single_asset_module()

with tab2:
    run_quantB()
