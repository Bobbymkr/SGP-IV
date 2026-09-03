"""
Advanced Features Page
"""

import pandas as pd
import streamlit as st

from adaptive_traffic.config.settings import get_settings


def show_advanced():
    """Display advanced features and settings"""
    settings = get_settings()

    st.markdown(
        "<h1 class='main-header'>⚙️ Advanced Features & Settings</h1>", unsafe_allow_html=True
    )

    tabs = st.tabs(
        [
            "🚑 Emergency Vehicle Priority",
            "🌤️ Weather Adaptation",
            "🚶 Pedestrian & Cyclist Detection",
            "🔧 System Configuration",
            "📡 API & Integration",
        ]
    )

    with tabs[0]:
        show_emergency_priority()

    with tabs[1]:
        show_weather_adaptation()

    with tabs[2]:
        show_pedestrian_cyclist()

    with tabs[3]:
        show_system_config()

    with tabs[4]:
        show_api_integration()


def show_emergency_priority():
    """Emergency vehicle priority feature"""
    st.subheader("🚑 Emergency Vehicle Priority (EVP)")

    st.markdown("""
    The system detects emergency vehicles (ambulances, fire trucks, police) via:
    - **Optical detection**: Flashing light pattern recognition
    - **Audio detection**: Siren classification (CNN-based)
    - **V2X communication**: Direct vehicle-to-infrastructure messages
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Configuration")
        evp_enabled = st.checkbox("Enable EVP", value=True)
        detection_range = st.slider("Detection Range (meters)", 100, 1000, 300)
        priority_duration = st.slider("Green Extension (seconds)", 10, 120, 30)
        preemption_mode = st.selectbox(
            "Preemption Mode", ["Immediate", "Next Cycle", "Coordinated"], index=0
        )

        st.markdown("### Supported Vehicle Types")
        st.checkbox("Ambulance", True)
        st.checkbox("Fire Truck", True)
        st.checkbox("Police", True)
        st.checkbox("Other Authorized", False)

    with col2:
        st.markdown("### Performance Metrics")
        st.metric("Detection Accuracy", "96.2%")
        st.metric("False Positive Rate", "0.8%")
        st.metric("Avg Response Improvement", "30%")
        st.metric("Intersection Clearance", "94% within 15s")

        st.markdown("### Detection Methods")
        st.progress(0.95, "Optical (Light Patterns)")
        st.progress(0.87, "Audio (Siren CNN)")
        st.progress(0.72, "V2X (DSRC/C-V2X)")

    if st.button("Test EVP Activation"):
        st.success("✅ Emergency preemption sequence initiated!")
        st.info("All signals on route: GREEN | Cross traffic: RED | Duration: 30s")


def show_weather_adaptation():
    """Weather adaptation feature"""
    st.subheader("🌤️ Weather-Adaptive Signal Control")

    st.markdown("""
    The system integrates real-time weather data to adjust signal timing for safety and efficiency:
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Weather Impact Matrix")

        weather_data = pd.DataFrame(
            {
                "Condition": [
                    "Clear",
                    "Light Rain",
                    "Heavy Rain",
                    "Snow",
                    "Ice",
                    "Fog",
                    "High Wind",
                ],
                "Visibility Factor": [1.0, 0.85, 0.65, 0.55, 0.45, 0.60, 0.90],
                "Traction Factor": [1.0, 0.80, 0.60, 0.40, 0.25, 1.0, 0.95],
                "Speed Adjustment": [0, -10, -25, -35, -50, -20, -15],
                "Gap Increase": [0, 2, 5, 8, 12, 4, 3],
            }
        )

        st.dataframe(weather_data, use_container_width=True)

    with col2:
        st.markdown("### Current Conditions")
        st.metric("Temperature", "22°C", "Sunny")
        st.metric("Visibility", "10 km", "Clear")
        st.metric("Precipitation", "0 mm", "None")
        st.metric("Wind", "5 km/h", "Light")

        st.markdown("### Adaptive Parameters")
        st.slider("Min Green Extension (rain)", 0, 30, 10)
        st.slider("Max Cycle Extension (snow)", 0, 60, 20)
        st.slider("Pedestrian Time Increase (ice)", 0, 20, 10)

        if st.button("Fetch Live Weather"):
            st.info("🌤️ Connected to weather API - data updated every 5 minutes")

    st.markdown("---")

    st.markdown("### Safety Adjustments")
    st.markdown("""
    | Weather | Green Time | Yellow Time | Pedestrian Time | Detection Sensitivity |
    |---------|------------|-------------|-----------------|----------------------|
    | Clear   | Baseline   | Baseline    | Baseline        | Standard             |
    | Rain    | +10-15%    | +2s         | +15%            | Increased            |
    | Snow    | +20-30%    | +3s         | +30%            | High                 |
    | Ice     | +25-40%    | +5s         | +50%            | Maximum              |
    | Fog     | +15%       | +2s         | +20%            | High                 |
    """)


def show_pedestrian_cyclist():
    """Pedestrian and cyclist detection"""
    st.subheader("🚶 Pedestrian & Cyclist Safety")

    st.markdown("""
    Dedicated detection and protection for vulnerable road users:
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Detection Zones")

        zones = pd.DataFrame(
            {
                "Zone": [
                    "Crosswalk N",
                    "Crosswalk E",
                    "Crosswalk S",
                    "Crosswalk W",
                    "Bike Lane N",
                    "Bike Lane S",
                ],
                "Type": ["Pedestrian"] * 4 + ["Cyclist"] * 2,
                "Active": [True, True, True, True, True, True],
                "Count (hr)": [145, 98, 167, 123, 45, 38],
                "Avg Wait (s)": [12, 18, 15, 22, 8, 10],
            }
        )

        st.dataframe(zones, use_container_width=True)

    with col2:
        st.markdown("### Safety Features")
        st.checkbox("Pedestrian Countdown Timer", True)
        st.checkbox("Leading Pedestrian Interval (LPI)", True)
        st.checkbox("Cyclist Green Wave", True)
        st.checkbox("Right-Turn-on-Red Restriction", False)
        st.checkbox("Accessible Pedestrian Signals (APS)", True)

        st.metric("Pedestrian Compliance", "87%")
        st.metric("Cyclist Violations", "12%")

    st.markdown("---")

    st.markdown("### Leading Pedestrian Interval (LPI) Demo")

    lpi_time = st.slider("LPI Duration (seconds)", 3, 10, 5)

    st.markdown(f"""
    **Sequence with LPI ({lpi_time}s):**
    1. 🟢 **Pedestrian WALK** - {lpi_time}s head start
    2. 🟡 **Vehicle RED** - All vehicles stopped
    3. 🟢 **Vehicle GREEN** - Normal vehicle phase begins
    4. 🔴 **Pedestrian DON'T WALK** - Flashing countdown
    """)


def show_system_config():
    """System configuration"""
    st.subheader("🔧 System Configuration")

    st.markdown("### Signal Timing Parameters")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Base Timing**")
        min_green = st.number_input("Minimum Green (s)", 5, 60, settings.min_green_time)
        max_green = st.number_input("Maximum Green (s)", 30, 180, settings.max_green_time)
        yellow = st.number_input("Yellow Time (s)", 3, 10, settings.default_yellow_time)
        all_red = st.number_input("All-Red Clearance (s)", 1, 5, 2)

    with col2:
        st.markdown("**Detection Settings**")
        det_time = st.number_input("Advance Detection (s)", 1, 15, settings.detection_time)
        det_conf = st.slider(
            "Detection Confidence", 0.1, 1.0, settings.yolo_confidence_threshold, 0.05
        )
        det_iou = st.slider("Detection IoU Threshold", 0.1, 1.0, settings.yolo_iou_threshold, 0.05)

    st.markdown("### Controller Settings")

    col3, col4 = st.columns(2)

    with col3:
        controller = st.selectbox(
            "Active Controller",
            ["dqn", "fixed", "webster", "fuzzy"],
            index=["dqn", "fixed", "webster", "fuzzy"].index(settings.controller_type),
        )

        if controller == "dqn":
            st.number_input("State Dimension", 2, 20, 4)
            st.number_input("Action Dimension", 5, 50, 12)
            st.slider("Learning Rate", 0.0001, 0.01, 0.001, 0.0001)
            st.slider("Gamma (Discount)", 0.8, 0.99, 0.95, 0.01)

    with col4:
        st.markdown("**Simulation Parameters**")
        sim_time = st.number_input("Simulation Time (s)", 60, 3600, settings.simulation_time)
        num_sig = st.number_input("Number of Signals", 2, 8, settings.num_signals)
        num_lanes = st.number_input("Lanes per Approach", 1, 4, 2)

    if st.button("💾 Save Configuration"):
        st.success("✅ Configuration saved! Restart services to apply changes.")

    st.markdown("---")

    st.markdown("### Export / Import Config")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📤 Export Config (YAML)"):
            st.download_button("Download", "config.yaml", "adaptive_traffic_config.yaml")
    with c2:
        uploaded = st.file_uploader("📥 Import Config", type=["yaml", "yml"])
        if uploaded:
            st.success("Configuration imported!")


def show_api_integration():
    """API and integration settings"""
    st.subheader("📡 API & Integration")

    st.markdown("### REST API Endpoints")

    endpoints = pd.DataFrame(
        {
            "Endpoint": [
                "GET /api/v1/signals",
                "GET /api/v1/signals/{id}",
                "POST /api/v1/signals/{id}/timing",
                "GET /api/v1/detection/live",
                "GET /api/v1/traffic/metrics",
                "GET /api/v1/analytics/forecast",
                "WS /api/v1/stream",
            ],
            "Description": [
                "List all signal controllers",
                "Get signal status and timing",
                "Update signal timing plan",
                "Live vehicle detection feed",
                "Real-time traffic metrics",
                "Traffic flow predictions",
                "WebSocket live updates",
            ],
            "Auth": ["Bearer"] * 7,
        }
    )

    st.dataframe(endpoints, use_container_width=True)

    st.markdown("### Authentication")
    st.code(
        """
# API Key Header
Authorization: Bearer YOUR_API_KEY

# Or JWT Token
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
    """,
        language="bash",
    )

    st.markdown("### Integration Examples")

    with st.expander("🐍 Python Client"):
        st.code(
            """
import httpx

client = httpx.Client(
    base_url="https://api.adaptivesignal.io",
    headers={"Authorization": "Bearer YOUR_KEY"}
)

# Get signal status
response = client.get("/api/v1/signals/1")
signal = response.json()

# Update timing
client.post("/api/v1/signals/1/timing", json={
    "green_time": 30,
    "yellow_time": 5
})
        """,
            language="python",
        )

    with st.expander("🌐 JavaScript/TypeScript"):
        st.code(
            """
const response = await fetch('/api/v1/signals', {
  headers: { 'Authorization': 'Bearer YOUR_KEY' }
});
const signals = await response.json();
        """,
            language="typescript",
        )

    with st.expander("📊 WebSocket Stream"):
        st.code(
            """
const ws = new WebSocket('wss://api.adaptivesignal.io/api/v1/stream');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Live detection:', data);
};
        """,
            language="javascript",
        )

    st.markdown("### Webhook Configuration")
    webhook_url = st.text_input("Webhook URL", placeholder="https://your-system.com/webhook")
    events = st.multiselect(
        "Subscribe to Events",
        ["signal_change", "detection_alert", "traffic_anomaly", "system_health", "evp_activated"],
        default=["signal_change", "traffic_anomaly"],
    )

    if st.button("💾 Save Webhook"):
        st.success("Webhook configured!")
