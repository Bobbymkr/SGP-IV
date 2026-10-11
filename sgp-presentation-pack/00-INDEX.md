# SGP Presentation Pack — Adaptive Traffic Signal Timer

Target: 15–20 min + live CPU detection demo. 5 days to SGP.
Commit: `4f7176e`. Models: full copy in `models-copy/`. Demo frames: training images (see `06-demo-RUNBOOK.md`).
Updates 2026-10-11: anchor KEEP, Surat 15/15, v6b alive-unpromoted, val notebook, STMP parser, per-camera geometry (see TRACE).

## Contents

| File | Beat (time) | One-liner |
|------|-------------|-----------|
| `01-detection.md` | Detector 3 min | YOLOv8n finale 0.8477 mAP50, fp32 live |
| `02-dataset.md` | Procedure 4 min | BMD-45 loops + reasoning, TrafficCAM check |
| `03-india.md` | India tuning 3 min | 6-class + city profiles + NTCIP |
| `04-streaming.md` | Streaming 4 min | frame → green, drop-oldest, closed loop |
| `05-other-parts.md` | Rest 3 min | decide, sim, API/UI, eval, ship |
| `06-demo-RUNBOOK.md` | Live demo | 2 commands, offline-safe, dataset frames |
| `07-slides-outline.md` | Slides | 12-slide plan extending bmd-finale.html |
| `TRACE.md` | Appendix | claim → file:line |
| `models-copy/` | Artifact | model.onnx 12.2 MB + model-int8.onnx + metadata.json |
| `refs/` | Excerpts | metadata, device.yaml, scenarios, data.yaml |

## Rehearsal order

1. Read 01→04 (10 min). 2. Run RUNBOOK once (20 min). 3. Build slides from 07.
