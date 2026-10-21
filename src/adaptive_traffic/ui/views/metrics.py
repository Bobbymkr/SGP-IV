"""
Impact Metrics Page
"""

import altair as alt
import pandas as pd
import streamlit as st

from adaptive_traffic.ui._facts import get_eval_facts, get_model_facts
from adaptive_traffic.ui._india import (
    CARBON_INR_PER_TONNE,
    CO2_T_PER_CAR_YEAR,
    LITRE_PER_US_GALLON,
    VALUE_OF_TIME_INR_PER_HOUR,
    VOLUME_SOURCE,
    format_inr_compact,
    format_lakh_crore_hours,
    fuel_rates,
    rates_line,
)
from adaptive_traffic.ui.theme import ACCENT, OK, WARN, card, heading, svg, tagline


def _show_breakdowns(total_litres, total_co2, total_economic, total_fuel_value, total_time_value):
    """The modelled detail behind the cards: pollutants, money split, 5-year view."""
    # Environmental breakdown
    st.markdown(
        heading("leaf", "Environmental Impact Breakdown"),
        unsafe_allow_html=True,
    )
    st.markdown(
        tagline("ILLUSTRATION", "Pollutant split from the same modelled tonnage."),
        unsafe_allow_html=True,
    )

    env_data = pd.DataFrame(
        {
            "Pollutant": ["CO₂", "NOx", "PM2.5", "VOCs", "CO"],
            "Reduction (t/yr)": [
                total_co2,
                total_co2 * 0.008,  # NOx ~0.8% of CO2
                total_co2 * 0.001,  # PM2.5
                total_co2 * 0.005,  # VOCs
                total_co2 * 0.02,  # CO
            ],
        }
    )

    env_chart = (
        alt.Chart(env_data)
        .mark_bar()
        .encode(
            x=alt.X(
                "Reduction (t/yr):Q",
                title="Annual reduction (tonnes, log scale)",
                scale=alt.Scale(type="log"),
            ),
            y=alt.Y("Pollutant:N", sort="-x"),
            color=alt.Color("Reduction (t/yr):Q", scale=alt.Scale(scheme="greens")),
            tooltip=[
                "Pollutant:N",
                "Reduction (t/yr):Q",
            ],
        )
        .properties(height=300)
    )

    st.altair_chart(env_chart, use_container_width=True)

    # Economic breakdown
    st.markdown(
        heading("gauge", "Economic Benefit Breakdown"),
        unsafe_allow_html=True,
    )
    st.markdown(
        tagline("ILLUSTRATION", "Value split of the modelled economic benefit."),
        unsafe_allow_html=True,
    )

    econ_data = pd.DataFrame(
        {
            "Category": [
                "Commuter Time Savings",
                "Commercial Vehicle Efficiency",
                "Fuel Cost Reduction",
                "Vehicle Wear Reduction",
                "Accident Cost Avoidance",
                "Emergency Response Improvement",
            ],
            "Annual Value (₹)": [
                total_time_value * 0.65,
                total_time_value * 0.15,
                total_fuel_value,
                total_time_value * 0.08,
                total_time_value * 0.07,
                total_time_value * 0.05,
            ],
        }
    )

    econ_chart = (
        alt.Chart(econ_data)
        .mark_arc(innerRadius=60)
        .encode(
            theta="Annual Value (₹):Q",
            color=alt.Color(
                "Category:N",
                scale=alt.Scale(
                    domain=[
                        "Commuter Time Savings",
                        "Commercial Vehicle Efficiency",
                        "Fuel Cost Reduction",
                        "Vehicle Wear Reduction",
                        "Accident Cost Avoidance",
                        "Emergency Response Improvement",
                    ],
                    range=[OK, "#64748b", "#94a3b8", "#cbd5e1", "#e2e8f0", "#f1f5f9"],
                ),
                legend=alt.Legend(orient="bottom", labelLimit=400),
            ),
            tooltip=["Category:N", alt.Tooltip("Annual Value (₹):Q", format=",.0f")],
        )
        .properties(height=400)
    )

    st.altair_chart(econ_chart, use_container_width=True)

    # Time-series projection
    st.markdown(
        heading("pulse", "5-Year Cumulative Impact"),
        unsafe_allow_html=True,
    )
    st.markdown(
        tagline("ILLUSTRATION", "The same projection, three years further on."),
        unsafe_allow_html=True,
    )

    years = list(range(1, 6))
    cumulative_fuel = [total_litres * y for y in years]
    cumulative_co2 = [total_co2 * y for y in years]
    cumulative_economic = [total_economic * y for y in years]

    proj_df = pd.DataFrame(
        {
            "Year": years * 3,
            "Metric": ["Fuel (L)"] * 5 + ["CO₂ (t)"] * 5 + ["Economic (₹)"] * 5,
            "Value": cumulative_fuel + cumulative_co2 + cumulative_economic,
        }
    )

    proj_chart = (
        alt.Chart(proj_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Year:O"),
            y=alt.Y("Value:Q", title="Cumulative"),
            tooltip=["Year:O", "Metric:N", alt.Tooltip("Value:Q", format=",.0f")],
        )
        .properties(height=180)
        .facet(column="Metric:N", columns=3)
        .resolve_scale(y="independent")
    )

    st.altair_chart(proj_chart, use_container_width=True)


