# Adaptive Traffic Signal Timer — Master Plan

*Status: IN EXECUTION · Created: 2026-08-26 · Last updated: 2026-09-18 (Phase 5 done)*

> **Maintenance rule:** this document is updated after EVERY phase completion and every
> decision change. Phase status table in §7 must always reflect reality. Benchmarks live
> in `docs/BENCHMARKS.md`, updated on every `make bench-*` run.

---

## 1. Project Vision

Modernize development of an AI-powered adaptive traffic signal control system using
**loop engineering** (automated verification loops) and **graph engineering**
(knowledge-graph-guided navigation), shifting human effort away from routine work and
toward **India-specific traffic edge cases**: driver discipline (lane adherence,
red-light stop-line behavior relative to camera line-of-sight), weather effects
(monsoon), and heterogeneous intersection geometries (3/4/5-way).

The project must be **device-versatile** — runs on any generation of edge hardware
deployed on Indian traffic signals — and **fast in every measurable axis**.

## 2. Locked Decisions

| # | Topic | Decision | Rationale |
|---|---|---|---|
| D1 | Legacy test runners (`tests/run_tests.py`, `tests/automated_test_runner.py`, `tests/comprehensive_test_framework.py`) | **Hard-delete** (~82KB redundant pytest orchestration) | One canonical verification entry point; git preserves history |
| D2 | Edge-case families | Driver discipline **and** weather together | Both feed queue-estimation error, the core metric |
| D3 | Weather data | Synthetic parametric model calibrated near-real for India; pluggable `WeatherSourcePort` for future IMD API | No real data source available now |
| D4 | "Fastest" targets | Sim throughput **and** detection latency, both measured | Two different bottlenecks, two ladders |
| D5 | Edge device | Unknown/generic → **ONNX Runtime tiering** (CPU-int8 / NPU / TensorRT-fp16); never Orin-specific | Indian ATCS deployments are fragmented: Jetson TX2→Orin NX, RK3588 NPU boxes, legacy x86 IPCs; Bengaluru BATCS runs C-DAC CoSiCoSt on mixed hardware across 165 junctions |
| D6 | Tier-low detection | Interpolation-only queue estimation now; frame-skip + background-subtraction hybrid logged as future upgrade if eval shows queue error above tolerance | Cheap, works on every generation |
| D7 | N-way intersections | Compatibility-graph scheduler; non-conflicting approaches share green; empty approaches skipped entirely; **no pedestrian phase** (added later, after core success) | Uniform 3/4/5/6-way via config; strict sequential rotation preserved as degenerate fallback case |
| D8 | Programming language | Python stays; speed via NumPy vectorization → Numba JIT → (only if proven wall) Rust PyO3 single-kernel extension. No engine rewrite | Polyglot kills dev-loop speed and portability; inference already runs C++/CUDA under ultralytics |
| D9 | Modularity | Ports & adapters contract (§4 Phase 1.5) before any new modules bolt on | Edge-device swap must touch only its adapter + YAML |
| D10 | Monitoring | Keep prometheus-client; phase-boundary histograms; `orjson` when payloads grow | Standard, negligible overhead |

## 3. Current-State Findings (verified 2026-08-26)

- Engine hardcodes 4-way phases at `src/adaptive_traffic/core/simulation/engine.py:65`
  (`phase_sequence=["NS_green","NS_yellow","EW_green","EW_yellow"]`) — n-way impossible today
- `core/detection/detector.py`: concrete `VehicleDetector`, imports `ultralytics`+`torch`
  at module top — no port interface
- `core/control/controllers.py`: PASS already has `BaseController` ABC with min/max green
  bounds — correct port pattern to follow
- API/UI layers clean: import only `config.settings`
- Perf tests quarantined (target deleted `Code/YOLO/darkflow` module) — no baseline exists
- `onnxruntime` in pyproject but unused — ready-made portability layer
- India taxonomy seeds exist as docs-only in `.opencode/skill/robustness-eval-patterns/SKILL.md`
  (incidents: autorickshaw_block, cattle_on_road, religious_crowd, political_rally,
  monsoon_flooding) and `queue-estimation-patterns/SKILL.md` (3–4 lane geometry)
