# 03 — Serving Indian traffic

## What "India-tuned" means (3 knobs)
1. Classes + thresholds: 6-class head; lower floors for small agents (two_wheeler/auto/cycle ≈0.4/0.4/0.35 vs 0.45 base) — recall on what Indian junctions actually contain.
2. City profiles (`config/city_profiles/`: mumbai, delhi, bangalore, tier2_default): vehicle_mix (e.g. Mumbai car .45 two_wheeler .25 auto .12), vehicle_lengths, signal_bounds (min 15 / max 90 / yellow 5 / all_red 3), behavior `aggressive_metro`, weather `heavy_monsoon`, detector_calibration per approach, ntcip_config. Switch city = switch file, no code change.
3. Actuation: NTCIP-1202 STMP/SNMP + J2735 SPAT/MAP/BSM (`src/adaptive_traffic/adapters/`, `core/ports/ntcip_port.py`). `run_closed_loop.py:5-8` — same loop aims at mock or real controller via `--ntcip-ip`.

## Decide rule (one line)
`policies.py`: green = `startup + Σ(n_class × headway_class)` with per-class discharge table (city-overridable), clockwise order, dynamic cap from cycle budget; manual protocol suppresses EVP on its route only; MARL slot is a no-op `Independent` today.

## Proof it matters
`evals/results/scorecard_1789305524.json`: 11/11 adaptive wins, e.g. x5way_typical_clear wait 11.09s vs 54.28s fixed (-79.6%), x4way_aggressive wait -47%, heavy_monsoon -55%, waterlogged -61%; dec_p95 ≤0.7ms (typical ≤0.13, budget 10ms); Surat incident rows (rally -32.3%, cattle -27.9%, VIP -24.8%, typical -41.1%, qerr 0.12-0.41) in `evals/results/scorecard_1790419766.json` (15/15 wins). Estimator geometry is now per-camera (`DetectorCalibration.frame_width_px/height_px`, legacy 640x480 default); STMP GET parses real varbinds on loopback (9 wire tests).

## Trace
`config/city_profiles/mumbai.json:4-43`; `src/adaptive_traffic/core/control/policies.py:1-17`; `src/adaptive_traffic/core/analytics/queue_estimator.py:1-14`; `configs/evals/scenarios.yaml:11-29`.
