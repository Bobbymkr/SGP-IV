"""Last static variant: Percentile calibrator + QOperator, 50 frames. Lighter than entropy."""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from requant_int8_v2 import build_calib_list, Reader

import onnxruntime as ort
from onnxruntime.quantization import (QuantFormat, QuantType, CalibrationMethod,
                                      quant_pre_process, quantize_static)
SRC = str(ROOT / "models/registry/india-yolov8n-final/model.onnx")
OUT = ROOT / "models/registry/india-yolov8n-final-candidates/model-v4-percentile-qop.onnx"
PRE = ROOT / "models/registry/india-yolov8n-final-candidates/_pre_percentile.onnx"
META = str(ROOT / "models/registry/india-yolov8n-final/metadata.json")

calib, _ = build_calib_list(200)
calib50 = calib[:50]
sess = ort.InferenceSession(SRC, providers=["CPUExecutionProvider"])
iname = sess.get_inputs()[0].name
t0 = time.time()
quant_pre_process(SRC, str(PRE))
quantize_static(str(PRE), str(OUT), Reader(calib50, iname),
                calibrate_method=CalibrationMethod.Percentile,
                quant_format=QuantFormat.QOperator,
                activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8,
                per_channel=False)
print(f"quant done in {time.time()-t0:.0f}s")

from adaptive_traffic.core.detection.adapters_onnx import OnnxDetector
from footage import load_frames
fs, _, _ = load_frames(str(ROOT / "data/trafficcam/images/val"), 20)
for tag, mp in [("fp32", SRC), ("pct50-qop", str(OUT))]:
    d = OnnxDetector(model_path=mp, metadata_path=META, confidence_threshold=0.25)
    t1 = time.perf_counter()
    counts = [len(d.detect(f).detections) for f in fs]
    dt = time.perf_counter() - t1
    print(tag, "det_total=", sum(counts), "zeros=", sum(1 for c in counts if c == 0),
          "max=", max(counts), "fps=", round(len(fs) / dt, 2))
