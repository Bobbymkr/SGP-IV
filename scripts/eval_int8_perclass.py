"""Per-class parity: fp32 vs v3-dynamic on identical 20 TrafficCAM frames."""
import json, sys
from collections import Counter
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
from footage import load_frames
from adaptive_traffic.core.detection.adapters_onnx import OnnxDetector

META = "models/registry/india-yolov8n-final/metadata.json"
fs, _, _ = load_frames("data/trafficcam/images/val", 20)
for tag, mp in [("fp32", "models/registry/india-yolov8n-final/model.onnx"),
                ("v3-dynamic", "models/registry/india-yolov8n-final-candidates/model-v3-dynamic.onnx")]:
    d = OnnxDetector(model_path=mp, metadata_path=META, confidence_threshold=0.25)
    c = Counter()
    for f in fs:
        for det in d.detect(f).detections:
            c[det.class_name] += 1
    print(tag, dict(c), "total=", sum(c.values()))
