import streamlit as st
import sys
from pathlib import Path

# Add both DXF-tools and DXF-viewer to the Python path
# Use absolute paths to ensure reliability
dxf_tools_path = Path("/Users/ryozo/Dropbox/Client/ULVAC/ElectricDesignManagement/Tools/DXF-tools")
dxf_viewer_path = Path("/Users/ryozo/Dropbox/Client/ULVAC/ElectricDesignManagement/Tools/DXF-viewer")

sys.path.insert(0, str(dxf_tools_path))
sys.path.insert(0, str(dxf_viewer_path))

# Import page modules
from pages import dxf_processor_main

st.set_page_config(
    page_title="DXF Processing Suite",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide sidebar
)

# Hide sidebar completely with CSS
st.markdown("""
<style>
    .css-1d391kg {
        display: none;
    }
    .css-1y4p8pa {
        padding-top: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 10rem;
    }
</style>
""", unsafe_allow_html=True)

# Run the main application
dxf_processor_main.app()