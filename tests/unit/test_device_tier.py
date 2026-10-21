"""device.yaml reader: explicit tiers pass through, garbage fails safe to low."""

from adaptive_traffic.config.device_tier import read_tier


def _write(tmp_path, text):
    p = tmp_path / "device.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_explicit_low_passes_backend_through(tmp_path):
    p = _write(tmp_path, "active_tier: low\ndetection:\n  low:\n    backend: onnx\n    prefer_int8: false\n")
    tier, cfg = read_tier(p)
    assert tier == "low" and cfg["backend"] == "onnx" and cfg["prefer_int8"] is False


def test_garbage_fails_safe_to_low(tmp_path):
    tier, cfg = read_tier(_write(tmp_path, "active_tier: jetson-ultra\n"))
    assert tier == "low" and cfg["backend"] == "onnx"


def test_missing_file_fails_safe(tmp_path):
    assert read_tier(tmp_path / "nope.yaml")[0] == "low"


def test_auto_resolves_on_this_box(tmp_path):
    tier, _ = read_tier(_write(tmp_path, "active_tier: auto\ndetection:\n  low:\n    backend: onnx\n"))
    assert tier in ("low", "mid", "high")
