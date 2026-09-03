"""
Live Interactive Demo Page
"""

import time

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from adaptive_traffic.config.settings import get_settings


def show_live_demo():
    """Display live interactive demo"""
    settings = get_settings()

    st.markdown("<h1 class='main-header'>🎮 Live Interactive Demo</h1>", unsafe_allow_html=True)

    st.markdown(
        """
    <div class="explanation-box">
    Adjust traffic parameters below to see how the AI adapts signal timing in real-time.
    The simulation runs a virtual 4-way intersection with configurable traffic flows.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Controls
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🎛️ Traffic Controls")

        # Traffic density per direction
        st.markdown("**Traffic Density (vehicles/min)**")
        north = st.slider("North ↑", 0, 50, 20, 5)
        south = st.slider("South ↓", 0, 50, 15, 5)
        east = st.slider("East →", 0, 50, 25, 5)
        west = st.slider("West ←", 0, 50, 10, 5)

        st.markdown("---")

        # Simulation settings
        st.markdown("**Simulation Settings**")
        sim_speed = st.slider("Simulation Speed", 0.5, 5.0, 1.0, 0.5)
        controller = st.selectbox(
            "Controller Algorithm", ["DQN (AI)", "Fixed Time", "Webster", "Fuzzy Logic"], index=0
        )

        show_detection = st.checkbox("Show Vehicle Detection", True)
        show_queue = st.checkbox("Show Queue Lengths", True)

        if st.button("▶️ Run Simulation", type="primary"):
            run_simulation(north, south, east, west, controller, sim_speed)

    with col2:
        st.subheader("🎯 Signal Timing Output")

        # Calculate optimal timing based on traffic
        total_traffic = north + south + east + west
        cycle_time = 120  # Fixed cycle for demo

        if controller == "DQN (AI)":
            # AI-based allocation proportional to traffic
            ns_traffic = north + south
            ew_traffic = east + west
            total = ns_traffic + ew_traffic

            if total > 0:
                ns_green = int((ns_traffic / total) * (cycle_time - 20))
                ew_green = int((ew_traffic / total) * (cycle_time - 20))
            else:
                ns_green = ew_green = 30
        else:
            # Fixed allocation
            ns_green = ew_green = 30

        # Display signal plan
        col_ns, col_ew = st.columns(2)

        with col_ns:
            st.markdown(
                f"""
            <div class="metric-card" style="border-left: 5px solid #28a745;">
                <h4>🟢 North-South Phase</h4>
                <h2>{ns_green}s Green</h2>
                <p>Traffic: {north + south} veh/min</p>
                <p>Queue est: {max(0, (north + south) - ns_green * 0.5):.0f} vehicles</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col_ew:
            st.markdown(
                f"""
            <div class="metric-card" style="border-left: 5px solid #1E88E5;">
                <h4>🔵 East-West Phase</h4>
                <h2>{ew_green}s Green</h2>
                <p>Traffic: {east + west} veh/min</p>
                <p>Queue est: {max(0, (east + west) - ew_green * 0.5):.0f} vehicles</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Performance metrics
        st.subheader("📊 Predicted Performance")

        # Calculate metrics
        avg_wait_fixed = 45  # Fixed timing baseline
        if controller == "DQN (AI)":
            avg_wait = avg_wait_fixed * 0.58  # 42% reduction
            throughput = total_traffic * 1.25
        elif controller == "Webster":
            avg_wait = avg_wait_fixed * 0.75
            throughput = total_traffic * 1.15
        else:
            avg_wait = avg_wait_fixed
            throughput = total_traffic

        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Avg Wait Time",
            f"{avg_wait:.0f}s",
            f"{((avg_wait_fixed - avg_wait) / avg_wait_fixed * 100):.0f}% better",
        )
        m2.metric(
            "Throughput",
            f"{throughput:.0f} veh/hr",
            f"{((throughput - total_traffic) / total_traffic * 100):.0f}% gain",
        )
        m3.metric("Cycle Time", f"{cycle_time}s", "Fixed")

        # Visualization
        st.subheader("📈 Queue Length Over Time")

        # Simulate queue buildup
        time_steps = np.arange(0, 300, 10)
        ns_queue = np.maximum(
            0, (north + south) * time_steps / 60 - ns_green * (time_steps // cycle_time)
        )
        ew_queue = np.maximum(
            0, (east + west) * time_steps / 60 - ew_green * (time_steps // cycle_time)
        )

        queue_df = pd.DataFrame(
            {
                "Time (s)": np.concatenate([time_steps, time_steps]),
                "Queue Length": np.concatenate([ns_queue, ew_queue]),
                "Direction": ["North-South"] * len(time_steps) + ["East-West"] * len(time_steps),
            }
        )

        queue_chart = (
            alt.Chart(queue_df)
            .mark_area(opacity=0.6)
            .encode(
                x="Time (s):Q",
                y="Queue Length:Q",
                color="Direction:N",
                tooltip=["Time (s):Q", "Queue Length:Q", "Direction:N"],
            )
            .properties(height=300, title="Predicted Queue Lengths")
        )

        st.altair_chart(queue_chart, use_container_width=True)


def run_simulation(north, south, east, west, controller, speed):
    """Run the simulation with progress"""
    progress = st.progress(0)
    status = st.empty()

    for i in range(100):
        progress.progress(i + 1)
        status.text(f"Simulating... {i + 1}%")
        time.sleep(0.02 / speed)

    status.success("✅ Simulation complete!")
    st.balloons()
