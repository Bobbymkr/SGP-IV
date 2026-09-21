"""Regression tests for OnnxDetector export-layout handling.

Locks in a real bug from the first trained-artifact run: ultralytics ONNX
export emits (1, 4+nc, N); the adapter assumed (N, 4+nc) and raised
"Unexpected ONNX output shape (10, 8400) for 6 classes".
"""

import numpy as np
import pytest

from adaptive_traffic.core.detection.adapters_onnx import OnnxDetector

CLASSES = ["car", "motorcycle", "bus", "truck", "bicycle", "auto"]


def _detector():
    det = OnnxDetector.__new__(OnnxDetector)
    det.class_names = CLASSES
    det.imgsz = 640
    det.confidence_threshold = 0.5
    det.iou_threshold = 0.45
    det.detection_thresholds = {}
    det.city_profile = None
    det.class_mapping = {}
    return det


def _export_layout_row():
    """One hot 'auto' detection in (4+nc,) column form: cx,cy,w,h + 6 scores."""
    col = np.zeros(10, dtype=np.float32)
    col[:4] = [320.0, 320.0, 100.0, 100.0]
    col[4 + 5] = 0.9  # class 5 == auto
    return col


def test_decode_native_layout():
    det = _detector()
    preds = np.zeros((3, 10), dtype=np.float32)
    preds[0] = _export_layout_row()
    boxes, scores, ids = det._decode(preds)
    assert len(boxes) == 1
    assert int(ids[0]) == 5
    assert scores[0] == pytest.approx(0.9)


def test_detect_transposes_export_layout():
    det = _detector()
    out = np.zeros((1, 10, 8400), dtype=np.float32)
    out[0, :, 0] = _export_layout_row()

    class FakeSession:
        def run(self, _outputs, _inputs):
            return [out]

    det.session = FakeSession()
    det.input_name = "images"

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    res = det.detect(frame)
    assert len(res.detections) == 1
    assert res.detections[0].class_name == "auto"


def test_detect_emits_xyxy_corners_like_ultralytics():
    """Contract: bbox is (x1, y1, x2, y2). The estimator unpacks corners, so
    an (x, y, w, h) box here silently empties every queue downstream."""
    det = _detector()
    out = np.zeros((1, 10, 8400), dtype=np.float32)
    out[0, :, 0] = _export_layout_row()  # cx=320, cy=320, w=h=100

    class FakeSession:
        def run(self, _outputs, _inputs):
            return [out]

    det.session = FakeSession()
    det.input_name = "images"

    frame = np.zeros((480, 640, 3), dtype=np.uint8)  # scale_x=1.0, scale_y=0.75
    (d,) = det.detect(frame).detections
    assert d.bbox == (270, 202, 370, 277)
    assert d.center == (320, 239)
    x1, y1, x2, y2 = d.bbox
    assert x2 > x1 and y2 > y1  # corners, not (x, y, w, h)
