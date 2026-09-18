"""Phase-boundary latency histograms (MASTER_PLAN Phase 5.4).

Four stages mirror the edge control loop:
detect -> estimate -> decide -> actuate.
Same boundaries the benches measure
(bench_detect / bench_decide / eval dec_p95),
so Prometheus and the scorecard never disagree about what a "stage" is.

Usage: one decorator per boundary method, nothing else to wire::

    from adaptive_traffic.core.monitoring import observe

    class OnnxDetector(DetectorPort):
        @observe("detect")
        def detect(self, frame): ...

Zero new dependencies (prometheus-client is a core dep). When
``settings.prometheus_enabled`` is False the decorator is a single flag
check — no timer, no observation. Scrape via ``GET /api/v1/health/metrics``.
"""

import contextlib
import functools
import time
from typing import Callable, Iterator

from prometheus_client import Histogram

from adaptive_traffic.config.settings import settings

# Buckets span the measured operating points (docs/BENCHMARKS.md):
# detect ~200ms CPU-int8 down to ~10ms GPU; estimate/decide sub-ms to ~1ms;
# actuate from sim microseconds to STMP network retries in seconds.
_BUCKETS = {
    "detect": (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    "estimate": (0.00025, 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025),
    "decide": (0.00001, 0.000025, 0.00005, 0.0001, 0.00025, 0.0005,
               0.001, 0.005),
    "actuate": (0.00001, 0.0001, 0.001, 0.01, 0.1, 1.0, 5.0),
}

STAGES: dict[str, Histogram] = {
    stage: Histogram(f"traffic_{stage}_seconds",
                     f"Latency of pipeline stage: {stage}",
                     buckets=buckets)
    for stage, buckets in _BUCKETS.items()
}


def observe(stage: str) -> Callable:
    """Decorate a boundary method to observe its stage histogram."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not settings.prometheus_enabled:
                return fn(*args, **kwargs)
            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                STAGES[stage].observe(time.perf_counter() - start)

        return wrapper

    return decorator


@contextlib.contextmanager
def timed(stage: str) -> Iterator[None]:
    """Context-manager form of :func:`observe` for inline pipeline stages."""
    if not settings.prometheus_enabled:
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        STAGES[stage].observe(time.perf_counter() - start)
