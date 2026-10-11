# 08 — int8 verdict: alive, unpromoted (KEEP by 0.0045)

v6b recipe (static MinMax-QDQ backbone, last-20 `/model.22/*` fp32 tail,
200-frame stratified calib) — first static int8 that scores above zero:

| Artifact | BMD-45 full val mAP50 | TrafficCAM-180 mAP50 | fps CPU | Verdict |
|---|---|---|---|---|
| fp32 canonical (`model.onnx`) | 0.8469 (reproduces 0.8477) | 0.4882 | 6.6-10.5 | SHIP — demo + low tier |
| int8 v6b (`model-v6b-*.onnx`) | 0.8224 (-0.0245) | 0.4646 (-0.0236) | 9.4-12.0 | KEEP — misses -0.02 gate by 0.0045 |
| shipped int8 (2026-09-13 static) | all-zero scores | - | - | DEAD — quarantined, never promote |
| v3 dynamic | parity counts | - | ~1 | 10x too slow — reference only |

Why static kept dying: full-static mangles the YOLOv8 DFL+Sigmoid tail
(v2 MinMax all-zero; entropy/percentile OOM on laptop RAM). fp32 tail fixed it;
same -0.024 signature on both datasets = coarse backbone scales, not collapse.
Recipe persisted in `scripts/requant_int8_v2.py`.

## SGP line (say this)

"Static int8 is alive for the first time — near fp32 quality at twice the speed —
but the gate is the gate: fp32 ships, int8 stays staged until it clears -0.02."

## Trace

`evals/results/anchor_bmdval_2026-10-11.txt`; `docs/BENCHMARKS.md` Static-int8 Anchor;
`notebooks/val_int8_drive.ipynb`; `models/registry/india-yolov8n-final-candidates/model-v6b-minmax-qdq-fp32tail-200f.onnx`.
