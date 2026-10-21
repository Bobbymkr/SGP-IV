# 01 — Project Facts (exact, verified 2026-10-21 — use ONLY these numbers)

## One-liners
- Project: AI adaptive traffic signal control tuned for India (hetero mix + monsoon + 3/4/5-way).
- Flow: Camera frame -> AI detects vehicles -> Queue per lane -> Green time adapted -> Signal + cars. Source: `docs/ARCHITECTURE.md:12-19`, `README.md:13-22`.
- Dependency rule: `core/domain.py <- ports <- adapters`. Heavy libs only in adapters. Source: `docs/ARCHITECTURE.md:143-154`, `AGENTS.md`.

## Detector (canonical model `models/registry/india-yolov8n-final/`)
- Model: YOLOv8n, 3.0M params, 11.7 MB fp32 ONNX opset17, imgsz 640. Source: `models/registry/india-yolov8n-final/metadata.json:1-25`, `README.md:36-37`.
- Quality full 10k BMD-45 val: overall mAP50 **0.8477** (+0.0184 vs loop-8 0.8293). Source: `models/registry/india-yolov8n-final/metadata.json:28-47`, `docs/BENCHMARKS.md:24`.
- Per-class mAP50: car 0.9189, auto 0.9171, motorcycle 0.8887, bus 0.8460, truck 0.8294, bicycle **0.6859 (weak tail — must show)**. Same source.
- Training: 8-loop chain 0.7949->0.8293 (loop1 20ep from COCO, loops 2-8 12ep from prev best) + finale 5ep lr=0.002 batch 32 from loop-8 best. Source: `docs/MASTER_PLAN.md:204`, `docs/BENCHMARKS.md:21-24`.
- Speed low-tier CPU fp32: **5.1-8.2 fps** (TrafficCAM 180 real frames, 123-197ms/frame). Colab fp32 6.58 fps. Source: `docs/BENCHMARKS.md:27`, `sgp-presentation-pack/08-int8-verdict.md:8`.
- Config: `configs/device.yaml:14-23` active low, backend onnx, `prefer_int8: false`, conf 0.45, target 5 fps.
- Detector code: `src/adaptive_traffic/core/detection/adapters_onnx.py:19-29` (BGR->RGB, /255, NCHW, NMS conf/IoU 0.45, city thresholds).

## int8 verdict (honest caveat — must include)
- Shipped 2026-09-13 static int8: DEAD all-zero scores. All pre-2026-09-21 int8 quality claims VOID. Source: `docs/BENCHMARKS.md:237-244`.
- v6b first alive static int8 (MinMax-QDQ backbone, last-20 `/model.22/*` fp32 tail, 200-frame calib): BMD full-val fp32 0.8469 vs int8 **0.8224 (delta -0.0245)**, TrafficCAM 0.4882 vs 0.4646 (delta -0.0236), 9.4 fps CPU. Gate needed -0.02 → **KEEP fp32, miss by 0.0045**. Source: `evals/results/anchor_bmdval_2026-10-11.txt:1`, `docs/BENCHMARKS.md:214-233`, `sgp-presentation-pack/08-int8-verdict.md:1-11`.
- SGP line: `Static int8 is alive for the first time — near fp32 quality at twice the speed — but the gate is the gate: fp32 ships, int8 stays staged.`

## Dataset contract
- Layout: `images/{train,val,test}/*.jpg` + `labels/**/*.txt` + `data.yaml` (absolute path) + `calibration/frames` (~200) + `meta/captures.json`. 6 classes car/motorcycle/bus/truck/bicycle/auto. Splits by junction x day, never random frame. Source: `docs/DATASET_SPEC.md:9-55`.
- Sources: BMD-45 official (153 GB PNGs, 10k val, OptionB 13->6 merge) canonical; TrafficCAM 2340 frames 8 cities local check; HeTra pilot superseded; synthetic 4032 renders unsuitable for quality (model blind 0/576). Source: `docs/BENCHMARKS.md:25-26`, `sgp-presentation-pack/02-dataset.md:17-18`.

## India tuning (Mumbai example)
- Mumbai: 4 lanes/approach, mix car 0.45 / two_wheeler 0.25 / auto 0.12, lengths car 4.5m bus 12m auto 3m, bounds min 15 / max 90 / yellow 5 / all_red 3, behavior aggressive_metro, weather heavy_monsoon. Source: `config/city_profiles/mumbai.json:1-43`.
- Cities: mumbai / delhi / bangalore / tier2_default. Switch city = switch file. Thresholds: car 0.5, bus/truck 0.45, two_wheeler/auto 0.4, cycle 0.35. Source: `config/city_profiles/mumbai.json:68-77`, `docs/ARCHITECTURE.md:160-175`.
- Green rule: `green = startup + SUM(n_class x headway_class)`, city-overridable headways, clockwise order default (argmax via flag), demand-share cap, manual suppresses EVP on its route only, MARL `Independent` no-op today. Source: `src/adaptive_traffic/core/control/policies.py:1-17`, `docs/BENCHMARKS.md:51-69`.

