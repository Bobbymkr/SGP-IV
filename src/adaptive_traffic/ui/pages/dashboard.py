"""
Dashboard Page - Real-time monitoring
"""

from datetime import datetime, timedelta

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from adaptive_traffic.config.settings import get_settings


def show_dashboard():
    """Display real-time dashboard"""
    settings = get_settings()

    st.markdown("<h1 class='main-header'>📊 Real-time Dashboard</h1>", unsafe_allow_html=True)

    # System status cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
        <div class="metric-card">
            <h3>🎥 Cameras</h3>
            <h2 style="color: #28a745;">12/12 Online</h2>
            <p>Uptime: 99.8%</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="metric-card">
            <h3>⚡ Processing</h3>
            <h2 style="color: #1E88E5;">Normal</h2>
            <p>CPU: 42% | Mem: 3.2/8 GB</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class="metric-card">
            <h3>🚦 Signals</h3>
            <h2 style="color: #28a745;">4/4 Active</h2>
            <p>Response: 120ms avg</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
        <div class="metric-card">
            <h3>🚗 Traffic</h3>
            <h2 style="color: #6f42c1;">342 veh/hr</h2>
            <p>Efficiency: 87%</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Tabs for different views
    tabs = st.tabs(["📈 Traffic Metrics", "🎯 Signal Status", "📊 Performance", "⚠️ Alerts"])

    with tabs[0]:
        show_traffic_metrics()

    with tabs[1]:
        show_signal_status()

    with tabs[2]:
        show_performance()

    with tabs[3]:
        show_alerts()


def show_traffic_metrics():
    """Traffic metrics view"""
    st.subheader("Real-time Traffic Volume")

    # Generate mock data for demonstration
    intersections = [
        "Main St & 5th Ave",
        "Broadway & Park Rd",
        "Central Ave & Oak St",
        "Highland & River Rd",
    ]
    current_volume = np.random.randint(150, 400, len(intersections))
    capacity = [400, 350, 300, 250]

    df = pd.DataFrame(
        {"Intersection": intersections, "Current Volume": current_volume, "Capacity": capacity}
    )
    df["Utilization (%)"] = (df["Current Volume"] / df["Capacity"] * 100).round(1)

    # Bar chart
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y("Intersection:N", sort="-x"),
            x=alt.X("Current Volume:Q", title="Vehicles per Hour"),
            color=alt.condition(
                'datum["Utilization (%)"] > 80',
                alt.value("#dc3545"),
                alt.condition(
                    'datum["Utilization (%)"] > 60', alt.value("#ffc107"), alt.value("#28a745")
                ),
            ),
            tooltip=["Intersection:N", "Current Volume:Q", "Capacity:Q", "Utilization (%):Q"],
        )
        .properties(title="Current Traffic Volume by Intersection", height=300)
    )

    # Add capacity reference lines
    capacity_lines = (
        alt.Chart(df)
        .mark_rule(color="red", strokeDash=[5, 5])
        .encode(y="Intersection:N", x="Capacity:Q")
    )

    st.altair_chart(chart + capacity_lines, use_container_width=True)

    # 24-hour pattern
    st.subheader("24-Hour Traffic Pattern")
    hours = list(range(24))
    pattern_data = pd.DataFrame(
        {
            "Hour": hours * len(intersections),
            "Intersection": sum([[i] * 24 for i in intersections], []),
            "Volume": np.concatenate(
                [
                    150
                    + 100 * np.sin((np.array(hours) - 8) * np.pi / 12)
                    + np.random.normal(0, 10, 24),
                    120
                    + 80 * np.sin((np.array(hours) - 9) * np.pi / 12)
                    + np.random.normal(0, 8, 24),
                    100
                    + 60 * np.sin((np.array(hours) - 7) * np.pi / 12)
                    + np.random.normal(0, 6, 24),
                    80
                    + 40 * np.sin((np.array(hours) - 10) * np.pi / 12)
                    + np.random.normal(0, 5, 24),
                ]
            ),
        }
    )

    pattern_chart = (
        alt.Chart(pattern_data)
        .mark_line()
        .encode(
            x=alt.X("Hour:Q", title="Hour of Day", scale=alt.Scale(domain=[0, 23])),
            y=alt.Y("Volume:Q", title="Vehicles per Hour"),
            color="Intersection:N",
            tooltip=["Hour:Q", "Volume:Q", "Intersection:N"],
        )
        .properties(title="24-hour Traffic Volume by Intersection", height=300)
    )

    st.altair_chart(pattern_chart, use_container_width=True)


