"""TensorRT adapter: provider gating, engine-cache key, factory fallback.

All hardware-dependent paths are mocked — these prove the wiring (provider
options, fp32 selection, cache key, graceful fallback), not on-device
latency. That needs a Jetson (see docs/device-tiers.md).
"""

import re

import pytest

from adaptive_traffic.core.detection.adapters_onnx import OnnxDetector
from adaptive_traffic.core.detection.adapters_tensorrt import (
    TensorRTDetector,
    device_tag,
    has_trt_provider,
    trt_cache_dir_for,
)
from adaptive_traffic.core.detection.base import DetectorPort

FINAL = "models/registry/india-yolov8n-final"
TRT_PROVIDERS = ["TensorrtExecutionProvider", "CUDAExecutionProvider",
                 "CPUExecutionProvider"]
CPU_PROVIDERS = ["CPUExecutionProvider"]


class FakeInput:
    name = "images"


class FakeSession:
    created = []

    def __init__(self, *args, **kwargs):
        FakeSession.created.append((args, kwargs))

    def get_inputs(self):
        return [FakeInput()]


def _mock_ort(monkeypatch, providers):
    import onnxruntime

    monkeypatch.setattr(onnxruntime, "get_available_providers",
                        lambda: providers)
    return onnxruntime


@pytest.fixture
def trt_available(monkeypatch, tmp_path):
    ort = _mock_ort(monkeypatch, TRT_PROVIDERS)
    monkeypatch.setattr(ort, "InferenceSession", FakeSession)
    FakeSession.created.clear()
    return tmp_path


def test_provider_gate(monkeypatch):
    _mock_ort(monkeypatch, CPU_PROVIDERS)
    assert not has_trt_provider()
    _mock_ort(monkeypatch, TRT_PROVIDERS)
    assert has_trt_provider()


def test_cache_dir_keyed_by_device_and_model(tmp_path):
    tag = device_tag()
    assert tag and "/" not in tag
    cache = trt_cache_dir_for(f"{FINAL}/model.onnx", root=str(tmp_path))
    assert cache.parent == tmp_path
    assert cache.name.startswith(f"{tag}_")
    assert re.fullmatch(r"[0-9a-f]{12}", cache.name.rsplit("_", 1)[1])


def test_from_registry_needs_provider(monkeypatch):
    _mock_ort(monkeypatch, CPU_PROVIDERS)
    with pytest.raises(RuntimeError):
        TensorRTDetector.from_registry(FINAL)


def test_from_registry_selects_fp32_and_trt_options(trt_available):
    det = TensorRTDetector.from_registry(
        FINAL, trt_cache_dir=str(trt_available))
    assert det.model_path.name == "model.onnx"
    providers = FakeSession.created[-1][1]["providers"]
    name, opts = providers[0]
    assert name == "TensorrtExecutionProvider"
    assert opts["trt_fp16_enable"] == "1"
    assert opts["trt_engine_cache_enable"] == "1"
    assert opts["trt_engine_cache_path"].startswith(str(trt_available))
    from pathlib import Path
    assert Path(opts["trt_engine_cache_path"]).is_dir()


def test_from_registry_honors_prefer_int8(trt_available):
    det = TensorRTDetector.from_registry(FINAL, prefer_int8=True,
                                         trt_cache_dir=str(trt_available))
    assert det.model_path.name == "model-int8.onnx"


def test_factory_falls_back_without_provider(monkeypatch):
    _mock_ort(monkeypatch, CPU_PROVIDERS)
    with pytest.warns(RuntimeWarning):
        det = DetectorPort.create(
            {"backend": "tensorrt", "registry_dir": FINAL})
    assert type(det) is OnnxDetector  # real fp32 fallback, loaded on CPU


def test_factory_uses_trt_when_available(trt_available):
    det = DetectorPort.create({"backend": "tensorrt", "registry_dir": FINAL,
                               "trt_cache_dir": str(trt_available)})
    assert isinstance(det, TensorRTDetector)


def test_factory_nonregistry_trt_path(trt_available):
    det = DetectorPort.create({"backend": "tensorrt",
                               "model_path": f"{FINAL}/model.onnx"})
    assert isinstance(det, TensorRTDetector)
