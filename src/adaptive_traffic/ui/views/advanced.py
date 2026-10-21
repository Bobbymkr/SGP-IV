"""Advanced Features & Settings.

Rule for this page: show what the running system actually does, and mark the
rest as specification. Every control here either feeds the real pipeline
(city, confidence, model, frames) or is a read-only value the engine reads.
"""

import streamlit as st

from adaptive_traffic.config.city_profiles import get_city_profile_or_default
from adaptive_traffic.config.settings import get_settings
from adaptive_traffic.ui._api_routes import API_ROUTES
from adaptive_traffic.ui._facts import get_eval_table, get_model_facts
from adaptive_traffic.ui.theme import ACCENT, banner, card, heading, svg, tagline


def show_advanced():
    """Display advanced features and settings"""
    st.markdown(
        f"<h1 class='main-header'>{svg('gauge', 32, ACCENT)} Advanced Features & Settings</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        banner(
            "The Configuration tab feeds the real pipeline and the API tab lists the real "
            "routes. The other three tabs are the specification of features this build "
            "does not run yet.",
            tag="SPEC",
        ),
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "Emergency Priority",
            "Weather Adaptation",
            "Pedestrian & Cyclist",
            "Configuration",
            "API & Integration",
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
    """Emergency vehicle priority — specification, not wired in this build."""
    st.markdown(heading("signal", "Emergency Vehicle Priority (EVP)"), unsafe_allow_html=True)

    st.markdown(
        tagline(
            "SPEC",
            "Not implemented in this build. The detector has no emergency-vehicle class, "
            "so no preemption can run.",
        ),
        unsafe_allow_html=True,
    )

    st.markdown("""
    The planned feature detects emergency vehicles (ambulances, fire trucks, police) by:
    - **Optical detection**: flashing light pattern recognition
    - **Audio detection**: siren classification
    - **V2X message**: direct vehicle-to-infrastructure alert
    """)

    model = get_model_facts()
    st.markdown("**What the current model can see**")
    st.markdown(
        f"Classes in `{model['name']}`: " + ", ".join(sorted(model["per_class"].keys())) + "."
    )
    st.caption("No ambulance, fire or police class, so EVP would need a separate model.")

    st.markdown(
        "**What is live instead**: priority for the ordinary vehicles we do detect, "
        "using the adaptive plan on the Comparison page."
    )