- `VehicleType` lacks AUTO (autorickshaw)
- graphify knowledge graph exists at `graphify-out/` (~816 nodes)

## 4. Phase Plan (execution order)

### Phase 0 — Measure *(gates all optimization)* — STATUS: pending
1. `make bench-sim`: sim steps/sec, fixed RNG seed, standard config
2. `make bench-detect`: detection fps on sample frames (CPU baseline)
3. Rewrite quarantined perf tests against the live engine
4. Record baselines in `docs/BENCHMARKS.md`; every later change re-benches against this
- **Exit criterion:** baseline numbers exist and are reproducible

### Phase 1 — One canonical dev loop — STATUS: pending
1. Hard-delete the three legacy runners (D1)
2. Makefile targets become the sole interface:
   - `loop-fast` — unit tests only, <30s target
   - `verify` — full suite + lint + type-check
   - `eval` — scenario matrix (Phase 4)
   - `graph-update` — `graphify update .`
   - `bench-sim`, `bench-detect`, `profile-device`
3. pyproject optional extras split: `[cv]` (opencv/ultralytics/torch/onnx),
   `[ui]` (streamlit/altair) — core install excludes heavy deps
4. AGENTS.md updated: make targets are the ONLY verification commands
- **Exit:** `make loop-fast` <30s