def show_metrics():
    """Display environmental and economic impact metrics"""
    st.markdown(
        f"<h1 class='main-header'>{svg('leaf', 32, OK)} " "Environmental & Economic Impact</h1>",
        unsafe_allow_html=True,
    )

    # Measured strip — eval matrix + registry, never hardcoded
    model = get_model_facts()
    ev = get_eval_facts()
    st.markdown(
        tagline("MEASURED", "Measured on the official 10k photo test and the eval matrix."),
        unsafe_allow_html=True,
    )
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(
            card("Smart wins", ev["wins_11"], "eval scenes", OK, "check"),
            unsafe_allow_html=True,
        )

    with m2:
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

    with m3:
        st.markdown(
            card("CPU speed", model["speed_short"], "fp32 bench", ACCENT, "pulse"),
            unsafe_allow_html=True,
        )

    with m4:
        st.markdown(
            card("Decide p95", ev["dec95"], "budget 10 ms", ACCENT, "cpu"),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Your city - every number below is computed from these two inputs
    st.markdown(heading("car", "Your city"), unsafe_allow_html=True)
    city = st.session_state.get("city", "mumbai")
    petrol, _diesel = fuel_rates(city)

    col1, col2 = st.columns(2)
    with col1:
        num_intersections = st.number_input(
            "Number of Signalized Intersections", min_value=1, max_value=1000, value=150
        )
    with col2:
        daily_traffic = st.number_input(
            "Average Daily Traffic per Intersection (veh/day)",
            min_value=1000,
            max_value=100000,
            value=25000,
            step=1000,
        )
    st.caption(rates_line(city))

    # The model: per-intersection volumes scaled by traffic, priced with today's rates.
    scale = daily_traffic / 25000
    litres_per_intersection = 12450 * LITRE_PER_US_GALLON * scale  # litres/year
    co2_per_intersection = 124 * scale  # tonnes CO2/year
    hours_per_intersection = 15333 * scale  # hours/year
    fuel_value_per = litres_per_intersection * petrol  # rupees/year
    time_value_per = hours_per_intersection * VALUE_OF_TIME_INR_PER_HOUR  # rupees/year
    carbon_value_per = co2_per_intersection * CARBON_INR_PER_TONNE  # rupees/year

    total_litres = litres_per_intersection * num_intersections
    total_co2 = co2_per_intersection * num_intersections
    total_hours = hours_per_intersection * num_intersections
    total_fuel_value = fuel_value_per * num_intersections
    total_time_value = time_value_per * num_intersections
    total_carbon_value = carbon_value_per * num_intersections
    total_economic = total_fuel_value + total_time_value

    # Key impact metrics
    st.markdown(
        heading("leaf", "Key Impact Metrics (Per Intersection / Year)"),
        unsafe_allow_html=True,
    )
    st.markdown(
        tagline(
            "ILLUSTRATION",
            "Modelled per intersection per year. Quantities are modelled; the prices "
            "and rates used to price them are real and dated.",
        ),
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            card(
                "Fuel Saved",
                f"{litres_per_intersection:,.0f} L",
                f"{format_inr_compact(fuel_value_per)} @ ₹{petrol}/L ({city.title()})",
                OK,
                "leaf",
            ),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            card(
                "CO₂ Reduced",
                f"{co2_per_intersection:,.0f} t",
                f"{format_inr_compact(carbon_value_per)} @ ₹{CARBON_INR_PER_TONNE:,.0f}/t · "
                f"≈{co2_per_intersection / CO2_T_PER_CAR_YEAR:,.0f} cars' emissions",
                ACCENT,
                "leaf",
            ),
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            card(
                "Time Saved",
                format_lakh_crore_hours(hours_per_intersection),
                f"vehicle-hours · {format_inr_compact(time_value_per)} @ "
                f"₹{VALUE_OF_TIME_INR_PER_HOUR:,.0f}/hour",
                ACCENT,
                "pulse",
            ),
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            card(
                "Emergency Response",
                "Not in this build",
                "preemption is specified, not wired",
                WARN,
                "signal",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # City-scale impact
    st.markdown(
        heading("car", "City-Scale Impact Projection"),
        unsafe_allow_html=True,
    )
    st.markdown(
        tagline(
            "ILLUSTRATION",
            "Same per-intersection model, scaled to your city and priced with today's rates.",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(heading("leaf", "Projected Annual Impact"), unsafe_allow_html=True)
    st.markdown(
        tagline(
            "ILLUSTRATION",
            "The same per-intersection model, scaled across your city.",
        ),
        unsafe_allow_html=True,
    )
    st.caption(
        f"Scaled from the per-intersection model by your traffic figure "
        f"({daily_traffic:,} veh/day)."
    )

    proj_col1, proj_col2, proj_col3, proj_col4 = st.columns(4)

    with proj_col1:
        st.markdown(
            card(
                "Fuel Savings",
                f"{total_litres / 1e5:.1f} lakh L",
                f"{format_inr_compact(total_fuel_value)} @ ₹{petrol}/L ({city.title()})",
                OK,
                "leaf",
            ),
            unsafe_allow_html=True,
        )

    with proj_col2:
        st.markdown(
            card(
                "CO₂ Reduction",
                f"{total_co2:,.0f} t",
                f"{format_inr_compact(total_carbon_value)} @ ₹{CARBON_INR_PER_TONNE:,.0f}/t · "
                f"≈{total_co2 / CO2_T_PER_CAR_YEAR:,.0f} cars' emissions",
                ACCENT,
                "leaf",
            ),
            unsafe_allow_html=True,
        )

    with proj_col3:
        st.markdown(
            card(
                "Time Savings",
                format_lakh_crore_hours(total_hours),
                f"vehicle-hours · {format_inr_compact(total_time_value)} @ "
                f"₹{VALUE_OF_TIME_INR_PER_HOUR:,.0f}/hour",
                ACCENT,
                "pulse",
            ),
            unsafe_allow_html=True,
        )

    with proj_col4:
        st.markdown(
            card(
                "3-year value",
                format_inr_compact(total_economic * 3),
                "modelled economic benefit (fuel + time), not ROI",
                WARN,
                "gauge",
            ),
            unsafe_allow_html=True,
        )

    with st.expander("Modelled breakdowns: pollutants, money split, 5-year view"):
        _show_breakdowns(
            total_litres, total_co2, total_economic, total_fuel_value, total_time_value
        )

    st.markdown("---")

    st.info(f"""
    **Methodology Notes (honest):**
    - Measured: eval matrix 11/11 wins + Surat 15/15, decide p95, 5-8 fps CPU (see Comparison page)
    - Projected here: modelled quantities (ILLUSTRATION) priced with real, dated rates
    - Rates: {rates_line(city, with_usd=False)} (the exchange rate is shown above)
    - Fuel and CO2 volumes are {VOLUME_SOURCE} (per-intersection constants from a US
      study, scaled by your traffic figure). Converting them to a share of the fuel
      actually burned at the junction needs a trip-length assumption we have not made
    - CO2: valued at the IISD social cost of carbon for India (2018), converted at the
      rate above. IISD's latest review notes India has no explicit carbon tax now, so
      this is a social-cost figure, not a market price
    - Time: valued at ₹{VALUE_OF_TIME_INR_PER_HOUR:,.0f}/vehicle-hour - our stated assumption,
      not a published MoRTH rate
    - Planned next: a traffic-derived model (impact model v2) replaces these constants
    - Actual results vary by city geometry, traffic patterns, and adoption rate
    """)
