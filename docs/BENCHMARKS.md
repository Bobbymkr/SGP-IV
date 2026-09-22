# Benchmarks

> Update this file on every `make bench-sim` run and every Phase 5 ladder step.
> Machine: dev workstation (Windows, Python 3.11.15, venv). Fixed seed=42 for sim.

## Sim Throughput (`make bench-sim`)

| Date | Config | steps/s | vehicles_completed | avg_wait_s | Notes |
|------|--------|---------|--------------------|------------|-------|
| 2026-08-26 | baseline (pre-vectorization) | 28,503 | 84 | 16.72 | pure-Python engine, default generation rates |

Target: ≥500 steps/s → **baseline already 57× above target.** Rust/Numba rung likely
unnecessary; NumPy vectorization still planned if eval matrix wall-time demands it.

## Detection (`make bench-detect`)

| Date | Backend | fps | Notes |
|------|---------|-----|-------|
| 2026-09-04 | onnx int8 (india-yolov8n, CPU) | 0.68 | 1477ms/frame on 20 synthetic-noise frames; 0 detections expected on noise. First run against a REAL trained artifact (Option A pilot, mAP50 0.98). NOTE: this int8 is a DYNAMIC-quant fallback — cell 17's FrameReader init-order bug broke static quant (fixed 2026-09-05, verified static 12.3→3.4MB locally; first true static artifact lands with the Option B run). Rerun on captured frames when available. |
| 2026-09-04 | trained model quality (Colab T4, HeTra pilot) | — | overall mAP50 0.9816; auto 0.9744; car 0.9896; bus 0.9810. Gate (0.50/0.35) PASSED. Val split covered only car/bus/auto — full 6-class coverage needs BMD-45 (Option B). |
| 2026-09-10 | trained model quality (8-loop BMD-45 chain, official val anchor) | — | 0.7949→0.8041→0.8085→0.8155→0.8206→0.8249→0.8285→**0.8293** overall; all 6 classes measured every loop; bicycle 0.5635→0.6561; no forgetting; static int8 throughout. Winner: models/registry/india-yolov8n-bmd/ (wired as low-tier default in device.yaml). |
| 2026-09-10 | onnx int8 static (india-yolov8n-bmd, CPU) | 3.14 | 319ms/frame on 20 synthetic-noise frames (vs 0.68 fps for the dynamic-fallback pilot int8 — static quant confirmed faster). 0 detections expected on noise. |
| 2026-09-13 | onnx int8 static (india-yolov8n-final, CPU) | 4.98 | 200.6ms/frame on 20 synthetic-noise frames (polish did not regress latency; vs 3.14 fps for loop-8). Finale mAP50 0.8477 full-val. |
| 2026-09-13 | trained model quality (finale joint polish, full 10k val) | — | **0.8477 overall (+0.0184 vs loop-8 0.8293 anchor, full-val)**; per-class car 0.9189 auto 0.9171 moto 0.8887 bus 0.846 truck 0.8294 bicycle 0.6859; 5ep low-LR from loop-8. |
| 2026-09-18 | onnx int8 static (india-yolov8n-final, CPU, `--frames-dir`) | 4.96 | 201.5ms/frame on 576 rendered test frames (`data/synthetic_india_yolo/images/test`); `det_total=0`, 576/576 zero-frames. Latency matches the noise row — but the renders are near-black schematics (mean 0.47 labels/frame, few-px boxes), so the photo-trained model is blind here. Verdict: `--frames-dir` path proven, renders unsuitable for quality; recorded phone footage is the real next source. |
| 2026-09-21 | onnx fp32 (india-yolov8n-final, CPU, `--frames-dir` renders) | 10.24 | 97.6ms/frame on the same 576 renders; still `det_total=0` — now with a *working* model (see §Detector QA below), so the renders-unsuitable verdict is re-confirmed on solid ground, not on a dead artifact. |
| 2026-09-21 | onnx fp32 (india-yolov8n-final, CPU, `--frames-dir` TrafficCAM val) | 5.1–8.2 | 123–197ms/frame on 180 real Indian CCTV frames; `det_total>0`, zero zero-frames. First real quality signal (see queue-proxy rows below). |

## Decide Path (`scripts/bench_decide.py`)

