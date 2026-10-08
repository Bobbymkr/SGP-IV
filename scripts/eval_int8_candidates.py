"""Eval int8 candidates head-to-head on identical TrafficCAM frames. No re-quant, no registry touch."""
import json, sys, time
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
from footage import load_frames
from adaptive_traffic.core.detection.adapters_onnx import OnnxDetector

META = "models/registry/india-yolov8n-final/metadata.json"
MODELS = {
    "fp32-canonical": "models/registry/india-yolov8n-final/model.onnx",
    "int8-shipped-dead": "models/registry/india-yolov8n-final/model-int8.onnx",
    "v2-static-minmax-qdq": "models/registry/india-yolov8n-final-candidates/model-v2-static-minmax-qdq.onnx",
    "v3-dynamic": "models/registry/india-yolov8n-final-candidates/model-v3-dynamic.onnx",
}
fs, _, _ = load_frames("data/trafficcam/images/val", 20)
out = {}
for tag, mp in MODELS.items():
    try:
        d = OnnxDetector(model_path=mp, metadata_path=META, confidence_threshold=0.25)
        t0 = time.perf_counter()
        counts = [len(d.detect(f).detections) for f in fs]
        dt = time.perf_counter() - t0
        out[tag] = {"det_total": sum(counts), "zeros": sum(1 for c in counts if c == 0),
                    "max": max(counts), "fps": round(len(fs) / dt, 2),
                    "degenerate": sum(counts) == 0}
    except Exception as e:  # noqa: BLE001
        out[tag] = {"error": repr(e)[:200]}
print(json.dumps(out, indent=2))
