"""
Main Streamlit Application Entry Point
Adaptive Traffic Signal Timer Dashboard
"""

import streamlit as st

from adaptive_traffic.config.settings import get_settings
from adaptive_traffic.ui.pages.advanced import show_advanced
from adaptive_traffic.ui.pages.comparison import show_comparison
from adaptive_traffic.ui.pages.dashboard import show_dashboard
from adaptive_traffic.ui.pages.live_demo import show_live_demo
from adaptive_traffic.ui.pages.metrics import show_metrics

# Import page modules
from adaptive_traffic.ui.pages.overview import show_overview

# Page configuration
st.set_page_config(
    page_title="Adaptive Traffic Signal Timer",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
.main-header {
    font-size: 2.5rem;
    color: #1E88E5;
    text-align: center;
    margin-bottom: 1rem;
}
.subheader {
    font-size: 1.5rem;
    color: #333;
    margin-bottom: 1rem;
}
.metric-card {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}
</style>
""",
    unsafe_allow_html=True,
)

# Initialize settings
settings = get_settings()

# Sidebar navigation
st.sidebar.title("🚦 Adaptive Traffic Signal")
st.sidebar.markdown(f"*v{settings.app_version}* - {settings.environment}")

page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 System Overview",
        "📊 Dashboard",
        "🎮 Live Demo",
        "📈 Algorithm Comparison",
        "🌍 Impact Metrics",
        "⚙️ Settings",
    ],
)

# Route to appropriate page
if page == "🏠 System Overview":
    show_overview()
elif page == "📊 Dashboard":
    show_dashboard()
elif page == "🎮 Live Demo":
    show_live_demo()
elif page == "📈 Algorithm Comparison":
    show_comparison()
elif page == "🌍 Impact Metrics":
    show_metrics()
elif page == "⚙️ Settings":
    show_advanced()

# Footer
st.markdown("---")
st.markdown(
    f"© 2024 {settings.app_name} | "
    f"Environment: {settings.environment} | "
    f"[Documentation](https://adaptive-traffic-signal.readthedocs.io)"
)
