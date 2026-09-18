"""
ONNX Detection Adapter
CPU/NPU backend — loads models from models/registry/<name>/ via metadata.json.
Works with fp32 and int8-quantized exports from the training pipeline.
"""

import json
from pathlib import Path
from typing import Dict, Optional

import numpy as np

from adaptive_traffic.config.city_profile import CityProfile
from adaptive_traffic.core.detection.base import DetectorPort
from adaptive_traffic.core.domain import DetectionResult, VehicleDetection


class OnnxDetector(DetectorPort):
    """ONNX Runtime vehicle detector (CPU/NPU providers)"""

    def __init__(
        self,
        model_path: str = "models/registry/india-yolov8n-final/model-int8.onnx",
        metadata_path: Optional[str] = None,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        providers: Optional[list] = None,
        city_profile: Optional[CityProfile] = None,
    ):
        import onnxruntime

        self.model_path = Path(model_path)
        if metadata_path is None:
            metadata_path = str(self.model_path.parent / "metadata.json")
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        self.class_names = self.metadata["classes"]
        self.imgsz = self.metadata.get("imgsz", 640)
        self.iou_threshold = iou_threshold
        self.city_profile = city_profile

        # Use city profile for confidence thresholds
        if city_profile:
            self.detection_thresholds = city_profile.detection_thresholds
            self.class_mapping = city_profile.class_mapping
            self.confidence_threshold = confidence_threshold
        else:
            self.detection_thresholds = {}
            self.class_mapping = {}
            self.confidence_threshold = confidence_threshold

        if providers is None:
            available = onnxruntime.get_available_providers()
            providers = [
                p for p in ("CUDAExecutionProvider", "CPUExecutionProvider") if p in available
            ]
        self.session = onnxruntime.InferenceSession(str(self.model_path), providers=providers)
        self.input_name = self.session.get_inputs()[0].name

    @classmethod
    def from_registry(
        cls,
        registry_dir: str,
        prefer_int8: bool = True,
        city_profile: Optional[CityProfile] = None,
        **kwargs,
    ) -> "OnnxDetector":
        d = Path(registry_dir)
        model = (
            d / "model-int8.onnx"
            if (prefer_int8 and (d / "model-int8.onnx").exists())
            else d / "model.onnx"
        )
        return cls(
            model_path=str(model),
            metadata_path=str(d / "metadata.json"),
            city_profile=city_profile,
            **kwargs,
        )

    def _get_threshold(self, class_name: str) -> float:
        """Get confidence threshold for a class"""
        return self.detection_thresholds.get(class_name, self.confidence_threshold)

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        import cv2

        img = cv2.resize(frame, (self.imgsz, self.imgsz))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        return np.ascontiguousarray(img.transpose(2, 0, 1)[None])

    def detect(self, frame: np.ndarray) -> DetectionResult:
        import time

        t0 = time.perf_counter()
        blob = self._preprocess(frame)
        preds = self.session.run(None, {self.input_name: blob})[0][0]
        nc = len(self.class_names)
        if preds.shape[0] == 4 + nc and preds.shape[1] != 4 + nc:
            preds = preds.T  # ultralytics ONNX export layout is (4+nc, N)

        boxes_raw, scores_raw, class_ids = self._decode(preds)
        keep = self._nms(boxes_raw, scores_raw)

        detections = []
        h, w = frame.shape[:2]
        scale_x, scale_y = w / self.imgsz, h / self.imgsz
        for i in keep:
            cx, cy, bw, bh = boxes_raw[i]
            class_id = int(class_ids[i])
            class_name = self.class_names[class_id]
            confidence = float(scores_raw[i])

            # Use city profile for class mapping if available
            if self.city_profile and self.class_mapping:
                mapped_name = self.class_mapping.get(class_id, class_name)
            else:
                mapped_name = class_name

            threshold = self._get_threshold(mapped_name)
            if confidence < threshold:
                continue

            detections.append(
                VehicleDetection(
                    class_id=class_id,
                    class_name=mapped_name,
                    confidence=confidence,
                    bbox=(
                        int((cx - bw / 2) * scale_x),
                        int((cy - bh / 2) * scale_y),
                        int(bw * scale_x),
                        int(bh * scale_y),
                    ),
                    center=(int(cx * scale_x), int(cy * scale_y)),
                )
            )

        return DetectionResult(
            frame_id=-1,
            timestamp=t0,
            detections=detections,
            processing_time=time.perf_counter() - t0,
            image_shape=(h, w),
        )

    def _decode(self, preds: np.ndarray):
        # ultralytics ONNX export layout: rows of [cx, cy, w, h, obj_conf?, classes...]
        # v8 export has no objectness: [cx, cy, w, h, nc...] then per-class scores
        if preds.shape[1] == 4 + len(self.class_names):
            boxes_xywh = preds[:, :4]
            class_scores = preds[:, 4:]
            class_ids = class_scores.argmax(axis=1)
            scores = class_scores.max(axis=1)
        elif preds.shape[1] == 5 + len(self.class_names):
            boxes_xywh = preds[:, :4]
            class_scores = preds[:, 5:]
            class_ids = class_scores.argmax(axis=1)
            scores = class_scores.max(axis=1) * preds[:, 4]
        else:
            raise ValueError(
                f"Unexpected ONNX output shape {preds.shape} for {len(self.class_names)} classes"
            )

        mask = scores >= self.confidence_threshold
        return boxes_xywh[mask], scores[mask], class_ids[mask]

    @staticmethod
    def _nms(boxes: np.ndarray, scores: np.ndarray) -> list:
        import cv2

        if len(boxes) == 0:
            return []
        xyxy = np.stack(
            [
                boxes[:, 0] - boxes[:, 2] / 2,
                boxes[:, 1] - boxes[:, 3] / 2,
                boxes[:, 0] + boxes[:, 2] / 2,
                boxes[:, 1] + boxes[:, 3] / 2,
            ],
            axis=1,
        ).astype(np.float32)
        indices = cv2.dnn.NMSBoxes(
            xyxy.tolist(),
            scores.astype(np.float32).tolist(),
            score_threshold=0.0,
            nms_threshold=0.45,
        )
        return np.array(indices).flatten().tolist()
