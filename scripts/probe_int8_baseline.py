"""Probe fp32 vs int8 on same frames. Usage: probe_int8_baseline.py <frames-dir> [max-frames]"""
import sys
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
from footage import load_frames
from adaptive_traffic.core.detection.adapters_onnx import OnnxDetector

frames_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\Temp\sgp-demo-frames"
maxf = int(sys.argv[2]) if len(sys.argv) > 2 else 20
fs, ns, sk = load_frames(frames_dir, maxf)
for tag, prefer in [("fp32", False), ("int8", True)]:
    d = OnnxDetector.from_registry("models/registry/india-yolov8n-final", prefer_int8=prefer)
    print(tag, "model=", d.model_path.name)
    totals, per = 0, []
    for f in fs:
        r = d.detect(f)
        per.append(len(r.detections))
        totals += len(r.detections)
    per_sorted = sorted(per)
    print(tag, "det_total=", totals, "min=", per_sorted[0], "max=", per_sorted[-1],
          "zeros=", sum(1 for x in per if x == 0))
