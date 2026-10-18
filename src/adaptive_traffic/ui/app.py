"""
Main Streamlit Application Entry Point
Adaptive Traffic Signal Timer Dashboard
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src layout, any launcher/cwd

import streamlit as st

from adaptive_traffic.config.city_profiles import list_city_profiles
from adaptive_traffic.config.settings import get_settings
from adaptive_traffic.ui._facts import get_model_facts
from adaptive_traffic.ui.theme import ACCENT, BASE_CSS, svg
from adaptive_traffic.ui.views.advanced import show_advanced
from adaptive_traffic.ui.views.comparison import show_comparison
from adaptive_traffic.ui.views.dashboard import show_dashboard
from adaptive_traffic.ui.views.live_demo import show_live_demo
from adaptive_traffic.ui.views.metrics import show_metrics

# Import page modules
from adaptive_traffic.ui.views.overview import show_overview

# Page configuration (theme colours live in .streamlit/config.toml)
st.set_page_config(
    page_title="Adaptive Traffic Signal Timer",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="auto",  # collapses on narrow screens, open on desktop
)

# Shared design system (single palette, cards, icons)
st.markdown(BASE_CSS, unsafe_allow_html=True)

# Initialize settings
settings = get_settings()

# Sidebar navigation
st.sidebar.markdown(
    f"## {svg('signal', 22, ACCENT)} Adaptive Traffic Signal",
    unsafe_allow_html=True,
)
st.sidebar.markdown(f"*v{settings.app_version}* - {settings.environment}")

cities = list_city_profiles()
st.sidebar.selectbox(
    "City (tuning file, no code change)",
    cities,
    index=cities.index("mumbai") if "mumbai" in cities else 0,
    key="city",
)

_model = get_model_facts()
st.sidebar.markdown(
    f"<div class='model-badge'>Eye: {_model['name']}<br>"
    f"{_model['overall'] * 100:.1f}% mAP50 · fp32 · {_model['speed_short']}</div>",
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "Navigate",
    [
        "System Overview",
        "Dashboard",
        "Live Demo",
        "Algorithm Comparison",
        "Impact Metrics",
        "Settings",
    ],
)

# Route to appropriate page
if page == "System Overview":
    show_overview()
elif page == "Dashboard":
    show_dashboard()
elif page == "Live Demo":
    show_live_demo()
elif page == "Algorithm Comparison":
    show_comparison()
elif page == "Impact Metrics":
    show_metrics()
elif page == "Settings":
    show_advanced()

# Footer
st.markdown("---")
st.markdown(
    f"© 2026 {settings.app_name} | "
    f"Environment: {settings.environment} | "
    f"[Docs](https://github.com/Bobbymkr/SGP-IV/tree/main/docs) | "
    f"[Proof pack](https://github.com/Bobbymkr/SGP-IV/tree/main/sgp-ppt-handoff)"
)