### Phase 1.5 — Modularity contract (D9) — STATUS: pending
1. Extract `core/domain.py`: `Vehicle`, `VehicleType`(+#`AUTO`), `Lane`, `Intersection`,
   `Direction`, `DetectionResult`, `TrafficState`, `SignalTiming`
2. `DetectorPort` ABC (`detect(frame)->DetectionResult`) + adapters:
   - `UltralyticsDetector` (dev machines)
   - `OnnxDetector` (CPU/NPU int8 — any generation)
   - `TensorRTDetector` (Jetson fp16; engine built+cached on-device under
     `models/trt_cache/` keyed by device+model hash)
   Heavy imports lazy, inside adapters only.
3. `WeatherSourcePort` ABC: `SyntheticWeatherSource` default; IMD-API adapter later
   with zero downstream changes
4. Controllers unchanged (`BaseController` stands); scheduler lands as new implementation
5. Dependency rule documented in AGENTS.md: `domain ← ports ← adapters`;
   UI/API → services only. graphify flags violations post-refactor
- **Exit:** torch importable nowhere except detection adapters; all tests green

### Phase 2 — India edge-case layer (D2, D3) — STATUS: pending
1. `core/simulation/behavior.py`:
   - `DisciplineProfile` per vehicle class: red-light violation probability,
     stop-line encroachment distance (meters past stop line → camera line-of-sight
     undercount), lateral lane-drift probability (bike filtering), wrong-side entry probability
   - Presets: `disciplined`, `typical_urban` (default), `aggressive_metro`
   - Hooks: violation sampled at signal transition in `_update_signals`;
     encroachment offsets vehicle position past stop line; drift reassigns `Vehicle.lane`
2. `core/simulation/weather.py`: states clear / light_rain / heavy_monsoon /
   waterlogged → per-state speed multiplier curve, YOLO confidence-degradation factor
   (simulates missed detections), lane-capacity reduction (waterlogged lanes unusable).
   Parameter values bounded by published Indian traffic-study ranges, sources cited inline
- **Exit:** encroached/rain-affected vehicles measurably distort queue estimates vs
  clear+disciplined run

### Phase 3 — Topology-generic N-way scheduler (D7) — STATUS: pending
1. Refactor `Intersection` to approach-set model (no hardcoded NS/EW)
2. Per-intersection config YAML: approach list + **compatibility matrix**
   (edge = may be green simultaneously)
3. Scheduler: per-approach demand from queue estimates → pick max-compatible group by
   demand → serve one optimal green (queue-derived, min/max bounded) → mark serviced →
   repeat until none left → new cycle. Empty approaches skipped. Zero compatibility
   edges ⇒ strict sequential rotation (fallback)
4. Works for 3/4/5-way via config alone
- **Exit:** same scheduler runs all three geometries in tests

### Phase 4 — Eval matrix — STATUS: pending
1. `evals/runner.py` + scenario YAMLs in `configs/evals/`
2. Dimensions: geometry {3,4,5-way} × discipline preset {3} × weather {4} ×
   incident type (taxonomy incl. India-specific) × hardware tier {low, mid-high
   simulated via degraded confidence/latency}
3. Each run: adaptive controller vs fixed-time baseline (cached per config hash).
   Metrics: avg waiting time, throughput, **queue-estimation error during
   encroachment/rain/tier-low**
4. Output: scorecard JSON (`orjson`) + console table; regression flag vs previous run
5. Scenarios run multiprocess-parallel
6. Includes `sensor_failure` degradation → last-known-good timing-plan fallback test
- **Exit:** `make eval` end-to-end; scorecard reproducible

### Phase 5 — Speed (D4, D8) — every axis, benchmark-gated ladder — STATUS: pending
1. **Sim kernel ladder:** NumPy vectorize `_update_vehicles`/car-following → re-bench →
   `numba @njit` remaining hot paths → re-bench → Rust PyO3 single-kernel extension
   ONLY if still wall-bound. Target ≥500 steps/s or documented plateau
2. **Detection:** single PyTorch→ONNX export; int8 quantization calibrated on Indian
   footage frames; provider chosen by `configs/device.yaml`; MJPEG quality/resize tuning
   before any streaming framework change
3. **Pipeline:** uvloop; capture thread → ring buffer (drop-oldest) → detector →
   estimator decoupled by queues; lazy heavy imports (from 1.5)
4. **Monitoring:** Prometheus histograms at phase boundaries
   detect→estimate→decide→actuate; `orjson` payloads when large
- **Exit:** each rung's keep/discard decided by bench delta, recorded in BENCHMARKS.md

### Phase 6 — Graph wiring & documentation — STATUS: pending
1. AGENTS.md workflow habits: verify via make targets; trace failures via
   `graphify query "<error>"`; `graphify update .` after refactors
2. `docs/device-tiers.md`: tier definitions + supported device matrix
   (TX2/Xavier/Orin family, RK3588-class, x86 IPC, generic ARM)
3. Future-upgrade log: tier-low hybrid detector trigger = eval queue-error breach

### Phase T — GPU training pipeline (train-on-GPU → deploy-anywhere) — STATUS: READY - blocked on data
Locked: annotated data will be provided by authorities · 6-class schema now, extend later
(flagged) · free Colab T4 tier (yolov8n-first strategy).

1. PASS `docs/DATASET_SPEC.md` v1: YOLO-format contract, 6 classes (car, motorcycle,
   bus, truck, bicycle, auto), junction×day split hygiene, capture-metadata request,
   calibration coverage rules. Class schema PROVISIONAL FLAG documented.
2. PASS `scripts/prepare_dataset.py`: YOLO + COCO-JSON converters, contract validator
   (`--check`), calibration sampler (`--make-calibration`). Dry-run passed on mock data.
3. PASS `notebooks/train_india_yolo.ipynb`: Colab notebook (20 cells) — validate → train
   yolov8n @70ep (T4-session sized; yolov8s optional second session, commented) →
   per-class mAP50 (auto highlighted) → ONNX export opset17 → int8 static quantization
   with dynamic fallback → registry packaging (`models/registry/india-yolov8{n,s}/`
   model.onnx + model-int8.onnx + metadata.json) → zip back to Drive.
4. PASS `OnnxDetector` completed: loads registry models via metadata.json (class list,
   imgsz, layout read from metadata, never hardcoded); fp32+int8 decode layouts;
   provider auto-pick CUDA→CPU; wired into `DetectorPort.create`.
5. PASS `configs/device.yaml`: tiers low/mid/high mapped to registry artifacts;
   high-tier TensorRT adapter still pending Phase 5 (falls back to ONNX).
6. PAUSED - When footage arrives: convert → `--check` → upload to Drive → Run all in Colab →
   drop registry zip into repo → rerun eval matrix.

## 5. Success Criteria (overall)

- [ ] `make loop-fast` <30s; single verification interface
- [ ] Eval matrix covers geometry × discipline × weather × incident × tier, reproducible
- [ ] Queue error demonstrably distorted by edge cases (proves the layer bites)
- [ ] Sim ≥500 steps/s OR plateau documented with ladder evidence
- [ ] Same codebase serves CPU-only box → Jetson via `device.yaml` alone
- [ ] N-way scheduler handles 3/4/5-way from config
- [ ] graphify current; AGENTS.md enforces loop/graph habits

## 6. Out of Scope (explicitly deferred)

Pedestrian phases · real IMD weather ingestion (interface reserved) · MARL
multi-intersection coordination · Rust rewrite beyond a proven-hot kernel ·
tier-low hybrid detector (until triggered).

## 7. Phase Status Board

> **Orca autobuild mirror:** `checkpoints/*.done` + `orca-pipeline.yaml` are the durable source; this table mirrors them for humans. `scripts/resume.ps1` reads both. On every phase gate, the pipeline does `git commit && touch checkpoints/phaseN.done && scripts/auto-graph.ps1` and updates this row.

| Phase | Status | Completed On | Checkpoint File | Notes |
|-------|--------|--------------|-----------------|-------|
| 0 Measure | PASS done | 2026-08-26 | `checkpoints/phase0.done` | sim 28,503 steps/s (57× target); loop-fast 7.4s; BENCHMARKS.md created |
| 1 Dev loop | PASS done | 2026-08-26 | `checkpoints/phase1.done` | 3 runners deleted; loop-fast/verify/eval/bench-sim/graph-update targets; [cv]/[ui] extras split |
| 1.5 Modularity | PASS done | 2026-08-26 | — (sub-phase, no ck) | core/domain.py (+AUTO, diagonal Directions); DetectorPort + Ultralytics/Onnx adapters; torch confined to adapters |
| 2 Edge cases | PASS done | 2026-08-26 | `checkpoints/phase2.done` | behavior.py (3 India presets, per-class overrides) + weather.py (4 states) integrated into engine |
| 3 N-way scheduler | PASS done | 2026-08-26 | — (sub-phase, no ck) | compatibility-graph groups; adaptive max-demand vs fixed round-robin; verified 3/4/5-way |
| 4 Eval matrix | PASS done | 2026-08-26 | `checkpoints/phase3.done` | evals/runner.py + configs/evals/scenarios.yaml; 11 scenarios ×2 modes in 22.4s; regression flagging live |
| 5 Speed | PASS done | 2026-09-18 | `checkpoints/phase5.done` | vectorization deferred (57× target); Steps 0–3: hygiene, -final refs, histograms+/metrics, staged pipeline. TRT rung: TensorRTDetector via ORT TRT-EP (fp16 + engine cache, fail-closed fallback) — code-complete, on-device latency validation pending Jetson hardware. |
| 6 Graph/docs | PASS done | 2026-09-03 | `checkpoints/phase6.done` | device-tiers.md added; AGENTS.md verification+dependency rules live |
| T Training pipeline | PASS done (finale) | 2026-09-13 | — | **Finale 5-ep joint polish from loop-8 best.pt:** 8-loop chain 0.7949→0.8293 → finale 0.8477 full-10k val (+0.0184, 6-class bicycle 0.6859); low-tier now india-yolov8n-final (4.98 fps static-int8, 200.6ms/frame). Earlier Option A pilot (HeTra mAP50 0.9816) superseded — finale is canonical. |
| **Orca Autobuild** | PASS wired | 2026-09-02 | `checkpoints/*.done` | `orca-pipeline.yaml` 5 phases + `scripts/resume.ps1` power-cut resume + `scripts/auto-graph.ps1` + `scripts/install-orca-startup.ps1` + single `.graph-mem` brain + `vault/` Obsidian mirror + freelm 6-pool `.env` — see `~/.agent/plans/orca-autobuild-plan.md` |
| P Policy ports | PASS done | 2026-09-21 | — | `core/control/policies.py` (Headway/Green/Order/Cap ports + Emergency/Manual priority + MARL slot); per-class weighted greens, clockwise default, demand-share cap, route-scoped manual-suppresses-EVP; `QueueEstimate.by_class`; engine delegates with legacy one flag away; 10 new unit tests; verify 92 passed; eval 11/11 wins (4 order-cost regressions documented in BENCHMARKS.md) |

## 8. Change Log

| Date | Change |
|------|--------|
| 2026-08-26 | Initial plan committed; execution started |
| 2026-08-26 | Phases 0–4 complete. Key results: eval matrix shows adaptive wins +76.5% wait reduction on 5-way, +31% on 3-way; queue_error gradient 0.00→0.88 across weather/discipline axes. Direction enum extended with diagonal legs for 5/6-way. VehicleType AUTO added. Legacy runners hard-deleted. |
| 2026-08-26 | Phase T built data-ready: DATASET_SPEC v1 (classes provisional — extend for tempos/e-rickshaws when confirmed), prepare_dataset.py dry-run passed on mock dataset, Colab notebook validated, OnnxDetector completed + device.yaml tiers wired. onnxruntime installed to venv. |
| 2026-09-03 | Phase 6 complete: device-tiers.md added; tensorrt→onnx fallback in DetectorPort; profile_device.py + bench_detect.py created; make bench-detect target added; loop-fast 7.4s PASS |
| 2026-09-04 | Phase T unblocked via HF IITM-HeTra_v2 (Option A pilot): convert_voc (recursive splits, BOM-tolerant, image index) + 8 regression tests; Colab yolov8n mAP50 0.9816/auto 0.9744 → models/registry/india-yolov8n/; eval matrix rerun clean (17.8s); bench-detect first real row; fixed ONNX export transpose + bench_detect len bugs; data.yaml now absolute-path with val→test fallback. |
| 2026-09-05 | Source switch to official iisc-aim/BMD-45 (CC-BY-4.0, commercial OK; 153 GB PNGs): notebook rewired to chunked PNG→JPG transcode pipeline (peak ~35 GB) + official 10k-image val split (no synthetic split); Option B merge covers 13/14 classes (Other dropped); pipeline dry-run green. Old kalyan1729 copy superseded. |
| 2026-09-10 | 8-loop cumulative chain complete (train_bmd_loop.ipynb): 0.7949→0.8293 overall on fixed official-val anchor, all 6 classes monotonic-or-flat, bicycle 0.56→0.66, zero forgetting; winner registry india-yolov8n-bmd/ extracted + wired as low-tier default; eval matrix clean (18.5s); full suite 48 passed. |
| 2026-09-13 | Finale joint polish complete (train_bmd_finale_drive.ipynb, Drive contract): 5 ep @lr0=0.002 from loop-8 → 0.8477 full-val (+0.0184), per-class car 0.9189 auto 0.9171 moto 0.8887 bus 0.846 truck 0.8294 bicycle 0.6859; promoted to india-yolov8n-final (low-tier default); bench_detect 4.98 fps, bench_decide 1.11ms p50; eval still 11/11 wins; full suite 48 passed. |
| 2026-09-10 | Fast-green plan done (Steps 0/1/2/4; 3 deferred by measurement): decide path 1.68ms p95 @300 boxes (6× under 10ms budget) → estimator optimization dropped; engine scheduler gained demand-following greens (discharge + 15s efficiency floor, 7–50 bounds), starvation-bounded argmax order, mid-phase preempt; eval carries dec_p50/p95 + >10ms flag. Adaptive now beats fixed in all 11 scenarios (x3way 8.7→4.0 headline). scripts/bench_decide.py added. |
| 2026-09-18 | Steps 2+3 (Phase 5): monitoring — core/monitoring.py (4 histograms at bench boundaries, /metrics endpoint), zero new deps; pipeline — core/pipeline.py (DropOldestBuffer + StagedPipeline, dual-shape normalization) + bench_detect --stages (233.6ms detect, same variance band). bench_decide @300: 0.93/1.19ms (no histogram overhead); eval 11/11 wins, wall 18.7s; loop-fast 49 passed, new files flake8-clean. orjson/uvloop skipped by measurement. Only the TRT adapter remains (needs hardware). |
| 2026-09-18 | Phase 5 done via TensorRT rung: core/detection/adapters_tensorrt.py — TensorRTDetector subclasses OnnxDetector, swaps in ORT TRT-EP (fp16 + engine cache under models/trt_cache/<device>_<modelhash>/), fail-closed with onnx fallback in DetectorPort.create. 8 mock-based unit tests (provider gate, cache key, fp32 selection, both factory paths); high-tier fallback smoke-tested on CPU box. Native TRT+pycuda logged as upgrade path if ORT-TRT ever proves wall-bound. On-device latency validation pending Jetson hardware. |
| 2026-09-18 | Steps 0+1 (Phase 5 finish, hardware-unknown): hygiene gate — phase6.done added (table↔checkpoints parity), `.backboard/`+`.superbrain/` ignored, finale docs/scorecards/EDA notebooks committed, pilot+bmd metadata.json committed as provenance (weights stay local-only, `.onnx` ignored). Registry refs fixed — mid/high tiers + bench_detect/OnnxDetector/DetectorPort defaults now resolve to india-yolov8n-final; yolov8s artifact never existed. |
| 2026-09-18 | Phase C lab slice: `core/closed_loop.py` bridge (estimate→decide→actuate) + `scripts/run_closed_loop.py` CI-sim (`--ntcip-ip` = hardware handoff) + 12 integration tests; wire tests caught 2 real STMP bugs (OID continuation bits, >255B SET pack crash — real adapter had never sent a full plan). Full suite 82 passed. Still hardware-gated: real-controller STMP, on-device TRT latency, live capture thread. |
| 2026-09-21 | Policy ports (screenshot-in → green-out, plug-and-play): per-city `discharge_headways` + `cycle_budget_s` on CityProfile; weighted discharge greens; clockwise order default (argmax via flag); demand-share cap; `ManualRegistry` + `EmergencyEvent` with route-scoped manual-suppresses-EVP rule; `Independent` MARL slot on engine; `closed_loop.decide/run_frame` priority-aware with public `sim.decide` seam. Verify 92 passed/1 skipped; eval 11/11 wins, dec95 ≤0.11ms; bench_decide @300 2.16/2.93ms p50/p95 (<10ms). 4 order-cost regressions vs argmax accepted + attributed (BENCHMARKS.md). |
| 2026-09-21 | Real-data QA (TrafficCAM bring-up, local 2GB pull): converter handles labelme/bbox/RLE + 13-label census (LMV/MotorBike/Auto/e-Rickshaw/LCV/Tractor aliases); contract `--check` green on 2340 frames/78 videos. Found + fixed 3 detector-path defects: (1) static int8 emits all-zero scores → low tier back to fp32 (5.1–8.2 fps measured, above target); all pre-09-21 int8 quality claims void. (2) ONNX bbox emitted (x,y,w,h) vs (x1,y1,x2,y2) contract → queues silently empty on real frames → fixed + regression test. (3) `_nms` ignored `iou_threshold` → wired, default 0.45 kept (F1-neutral per greedy matching P.84/R.38). First real numbers: queue RMSE 28.9 proxy (labels-vs-queue-zone caveat; hybrid FIRE not actionable without hand-count GT). |
