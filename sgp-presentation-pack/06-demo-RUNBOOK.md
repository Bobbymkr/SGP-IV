# 06 — Live CPU demo RUNBOOK (dataset frames, offline-safe)

## Setup (once, 5 min)
`.venv\Scripts\python.exe -c "import onnxruntime, ultralytics; print('ok')"`
Confirm: `models/registry/india-yolov8n-final/model.onnx` present (copied to `sgp-presentation-pack/models-copy/`).

## Frames (training images work — approved)
- Pool A: `data/synthetic_india_yolo/images/val/` (from 4032-file pool)
- Pool B: `data/trafficcam/images/val/` (from 2340-file pool)
- Filenames carry tags: `..._3way_clear_aggressive_metro_...`, `..._heavy_monsoon_...` — call one clear + one monsoon for contrast.
- If a val/ subdir is empty, fall back to `images/test/` or top-level `images/` (flat layout varies). Pick 20 files, copy to `C:\Temp\sgp-demo-frames\` so the demo dir is stable.

## Command 1 — detection (60-90s)
`.venv\Scripts\python.exe scripts\bench_detect.py --frames-dir C:\Temp\sgp-demo-frames --max-frames 20`
Say: fp32 CPU 5–8 fps expected; histogram + per-class counts print — det_total=0 would be visible, not silent. Point at auto/moto rows (India mix).

## Command 2 — closed loop (60s)
`.venv\Scripts\python.exe scripts\run_closed_loop.py --frames-dir C:\Temp\sgp-demo-frames --max-frames 5 --city mumbai`
Say: same frames → queue → green → mock STMP actuate; `--ntcip-ip` aims same loop at real controller (no code change). Exit 1 if any frame fails to actuate.

## If hall Wi-Fi/GPU dies
- Pre-run both commands once, save console output to `refs/demo-output.txt`.
- Backup: `ui/replay.py` or `docs/demo-deck/bmd-finale.html` frame walk.
- Caveat line: fp32 ships; shipped int8 dead (all-zero), v6b alive but unpromoted (KEEP by 0.0045) — `configs/device.yaml:18-21`.
