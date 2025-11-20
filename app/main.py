import streamlit as st
from app.single_asset import run_single_asset_module

st.set_page_config(layout="wide")

st.sidebar.title("Navigation")
choice = st.sidebar.radio("Select Module", ["Single Asset"])

if choice == "Single Asset":
    run_single_asset_module()
