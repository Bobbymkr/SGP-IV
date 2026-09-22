"""Drop-oldest buffer + staged detect->estimate->decide chain."""

import threading
import time

import pytest

from adaptive_traffic.config.city_profile import get_city_profile
from adaptive_traffic.core.analytics.queue_estimator import QueueEstimator
from adaptive_traffic.core.domain import VehicleDetection
from adaptive_traffic.core.pipeline import DropOldestBuffer, StagedPipeline


class FakeDetector:
    """Returns a canned payload; set .shaped to mimic DetectionResult."""

    def __init__(self, dets, shaped=False):
        self.dets = dets
        self.shaped = shaped
        self.calls = 0

    def detect(self, frame):
        self.calls += 1
        if self.shaped:

            class Shaped:
                pass

            out = Shaped()
            out.detections = self.dets
            return out
        return self.dets


class FakeEstimator:
    def __init__(self):
        self.calls = 0
        self.seen = None

    def estimate_from_detections(self, dets):
        self.calls += 1
        self.seen = dets
        return {"n": len(dets)}


def _det():
    return VehicleDetection(
        class_id=2, class_name="car", confidence=0.9, bbox=(100, 300, 150, 360), center=(125, 330)
    )


def test_buffer_drops_oldest():
    buf = DropOldestBuffer(maxsize=3)
    for i in range(5):
        buf.put(i)
    assert [buf.get() for _ in range(3)] == [2, 3, 4]
    assert buf.get() is None
    assert (buf.received, buf.dropped, buf.served) == (5, 2, 3)


@pytest.mark.parametrize("shaped", [False, True])
def test_process_normalizes_detector_shapes(shaped):
    pipe = StagedPipeline(FakeDetector([_det(), _det()], shaped=shaped), FakeEstimator())
    res = pipe.process(object())
    assert res.estimate == {"n": 2}
    assert res.decision is None
    assert set(res.stage_ms) == {"detect", "estimate"}
    assert isinstance(pipe.estimator.seen, list)


def test_process_with_decide():
    est = FakeEstimator()
    decide = lambda e: e["n"] * 10  # noqa: E731
    pipe = StagedPipeline(FakeDetector([_det()]), est, decide=decide)
    res = pipe.process(object())
    assert res.decision == 10
    assert "decide" in res.stage_ms


def test_drain_is_ordered_and_bounded():
    pipe = StagedPipeline(FakeDetector([]), FakeEstimator())
    for i in range(5):
        pipe.submit(i)
    assert len(pipe.drain(limit=2)) == 2
    assert len(pipe.drain()) == 2  # buffer held max 4; 1 dropped
    assert pipe.buffer.dropped == 1


def test_worker_thread_processes_then_stops():
    pipe = StagedPipeline(FakeDetector([]), FakeEstimator())
    for i in range(3):
        pipe.submit(i)
    stop = threading.Event()
    t = threading.Thread(target=pipe.run_worker, args=(stop,))
    t.start()
    deadline = time.time() + 5
    while pipe.estimator.calls < 3 and time.time() < deadline:
        time.sleep(0.01)
    stop.set()
    t.join(timeout=5)
    assert pipe.estimator.calls == 3
    assert not t.is_alive()


def test_real_estimator_seam():
    pipe = StagedPipeline(
        FakeDetector([_det(), _det()], shaped=True), QueueEstimator(get_city_profile("bangalore"))
    )
    res = pipe.process(object())
    assert type(res.estimate).__name__ == "QueueEstimate"
