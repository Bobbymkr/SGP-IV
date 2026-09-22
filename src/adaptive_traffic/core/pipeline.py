"""Decoupled detect -> estimate -> decide stages (MASTER_PLAN Phase 5.3).

Slow detection must never block estimation: frames land in a bounded
drop-oldest buffer, and each stage observes its Step-2 histogram, so the
bench (`bench_detect --stages`), the scorecard (`dec_p50/p95_ms`), and
Prometheus all slice the same boundaries.

Two shapes, one class:

* ``process(frame)`` — inline, deterministic; the primary path and what the
  benches exercise.
* ``submit(frame)`` + ``drain()`` (+ optional ``run_worker`` thread) — the
  edge-runner shape for a live camera feed. No live caller exists yet (the
  API serves mock detections, the sim synthesizes its own vehicles), so
  nothing starts the worker today; the primitives are covered by unit tests
  and ready when the runner lands.

Stdlib only at import time; detector / estimator / decide callback are
duck-typed so this module never imports heavy CV libs.
"""

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from adaptive_traffic.core.monitoring import timed


class DropOldestBuffer:
    """Thread-safe bounded frame buffer; a full buffer drops the oldest frame.

    Dropping (not blocking) is the point: on a slow detector the control loop
    must always see the freshest frame, never a growing backlog.
    """

    def __init__(self, maxsize: int = 4):
        self._buf: deque = deque(maxlen=maxsize)
        self._lock = threading.Lock()
        self.received = 0
        self.dropped = 0
        self.served = 0

    def put(self, frame: Any) -> None:
        """Enqueue without blocking; oldest frame is evicted when full."""
        with self._lock:
            if len(self._buf) == self._buf.maxlen:
                self.dropped += 1
            self._buf.append(frame)
            self.received += 1

    def get(self) -> Optional[Any]:
        """Oldest buffered frame, or None when empty. Never blocks."""
        with self._lock:
            if not self._buf:
                return None
            self.served += 1
            return self._buf.popleft()

    def qsize(self) -> int:
        with self._lock:
            return len(self._buf)


@dataclass
class StageResult:
    """One frame through the pipeline, with per-stage wall time in ms."""

    detections: Any = None
    estimate: Any = None
    decision: Any = None
    stage_ms: dict = field(default_factory=dict)


class StagedPipeline:
    """Chains detector -> estimator -> optional decide callback per frame."""

    def __init__(
        self, detector, estimator, decide: Optional[Callable] = None, buffer_size: int = 4
    ):
        self.detector = detector
        self.estimator = estimator
        self.decide = decide
        self.buffer = DropOldestBuffer(buffer_size)

    def process(self, frame: Any) -> StageResult:
        """Run one frame through all stages inline; return timings."""
        out = StageResult()
        start = time.perf_counter()
        with timed("detect"):
            out.detections = self.detector.detect(frame)
        out.stage_ms["detect"] = (time.perf_counter() - start) * 1000
        # DetectorPort has two live return shapes: DetectionResult (ONNX)
        # and bare List[VehicleDetection] (ultralytics legacy). Normalize
        # once here so every caller sees a list.
        raw = out.detections
        dets = raw.detections if hasattr(raw, "detections") else raw
        start = time.perf_counter()
        with timed("estimate"):
            out.estimate = self.estimator.estimate_from_detections(dets)
        out.stage_ms["estimate"] = (time.perf_counter() - start) * 1000
        if self.decide is not None:
            start = time.perf_counter()
            with timed("decide"):
                out.decision = self.decide(out.estimate)
            out.stage_ms["decide"] = (time.perf_counter() - start) * 1000
        return out

    def submit(self, frame: Any) -> None:
        """Non-blocking enqueue from a capture thread."""
        self.buffer.put(frame)

    def drain(self, limit: Optional[int] = None) -> list[StageResult]:
        """Process buffered frames oldest-first; one result per frame."""
        results = []
        while limit is None or len(results) < limit:
            frame = self.buffer.get()
            if frame is None:
                break
            results.append(self.process(frame))
        return results

    def run_worker(self, stop: threading.Event, idle_s: float = 0.005) -> None:
        """Background-consumer loop for the future edge runner."""
        while not stop.is_set():
            if not self.drain():
                stop.wait(idle_s)