| Date | Detections | estimate | +state | +decide | total p50 | total p95 | Budget |
|------|-----------|----------|--------|---------|-----------|-----------|--------|
| 2026-09-10 | 50 | 0.18ms | ~0ms | 0.02ms | 0.18ms | 0.28ms | <10ms PASS |
| 2026-09-10 | 150 | 0.48ms | ~0ms | 0.03ms | 0.48ms | 0.66ms | <10ms PASS |
| 2026-09-10 | 300 | 0.98ms | ~0ms | 0.02ms | 1.02ms | 1.68ms | <10ms PASS (6× headroom) |
| 2026-09-13 | 50 | 0.30ms | ~0ms | 0.04ms | 0.30ms | 0.45ms | <10ms PASS |
| 2026-09-13 | 150 | 0.81ms | ~0ms | 0.03ms | 0.56ms | 0.93ms | <10ms PASS |
| 2026-09-13 | 300 | 1.13ms | ~0ms | 0.02ms | 1.11ms | 1.83ms | <10ms PASS (5× headroom) |
| 2026-09-21 | 50 | 0.30ms | ~0ms | 0.04ms | 0.30ms | 0.54ms | <10ms PASS |
| 2026-09-21 | 150 | 0.74ms | ~0ms | 0.03ms | 0.82ms | 1.28ms | <10ms PASS |
| 2026-09-21 | 300 | 2.01ms | ~0ms | 0.06ms | 2.16ms | 2.93ms | <10ms PASS (3× headroom) |

Estimator scales ~3.3µs/detection (linear); decide path flat ~0.02ms.
Verdict: Steps 3–4 (estimator optimization) NOT needed — budget met with 6×
headroom at 300 boxes. Effort goes to durations (Step 1) + event triggering
(Step 2) + eval latency columns (Step 4).

2026-09-21: estimate @300 rose 1.13→2.01ms from per-class queue aggregation
(`by_class` for the weighted green policy). Budget still met 3× — no action.

## Policy Ports (2026-09-21, plug-and-play timing)

`core/control/policies.py`: HeadwayTable (per-class discharge seconds, city-
overridable) + Green (weighted discharge) + Order (clockwise default, argmax
legacy) + Cap (dynamic demand-share) + Emergency/Manual priority + MARL
`Independent` slot. Engine delegates via injected policies; legacy behavior is
one config away (`green_policy=flat, order_policy=argmax, cap_policy=fixed_max`).
`QueueEstimate.by_class` feeds class mix through `closed_loop.inject_estimate`
(typed vehicles, all-CAR fallback for old estimates).

Attribution (trimmed 1500-step runs): weighted+argmax+share == legacy to the
digit on sim traffic (mixed sim fleets average ~2.0s/veh; share cap rarely
binds) — the duration/cap change is neutral in sim and only bites with real
detector class mixes. The 4 eval regressions are 100% the clockwise order:
5-way (4 groups × 15s floor rotation) +29%, saturated 4-way waterlogged
+9–18% (strict alternation vs greedy back-to-back service). Still beats fixed
19–75% everywhere; `dec95_a` ≤0.11ms. Clockwise is the operator requirement
(predictable right-hand rule, smooth transitions); argmax stays one flag away.
Mid-phase preempt (>25% imbalance) partially offsets heavy-direction waits.

## Adaptive Durations (Steps 1+2+4, 2026-09-10)

Final formula (engine `_group_green_times`): `green = max(15s floor,
min(50s, queued × 2.0s + 2s startup))`, Indian 7–50 bounds, order = argmax
demand + starvation bound (forced service after a full rotation) + zero-skip,
mid-phase preempt past min-green on >25% imbalance. Eval `dec95_a` ≤0.08ms
everywhere (budget <10ms met ~125×).
Design iterations measured on x3way (fixed baseline 8.7): fixed-split 6.0 →
naive proportional 7.8 (singleton starvation: pair-sum always beats singleton)
→ discharge-following 5.6 but light-4way chopped (9.3, lost-time overhead) →
**+15s efficiency floor: 4.0**. Final matrix: adaptive beats fixed in ALL 11
scenarios (deltas +2.9% … +79.6%); scorecard carries `dec_p50/p95_ms` with a
>10ms regression flag.

