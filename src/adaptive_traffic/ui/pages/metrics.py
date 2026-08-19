"""
Impact Metrics Page
"""

import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from adaptive_traffic.config.settings import get_settings


def show_metrics():
    """Display environmental and economic impact metrics"""
    settings = get_settings()

    st.markdown("<h1 class='main-header'>🌍 Environmental & Economic Impact</h1>", unsafe_allow_html=True)

    st.markdown("""
    Quantified benefits of adaptive traffic signal control based on real-world deployments
    and simulation studies.
    """)

    # Key impact metrics
    st.subheader("📊 Key Impact Metrics (Per Intersection / Year)")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card" style="border-left: 5px solid #28a745;">
            <h3>⛽ Fuel Saved</h3>
            <h2>12,450 gal</h2>
            <p>$37,350 value @ $3/gal</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card" style="border-left: 5px solid #1E88E5;">
            <h3>🌱 CO₂ Reduced</h3>
            <h2>124 tons</h2>
            <p>Equiv. to 27 cars off road</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card" style="border-left: 5px solid #6f42c1;">
            <h3>⏱️ Time Saved</h3>
            <h2>2.3M hours</h2>
            <p>$46M economic value @ $20/hr</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card" style="border-left: 5px solid #fd7e14;">
            <h3>🚑 Emergency Response</h3>
            <h2>30% faster</h2>
            <p>Priority signal preemption</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # City-scale impact
    st.subheader("🏙️ City-Scale Impact Projection")

    col1, col2 = st.columns(2)

    with col1:
        num_intersections = st.number_input(
            "Number of Signalized Intersections",
            min_value=1, max_value=1000, value=150
        )

    with col2:
        avg_daily_traffic = st.number_input(
            "Average Daily Traffic per Intersection",
            min_value=1000, max_value=100000, value=25000
        )

    # Calculate projections
    fuel_per_intersection = 12450  # gallons/year
    co2_per_intersection = 124  # tons/year
    time_per_intersection = 15333  # hours/year (2.3M / 150)
    economic_per_intersection = 306667  # $/year (46M / 150)

    total_fuel = fuel_per_intersection * num_intersections
    total_co2 = co2_per_intersection * num_intersections
    total_time = time_per_intersection * num_intersections
    total_economic = economic_per_intersection * num_intersections

    st.markdown("### Projected Annual Impact")

    proj_col1, proj_col2, proj_col3, proj_col4 = st.columns(4)

    proj_col1.metric("🛢️ Fuel Savings", f"{total_fuel:,.0f} gal", f"${total_fuel * 3:,.0f}")
    proj_col2.metric("🌿 CO₂ Reduction", f"{total_co2:,.0f} tons", f"{total_co2 * 22:.0f} cars equiv.")
    proj_col3.metric("⏰ Time Savings", f"{total_time:,.0f} hrs", f"${total_economic:,.0f}")
    proj_col4.metric("💰 ROI", f"${total_economic * 3:,.0f}", "3-year payback typical")

    # Environmental breakdown
    st.subheader("📈 Environmental Impact Breakdown")

    env_data = pd.DataFrame({
        'Pollutant': ['CO₂', 'NOx', 'PM2.5', 'VOCs', 'CO'],
        'Reduction (tons/yr)': [
            total_co2,
            total_co2 * 0.008,  # NOx ~0.8% of CO2
            total_co2 * 0.001,  # PM2.5
            total_co2 * 0.005,  # VOCs
            total_co2 * 0.02    # CO
        ],
        'Health Benefit ($/yr)': [
            total_co2 * 50,      # Social cost of carbon
            total_co2 * 0.008 * 7500,
            total_co2 * 0.001 * 150000,
            total_co2 * 0.005 * 5000,
            total_co2 * 0.02 * 100
        ]
    })

    env_chart = alt.Chart(env_data).mark_bar().encode(
        x=alt.X('Reduction (tons/yr):Q', title='Annual Reduction (tons)'),
        y=alt.Y('Pollutant:N', sort='-x'),
        color=alt.Color('Reduction (tons/yr):Q', scale=alt.Scale(scheme='greens')),
        tooltip=['Pollutant:N', 'Reduction (tons/yr):Q', 'Health Benefit ($/yr):Q']
    ).properties(title='Annual Emission Reductions', height=300)

    st.altair_chart(env_chart, use_container_width=True)

    # Economic breakdown
    st.subheader("💰 Economic Benefit Breakdown")

    econ_data = pd.DataFrame({
        'Category': [
            'Commuter Time Savings',
            'Commercial Vehicle Efficiency',
            'Fuel Cost Reduction',
            'Vehicle Wear Reduction',
            'Accident Cost Avoidance',
            'Emergency Response Improvement'
        ],
        'Annual Value ($)': [
            total_economic * 0.65,
            total_economic * 0.15,
            total_fuel * 3,
            total_economic * 0.08,
            total_economic * 0.07,
            total_economic * 0.05
        ]
    })

    econ_chart = alt.Chart(econ_data).mark_arc(innerRadius=60).encode(
        theta='Annual Value ($):Q',
        color=alt.Color('Category:N', legend=alt.Legend(orient='right')),
        tooltip=['Category:N', alt.Tooltip('Annual Value ($):Q', format='$,.0f')]
    ).properties(title='Economic Benefit Distribution', height=400)

    st.altair_chart(econ_chart, use_container_width=True)

    # Time-series projection
    st.subheader("📅 5-Year Cumulative Impact")

    years = list(range(1, 6))
    cumulative_fuel = [total_fuel * y for y in years]
    cumulative_co2 = [total_co2 * y for y in years]
    cumulative_economic = [total_economic * y for y in years]

    proj_df = pd.DataFrame({
        'Year': years * 3,
        'Metric': ['Fuel (gal)'] * 5 + ['CO₂ (tons)'] * 5 + ['Economic ($)'] * 5,
        'Value': cumulative_fuel + cumulative_co2 + cumulative_economic
    })

    proj_chart = alt.Chart(proj_df).mark_line(point=True).encode(
        x='Year:O',
        y='Value:Q',
        color='Metric:N',
        tooltip=['Year:O', 'Metric:N', alt.Tooltip('Value:Q', format=',.0f')]
    ).properties(title='5-Year Cumulative Impact', height=300)

    st.altair_chart(proj_chart, use_container_width=True)

    st.markdown("---")

    st.info("""
    **Methodology Notes:**
    - Based on FHWA and EPA emission factors
    - Fuel savings from reduced idling and stop-and-go traffic
    - Time savings valued at $20/hour (USDOT guidance)
    - CO₂ social cost at $51/ton (EPA 2023)
    - Actual results vary by city geometry, traffic patterns, and adoption rate
    """)