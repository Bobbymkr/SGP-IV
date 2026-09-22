"""Phase-boundary histograms: recorded when enabled, silent when disabled."""

import asyncio
import re

from prometheus_client import generate_latest

from adaptive_traffic.config.settings import settings
from adaptive_traffic.core.monitoring import observe, timed


def _count(stage: str) -> float:
    m = re.search(rf"^traffic_{stage}_seconds_count (\S+)$", generate_latest().decode(), re.M)
    return float(m.group(1)) if m else 0.0


def test_observe_records_call():
    before = _count("decide")

    @observe("decide")
    def fn():
        return 42

    assert fn() == 42
    assert _count("decide") == before + 1


def test_timed_records_block():
    before = _count("estimate")
    with timed("estimate"):
        pass
    assert _count("estimate") == before + 1


def test_disabled_records_nothing():
    before = _count("actuate")
    old, settings.prometheus_enabled = settings.prometheus_enabled, False
    try:

        @observe("actuate")
        def fn():
            return 1

        fn()
        with timed("actuate"):
            pass
    finally:
        settings.prometheus_enabled = old
    assert _count("actuate") == before


def test_metrics_endpoint_exposes_histograms():
    from adaptive_traffic.api.routes.health import prometheus_metrics

    resp = asyncio.run(prometheus_metrics())
    assert resp.status_code == 200
    assert b"traffic_detect_seconds" in resp.body