## Test Suite Wall Time

| Date | Scope | Wall |
|------|-------|------|
| 2026-08-26 | unit+integration (`loop-fast` scope) | 7.4s PASS (<30s target) |
| 2026-08-26 | unit+integration (post engine refactor) | 1.1–1.5s PASS |

## Eval Matrix (`make eval`)

| Date | Scenarios | Wall | Notes |
|------|-----------|------|-------|
| 2026-08-26 | 11 scenarios × {adaptive, fixed} multiprocess | 22.4s | first scorecard: evals/results/scorecard_*.json |
| 2026-09-21 | 11 scenarios × {adaptive, fixed} multiprocess | 12.5s | policy-ports run (`evals/results/scorecard_1789972903.json`): 11/11 adaptive wins (deltas +19.3% … +75.2%), `dec95_a` ≤0.11ms; 4 regressions vs argmax run flagged above (order-policy cost, accepted) |

Headline findings (see scorecard): adaptive scheduling cuts avg waiting time 76.5% on
5-way and 31% on 3-way; fixed-time competitive on balanced 4-ways. Queue-estimation
error scales with weather/degradation: 0.00 (clear/disciplined) → 0.76 (waterlogged)
→ 1.32 (5-way monsoon, fixed).

## Phase Histograms (Step 2, 2026-09-18)

`core/monitoring.py`: four `traffic_<stage>_seconds` Histograms
(detect/estimate/decide/actuate) wired by one `@observe` decorator at each
bench boundary — both `detect()` adapters, `estimate_from_detections`,
engine `_refresh_green_plan` + `_next_phase`, engine `_update_lane_signals`
+ STMP `set_phase_timing` (mocks excluded). Scrape at
`GET /api/v1/health/metrics` (404 when `prometheus_enabled=false`).

Overhead unmeasurable: bench_decide @300 det 1.11/1.83ms p50/p95 (09-13) →
0.93/1.19ms (09-18); the delta is run-to-run variance (±10% band), not the
~µs histogram observe. Eval still 11/11 adaptive wins, wall 18.7s.

## Staged Pipeline (Step 3, 2026-09-18)

`core/pipeline.py`: `DropOldestBuffer` (bounded, never blocks; counters
received/dropped/served) + `StagedPipeline.process()` (inline
detect→estimate→decide with per-stage ms). Dual DetectorPort return shapes
(DetectionResult vs legacy List) normalized once at the seam. No live caller
yet — API serves mocks, sim is synthetic — so the worker loop exists for the
future edge runner, covered by unit tests (11 new: buffer, stages, shapes,
thread, /metrics).

`bench_detect --stages` first row (onnx int8, synth noise): detect
233.6ms/frame vs plain-path 216.8ms same day — same variance band as the
canonical 4.98 fps row; estimate 0.055ms (0 dets on noise; scales ~3.3µs/det
per the Decide-Path table). Methodology note: an early version of this flag
submitted all frames up front and divided by n while the buffer held 4 —
caught by the numbers, fixed to inline `process()` per frame.

## Queue-Error Proxy (`scripts/score_queue.py`, Phase B 2026-09-18)

Labels-as-GT on the 576 rendered test frames (proxy: labels count ALL visible
vehicles, estimator counts queue-zone only — expect systematic undercount):

| Conf | det RMSE/MAE/bias | queue RMSE/MAE/bias | Per-weather queue RMSE (clear/light/monsoon/waterlogged) | Trigger |
|------|-------------------|---------------------|----------------------------------------------------------|---------|
| 0.45 | 0.788/0.465/-0.465 | 0.788/0.465/-0.465 | 0.95 / 0.81 / 0.58 / 0.76 | INCONCLUSIVE |
| 0.50 | 0.788/0.465/-0.465 | 0.788/0.465/-0.465 | 0.95 / 0.81 / 0.58 / 0.76 | INCONCLUSIVE |

Identical rows = detector found 0/576 (threshold irrelevant when blind). The
0.788 RMSE is pure domain gap (bias −0.465 = GT mean), NOT interpolation error,
so the 0.5 hybrid trigger is **undecided, not fired** — the script gates the
verdict on detector non-blindness. Per-frame rows in
`evals/results/queue_proxy_conf04{5,0}.csv`. First honest qerr needs phone
footage + `--gt-csv` hand counts (protocol in TESTING_DOCUMENTATION.md).

