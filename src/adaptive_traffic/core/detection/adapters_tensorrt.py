"""TensorRT Detection Adapter (Jetson fp16 path).

Reuses OnnxDetector end-to-end and only swaps the execution provider to
ONNX Runtime's TensorrtExecutionProvider with fp16 + on-device engine cache
(``models/trt_cache/<device>_<modelhash>/`` — first boot builds, later boots
reload). No pycuda, no hand-rolled engine code.
# ponytail: native TRT+pycuda only if ORT-TRT ever proves wall-bound.

Fail-closed: constructing without the TRT provider raises RuntimeError and
DetectorPort.create falls back to plain ONNX with a warning, so the same
config runs on a Jetson and on a CPU-only box.
"""

import hashlib
import platform
import re
from pathlib import Path
from typing import Optional

from adaptive_traffic.config.city_profile import CityProfile
from adaptive_traffic.core.detection.adapters_onnx import OnnxDetector

DEFAULT_TRT_CACHE_ROOT = "models/trt_cache"


def has_trt_provider() -> bool:
    """True when onnxruntime exposes TensorrtExecutionProvider on this box."""
    try:
        import onnxruntime
    except ImportError:
        return False
    return "TensorrtExecutionProvider" in onnxruntime.get_available_providers()


def device_tag() -> str:
    """Short device slug for the engine-cache key (Jetson model or arch)."""
    try:
        raw = Path("/proc/device-tree/model").read_bytes().split(b"\x00")[0]
        slug = re.sub(r"[^a-z0-9]+", "-", raw.decode().lower()).strip("-")
        if slug:
            return slug
    except OSError:
        pass
    return platform.machine().lower()


def trt_cache_dir_for(model_path: str,
                      root: str = DEFAULT_TRT_CACHE_ROOT) -> Path:
    """Cache dir keyed by device + model hash, per MASTER_PLAN Phase 1.5."""
    digest = hashlib.sha1(Path(model_path).read_bytes()).hexdigest()[:12]
    return Path(root) / f"{device_tag()}_{digest}"


class TensorRTDetector(OnnxDetector):
    """ONNX Runtime detector with the TensorRT fp16 provider + engine cache."""

    def __init__(
        self,
        model_path: str,
        metadata_path: Optional[str] = None,
        trt_cache_dir: Optional[str] = None,
        providers: Optional[list] = None,
        city_profile: Optional[CityProfile] = None,
        **kwargs,
    ):
        if not has_trt_provider():
            raise RuntimeError(
                "TensorrtExecutionProvider unavailable on this box; "
                "use the onnx backend instead."
            )
        if providers is None:
            cache = (Path(trt_cache_dir) if trt_cache_dir
                     else trt_cache_dir_for(model_path))
            cache.mkdir(parents=True, exist_ok=True)
            providers = [
                ("TensorrtExecutionProvider", {
                    "trt_fp16_enable": "1",
                    "trt_engine_cache_enable": "1",
                    "trt_engine_cache_path": str(cache),
                }),
                "CUDAExecutionProvider",
                "CPUExecutionProvider",
            ]
        super().__init__(
            model_path=model_path,
            metadata_path=metadata_path,
            providers=providers,
            city_profile=city_profile,
            **kwargs,
        )

    @classmethod
    def from_registry(
        cls,
        registry_dir: str,
        prefer_int8: bool = False,
        trt_cache_dir: Optional[str] = None,
        city_profile: Optional[CityProfile] = None,
        **kwargs,
    ) -> "TensorRTDetector":
        # fp16 needs the fp32 source; an int8 file with fp16 enabled is a
        # wrong combo, so fp32 wins unless it is missing from the registry.
        d = Path(registry_dir)
        model = (d / "model.onnx" if (d / "model.onnx").exists()
                 else d / "model-int8.onnx")
        if prefer_int8 and (d / "model-int8.onnx").exists():
            model = d / "model-int8.onnx"
        return cls(
            model_path=str(model),
            metadata_path=str(d / "metadata.json"),
            trt_cache_dir=trt_cache_dir,
            city_profile=city_profile,
            **kwargs,
        )
