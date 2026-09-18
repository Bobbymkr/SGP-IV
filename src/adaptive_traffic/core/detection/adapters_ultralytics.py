"""
Ultralytics YOLO Detection Adapter
Heavy imports (ultralytics, torch) are lazy, inside this module only
"""

import logging
from typing import Dict, List, Optional

import cv2
import numpy as np

from adaptive_traffic.config.city_profile import CityProfile
from adaptive_traffic.core.detection.base import DetectorPort
from adaptive_traffic.core.domain import VehicleDetection
from adaptive_traffic.core.monitoring import observe

logger = logging.getLogger(__name__)


class UltralyticsDetector(DetectorPort):
    """YOLOv8-based vehicle detector optimized for traffic monitoring"""

    # Default COCO class IDs for vehicles (used when no city profile)
    DEFAULT_VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck", 1: "bicycle"}

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = "auto",
        image_size: int = 640,
        city_profile: Optional[CityProfile] = None,
    ):
        import torch
        from ultralytics import YOLO

        self.model_path = model_path
        self.iou_threshold = iou_threshold
        self.image_size = image_size
        self.city_profile = city_profile

        # Use city profile for confidence thresholds and class mapping
        if city_profile:
            self.detection_thresholds = city_profile.detection_thresholds
            self.class_mapping = city_profile.class_mapping
            # Use default confidence as fallback
            self.confidence_threshold = confidence_threshold
        else:
            self.detection_thresholds = {}
            self.class_mapping = {}
            self.confidence_threshold = confidence_threshold

        # Setup device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Load model
        logger.info(f"Loading YOLO model from {model_path} on {self.device}")
        self.model = YOLO(model_path)
        self.model.to(self.device)

        # Warm up
        dummy = np.zeros((image_size, image_size, 3), dtype=np.uint8)
        _ = self.model(dummy, verbose=False)

        logger.info("Vehicle detector initialized successfully")

    def _get_threshold(self, class_name: str) -> float:
        """Get confidence threshold for a class"""
        return self.detection_thresholds.get(class_name, self.confidence_threshold)

    @observe("detect")
    def detect(self, frame: np.ndarray) -> List[VehicleDetection]:
        # ponytail: returns List[VehicleDetection] to preserve legacy behavior;
        # wrap in DetectionResult when callers migrate (Phase 5)
        results = self.model(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.image_size,
            verbose=False,
            device=self.device,
        )

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                det = self._box_to_detection(box)
                if det is not None:
                    detections.append(det)

        return detections

    def detect_batch(self, images: List[np.ndarray]) -> List[List[VehicleDetection]]:
        """Detect vehicles in multiple frames"""
        results = self.model(
            images,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.image_size,
            verbose=False,
            device=self.device,
        )

        batch_detections = []
        for result in results:
            detections = []
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    det = self._box_to_detection(box)
                    if det is not None:
                        detections.append(det)
            batch_detections.append(detections)

        return batch_detections

    def _box_to_detection(self, box) -> VehicleDetection | None:
        class_id = int(box.cls[0])

        # Determine class name - use city profile mapping if available
        if self.city_profile and self.class_mapping:
            class_name = self.class_mapping.get(
                class_id, self.DEFAULT_VEHICLE_CLASSES.get(class_id, "unknown")
            )
        else:
            class_name = self.DEFAULT_VEHICLE_CLASSES.get(class_id)

        # Filter for vehicle classes only
        if class_name is None or class_name == "unknown":
            return None

        confidence = float(box.conf[0])
        threshold = self._get_threshold(class_name)
        if confidence < threshold:
            return None

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        return VehicleDetection(
            class_id=class_id,
            class_name=class_name,
            confidence=confidence,
            bbox=(x1, y1, x2, y2),
            center=(center_x, center_y),
        )


class MultiCameraDetector:
    """Multi-camera vehicle detection with fusion"""

    def __init__(self, camera_configs: List[Dict]):
        self.detectors = {}
        for config in camera_configs:
            camera_id = config["camera_id"]
            self.detectors[camera_id] = UltralyticsDetector(
                model_path=config.get("model_path", "yolov8n.pt"),
                confidence_threshold=config.get("confidence", 0.5),
                iou_threshold=config.get("iou", 0.45),
                device=config.get("device", "auto"),
            )

    def detect_all(self, images: Dict[str, np.ndarray]) -> Dict[str, List[VehicleDetection]]:
        """Run detection on all cameras"""
        results = {}
        for camera_id, image in images.items():
            if camera_id in self.detectors:
                results[camera_id] = self.detectors[camera_id].detect(image)
        return results


def create_detector(config: Dict) -> UltralyticsDetector:
    """Factory function to create vehicle detector"""
    return UltralyticsDetector(
        model_path=config.get("model_path", "yolov8n.pt"),
        confidence_threshold=config.get("confidence_threshold", 0.5),
        iou_threshold=config.get("iou_threshold", 0.45),
        device=config.get("device", "auto"),
        image_size=config.get("image_size", 640),
    )
