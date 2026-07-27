import os
import threading
import time
import requests
import streamlit as st
import uvicorn

from server import app as fastapi_app


def run_fastapi():
    try:
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")
    except Exception:
        pass


if "fastapi_started" not in st.session_state:
    try:
        res = requests.get("http://127.0.0.1:8000/api/trending", timeout=0.6)
    except Exception:
        t = threading.Thread(target=run_fastapi, daemon=True)
        t.start()
        time.sleep(1.2)
    st.session_state.fastapi_started = True

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
    st.iframe("http://127.0.0.1:8000", height=980)
else:
    st.components.v1.iframe("http://127.0.0.1:8000", height=980, scrolling=True)
