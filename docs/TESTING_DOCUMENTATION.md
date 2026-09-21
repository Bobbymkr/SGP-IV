# Testing Documentation (current as of 2026-09-18 cleanup)

> Pre-cleanup version claimed deleted runners and >95% coverage. It was retired;
> see `docs/TEST_CLEANUP_LOG.md` (pre-rewrite blob `7151494d0a15cf561bed26d17f373c55d86cab3b`).
> This page describes what actually runs today.

## Canonical commands (AGENTS.md — the ONLY verification entry points)

| Command (Windows: run the underlying command directly) | What it proves |
|---|---|
| `pytest tests/unit tests/integration -q -x --no-header -p no:cacheprovider` (`make loop-fast`) | Unit + integration green, <30s target |
| `pytest -q` (`make verify`) | Full suite (`loop-fast` scope today — perf/security dirs hold only the live classes below) |
| `python evals/runner.py` (`make eval`) | 11 scenarios × adaptive/fixed, `dec_p95` regression flag (>10ms fails), >5% wait regression flag |
| `python scripts/bench_sim.py` | Sim throughput (baseline 28,503 steps/s, 57× the 500 target) |
| `python scripts/bench_detect.py --backend onnx --registry models/registry/india-yolov8n-final` | Detection latency on **synthetic noise** (4.98 fps canonical; 0 detections expected — NOT a quality proof) |
| `python scripts/bench_detect.py --backend onnx --registry models/registry/india-yolov8n-final --frames-dir <dir> [--max-frames N]` | Detection latency + per-frame histogram + per-class counts on disk frames (rendered set or recorded footage) |
| `python scripts/score_queue.py --frames-dir <dir> --labels-dir <labels> [--conf 0.45] [--out-csv out.csv]` | Detector + queue error vs YOLO labels (PROXY — see gaps). With `--gt-csv ground_truth.csv` instead of `--labels-dir`: honest qerr vs hand counts |
| `python scripts/bench_detect.py --stages` | Staged detect+estimate path timing |
| `python scripts/bench_decide.py --counts 50,150,300` | Decide path ~1ms p50 @300 det (6× under 10ms budget) |
| `python scripts/run_closed_loop.py [--frames-dir <dir>] [--max-frames N] [--ntcip-ip <ip>]` | Full loop frames→detect→estimate→decide→actuate (mock STMP by default; real controller via `--ntcip-ip`). Exit 1 on any actuation failure |
| `python scripts/profile_device.py --write` | Tier probe → writes `active_tier` in `configs/device.yaml` |

## Live test inventory

