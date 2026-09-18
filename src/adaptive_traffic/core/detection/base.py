"""
Detector Port
Backend-agnostic vehicle detection contract
"""

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from adaptive_traffic.config.city_profile import CityProfile
from adaptive_traffic.core.domain import DetectionResult


class DetectorPort(ABC):
    """Port for pluggable detection backends"""

    @abstractmethod
    def detect(self, frame: np.ndarray) -> DetectionResult:
        """Detect vehicles in a single frame"""
        pass

    @classmethod
    def create(cls, config: dict, city_profile: Optional[CityProfile] = None) -> "DetectorPort":
        backend = config.get("backend", config.get("detection_backend", "ultralytics"))
        if backend == "ultralytics":
            from adaptive_traffic.core.detection.adapters_ultralytics import UltralyticsDetector

            return UltralyticsDetector(
                model_path=config.get("model_path", "yolov8n.pt"),
                confidence_threshold=config.get("confidence_threshold", 0.5),
                iou_threshold=config.get("iou_threshold", 0.45),
                device=config.get("device", "auto"),
                image_size=config.get("image_size", 640),
                city_profile=city_profile,
            )
        if backend == "onnx":
            from adaptive_traffic.core.detection.adapters_onnx import OnnxDetector

            if "registry_dir" in config:
                return OnnxDetector.from_registry(
                    config["registry_dir"],
                    city_profile=city_profile,
                    **{
                        k: config[k]
                        for k in ("prefer_int8", "confidence_threshold", "providers")
                        if k in config
                    },
                )
            return OnnxDetector(
                model_path=config.get(
                    "                model_path", "models/registry/india-yolov8n-final/model-int8.onnx"
                ),
                confidence_threshold=config.get("confidence_threshold", 0.5),
                iou_threshold=config.get("iou_threshold", 0.45),
                providers=config.get("providers"),
                city_profile=city_profile,
            )
        if backend == "tensorrt":
            # ponytail: adapter pending real Jetson hardware; fall back to ONNX runtime
            # (device.yaml documents this). Replace with adapters_tensorrt when available.
            import warnings

            warnings.warn(
                "tensorrt backend not available; falling back to onnx. "
                "Build the TRT adapter on-device to use fp16.",
                RuntimeWarning,
                stacklevel=2,
            )
            config = {**config, "backend": "onnx", "prefer_int8": False}
            return cls.create(config, city_profile)
        raise ValueError(f"Unknown detection backend: {backend}")