## Streaming / closed loop
- Path: `DetectorPort` -> `QueueEstimator` (per-lane + per-class) -> policies Green/Order/Cap -> NTCIP STMP SET (UDP 5000) + J2735 SPAT 10 Hz (UDP 1736), BSM refine (1735), SNMP monitor (161). Source: `docs/ARCHITECTURE.md:21-35`, `docs/ARCHITECTURE.md:179-195`.
- Pipeline: `src/adaptive_traffic/core/pipeline.py` DropOldestBuffer (never blocks) + `process()` inline bench path + `submit/drain/run_worker` edge shape (no live caller yet). Closed loop: `src/adaptive_traffic/core/closed_loop.py` `run_frame: process -> inject_estimate -> decide -> actuate`, shared by `scripts/run_closed_loop.py` + tests.
- Decide speed: p50 ~1-2ms / p95 <3ms @300 detections, budget 10ms. Fresh eval dec95_a <=0.11ms all scenarios. Source: `docs/BENCHMARKS.md:29-49`, fresh `evals/results/scorecard_1792164898.json`.
- Sim speed: 28,503 steps/s, 57x the 500 target. Source: `docs/BENCHMARKS.md:6-13`.

## Eval proofs (use these tables)
- Fresh 2026-10-16 (11 scenarios, wall 11.7s, `evals/results/scorecard_1792164898.json`): 11/11 adaptive wins. Deltas: x4way_disciplined 25.8%, x4way_aggressive 47.4%, x3way 53.2%, x5way 73.6%, light_rain 34.7%, heavy_monsoon 55.3%, waterlogged 53.8%, aggressive_waterlogged 25.5%, x5way_monsoon 75.2%, sensor_failure 53.8%, lane_block 19.3%.
- Canonical Surat 15-scenario (`evals/results/scorecard_1790419766.json:1-336`, wall 24.19s, `docs/REVIEW_BRIEF.md:1-36`): 15/15 wins incl. x4way_surat_typical 18.2 vs 30.88 (41.06%), rally 13.31 vs 19.66 (32.3%), cattle 22.87 vs 31.71 (27.88%), VIP 36.03 vs 47.93 (24.83%). Incidents are synthetic-approx (rally=closure+surge, cattle=60s halt+pin, vip=120s pin), NOT field events — must label.
- Tests fresh today: 122 passed, 1 skipped (`tests/unit` + `tests/integration`). Full inventory in `docs/TESTING_DOCUMENTATION.md:23-40`.

## Dashboard (Streamlit UI — 6 pages, 9 tabs)
- Every number on screen is marked MEASURED (read from disk), ILLUSTRATION (modelled) or SPEC (not built). No unlabeled numbers. Source: `src/adaptive_traffic/ui/theme.py:58-89`, `src/adaptive_traffic/ui/_facts.py`.
- Pages: System Overview · Dashboard (Simulated City) · Live Demo · Algorithm Comparison · Impact Metrics · Settings. Source: `src/adaptive_traffic/ui/views/`.
- Live Demo runs the REAL pipeline on BMD-45 photos (8 photos, 52 cars, 3/3 actuated) and shows the last run + history. Source: `src/adaptive_traffic/ui/views/live_demo.py`.
- Settings → Configuration feeds the real run (city, confidence 0.45, registry, backend, frames). Settings → API lists all 35 served routes; the API has NO authentication (open routes, do not expose publicly). Source: `src/adaptive_traffic/ui/views/advanced.py`, `tests/unit/test_ui_api_routes.py`.
- Screenshots for slides: `sgp-ppt-handoff/ui-screens/01..09`. Impeccable critique 23/40 → 25/40; deterministic detector 8-10 findings → 0.

## India rates (real, dated 21 Oct 2026 — the UI uses these)
- Petrol ₹/L: Mumbai **111.21**, Delhi **102.12**, Bangalore **111.68**, Surat **101.82**; diesel Mumbai 97.83, Delhi 95.20, Bangalore 99.56, Surat 97.95. tier2_default = national average of the four.
- 1 USD = **₹94.77**. Carbon **₹8,150/t CO2e** (IISD social cost of carbon for India, 2018, US$86/t). Value of time **₹100/vehicle-hour** (our stated assumption, not a published MoRTH rate).
- Modelled per intersection per year: **47,128 L fuel saved** (~9 % of fuel burned there, India 5.6 L/100 km per IEA), **124 t CO2** (~80 cars), **15,333 hours** of waiting saved, worth **₹15.3 lakh** (fuel + time).
- Source of truth: `src/adaptive_traffic/ui/_india.py` (every constant dated and attributed). Test: `tests/unit/test_ui_india_costs.py`.

## Ship / ops
- `configs/device.yaml` tiers low/mid/high share `-final` nano until yolov8s exists. `configs/docker/` compose+nginx. `scripts/profile_device.py` writes active_tier. TensorRT falls back to onnx off-Jetson. Hardware handoff: `scripts/run_closed_loop.py --ntcip-ip <ip>`.
- Notebooks canonical: `notebooks/train_bmd_finale_drive.ipynb` (Drive-native), `notebooks/train_bmd_loop.ipynb` (8-loop chain), `notebooks/val_int8_drive.ipynb` (anchor only). Legacy: `notebooks/train_bmd_finale.ipynb`.
