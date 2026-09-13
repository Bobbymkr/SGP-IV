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

## Decide Path (`scripts/bench_decide.py`)

| Date | Detections | estimate | +state | +decide | total p50 | total p95 | Budget |
|------|-----------|----------|--------|---------|-----------|-----------|--------|
| 2026-09-10 | 50 | 0.18ms | ~0ms | 0.02ms | 0.18ms | 0.28ms | <10ms ✅ |
| 2026-09-10 | 150 | 0.48ms | ~0ms | 0.03ms | 0.48ms | 0.66ms | <10ms ✅ |
| 2026-09-10 | 300 | 0.98ms | ~0ms | 0.02ms | 1.02ms | 1.68ms | <10ms ✅ (6× headroom) |
| 2026-09-13 | 50 | 0.30ms | ~0ms | 0.04ms | 0.30ms | 0.45ms | <10ms ✅ |
| 2026-09-13 | 150 | 0.81ms | ~0ms | 0.03ms | 0.56ms | 0.93ms | <10ms ✅ |
| 2026-09-13 | 300 | 1.13ms | ~0ms | 0.02ms | 1.11ms | 1.83ms | <10ms ✅ (5× headroom) |

Estimator scales ~3.3µs/detection (linear); decide path flat ~0.02ms.
Verdict: Steps 3–4 (estimator optimization) NOT needed — budget met with 6×
headroom at 300 boxes. Effort goes to durations (Step 1) + event triggering
(Step 2) + eval latency columns (Step 4).

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
| 2026-08-26 | unit+integration (`loop-fast` scope) | 7.4s ✅ (<30s target) |
| 2026-08-26 | unit+integration (post engine refactor) | 1.1–1.5s ✅ |

## Eval Matrix (`make eval`)

| Date | Scenarios | Wall | Notes |
|------|-----------|------|-------|
| 2026-08-26 | 11 scenarios × {adaptive, fixed} multiprocess | 22.4s | first scorecard: evals/results/scorecard_*.json |

Headline findings (see scorecard): adaptive scheduling cuts avg waiting time 76.5% on
5-way and 31% on 3-way; fixed-time competitive on balanced 4-ways. Queue-estimation
error scales with weather/degradation: 0.00 (clear/disciplined) → 0.76 (waterlogged)
→ 1.32 (5-way monsoon, fixed).