> WARNING 2026-09-21 correction: those two proxy rows were computed with the
> **degenerate int8** (all-zero scores — see §Detector QA below), so the
> RMSE numbers are invalid, not just proxy-limited. Real fp32 proxy rows
> follow in the TrafficCAM table. The renders-unsuitable verdict itself was
> re-confirmed with working fp32 (0/576 again).

## Queue-Error on Real Footage (TrafficCAM val, fp32, 2026-09-21)

First honest detector+queue numbers on real Indian CCTV (180 val frames,
local run, GT = converted 6-class labels):

| Conf | det RMSE/MAE/bias | queue RMSE/MAE/bias | det hist | queue zeros |
|------|-------------------|---------------------|----------|-------------|
| 0.45 | 28.69/24.29/−23.76 | 28.89/24.91/−24.38 | p50 7, max 12, 0 zeros | 15/180 |

Greedy IoU≥0.5 class-aware matching on 50 frames @conf 0.25: P=0.836 R=0.384
F1=0.527 (NMS iou threshold 0.45/0.6/0.7 all F1≈0.52–0.53 — NMS is not the
lever; small-object recall is). Caveats: labels count ALL visible vehicles
vs queue-zone-only estimation (structural undercount bias); estimator
geometry is still 640×480-hardcoded while frames are 1080p (coarse
lane/direction buckets — per-camera calibration is the follow-up). The
hybrid-trigger FIRE on this proxy row is **not actionable** — the 0.5 trigger
is calibrated for hand-count `--gt-csv` GT with a matching queue definition.

## TrafficCAM Candidate (2026-09-21, NOT promoted)

`notebooks/training_output_zips/trafficcam_candidate_2026-09-21.zip` (local-only,
gitignored like all training zips): 10-ep T4 polish from `best_f007.pt`,
12.3MB fp32 + 3.4MB int8. Local 50-frame val sample @conf 0.45, greedy IoU≥0.5:

| Model | max score | det | P | R | F1 | fps CPU |
|---|---|---|---|---|---|---|
| finale fp32 (canonical) | 0.899 | 415 | 0.923 | 0.163 | 0.278 | 7.4 |
| candidate fp32 | 0.959 | 446 | 0.868 | 0.165 | 0.277 | 7.3 |
| candidate int8 (alive, non-zero) | 0.964 | 441 | 0.878 | 0.165 | 0.278 | 0.76 |

Verdict: **finale stays canonical.** TrafficCAM F1 ties (0.277 vs 0.278, noise);
candidate int8 is quality-alive but 10× too slow for low-tier (0.76 vs 5 fps
target — dynamic-quant matmuls lose on this 3M-param model); BMD-45
no-forgetting anchor unmeasured locally. Promote only on: TrafficCAM F1 up +
BMD-Val within −0.02 + int8 ≥4.5fps.

## Head-to-Head on TrafficCAM Val (2026-09-21, same 180 frames)

Finale ONNX measured locally (`yolo val`, CPU): **mAP50 0.488** vs the run
log's candidate **0.635** (car .582 / moto .633 / bus .541 / truck .696 /
auto .728; bicycle has 0 val instances — unvalidated for both). That is
+0.147 (+30% relative) on the new domain: the fine-tune genuinely learned
TrafficCAM. It does NOT clear the BMD no-forgetting anchor (unmeasurable
locally — 153GB BMD val not on hand), so the candidate is staged as a
**local-only alternative registry** `models/registry/india-yolov8n-trafficcam/`
(gitignored; provenance in its metadata.json + the training zip): usable today
via `--registry models/registry/india-yolov8n-trafficcam` for head-to-head
evals, wired to nothing by default. Canonical path unchanged.