def show_signal_status():
    """Signal status view"""
    st.subheader("Traffic Signal Status")

    signals = [
        {"id": 1, "direction": "North", "state": "🟢 Green", "timer": 23, "queue": 12},
        {"id": 2, "direction": "East", "state": "🔴 Red", "timer": 45, "queue": 8},
        {"id": 3, "direction": "South", "state": "🟢 Green", "timer": 18, "queue": 15},
        {"id": 4, "direction": "West", "state": "🟡 Yellow", "timer": 3, "queue": 5},
    ]

    cols = st.columns(4)
    for i, sig in enumerate(signals):
        with cols[i]:
            st.markdown(
                f"""
            <div class="metric-card">
                <h4>Signal {sig['id']} - {sig['direction']}</h4>
                <h2>{sig['state']}</h2>
                <p>Timer: {sig['timer']}s | Queue: {sig['queue']} vehicles</p>
            </div>
            """,
                unsafe_allow_html=True,
            )


def show_performance():
    """Performance analytics"""
    st.subheader("System Performance")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Avg Wait Time Reduction", "42%", "8%")
    with col2:
        st.metric("Fuel Savings", "12,450 gal", "5%")
    with col3:
        st.metric("CO₂ Reduction", "124 tons", "7%")
    with col4:
        st.metric("System Accuracy", "94.2%", "1.5%")

    # Before/After comparison
    st.subheader("Before vs After Implementation")

    metrics = ["Avg Wait Time (s)", "Flow Rate (veh/min)", "Congestion (min/day)", "Fuel (gal/day)"]
    before = [78, 12, 124, 1450]
    after = [45, 18, 52, 1120]

    comp_df = pd.DataFrame(
        {
            "Metric": metrics + metrics,
            "Value": before + after,
            "System": ["Before"] * 4 + ["After"] * 4,
        }
    )

    comp_chart = (
        alt.Chart(comp_df)
        .mark_bar()
        .encode(
            x="System:N",
            y="Value:Q",
            color=alt.Color(
                "System:N",
                scale=alt.Scale(domain=["Before", "After"], range=["#dc3545", "#28a745"]),
            ),
            column="Metric:N",
            tooltip=["Metric:N", "Value:Q", "System:N"],
        )
        .properties(width=120, height=250)
    )

    st.altair_chart(comp_chart, use_container_width=True)

    # Efficiency trend
    st.subheader("Efficiency Trend (90 days)")
    dates = pd.date_range(start=datetime.now() - timedelta(days=90), periods=90, freq="D")
    base_eff = 75
    improvement = np.minimum(15 * (1 - np.exp(-np.arange(90) / 30)), 15)
    noise = np.random.normal(0, 1.5, 90)
    efficiency = base_eff + improvement + noise

    eff_df = pd.DataFrame({"Date": dates, "Efficiency (%)": efficiency})

    eff_chart = (
        alt.Chart(eff_df)
        .mark_line(point=True)
        .encode(
            x="Date:T",
            y=alt.Y("Efficiency (%):Q", scale=alt.Scale(domain=[70, 100])),
            tooltip=["Date:T", "Efficiency (%):Q"],
        )
        .properties(title="System Efficiency Trend", height=300)
    )

    st.altair_chart(eff_chart, use_container_width=True)


def show_alerts():
    """Alerts and notifications"""
    st.subheader("System Alerts")

    alerts = [
        {
            "time": "08:32",
            "type": "🚦 Traffic",
            "severity": "High",
            "msg": "Unusual congestion at Main St & 5th Ave",
            "status": "Active",
        },
        {
            "time": "07:45",
            "type": "💻 System",
            "severity": "Medium",
            "msg": "Camera #3 intermittent connectivity",
            "status": "Active",
        },
        {
            "time": "23:12",
            "type": "🔧 Maintenance",
            "severity": "Low",
            "msg": "Scheduled update completed",
            "status": "Resolved",
        },
        {
            "time": "17:30",
            "type": "🔒 Security",
            "severity": "Critical",
            "msg": "Unauthorized access attempt",
            "status": "Resolved",
        },
    ]

    for alert in alerts:
        severity_color = {
            "Critical": "#dc3545",
            "High": "#fd7e14",
            "Medium": "#ffc107",
            "Low": "#6c757d",
        }[alert["severity"]]
        status_badge = "🔴 Active" if alert["status"] == "Active" else "🟢 Resolved"

        st.markdown(
            f"""
        <div style="border-left: 5px solid {severity_color}; padding: 10px; margin: 10px 0; background: #f8f9fa; border-radius: 4px;">
            <div style="display: flex; justify-content: space-between;">
                <strong>{alert['type']} - {alert['severity']}</strong>
                <span>{status_badge}</span>
            </div>
            <p style="margin: 5px 0;">{alert['msg']}</p>
            <small style="color: #6c757d;">{alert['time']}</small>
        </div>
        """,
            unsafe_allow_html=True,
        )
