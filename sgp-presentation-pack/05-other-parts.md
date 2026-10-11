# 05 — Other parts (3-min sweep)

## Decide brain — `core/`
- `control/policies.py`, `controllers.py`: adaptive vs fixed, green split, EVP + manual override.
- `analytics/queue_estimator.py`, `forecaster.py`, `robustness_eval.py`: queues, demand forecast, degradation.
- `domain.py:11-74`: VehicleType, DetectionResult, SignalTiming, TrafficState. `monitoring.py`: Prometheus per-stage.

## World model — `core/simulation/`
`engine.py` 28,503 steps/s (57× target, `BENCHMARKS.md:10`); `behavior.py` disciplined/typical/aggressive; `weather.py` clear/rain/monsoon/waterlogged.

## Serve — `api/` + `ui/`
`api/routes/`: detection, signals, analytics, health; `api/main.py` (mock detections today). `ui/pages/`: overview, dashboard, live_demo, comparison, metrics; `ui/replay.py` replays logged frames — use for hall backup video.

## Train/eval/proof
Notebooks: loop, finale_drive (canonical, dual-path Drive prep + v6 recipe), finale (legacy), eval_trafficcam_drive, val_int8_drive (anchor-only), probe/EDA/pseudo. Evals: `configs/evals/scenarios.yaml` 11 scenarios ×2 (adaptive/fixed), `evals/runner.py`, `evals/results/scorecard_1789305524.json` 11/11 wins. Tests: `tests/{unit,integration,performance,security}` (102 passed 2026-10-11); gates `make loop-fast / verify / eval`.

## Ship/ops
`configs/docker/` compose + nginx; `scripts/profile_device.py` → `configs/device.yaml` tiers; TensorRT falls back to onnx until engine built; `scripts/run_production.py`, `run_closed_loop.py --ntcip-ip` = hardware handoff.

## Knowledge
`docs/MASTER_PLAN.md`, `ARCHITECTURE.md`, `TRACK_RECORD.md`, `INDUSTRY_DEMO.md`, `demo-deck/bmd-finale.html`, `agent-memory/`, `graphify-out/`.
