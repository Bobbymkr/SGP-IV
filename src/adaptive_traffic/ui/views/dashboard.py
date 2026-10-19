"""
Dashboard Page - Real-time monitoring
"""

from datetime import datetime, timedelta

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from adaptive_traffic.ui._facts import get_eval_facts, get_model_facts
from adaptive_traffic.ui.theme import (
    ACCENT,
    BAD,
    INK,
    MUTED,
    OK,
    WARN,
    banner,
    card,
    heading,
    svg,
    tagline,
)


def show_dashboard():
    """Display real-time dashboard"""
    st.markdown(
        f"<h1 class='main-header'>{svg('gauge', 34, ACCENT)} Simulated City Dashboard</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        banner(
            "This page runs a simulated city: the status cards, traffic volumes, signal "
            "states and alerts are illustrations. The Performance tab carries measured "
            "results; the full proof is on the Comparison page."
        ),
        unsafe_allow_html=True,
    )

    # System status cards (illustration values — measured proof is on Comparison)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            card("Cameras", "12/12 Online", "uptime 99.8%", ACCENT, "camera"),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            card("Processing", "Normal", "CPU 42%", ACCENT, "cpu"),
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            card("Signals", "4/4 Active", "120ms avg", OK, "signal"),
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            card("Traffic", "342 veh/hr", "efficiency 87%", ACCENT, "car"),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Tabs for different views
    tabs = st.tabs(["Traffic Metrics", "Signal Status", "Performance", "Alerts"])

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
    st.markdown(heading("car", "Real-time Traffic Volume"), unsafe_allow_html=True)
    st.markdown(
        tagline("ILLUSTRATION", "Simulated traffic for the selected city. No live camera feed."),
        unsafe_allow_html=True,
    )

    city = st.session_state.get("city", "mumbai").title()
    dirs = ["North", "East", "South", "West"]
    intersections = [f"{city} J{i} {d}" for i, d in enumerate(dirs, 1)]
    rng = np.random.default_rng(42)  # stable across reruns so states stay comparable
    current_volume = rng.integers(150, 400, len(intersections))
    capacity = [400, 350, 300, 250]

    df = pd.DataFrame(
        {"Intersection": intersections, "Current Volume": current_volume, "Capacity": capacity}
    )
    df["Utilization (%)"] = (df["Current Volume"] / df["Capacity"] * 100).round(1)
    df["Color"] = df["Utilization (%)"].apply(
        lambda u: BAD if u > 80 else (WARN if u > 60 else OK)
    )

    # Bar chart
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y("Intersection:N", sort="-x"),
            x=alt.X("Current Volume:Q", title="Vehicles per Hour"),
            color=alt.Color(
                "Color:N",
                scale=alt.Scale(domain=[BAD, WARN, OK], range=[BAD, WARN, OK]),
                legend=None,
            ),
            tooltip=["Intersection:N", "Current Volume:Q", "Capacity:Q", "Utilization (%):Q"],
        )
        .properties(title="Current Traffic Volume by Intersection", height=300)
    )

    # Add capacity reference lines
    capacity_lines = (
        alt.Chart(df)
        .mark_rule(color=BAD, strokeDash=[5, 5])
        .encode(y="Intersection:N", x="Capacity:Q")
    )

    st.altair_chart(chart + capacity_lines, use_container_width=True)
    st.caption(
        "Colour: green = under 60% of capacity, amber = 60-80%, red = over 80%. "
        "Dashed line = capacity."
    )

    # 24-hour pattern
    st.markdown(heading("pulse", "24-Hour Traffic Pattern"), unsafe_allow_html=True)
    hours = list(range(24))
    pattern_data = pd.DataFrame(
        {
            "Hour": hours * len(intersections),
            "Intersection": sum([[i] * 24 for i in intersections], []),
            "Volume": np.concatenate(
                [
                    150
                    + 100 * np.sin((np.array(hours) - 8) * np.pi / 12)
                    + rng.normal(0, 10, 24),
                    120
                    + 80 * np.sin((np.array(hours) - 9) * np.pi / 12)
                    + rng.normal(0, 8, 24),
                    100
                    + 60 * np.sin((np.array(hours) - 7) * np.pi / 12)
                    + rng.normal(0, 6, 24),
                    80
                    + 40 * np.sin((np.array(hours) - 10) * np.pi / 12)
                    + rng.normal(0, 5, 24),
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
    st.markdown(heading("signal", "Traffic Signal Status"), unsafe_allow_html=True)
    st.markdown(
        tagline("ILLUSTRATION", "Sample signal states from the simulated city."),
        unsafe_allow_html=True,
    )

    signals = [
        {"id": 1, "direction": "North", "state": "Green", "tone": OK, "timer": 23, "queue": 12},
        {"id": 2, "direction": "East", "state": "Red", "tone": BAD, "timer": 45, "queue": 8},
        {"id": 3, "direction": "South", "state": "Green", "tone": OK, "timer": 18, "queue": 15},
        {"id": 4, "direction": "West", "state": "Yellow", "tone": WARN, "timer": 3, "queue": 5},
    ]

    cols = st.columns(4)
    for i, sig in enumerate(signals):
        with cols[i]:
            st.markdown(
                f"""
            <div class="metric-card">
                <div style="font-size:.8rem;font-weight:600;color:{MUTED}">
                    Signal {sig['id']} - {sig['direction']}
                </div>
                <div style="font-size:1.4rem;font-weight:700;color:{INK}">
                    <span style="display:inline-block;width:9px;height:9px;border-radius:50%;
                        background:{sig['tone']};margin-right:.4rem"></span>{sig['state']}
                </div>
                <div style="font-size:.82rem;color:{MUTED}">
                    Timer: {sig['timer']}s | Queue: {sig['queue']} vehicles
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def show_performance():
    """Performance analytics — measured results first, illustrations labelled"""
    st.markdown(heading("gauge", "System Performance"), unsafe_allow_html=True)

    model = get_model_facts()
    ev = get_eval_facts()
    st.markdown(
        tagline("MEASURED", "Measured on the official 10k photo test and the eval matrix."),
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            card("Wait time cut", ev["wait_band"], "vs fixed timing (eval)", OK, "gauge"),
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            card(
                "Detection mAP50",
                f"{model['overall'] * 100:.1f}%",
                "10k photo test",
                ACCENT,
                "camera",
            ),
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            card("Decide p95", ev["dec95"], "budget 10 ms", ACCENT, "cpu"),
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            card("CPU speed", model["speed_short"], "fp32 bench", ACCENT, "pulse"),
            unsafe_allow_html=True,
        )

    # Before/After comparison
    st.markdown(heading("gauge", "Before vs After Implementation"), unsafe_allow_html=True)
    st.markdown(
        tagline("ILLUSTRATION", "Modelled before/after for one intersection. Not measured."),
        unsafe_allow_html=True,
    )

    metrics = ["Avg Wait Time (s)", "Flow Rate (veh/min)", "Congestion (min/day)", "Fuel (L/day)"]
    before = [78, 12, 124, 5489]
    after = [45, 18, 52, 4240]
    index_after = [round(a / b * 100) for a, b in zip(after, before)]

    comp_df = pd.DataFrame(
        {
            "Metric": metrics * 2,
            "Index": [100] * 4 + index_after,
            "Actual": before + after,
            "System": ["Before"] * 4 + ["After"] * 4,
        }
    )

    comp_chart = (
        alt.Chart(comp_df)
        .mark_bar()
        .encode(
            x=alt.X("Metric:N", title=None, sort=metrics),
            y=alt.Y("Index:Q", title="Index (before = 100)"),
            color=alt.Color(
                "System:N",
                scale=alt.Scale(domain=["Before", "After"], range=[BAD, OK]),
            ),
            xOffset=alt.XOffset("System:N"),  # grouped, not stacked
            tooltip=[
                "Metric:N",
                "System:N",
                alt.Tooltip("Actual:Q", format=",.0f"),
                alt.Tooltip("Index:Q"),
            ],
        )
        .properties(height=280)
    )

    st.altair_chart(comp_chart, use_container_width=True)

    # Efficiency trend
    st.markdown(heading("pulse", "Efficiency Trend (90 days)"), unsafe_allow_html=True)
    st.markdown(
        tagline("ILLUSTRATION", "Modelled trend for a city that rolled the system out."),
        unsafe_allow_html=True,
    )
    dates = pd.date_range(start=datetime.now() - timedelta(days=90), periods=90, freq="D")
    base_eff = 75
    improvement = np.minimum(15 * (1 - np.exp(-np.arange(90) / 30)), 15)
    noise = np.random.default_rng(7).normal(0, 1.5, 90)
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
    st.markdown(heading("signal", "System Alerts"), unsafe_allow_html=True)
    st.markdown(
        tagline("ILLUSTRATION", "Sample alerts. This build has no field-event feed yet."),
        unsafe_allow_html=True,
    )

    city = st.session_state.get("city", "mumbai").title()
    alerts = [
        {
            "time": "08:32",
            "type": "Traffic",
            "severity": "High",
            "msg": f"Unusual congestion at {city} J1 North",
            "status": "Active",
        },
        {
            "time": "07:45",
            "type": "System",
            "severity": "Medium",
            "msg": "Camera #3 intermittent connectivity",
            "status": "Active",
        },
        {
            "time": "23:12",
            "type": "Maintenance",
            "severity": "Low",
            "msg": "Scheduled update completed",
            "status": "Resolved",
        },
        {
            "time": "17:30",
            "type": "Security",
            "severity": "Critical",
            "msg": "Unauthorized access attempt",
            "status": "Resolved",
        },
    ]

    for alert in alerts:
        severity_color = {
            "Critical": "#dc2626",
            "High": "#d97706",
            "Medium": "#b45309",
            "Low": "#64748b",
        }[alert["severity"]]
        status_color = "#dc2626" if alert["status"] == "Active" else "#16a34a"
        dot = (
            "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
            f"background:{severity_color};margin-right:.4rem'></span>"
        )
        status_dot = (
            "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
            f"background:{status_color};margin-right:.3rem'></span>"
        )

        st.markdown(
            f"""
        <div style="border:1px solid #e2e8f0; padding:10px; margin:10px 0; background:#ffffff;
            border-radius:8px;">
            <div style="display: flex; justify-content: space-between; align-items:center;">
                <strong>{dot}{alert['type']} - {alert['severity']}</strong>
                <span>{status_dot}{alert['status']}</span>
            </div>
            <p style="margin: 5px 0;">{alert['msg']}</p>
            <small style="color:#475569;">{alert['time']}</small>
        </div>
        """,
            unsafe_allow_html=True,
        )