Training notes from the run log (20ep — operator edit, not the notebook's 10):
`optimizer=auto` silently overrode `lr0=0.002`/momentum → AdamW(lr=0.001);
ultralytics removed duplicate labels on ~20 frames (source annotation
duplicates, harmless); 6.5% of train frames are `UCF_*`-prefixed
(non-Indian subset — val is pure-Indian: BLR/Mumbai/NITK4/Noida); static quant
degenerate a second time → dynamic fallback won (max score 0.917, recipe now
recorded as `quant_kind` in Cell 5 metadata).

## ITD-X Pseudo-Label Pool (2026-09-22, SHIPPED as model-derived GT)

`notebooks/training_output_zips/itd_x_2026-09-22.zip` (local-only): ITD-X at
conf 0.35 over 300 unlabelled TrafficCAM frames (frame0 human labels skipped),
mapped to the 6-contract (pedestrain dropped). Validation on receipt: 300/300
image↔label match, **0 invalid lines**, 8,253 boxes (27.5/frame), per-class
car 3363 / moto 3106 / bus 511 / truck 461 / auto 803 / bicycle 9.
Spot-check grid eyeballed: tight boxes, correct classes incl. dense scenes and
distant vehicles; label-text overlap in the densest zones is rendering-only.
Verdict: ship as a model-derived pool (SOURCE.txt provenance in-zip); reported
separately from human GT, never mixed. Bicycle remains thin (9) — the class
still needs a dedicated source. Still owed from the run: Cell-2 ITD-X val mAP
table for the head-to-head (finale 0.488 / candidate 0.635).

## Detector QA Findings (2026-09-21, from the TrafficCAM bring-up)

1. **Dead int8 (critical):** `model-int8.onnx` emits all-zero scores on every
   frame including dense scenes where fp32 peaks at 0.899 — degenerate static
   quantization, not a domain gap. Every pre-2026-09-21 int8 quality claim is
   void (latency rows stand). Low tier now runs fp32 (`prefer_int8: false` in
   `configs/device.yaml` + factory default): measured 5.1–8.2 fps CPU, above
   the 5 fps target and faster than the dead int8's 200ms/frame. No verified
   int8 exists; the train notebook now gates packaging on a non-degeneracy
   assert (max calibration score > 0).
2. **bbox contract violation (critical):** `OnnxDetector` emitted `(x, y, w, h)`
   while `VehicleDetection` promises `(x1, y1, x2, y2)` (and Ultralytics emits
   corners) — the estimator unpacked corners and filtered every real queue
   out (145/180 zero-queues → 15/180 after the fix). Locked by
   `test_detect_emits_xyxy_corners_like_ultralytics`.
3. **NMS threshold (measured, kept):** `_nms` hardcoded 0.45 ignoring the
   constructor's `iou_threshold` — now wired (default unchanged: F1-neutral
   per the matching study above).

## Closed Loop (Phase C lab slice, 2026-09-18)

`scripts/run_closed_loop.py` (frames → detect → estimate → decide → actuate,
mock STMP): 10/10 actuated on rendered test frames in 2.2s; zero-demand holds
position (`0_green`↔`0_yellow`, cycle 74s = 30+30 greens + 5+5 yellow + 2+2
all-red). `--ntcip-ip` aims the same loop at a real controller (hardware
handoff, untested).

Wire-level STMP fix (found by `tests/integration/test_stmp_wire.py`, fixed same
day): OID BER set the continuation bit on the wrong bytes (every OID containing
1206 — i.e. all of them — was malformed), and a full 4-phase SET crashed in
`struct.pack("!B", len)` (~300B of varbinds vs a 1-byte prefix) before anything
reached the wire. Fixed with correct base-128 continuation + BER long-form
lengths. The real adapter had therefore never sent a complete timing plan;
`_parse_stmp_response` remains an unimplemented stub (GET returns defaults).

2026-09-21: first real-footage closed loop — candidate registry on 8 TrafficCAM
val frames: 8/8 actuated (mock STMP), det 6–8 → queue 6–8 → demands [6–8, 0],
cycle breathing 61–66s with demand. Screenshot-flow proven on real pixels.

## Deliberate skips (measured, not deferred)

- orjson: scorecards ~6KB, API payloads tiny — D10's "when payloads grow"
  unmet. stdlib json stays; no new dep.
- uvloop: uninstallable on the Windows dev host and no async hot loop exists
  (mock API + sync sim). Deploy-time `uvicorn --loop uvloop` on Linux if a
  profile ever justifies it.
