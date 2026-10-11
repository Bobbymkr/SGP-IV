# 01 — Detection: what this project did

## Headline (say this)
YOLOv8n, India-tuned, **0.8477 mAP50 on full 10k BMD-45 val** (+0.0184 over loop-8 0.8293). Ships as fp32 ONNX 640px, **5.1–8.2 fps CPU** on low-tier edge. int8 voided — honest caveat, fp32 is the demo. Re-validated 2026-10-11: fp32 0.8469 full-val; v6b int8 alive but unpromoted (see 08).

## Per-class mAP50 (from registry metadata)
car .9189, auto .9171, motorcycle .8887, bus .8460, truck .8294, bicycle .6859. Bicycle is the weak tail — say it, show one miss frame.

## How detection runs (demo path)
`OnnxDetector` (`src/adaptive_traffic/core/detection/adapters_onnx.py:19`): loads `models/registry/<name>/` via `metadata.json`, BGR→RGB, /255, NCHW, NMS conf 0.5 / IoU 0.45, city-profile thresholds. Backends: ultralytics (train) / onnx (CPU) / tensorrt (Jetson, falls back to onnx).

## Tier truth
`configs/device.yaml:12-22` — active low, onnx, `prefer_int8:false` (2026-09-13 static int8 emits all-zero scores). Mid/high share the same nano registry until a yolov8s exists; they differ by runtime/thresholds only.

## Trace
`models/registry/india-yolov8n-final/metadata.json:28-47`, `model.onnx` 12,269,662 B; `docs/INDUSTRY_DEMO.md:7-8`; `docs/BENCHMARKS.md` Detection + Detector QA; `scripts/bench_detect.py:1-9`.
