import os
import requests
import streamlit as st

# Your deployed FastAPI backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "https://movie-recommender-3i6i.onrender.com")

st.set_page_config(
    page_title="CinematicAI — Universal Movie Platform",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header[data-testid="stHeader"] {display: none !important;}
    footer {display: none !important;}
    [data-testid="stSidebar"] {display: none !important;}
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    iframe {
        border: none !important;
        width: 100% !important;
        height: 100vh !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if hasattr(st, "iframe"):
    st.iframe(BACKEND_URL, height=980)
else:
    st.components.v1.iframe(BACKEND_URL, height=980, scrolling=True)
