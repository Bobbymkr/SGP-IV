"""
Vehicle Detection Module (backward-compat shim)
Concrete implementation moved to adapters_ultralytics.py
"""

from adaptive_traffic.core.detection.adapters_ultralytics import (
    MultiCameraDetector,
    UltralyticsDetector,
    create_detector,
)
from adaptive_traffic.core.detection.base import DetectorPort
from adaptive_traffic.core.domain import DetectionResult, VehicleDetection

VehicleDetector = UltralyticsDetector

__all__ = [
    "VehicleDetection",
    "DetectionResult",
    "DetectorPort",
    "UltralyticsDetector",
    "MultiCameraDetector",
    "create_detector",
    "VehicleDetector",
]
