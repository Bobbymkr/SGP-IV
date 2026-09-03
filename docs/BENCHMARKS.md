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
| — | pending Phase 5 ONNX tiering | — | deferred until DetectorPort adapters exist |

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