def show_weather_adaptation():
    """Weather adaptation — the real city weather profile plus eval evidence."""
    st.markdown(heading("leaf", "Weather-Adaptive Signal Control"), unsafe_allow_html=True)

    city = st.session_state.get("city", "mumbai")
    profile = get_city_profile_or_default(city)

    st.markdown(
        tagline(
            "MEASURED",
            "The engine reads the city weather profile. The eval matrix includes "
            "rain, monsoon and waterlogged scenes.",
        ),
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            card(
                "Weather in use",
                str(profile.weather_profile).replace("_", " ").title(),
                f"city profile: {city}",
                ACCENT,
                "leaf",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            card(
                "Driving behaviour",
                str(profile.behavior_preset).replace("_", " ").title(),
                f"city profile: {city}",
                ACCENT,
                "car",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("**Rain and flood scenes in the eval matrix** (real runs, same policy):")
    table = get_eval_table()
    rain_scenes = [
        row["Scenario"]
        for row in table["fresh"]
        if any(k in row["Scenario"] for k in ("rain", "monsoon", "waterlogged"))
    ]
    st.markdown("\n".join(f"- `{s}`" for s in rain_scenes) or "- none in this scorecard")
    st.caption("Scene names come from the eval scorecards; the per-scene times are on Comparison.")

    st.markdown(
        "**Not in this build**: a live weather feed, per-condition speed factors and "
        "gap tables. Those would need a weather API and a timing model that reads it."
    )


def show_pedestrian_cyclist():
    """Pedestrian and cyclist safety — honest status against the real model."""
    st.markdown(heading("car", "Pedestrian & Cyclist Safety"), unsafe_allow_html=True)

    model = get_model_facts()
    st.markdown(
        tagline(
            "SPEC",
            "Not implemented in this build: the model detects vehicles only, "
            "no pedestrian or cyclist class.",
        ),
        unsafe_allow_html=True,
    )

    st.markdown("**Classes the current model can see**")
    st.markdown(", ".join(sorted(model["per_class"].keys())))

    st.markdown(
        "**What the planned feature needs**\n"
        "- a pedestrian and cyclist class in the detector\n"
        "- crossing and cycle-lane zones per intersection\n"
        "- a leading pedestrian interval and clearance phase in the timing plan\n"
        "- accessible signal support (audio + vibrotactile)"
    )
    st.caption("The signal plan already carries a pedestrian phase field; it is not filled yet.")


def show_system_config():
    """System configuration — the knobs that really drive the pipeline."""
    settings = get_settings()
    st.markdown(heading("cpu", "System Configuration"), unsafe_allow_html=True)

    st.markdown(
        tagline(
            "MEASURED",
            "These five controls are passed to the real pipeline run on the Live Demo page.",
        ),
        unsafe_allow_html=True,
    )

    city = st.session_state.get("city", "mumbai")
    profile = get_city_profile_or_default(city)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Pipeline**")
        st.number_input(
            "Detection confidence",
            min_value=0.05,
            max_value=0.95,
            value=0.45,
            step=0.05,
            key="det_conf",
            help="Passed to the real detector as --conf.",
        )
        st.number_input(
            "Photos to run",
            min_value=1,
            max_value=40,
            value=8,
            step=1,
            key="run_frames",
            help="Passed to the real run as --max-frames.",
        )
        st.number_input(
            "Closed-loop frames",
            min_value=1,
            max_value=20,
            value=3,
            step=1,
            key="run_closed_frames",
            help="Passed to the real run as --closed-frames.",
        )

    with col2:
        st.markdown("**Model**")
        st.text_input(
            "Model registry",
            value="models/registry/india-yolov8n-final",
            key="model_registry",
            help="Passed to the real run as --registry.",
        )
        st.selectbox(
            "Backend",
            ["onnx", "ultralytics", "tensorrt"],
            index=0,
            key="run_backend",
            help="Passed to the real run as --backend.",
        )

    st.markdown("### City in use")
    st.markdown(
        f"`{city}` — {profile.lanes_per_approach} lanes per approach, "
        f"green {profile.signal_bounds.min_green}-{profile.signal_bounds.max_green}s. "
        "Change the city in the sidebar."
    )

    st.markdown("### Engine defaults (read-only)")
    st.markdown(
        tagline(
            "SPEC",
            "Read from config/settings.py. The engine reads them, this page does not change them.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        f"- Minimum green: {settings.min_green_time}s\n"
        f"- Maximum green: {settings.max_green_time}s\n"
        f"- Yellow time: {settings.default_yellow_time}s\n"
        f"- Detection time: {settings.detection_time}s\n"
        f"- Controller in use: adaptive weighted + clockwise (Green / Order / Cap)\n"
        f"- Simulation time: {settings.simulation_time}s, signals: {settings.num_signals}"
    )
    st.caption(
        "These come from config/settings.py and the .env file. The engine reads them, "
        "this page does not change them. The controller listed above is the one wired "
        "into eval and the closed loop; the old DQN setting is unused."
    )

    st.markdown("### Export current setup")
    export = (
        f"city: {city}\n"
        f"backend: {st.session_state.get('run_backend', 'onnx')}\n"
        f"registry: {st.session_state.get('model_registry', '')}\n"
        f"confidence: {st.session_state.get('det_conf', 0.45)}\n"
        f"max_frames: {st.session_state.get('run_frames', 8)}\n"
        f"closed_frames: {st.session_state.get('run_closed_frames', 3)}\n"
    )
    st.download_button("Download setup (YAML)", export, "adaptive_traffic_setup.yaml")


def show_api_integration():
    """API and integration — the routes the FastAPI app really serves."""
    st.markdown(heading("cpu", "API & Integration"), unsafe_allow_html=True)

    st.markdown(
        tagline(
            "MEASURED",
            "These routes are served by the FastAPI app in src/adaptive_traffic/api.",
        ),
        unsafe_allow_html=True,
    )

    groups = [
        ("Health", "/api/v1/health", "/api/v1/version"),
        ("Signals and timing", "/api/v1/signals", "/api/v1/signals/plans"),
        (
            "Detection",
            "/api/v1/detection",
        ),
        (
            "Analytics",
            "/api/v1/analytics",
        ),
    ]
    for name, *prefixes in groups:
        st.markdown(f"**{name}**")
        rows = "\n".join(
            f"| `{m}` | `{p}` | {d} |"
            for m, p, d in API_ROUTES
            if any(p.startswith(pref) for pref in prefixes)
        )
        st.markdown(f"""
| Method | Path | What it does |
|---|---|---|
{rows}
""")

    st.markdown("### Run the API")
    st.code(
        "# Windows\n"
        ".venv\\Scripts\\python.exe -m uvicorn adaptive_traffic.api.main:app --port 8000\n"
        "\n"
        "# Linux / macOS\n"
        ".venv/bin/python -m uvicorn adaptive_traffic.api.main:app --port 8000",
        language="bash",
    )
    st.caption("Read the docs at /docs once it is running.")

    st.markdown("### Authentication")
    st.markdown(
        tagline(
            "SPEC",
            "There is no authentication in this build. Every route above is open, so do not "
            "expose this service to a public network.",
        ),
        unsafe_allow_html=True,
    )

    st.markdown("### Integration examples")

    with st.expander("Python client"):
        st.code(
            """
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Signal status
signal = client.get("/api/v1/signals/1").json()

# Update the timing plan
client.post("/api/v1/signals/1/timing", json={
    "green_time": 30,
    "yellow_time": 5
})
        """,
            language="python",
        )

    with st.expander("JavaScript / TypeScript"):
        st.code(
            """
const response = await fetch('/api/v1/signals/');
const signals = await response.json();
        """,
            language="typescript",
        )

    st.markdown("### Webhooks")
    st.markdown(
        "Not built in this release. The API exposes analytics ingest "
        "(`POST /api/v1/analytics/ingest`) if you need to push events in."
    )
