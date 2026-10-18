"""
System Overview Page
"""

import streamlit as st

from adaptive_traffic.config.city_profiles import get_city_profile_or_default
from adaptive_traffic.config.settings import get_settings
from adaptive_traffic.ui._facts import get_eval_facts, get_model_facts
from adaptive_traffic.ui.theme import ACCENT, OK, card, heading, steps, svg, tagline


def _pretty(value: str) -> str:
    """aggressive_metro -> Aggressive Metro (raw config keys are not review-readable)."""
    return str(value).replace("_", " ").title()


def show_overview():
    """Display system overview page"""
    settings = get_settings()
    model = get_model_facts()
    ev = get_eval_facts()

    st.markdown(
        f"<h1 class='main-header'>{svg('signal', 34, ACCENT)} "
        "Adaptive Traffic Signal Timer</h1>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(heading("cpu", "AI-Powered Traffic Management"), unsafe_allow_html=True)
        st.markdown("""
        Traditional traffic lights use fixed timing that doesn't adapt to real conditions.
        Our **Adaptive Traffic Signal System** uses artificial intelligence to watch traffic
        in real-time and adjust signal timing automatically for optimal flow.

        ## How It Works
        """)
        st.markdown(
            steps(
                [
                    ("camera", "Watch Traffic", "cameras monitor vehicle queues"),
                    ("cpu", "Analyze Patterns", "AI processes traffic data"),
                    ("gauge", "Optimize Timing", "optimal green light duration"),
                    ("pulse", "Adapt Continuously", "signals adjust in real-time"),
                ]
            ),
            unsafe_allow_html=True,
        )
        st.caption(
            "Hard words made easy: mAP50 = how accurate the AI finds vehicles, 0 to 100. "
            "The small fast model (int8) is staged; the model that ships is fp32."
        )

        st.markdown(heading("check", "Key Benefits"), unsafe_allow_html=True)
        st.markdown(
            tagline("MEASURED", "Measured on the official 10k photo test and the eval matrix."),
            unsafe_allow_html=True,
        )
        col_b1, col_b2, col_b3 = st.columns(3)

        with col_b1:
            st.markdown(
                card("Smart beats fixed", ev["wins_11"], "eval scenes won", OK, "check"),
                unsafe_allow_html=True,
            )

        with col_b2:
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

        with col_b3:
            st.markdown(
                card("CPU speed", model["speed_short"], "fp32 bench", ACCENT, "pulse"),
                unsafe_allow_html=True,
            )

        st.markdown("---")

        st.markdown(
            f"""
        ## System Architecture

        - **Eye (detect)**: YOLOv8 `{model['name']}` — {model['overall']:.4f} mAP50, fp32
        - **Brain (decide)**: Green / Order / Cap policies; the old DQN stays dormant
        - **Hands (actuate)**: NTCIP STMP to signal box + J2735 SPAT to cars
        - **API Layer**: FastAPI RESTful services
        - **Dashboard**: Streamlit real-time monitoring
        """
        )

    with col2:
        st.markdown(heading("cpu", "Our AI Model"), unsafe_allow_html=True)

        st.markdown(
            card(
                "Detection quality",
                f"{model['overall'] * 100:.1f}%",
                f"{model['name']} · mAP50 = {model['overall']:.4f} (10k photo test)",
                OK,
                "camera",
            ),
            unsafe_allow_html=True,
        )
        st.caption(f"Speed {model['speed']}. Small-fast int8 {model['int8']}.")
        st.markdown(
            card(
                "Smart beats fixed",
                f"{ev['wins_11']} scenes",
                f"{ev['wins_15']} in the 15-scene Surat card",
                OK,
                "check",
            ),
            unsafe_allow_html=True,
        )

        st.markdown(heading("gauge", "Configuration"), unsafe_allow_html=True)
        city = st.session_state.get("city", "mumbai")
        profile = get_city_profile_or_default(city)
        st.markdown(
            f"""
| Setting | Value |
|---|---|
| City | {city.title()} |
| Lanes per approach | {profile.lanes_per_approach} |
| Driving behaviour | {_pretty(profile.behavior_preset)} |
| Weather profile | {_pretty(profile.weather_profile)} |
| Green time bounds | {profile.signal_bounds.min_green}-{profile.signal_bounds.max_green} s |
| Environment | {settings.environment} |
"""
        )

        st.markdown(heading("pulse", "Quick Actions"), unsafe_allow_html=True)
        if st.button("Reload Configuration"):
            st.rerun()

        st.info("Use Navigate on the left to open the Dashboard or the Live Demo.")

    with st.expander("Words used on this dashboard (plain English)"):
        st.markdown(
            """
| Word | What it means here |
|---|---|
| mAP50 | How accurate the AI is at finding vehicles, 0 to 100. 84.8% = 0.8477. |
| eval matrix | The set of traffic scenes we ran to compare the AI against fixed timing. |
| p95 | The slowest decision in 95 cases out of 100. Our budget is 10 ms. |
| NTCIP STMP | The standard used to send a timing plan to a real signal box. |
| SPAT | A message broadcast to cars telling them what the light is doing. |
| DQN / Webster / Fuzzy | Older timing ideas kept in the code. Not used, not evaluated. |
| int8 / fp32 | A smaller, faster model build versus the full-size one that ships. |
"""
        )
