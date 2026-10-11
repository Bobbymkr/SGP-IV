# 04 — Streaming: frame → green

## Path (draw this)
Camera frame → `DetectorPort` (YOLOv8 ONNX) → `QueueEstimator` (detections → per-lane queue) → `GreenPolicy` (weighted discharge) → NTCIP cycle config → controller / SPAT. `docs/ARCHITECTURE.md:21-29` + frame-to-green Mermaid.

## Non-blocking design
`core/pipeline.py:1-20` `StagedPipeline`: bounded drop-oldest buffer (slow detect never blocks estimate); `process(frame)` = deterministic inline path benches use; `submit/drain/run_worker` = edge-runner shape for live feed (no live caller yet — API serves mock, sim synthesizes; primitives unit-tested, ready). Stage histograms shared by bench, scorecard (`dec_p50/p95_ms`), Prometheus.

## Closed loop (demo this)
`core/closed_loop.py:1-13` `run_frame`: `pipeline.process → inject_estimate → decide → actuate`. One function shared by `scripts/run_closed_loop.py` and integration test; future edge runner calls same fn per drained frame.

## Footage helpers
`scripts/footage.py:1-10`: `load_frames` (sorted, BGR, skip-unreadable), `det_hist` (min/p50/p95/max/zeros), `parse_weather` (clear/light_rain/heavy_monsoon/waterlogged from filename), `err_stats`, YOLO-label + hand-count CSV ground truth. `bench_detect.py:4-9`: synthetic-noise default (latency only) vs `--frames-dir` real files (histogram + per-class counts — det_total=0 can't pass silently).

## Honest gap (say it)
No live RTSP runner today. Streaming primitives + mock actuation are proven; camera handoff is the next slice.

## Trace
`src/adaptive_traffic/core/pipeline.py`, `closed_loop.py`, `scripts/footage.py`, `bench_detect.py`, `run_closed_loop.py`, `score_queue.py`.
