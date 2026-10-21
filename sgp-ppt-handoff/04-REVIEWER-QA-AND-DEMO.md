# 04 — Reviewer QA + Demo Runbook (for PPT agent: add backup slide + notes)

## Hard questions + 1-line answers (put in speaker notes, not on slides)
1. Why not int8? Old int8 dead all-zero; v6b alive but -0.0245 vs -0.02 gate, miss by 0.0045, so fp32 ships. Src: `configs/device.yaml:18-21`.
2. Real footage? Yes 180 TrafficCAM frames, det>0 every frame, 5.1-8.2 fps. Queue RMSE 28.9 is proxy (labels count all cars, estimator counts queue-zone only) — not actionable. Honest qerr needs hand-count CSV.
3. Incidents real? No — synthetic-approx (sensor_failure->waterlogged, lane_block->0.3x rate, rally/cattle/vip pins). Labeled in every scorecard `notes` + `incident_model` fields. Never lose 19-75%.
4. Live camera? No. Primitives tested (`test_pipeline.py` 7, worker thread), no RTSP caller. That is next slice.
5. Real signal box? No. Mock STMP + 9 loopback wire tests (found 2 real OID/length bugs). Handoff is one flag: `--ntcip-ip <ip>`.
6. Jetson speed? Code-complete (ORT TRT-EP fp16 + cache), fallback tested on CPU, on-device latency pending hardware.
7. Why bicycle weak? 0.6859 — small objects, recall is lever (P 0.836 R 0.384 F1 0.527 @0.25). Say it, show miss frame.
8. Contribution? Contract -> 8 loops -> finale polish -> fp32 registry -> eval + closed-loop + city profiles, all switchable via `device.yaml` / city file alone.

## Demo runbook (slides 9-10)

**Fastest path - the dashboard does the whole demo in one click:**
`.venv\Scripts\python.exe -m streamlit run src/adaptive_traffic/ui/app.py --server.port 8503`
then open http://localhost:8503 -> **Live Demo** -> **Run real pipeline (photos to AI to green)**.
It runs the real detector on real TrafficCAM frames and prints fps, cars found and
actuated count. The run is cancellable, and the page shows the last run + history.
Screenshots of every page are in `ui-screens/`.

Cmd0 (60-90s, same engine, terminal): `.venv\Scripts\python.exe scripts\demo_sgp.py --city mumbai --max-frames 20`

Setup once (5 min): `.venv\Scripts\python.exe -c "import onnxruntime, ultralytics; print('ok')"` + confirm `models/registry/india-yolov8n-final/model.onnx` present (copy in `sgp-presentation-pack/models-copy/`).
Frames: `data/synthetic_india_yolo/images/val/` (4032 pool) or `data/trafficcam/images/val/` (2340 pool). Filenames carry tags `..._3way_clear_...`, `..._heavy_monsoon_...` — pick 1 clear + 1 monsoon. Copy 20 to `C:\Temp\sgp-demo-frames\`.
Cmd1 (60-90s): `.venv\Scripts\python.exe scripts\bench_detect.py --frames-dir C:\Temp\sgp-demo-frames --max-frames 20` — say fp32 5-8 fps, det_total=0 would show.
Cmd2 (60s): `.venv\Scripts\python.exe scripts\run_closed_loop.py --frames-dir C:\Temp\sgp-demo-frames --max-frames 5 --city mumbai` — say queue -> green -> mock actuate; exit 1 if any fail.
If hall dies: pre-run both once, save to `refs/demo-output.txt`; backup `ui/replay.py` or `docs/demo-deck/bmd-finale.html`.

## What the dashboard shows (use it in slides)
- Every number on screen is tagged **MEASURED** (read from the scorecards/metadata on disk),
  **ILLUSTRATION** (modelled) or **SPEC** (not built) - say this out loud, it is the point.
- Measured proof lives on **Algorithm Comparison**: 11/11 scenes, wait down 19-75%.
- Impact Metrics prices its projections in rupees with dated Indian rates (petrol
  Rs 111.21/L Mumbai, carbon Rs 8,150/t IISD) and says plainly that the volumes are modelled.
- Settings shows what is really configurable, and that the API has no authentication yet.

## Visual guidance for PPT agent
- Fonts: large (>=24pt body), high contrast, no paragraph walls.
- Charts: redraw scorecard deltas as bars (adaptive short/green, fixed tall/gray); per-class mAP50 as horizontal bars with bicycle red.
- Diagrams: convert Mermaid in `docs/ARCHITECTURE.md:12-35` to flat PPT shapes (no Mermaid code on slides).
- Footer on proof slides: tiny source line e.g. `metadata.json:28-47 | BENCHMARKS.md | scorecard_1790419766.json`.
