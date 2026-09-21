"""Closed-loop integration: frame -> detect -> estimate -> decide -> actuate.

First test in the repo to exercise the whole path in one go (Phase C lab
slice). Detector is faked (fast, deterministic); estimator, engine scheduler,
cycle math, and STMP actuation are all real. One variant uses the real int8
model on noise frames to prove the true E2E including model load.
"""

import numpy as np
import pytest

from adaptive_traffic.adapters.ntcip_stmp import MockNTCIP1202STMPAdapter
from adaptive_traffic.config.city_profile import get_city_profile
from adaptive_traffic.core.analytics.queue_estimator import LaneQueue, QueueEstimate
from adaptive_traffic.core.closed_loop import create_loop, decide, run_frame
from adaptive_traffic.core.domain import VehicleDetection
from adaptive_traffic.core.pipeline import StagedPipeline
from adaptive_traffic.core.analytics.queue_estimator import QueueEstimator


def _car(x1, y1=300, y2=460):
    cx = (x1 + x1 + 50) // 2
    return VehicleDetection(
        class_id=0, class_name="car", confidence=0.9,
        bbox=(x1, y1, x1 + 50, y2), center=(cx, (y1 + y2) // 2),
    )


class FakeDetector:
    def __init__(self, dets):
        self.dets = dets

    def detect(self, frame):
        return self.dets


@pytest.fixture()
def loop():
    profile = get_city_profile("bangalore")
    sim, ix_id = create_loop(city_profile=profile)
    stmp = MockNTCIP1202STMPAdapter({})
    return profile, sim, ix_id, stmp


def test_full_loop_canned_detections(loop):
    profile, sim, ix_id, stmp = loop
    # bottom-half bboxes -> south approach, inside the 50m queue zone
    pipe = StagedPipeline(FakeDetector([_car(50), _car(300), _car(500)]),
                          QueueEstimator(profile))
    r = run_frame(pipe, sim, ix_id, stmp, object())

    assert r["detected"] == 3 and r["queued"] == 3
    assert r["injected"] == {"south": 3} and sum(r["demands"]) == 3
    assert r["actuated"] is True
    assert set(r["stage_ms"]) >= {"detect", "estimate"}
    # demand green: 3*2.0+2 = 8s -> efficiency floor 15s; empty group -> base 30s
    assert r["greens"] == {0: 15.0, 1: 30.0}
    assert r["cycle_length"] == pytest.approx(15 + 30 + 2 * 5 + 2 * 2)
    pushed = stmp.get_phase_timing()
    assert pushed.cycle_length == pytest.approx(r["cycle_length"])
    assert [p.green_time for p in pushed.phases] == [15.0, 30.0]


def test_demand_steers_next_phase(loop):
    _, sim, ix_id, _ = loop
    est = QueueEstimate(
        intersection_id=ix_id, timestamp=0.0, lanes=[],
        by_direction={"east": LaneQueue("east_0", "east", 6, 30.0, 5.0, 0.9)},
        total_vehicles=6, total_length_m=30.0,
    )
    from adaptive_traffic.core.closed_loop import inject_estimate

    inject_estimate(sim, ix_id, est)
    first = decide(sim, ix_id)   # 0_green -> 0_yellow (yellow always follows green)
    assert first["phase"] == "0_yellow"
    second = decide(sim, ix_id)  # east-only demand -> E/W group served next
    assert second["phase"] == "1_green"
    assert second["demands"][1] == 6


def test_empty_frame_stays_put_but_actuates(loop):
    profile, sim, ix_id, stmp = loop
    pipe = StagedPipeline(FakeDetector([]), QueueEstimator(profile))
    r = run_frame(pipe, sim, ix_id, stmp, object())

    assert r["detected"] == 0 and r["queued"] == 0
    assert r["demands"] == [0, 0] and r["actuated"] is True
    assert r["phase"] in ("0_green", "0_yellow")  # nothing waiting: hold position


def test_real_model_end_to_end(loop):
    pytest.importorskip("onnxruntime")
    from adaptive_traffic.core.detection.adapters_onnx import OnnxDetector

    profile, sim, ix_id, stmp = loop
    detector = OnnxDetector.from_registry("models/registry/india-yolov8n-final")
    pipe = StagedPipeline(detector, QueueEstimator(profile))
    rng = np.random.default_rng(42)
    for _ in range(2):
        r = run_frame(pipe, sim, ix_id, stmp,
                      rng.integers(0, 255, (640, 640, 3), dtype=np.uint8))
        assert r["actuated"] is True
        assert set(r["stage_ms"]) >= {"detect", "estimate"}
