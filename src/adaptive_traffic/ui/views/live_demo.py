"""Live Interactive Demo Page.

Two clearly separate things, never mixed:
  1. Simulated junction  - slider-driven, ILLUSTRATION (a model, not a measurement)
  2. Real pipeline       - real detector on real traffic photos, MEASURED
The simulator sliders never touch the real run; the real run never pretends to
be driven by the sliders.
"""

import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from adaptive_traffic.ui._facts import get_eval_facts
from adaptive_traffic.ui.theme import ACCENT, OK, card, heading, svg, tagline

HISTORY_KEY = "run_history"
RUN_KEY = "run_state"


def show_live_demo():
    """Display live interactive demo"""
    st.markdown(
        f"<h1 class='main-header'>{svg('pulse', 32, ACCENT)} Live Demo</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="explanation-box">
    Two separate things on this page: a <b>simulated junction</b> you drive with the sliders,
    and the <b>real pipeline</b> that reads real traffic photos and plans real green time.
    The simulation is an illustration. The pipeline output is measured.
    </div>
    """,
        unsafe_allow_html=True,
    )

    _run_panel()

    st.markdown("---")

    controls, output = st.columns([1, 2])

    with controls:
        st.markdown(heading("signal", "Simulated junction"), unsafe_allow_html=True)
        st.markdown(
            tagline("ILLUSTRATION", "Move a slider and the junction re-plans instantly."),
            unsafe_allow_html=True,
        )
        st.markdown("**Traffic demand (vehicles/min)**")
        north = st.slider("North", 0, 50, 30, 5)
        south = st.slider("South", 0, 50, 15, 5)
        east = st.slider("East", 0, 50, 10, 5)
        west = st.slider("West", 0, 50, 5, 5)

        st.markdown("---")
        st.markdown("**Timing policy**")
        controller = st.selectbox(
            "Policy",
            ["Adaptive (weighted + clockwise)", "Fixed time (baseline)"],
            index=0,
        )
        st.caption("Green = startup + Σ(vehicles × headway). Clockwise is the default order.")
        horizon = st.slider("Sim horizon (minutes)", 1, 10, 5)

    with output:
        st.markdown(heading("gauge", "Simulator output"), unsafe_allow_html=True)

        cycle_time = 120  # fixed cycle for the illustration

        if controller.startswith("Adaptive"):
            # Weighted-discharge illustration: share of cycle minus lost time.
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

        col_ns, col_ew = st.columns(2)

        with col_ns:
            st.markdown(
                card(
                    "North-South Phase",
                    f"{ns_green}s Green",
                    f"{north + south} veh/min demand",
                    OK,
                    "signal",
                ),
                unsafe_allow_html=True,
            )

        with col_ew:
            st.markdown(
                card(
                    "East-West Phase",
                    f"{ew_green}s Green",
                    f"{east + west} veh/min demand",
                    ACCENT,
                    "signal",
                ),
                unsafe_allow_html=True,
            )

        ev = get_eval_facts()
        st.markdown(
            tagline(
                "MEASURED",
                f"On the eval matrix the adaptive plan cut waiting by {ev['wait_band']} "
                f"in {ev['wins_11']} scenes.",
            ),
            unsafe_allow_html=True,
        )

        st.markdown(heading("pulse", "Queue length over time"), unsafe_allow_html=True)
        time_steps = np.arange(0, horizon * 60, 10)
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
            .mark_area(opacity=0.5, stroke="white", strokeWidth=1)
            .encode(
                x="Time (s):Q",
                y="Queue Length:Q",
                color=alt.Color(
                    "Direction:N",
                    scale=alt.Scale(
                        domain=["North-South", "East-West"],
                        range=[ACCENT, "#94a3b8"],
                    ),
                ),
                tooltip=["Time (s):Q", "Queue Length:Q", "Direction:N"],
            )
            .properties(height=300, title="Simulated queue lengths (illustration)")
        )

        st.altair_chart(queue_chart, use_container_width=True)

    st.caption("The real pipeline run is at the top of this page; the sliders do not drive it.")


def _pipeline_config() -> dict:
    """Values set on the Settings page, with the demo defaults as fallback."""
    s = st.session_state
    return {
        "city": s.get("city", "mumbai"),
        "conf": s.get("det_conf", 0.45),
        "frames": s.get("run_frames", 8),
        "closed_frames": s.get("run_closed_frames", 3),
        "registry": s.get("model_registry", "models/registry/india-yolov8n-final"),
        "backend": s.get("run_backend", "onnx"),
    }


def get_run_history() -> list:
    """Past real-pipeline runs in this session (newest first)."""
    return st.session_state.get(HISTORY_KEY, [])


def _show_run_status():
    """Last-run status so the reviewer always knows how fresh the numbers are."""
    history = get_run_history()
    if not history:
        st.markdown(
            tagline(
                "MEASURED",
                "No real run yet in this session. Press the button above to run the pipeline.",
            ),
            unsafe_allow_html=True,
        )
        return
    last = history[0]
    c1, c2 = st.columns([2, 3])
    with c1:
        st.markdown(
            card(
                "Last run",
                last["time"],
                f"{last['city']} · {last['summary']}",
                OK if last["ok"] else "#dc2626",
                "pulse",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown("**Run history (this session)**")
        st.dataframe(
            pd.DataFrame(history)[["time", "city", "summary", "ok"]],
            use_container_width=True,
            hide_index=True,
        )


def _parse_run(stdout: str, city: str, ok: bool) -> dict:
    """Turn the demo script output into one history row."""
    cars = re.search(r"AI result: (\d+) photos, ([\d.]+) per second, (\d+) cars found", stdout)
    loop = re.search(r"Loop: actuated=(\d+)/(\d+)", stdout)
    source = re.search(r"Frames: \d+ from (\S+)", stdout)
    parts = []
    if cars:
        parts.append(f"{cars.group(3)} cars in {cars.group(1)} photos")
    if loop:
        parts.append(f"{loop.group(1)}/{loop.group(2)} actuated")
    return {
        "time": time.strftime("%H:%M:%S"),
        "city": city,
        "summary": ", ".join(parts) or ("completed" if ok else "failed"),
        "source": source.group(1) if source else "unknown",
        "ok": ok,
    }


def _start_run(cfg: dict) -> None:
    """Start the real pipeline in a worker thread so the page stays responsive."""
    repo = Path(__file__).resolve().parents[4]
    cmd = [
        sys.executable,
        str(repo / "scripts/demo_sgp.py"),
        "--city",
        str(cfg["city"]),
        "--max-frames",
        str(cfg["frames"]),
        "--closed-frames",
        str(cfg["closed_frames"]),
        "--conf",
        str(cfg["conf"]),
        "--registry",
        str(cfg["registry"]),
        "--backend",
        str(cfg["backend"]),
    ]
    state = {"proc": None, "out": "", "err": "", "ok": False, "done": False, "cancelled": False}

    def worker():
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(repo)
        )
        state["proc"] = proc
        out, err = proc.communicate()
        state.update(
            out=out or "",
            err=err or "",
            ok=proc.returncode == 0,
            done=True,
            cancelled=state["cancelled"],
        )

    threading.Thread(target=worker, daemon=True).start()
    st.session_state[RUN_KEY] = state


def _record_run(state: dict, city: str) -> None:
    """Store a finished run in the history (once)."""
    if state.get("recorded"):
        return
    state["recorded"] = True
    history = get_run_history()
    st.session_state[HISTORY_KEY] = [
        _parse_run(state["out"], city, state["ok"]),
        *history,
    ][:5]


@st.fragment(run_every=1.0)
def _run_panel():
    """The real-pipeline panel: status, run/cancel, output. Refreshes every second."""
    st.session_state.setdefault(RUN_KEY, None)
    cfg = _pipeline_config()
    state = st.session_state[RUN_KEY]

    st.markdown(heading("cpu", "Real pipeline on real traffic photos"), unsafe_allow_html=True)
    st.markdown(
        tagline(
            "MEASURED",
            "Real detector, real queue estimator, real signal plan, on real Indian "
            "CCTV frames (BMD-45 is the training set, not the demo footage).",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        f"Config in effect: city **{cfg['city']}**, confidence **{cfg['conf']}**, "
        f"registry **{cfg['registry']}**, backend **{cfg['backend']}**, "
        f"photos **{cfg['frames']}** (change it on the Settings page)."
    )

    if state is None:
        if st.button("Run real pipeline (photos to AI to green)", type="primary"):
            _start_run(cfg)
        st.caption("Usually a few seconds; longer the first time while the model warms up.")
        _show_run_status()
        return

    if not state["done"]:
        st.markdown(
            tagline("MEASURED", "Pipeline running - the page stays responsive."),
            unsafe_allow_html=True,
        )
        if st.button("Cancel run", key="cancel_run"):
            state["cancelled"] = True
            proc = state.get("proc")
            if proc and proc.poll() is None:
                proc.terminate()
        return

    _record_run(state, str(cfg["city"]))
    if not state.get("notified"):
        state["notified"] = True
        st.rerun()  # full rerun so the sidebar "last real run" badge refreshes
    if state.get("cancelled"):
        st.warning("Run cancelled by the operator.")
    elif state["ok"]:
        st.success("Real loop complete: photos, AI, queue, green, mock signal.")
    else:
        st.error("Loop failed - the output above shows why (never hidden).")
    st.code(state["out"][-4000:] or "(no output)", language="text")
    if not state["ok"] and state["err"]:
        st.code(state["err"][-2000:], language="text")
    if st.button("Run again", key="run_again"):
        st.session_state[RUN_KEY] = None
    _show_run_status()
