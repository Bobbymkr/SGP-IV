# 03 — Proof Index (reviewer-grade: claim -> evidence -> status)

## Fresh verification (2026-10-21, cite as TODAY)
- Tests: `122 passed, 1 skipped` — cmd `.venv\Scripts\python.exe -m pytest tests/unit tests/integration -q -p no:cacheprovider`
- Eval: `11/11 adaptive wins, wall 11.7s` — cmd `python evals/runner.py` → `evals/results/scorecard_1792164898.json` (dec95_a <=0.11ms all rows)
- Dashboard: every number labelled MEASURED / ILLUSTRATION / SPEC; real pipeline run 8 photos, 52 cars, 3/3 actuated on TrafficCAM val frames; last-run status + history; review score 28/40, detector 0-1 findings
- India rates live (21 Oct 2026): petrol Mumbai 111.21 / Delhi 102.12 / Bangalore 111.68 / Surat 101.82 ₹/L; 1 USD = 94.77; carbon 8,150 ₹/t (IISD 2018); value of time 100 ₹/veh-h (stated assumption)
- Git head: `3a41b54` (check `git log --oneline -15`)

## Claim -> source (copy TRACE + refreshed)
- 0.8477 + per-class + 5ep lr0.002 + official-full-10k -> `models/registry/india-yolov8n-final/metadata.json:28-47`
- fp32 5.1-8.2 fps CPU; int8 voided all-zero -> `docs/BENCHMARKS.md:27`, `docs/BENCHMARKS.md:237-244`; `configs/device.yaml:18-21`
- OnnxDetector preprocess/NMS/city thresholds -> `src/adaptive_traffic/core/detection/adapters_onnx.py:19-29`
- Dataset contract -> `docs/DATASET_SPEC.md:9-30`; `scripts/prepare_dataset.py`
- Loop chain + finale canonical -> `notebooks/train_bmd_loop.ipynb`, `notebooks/train_bmd_finale_drive.ipynb`
- Mumbai mix/bounds/behavior/weather -> `config/city_profiles/mumbai.json:4-43`; cities bangalore/delhi/mumbai/tier2_default
- Green rule + EVP/manual + MARL slot -> `src/adaptive_traffic/core/control/policies.py:1-17`
- Queues -> `src/adaptive_traffic/core/analytics/queue_estimator.py:1-14`
- Pipeline buffer/process/submit -> `src/adaptive_traffic/core/pipeline.py`; run_frame -> `src/adaptive_traffic/core/closed_loop.py:1-13`; lab runner -> `scripts/run_closed_loop.py:1-8`
- Footage helpers + bench -> `scripts/footage.py`; `scripts/bench_detect.py`; `scripts/score_queue.py`; `scripts/bench_decide.py`
- 11 scenarios x2 -> `configs/evals/scenarios.yaml:1-95`; wins + dec_p95 -> `evals/results/scorecard_1792164898.json` (today) + `evals/results/scorecard_1789305524.json`
- Surat 15/15 -> `evals/results/scorecard_1790419766.json:1-336`; brief -> `docs/REVIEW_BRIEF.md:1-36`
- Sim 28,503 steps/s 57x -> `docs/BENCHMARKS.md:6-13`
- Frame-to-green diagram -> `docs/ARCHITECTURE.md:21-35`; old deck -> `docs/demo-deck/bmd-finale.html`
- v6b KEEP fp32 0.8469 vs int8 0.8224; TrafficCAM 0.4882 vs 0.4646 -> `evals/results/anchor_bmdval_2026-10-11.txt:1`; `docs/BENCHMARKS.md:214-233`
- STMP GET parser + 9 wire tests -> `src/adaptive_traffic/adapters/ntcip_stmp.py:163-`; `tests/integration/test_stmp_wire.py`
- Per-camera geometry + 2 tests -> `src/adaptive_traffic/config/city_profile.py:46-`; `tests/unit/test_estimator_geometry.py`
- India rates (per-city fuel, USD/INR, carbon, time value) -> `src/adaptive_traffic/ui/_india.py`; guarded by `tests/unit/test_ui_india_costs.py`
- Dashboard truth labels + API route truth -> `src/adaptive_traffic/ui/theme.py:58-89`; `src/adaptive_traffic/ui/views/advanced.py`; `tests/unit/test_ui_api_routes.py`
- UI screens for slides -> `sgp-ppt-handoff/ui-screens/01-overview.png` … `09-settings-api.png`

## Status matrix (put on slide 12 / appendix)
| Part | Status | Proof |
|---|---|---|
| Dev loop, modularity, behavior+weather, N-way, eval matrix | DONE + TESTED | MASTER_PLAN §7 PASS; 122 passed; 11/11 + 15/15 wins |
| Detector fp32 0.8477 + city profiles + NTCIP/J2735 mocks + pipeline + monitoring + closed-loop mock | DONE + TESTED | bench 5-8 fps; decide <3ms; `test_ntcip.py` 20 mocks; `test_closed_loop.py` 4; `test_stmp_wire.py` 9 loopback |
| Phone-footage honest qerr (`score_queue --gt-csv`) | READY-TO-TEST, no hardware | Protocol `docs/TESTING_DOCUMENTATION.md:53-66`, 50 frames + hand-count CSV |
| Live RTSP runner, real-controller STMP `--ntcip-ip`, on-device TRT latency, verified int8 | HARDWARE-GATED / STAGED | v6b staged `models/registry/india-yolov8n-final-candidates/`; `prefer_int8:false` |
| Pedestrian phase, real IMD ingest, MARL coord, Rust kernel, hybrid detector | DEFERRED by design | `docs/MASTER_PLAN.md:184-188` out-of-scope |

## Test inventory (fresh names for appendix)
`test_bench_footage.py` 6, `test_device_tier.py` 4, `test_estimator_geometry.py` 2, `test_eval_runner.py` 2, `test_monitoring.py` 4, `test_onnx_adapter.py` 3, `test_pipeline.py` 7, `test_policies.py` 10, `test_prepare_dataset.py` 11, `test_tensorrt.py` 8 mocked, `test_closed_loop.py` 4, `test_ntcip.py` 20 mocks, `test_stmp_wire.py` 9, `test_ui_api_routes.py` 3, `test_ui_india_costs.py` 10, `test_integration.py` 7+1 skip. Weak-only: `test_performance.py` synth load, `test_security.py` helpers — do NOT claim API auth proof (the API has no authentication).