| File | Tests | Proves / does NOT prove |
|---|---|---|
| `tests/unit/test_pipeline.py` (6) | buffer drop-oldest, dual detector-shape normalization, decide hook, drain bounds, worker thread, real-estimator seam | Proves staged pipeline seams. Keep. |
| `tests/unit/test_onnx_adapter.py` (2) | native-layout decode, export-layout transpose via fake session | Locks a real export bug. Keep. |
| `tests/unit/test_tensorrt.py` (8) | provider gate, cache key, fp32/int8 selection, factory fallback/paths — all mocked | Proves wiring only. On-device latency pending Jetson hardware. Keep with that label. |
| `tests/unit/test_monitoring.py` (4) | `observe`/`timed` record, disabled-mode silence, `/metrics` endpoint | Keep. |
| `tests/unit/test_prepare_dataset.py` (8) | VOC split-nesting + BOM bugs, class mapping, calibration sampler | Locks real pilot bugs. Keep. |
| `tests/integration/test_ntcip.py` (20) | STMP SET/GET, SNMP status/faults/counters, J2735 BSM/SPAT/MAP, full-stack + disconnect fallback — all `Mock*` adapters | Proves protocol logic. No real controller/RSU touched. Keep. |
| `tests/integration/test_closed_loop.py` (4) | Canned-detect full loop (cycle math, STMP receipt), demand-steering (`1_green` on east-only demand), empty-frame hold, real-int8-model E2E | First whole-path test; bridge is `core/closed_loop.py`. Keep. |
| `tests/integration/test_stmp_wire.py` (8) | Real adapter vs fake UDP controller: header/OID/varbind bytes, long-form lengths, SET success, tid sequencing, fast timeout-false, GET-defaults stub documented | Found + fixed 2 wire bugs (OID continuation bits, >255B SET crash). Keep. |
| `tests/integration/test_integration.py` (8 run, 1 skipped) | timing sync, shared-state threads, error isolation, concurrent timing, memory bounds, format conversions | Generic coordination toys, not pipeline proofs. Weak but live; replace with recorded-footage tests in Phase B. |
| `tests/performance/test_performance.py` (3) | `TestSystemStress`: threads×FFT, memory-growth loop, alloc-then-free recovery | Synthetic load only — says nothing about detect/estimate/decide throughput. Weak; real perf signal is `bench_*` + eval. |
| `tests/unit/test_bench_footage.py` (6) | `load_frames` sort/limit/corrupt-skip, histogram quantiles, weather-tag parse, RMSE/MAE/bias, YOLO-GT counting, hand-count CSV parse | Pure helpers, no model. Keep. |
| `tests/unit/test_policies.py` (10) | weighted discharge math, class aliases + city override, factory defaults/legacy escape, clockwise skip/hold, argmax parity + starvation, demand-share cap, route-scoped manual-suppresses-EVP, estimator `by_class`, mixed-class engine green, manual hold | Proves policy seams without model/camera. Keep. |
| `tests/security/test_security.py` (4) | masking toy dicts, protocol allow-list, log-pattern scan, sanitizer unit | Generic helpers only — does NOT prove API input validation or auth (no auth exists on the API). Needs dedicated boundary tests. |

## Known gaps (lab-only status)

1. ~~`bench_detect` runs on random noise~~ DONE (footage path exists) — but the
   rendered set is unsuitable for quality: near-black schematics, mean 0.47
   labels/frame, photo-trained int8 detects 0/576 (see BENCHMARKS.md queue-proxy
   table). First honest qerr still needs phone footage + `--gt-csv` (protocol below).
2. `evals/runner.py` incidents are approximated (`sensor_failure→waterlogged`,
   `lane_block→0.3× rate`) — now labeled `incident_model: synthetic-approx:*`
   per scenario + a `notes` field in every scorecard since 2026-09-18.
3. Lab slice of the closed loop DONE (`core/closed_loop.py` + `run_closed_loop.py` + 12 tests). Remains for hardware: real-controller STMP (`--ntcip-ip`, untested), on-device TensorRT latency, camera-feed runner (the `run_worker` primitives are tested; no live capture thread exists yet).
4. Tier-low hybrid detector trigger: eval `qerr` > 0.5 RMSE (`docs/device-tiers.md`). Not yet measured on real footage — `score_queue.py` gates its verdict on detector non-blindness so a blind run reads INCONCLUSIVE, never FIRES.

## Phone-footage protocol (the real Phase B qerr — no hardware needed)

1. Capture: phone on tripod/balcony, fixed mount overlooking one approach, 720p,
   10 min covering one full peak (or 2×5 min peak/off-peak). Note height,
   direction, weather, time in the run log.
2. Extract 50 frames evenly spaced: `python -c` with cv2 (`VideoCapture` +
   `CAP_PROP_POS_FRAMES`) or any frame tool into `footage/<run>/frames/`.
3. Hand-count queued vehicles per frame into `footage/<run>/ground_truth.csv`:
   `frame,count` header, one row per frame (queue = stopped/creeping vehicles
   behind the stop line, both directions summed — must match the estimator's
   `total_vehicles` definition).
4. Run once per threshold: `python scripts/score_queue.py --frames-dir footage/<run>/frames --gt-csv footage/<run>/ground_truth.csv --conf 0.45 --out-csv evals/results/queue_phone_<run>_045.csv` (repeat with `--conf 0.5`).
5. Record the RMSE row in BENCHMARKS.md. If queue RMSE > 0.5 with a non-blind
   detector, the tier-low hybrid trigger FIRES.

## Policy

Delete stale tests; don't quarantine them. Every deletion gets a row in
`docs/TEST_CLEANUP_LOG.md` with blob hash + restore command.
