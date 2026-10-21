"""Offline review-day replay: TrafficCAM val frames -> run_frame (this device).

TrafficCAM val first, synthetic val/test fallback, synth-noise last resort.
One 4-way loop; mock STMP (lab-safe). Manual holds auto-release at 120s
(ManualRegistry.MAX_HOLD_S). Stdlib + numpy only at import.
"""

from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
VAL_CANDIDATES = [
    REPO / "data" / "trafficcam" / "images" / "val",
    REPO / "data" / "synthetic_india_yolo" / "images" / "val",
    REPO / "data" / "synthetic_india_yolo" / "images" / "test",
]

_state = None


def resolve_val_dir():
    for d in VAL_CANDIDATES:
        if d.is_dir() and any(d.iterdir()):
            return d
    return None


def get_state():
    """Singleton (sim, pipe, stmp, manual, frames). Built lazily for Streamlit reruns."""
    global _state
    if _state is not None:
        return _state
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    from footage import load_frames

    from adaptive_traffic.adapters import create_ntcip_adapter
    from adaptive_traffic.config.city_profile import get_city_profile
    from adaptive_traffic.core.analytics.queue_estimator import QueueEstimator
    from adaptive_traffic.core.closed_loop import create_loop
    from adaptive_traffic.core.closed_loop import run_frame as _run_frame
    from adaptive_traffic.core.control.policies import ManualProtocol, ManualRegistry
    from adaptive_traffic.core.detection.base import DetectorPort
    from adaptive_traffic.core.pipeline import StagedPipeline

    val_dir = resolve_val_dir()
    frames, names, skipped = load_frames(val_dir, max_frames=60) if val_dir else ([], [], 0)
    if not frames:  # last resort: deterministic synth-noise (latency-only)
        rng = np.random.default_rng(42)
        frames = [rng.integers(0, 255, (640, 640, 3), dtype=np.uint8) for _ in range(20)]
        names = [f"synth-{i}" for i in range(20)]

    from adaptive_traffic.config.device_tier import read_tier

    tier, det_cfg = read_tier()
    detector = DetectorPort.create(det_cfg)
    profile = get_city_profile("bangalore")
    pipe = StagedPipeline(detector=detector, estimator=QueueEstimator(profile))
    sim, ix_id = create_loop(city_profile=profile)
    stmp = create_ntcip_adapter({"ntcip_controller_ip": "127.0.0.1"}, mock=True)
    _state = {
        "pipe": pipe,
        "sim": sim,
        "ix": ix_id,
        "stmp": stmp,
        "manual": ManualRegistry(),
        "frames": frames,
        "names": names,
        "skipped": skipped,
        "val_dir": val_dir,
        "idx": 0,
        "tier": tier,
        "det_cfg": det_cfg,
        "run_frame": _run_frame,
        "ManualProtocol": ManualProtocol,
    }
    return _state


def tick():
    """Next val frame through the real loop. Returns result + health flags."""
    s = get_state()
    i = s["idx"] % len(s["frames"])
    s["idx"] += 1
    vid = s["names"][i].split("_frame")[0]
    if s.get("vid") != vid:  # video cut: EMA must not leak across scenes
        s["pipe"].estimator.reset()
        s["vid"] = vid
    r = s["run_frame"](s["pipe"], s["sim"], s["ix"], s["stmp"], s["frames"][i], manual=s["manual"])
    r["frame_name"] = s["names"][i]
    r["health"] = {
        "camera": "FAIL" if s["skipped"] else "OK",
        "detector": "WARN" if r["detected"] == 0 else "OK",
        "controller": "OK" if r["actuated"] else "FAIL",
        "queue": "WARN" if r["queued"] > 40 else "OK",
    }
    if r["actuated"]:
        s["cycles"] = s.get("cycles", 0) + 1
    try:
        faults = s["stmp"].get_faults()
    except Exception:
        faults = []
    try:
        connected = bool(s["stmp"].is_connected())
    except Exception:
        connected = False
    r["ntcip"] = {
        "transport": "mock",
        "connected": connected,
        "faults": len(faults),
        "cycles": s.get("cycles", 0),
    }
    r["val_dir"] = str(s["val_dir"]) if s["val_dir"] else "synth-noise"
    r["tier"] = s["tier"]
    r["backend"] = s["det_cfg"].get("backend", "onnx")
    r["single_approach"] = True  # one camera view: totals honest, direction splits illustrative
    r["audit"] = list(s["manual"].audit[-5:])
    return r


def hold(group_idx: int = 0, operator: str = "traffic-police"):
    s = get_state()
    s["manual"].activate(
        s["ManualProtocol"](
            route_id="review-route",
            intersection_ids=[s["ix"]],
            group_idxs=[group_idx],
            approval_id=f"hold-{s['ix']}-{group_idx}",
            signer_role="traffic-police",
            operator=operator,
        )
    )


def release():
    s = get_state()
    for aid in list(s["manual"].active):
        s["manual"].revoke(aid, reason="operator-release")
