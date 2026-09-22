# Adaptive Traffic Signal Timer

> AI-powered adaptive traffic signal control system with real-time vehicle detection, dynamic signal timing optimization, and predictive analytics. Tuned for Indian traffic conditions (heterogeneous vehicle mix, monsoon weather, 3/4/5-way geometries).

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-orange.svg)](https://ultralytics.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## BMD-45 Finale Results

Canonical model: `models/registry/india-yolov8n-final/` (Git LFS: fp32 ONNX, int8 ONNX, plus registry metadata).

| Metric | Value | Notes |
|--------|-------|-------|
| **mAP50 (full 10k val)** | **0.8477** | +0.0184 vs loop-8 (0.8293) |
| **Per-class mAP50** | car 0.9189, auto 0.9171, moto 0.8887, bus 0.8460, truck 0.8294, bicycle 0.6859 | Official BMD-45 10k val |
| **Inference speed** | **5.1-8.2 fps CPU (fp32)** | Low-tier runs fp32; see note below |
| **Model size** | 3.0M params (11.7 MB fp32 / 3.4 MB int8) | YOLOv8n, ONNX opset17 |
| **Training** | 8-loop chain (0.7949 to 0.8293) + 5-epoch joint polish at lr 0.002 from loop-8 | Colab T4; see `notebooks/` |
| **Eval matrix** | 11/11 adaptive wins over fixed-time | `make eval`; decide p95 under 3 ms at 300 detections |

Note (2026-09-21 Detector QA): the finale static-int8 artifact emits all-zero scores (degenerate quantization), so every pre-2026-09-21 int8 quality claim is void. Latency rows stand. Low tier runs fp32 (`prefer_int8: false` in `configs/device.yaml`) until a verified int8 is promoted. The TrafficCAM fine-tune candidate (+30% on TrafficCAM val) is staged as a local-only alternative registry, not promoted: finale stays canonical. Details in `docs/BENCHMARKS.md`.

---

## Overview

Camera frames flow through detection into queue estimation, then a policy pipeline decides green durations, phase order, and caps, and actuates via NTCIP STMP (with J2735 SPAT broadcast to connected vehicles). City profiles (Mumbai, Delhi, Bangalore, tier-2 default) carry lanes, behavior, weather, and calibration data so per-city tuning never touches code.

### Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Vehicle Detection** | YOLOv8 via ONNX Runtime (fp32/int8), Ultralytics (dev/GPU), TensorRT fp16 on Jetson with ONNX fallback |
| **Adaptive Signal Control** | Policy pipeline: weighted-discharge greens, clockwise order (argmax available), demand-share cap; manual and emergency-vehicle priority |
| **Closed-Loop Actuation** | `src/adaptive_traffic/core/closed_loop.py`: estimate to decide to NTCIP STMP SET; mock-STMP CI sim plus `--ntcip-ip` hardware handoff |
| **Queue Estimation** | Pixel-to-meter geometry, per-class vehicle lengths, BSM fusion; per-class breakdown feeds the green policy |
| **City Profiles** | JSON profiles + `CITY_PROFILE` env var drive lanes, headways, signal bounds, weather, incident weights |
| **NTCIP 1202 / J2735 V2X** | STMP actuation (UDP 5000), SNMP monitoring (UDP 161), BSM receive (1735) + SPAT transmit (1736) |
| **Simulation and Eval** | Microscopic N-way sim (compatibility-graph scheduler, India behavior presets, monsoon weather states); 11-scenario adaptive-vs-fixed matrix |
| **Monitoring** | Prometheus phase histograms (detect/estimate/decide/actuate) at `GET /api/v1/health/metrics` |
| **Live Dashboard and REST API** | Streamlit dashboard + FastAPI; staged pipeline (drop-oldest buffer) ready for the edge runner |

Legacy controllers (`Fixed`/`Webster`/`Fuzzy`/`DQN` in `src/adaptive_traffic/core/control/controllers.py`) are dormant alternatives, unwired from eval and closed-loop. Webster remains the documented fallback pattern.

---

## Architecture

```
UI/API Layer (FastAPI + Streamlit)
  /api/v1/signals/*      Signal control, timing plans, NTCIP/J2735 endpoints
  /api/v1/detection/*    Detection inference, cameras
  /api/v1/analytics/*    Forecast, queue metrics, recommendations
  /api/v1/health/*       Health, readiness, liveness, Prometheus metrics
Services Layer (config.settings only)
  SignalControlService / DetectionService / SimulationService /
  AnalyticsService / CityProfileService
Core Domain (core/domain.py: pure dataclasses, no external deps)
Ports Layer (core/ports/)
  DetectorPort  NTCIPPort (STMP actuation + SNMP monitoring)  J2735Port
Adapters Layer (adapters/ + core/detection/; heavy libs live ONLY here)
  UltralyticsDetector (dev/GPU)  OnnxDetector (edge CPU/NPU)
  TensorRTDetector (Jetson fp16, engine cache; ONNX fallback off-Jetson)
  NTCIP1202STMPAdapter  NTCIPSNMPAdapter  J2735Adapter  Mocks for tests
Engine Layer
  TrafficSimulation (N-way scheduler)  BehaviorEngine (3 India presets)
  WeatherModel (clear/rain/monsoon/waterlogged)  Timing policies
  (Headway/Green/Order/Cap in core/control/policies.py)
  QueueEstimator  RobustnessEvaluator  ClosedLoop (`src/adaptive_traffic/core/closed_loop.py`: estimate->decide->actuate)
Configuration (config/ + configs/)
  settings.py (Pydantic Settings + env)  city_profiles/*.json
  device.yaml (hardware tier -> backend/model mapping)
```

Dependency rule: `core/domain.py <- ports <- adapters`. UI/API import services and `config.settings` only. Full diagram and wiring points: `docs/ARCHITECTURE.md`.

### Hardware Tiers (`configs/device.yaml`)

| Tier | Backend | Model | Notes |
|------|---------|-------|-------|
| low | onnx (fp32; int8 until verified) | india-yolov8n-final | ~5 fps target on any CPU box |
| mid | onnx fp32 | india-yolov8n-final | GPU/NPU machines |
| high | tensorrt fp16 + engine cache, onnx fallback | india-yolov8n-final | Jetson; on-device latency validation pending hardware |

---

## Project Structure

```
.
├── README.md
├── configs/
│   ├── device.yaml               # hardware tier -> backend/model mapping
│   ├── development.yaml / staging.yaml / production.yaml
│   ├── city_profiles/            # mumbai, delhi, bangalore, tier2_default
│   ├── evals/scenarios.yaml      # eval matrix scenarios
│   └── docker/                   # compose, nginx, monitoring
├── src/adaptive_traffic/
│   ├── api/routes/               # health, signals, detection, analytics
│   ├── ui/                       # Streamlit app + pages
│   ├── config/                   # settings.py, city_profile.py
│   ├── core/
│   │   ├── domain.py             # shared dataclasses (no external deps)
│   │   ├── ports/                # DetectorPort, NTCIP/J2735 ports
│   │   ├── detection/            # ultralytics / onnx / tensorrt adapters
│   │   ├── control/policies.py   # canonical timing policies (Headway/Green/Order/Cap)
│   │   ├── control/controllers.py# dormant alternative controllers
│   │   ├── simulation/           # engine, behavior, weather
│   │   ├── analytics/            # queue_estimator, robustness_eval, forecaster
│   │   ├── closed_loop.py        # estimate -> decide -> actuate bridge
│   │   ├── pipeline.py           # staged pipeline (drop-oldest buffer)
│   │   └── monitoring.py         # Prometheus phase histograms
│   ├── adapters/                 # NTCIP STMP/SNMP, J2735 adapters + factories
│   └── services/                 # service layer (settings only)
├── evals/runner.py               # scenario matrix runner (make eval)
├── scripts/                      # bench_sim, bench_detect, bench_decide,
│                                 # run_closed_loop, score_queue, profile_device
├── tests/                        # unit / integration (+ performance, security)
├── notebooks/                    # train_bmd_finale_drive (canonical),
│                                 # train_bmd_loop (8-loop chain),
│                                 # train_trafficcam_loop, EDA/probe notebooks
├── models/registry/              # india-yolov8n-final (canonical, LFS);
│                                 # india-yolov8n-trafficcam (local-only alt)
├── docs/                         # ARCHITECTURE, BENCHMARKS, MASTER_PLAN (status board),
│                                 # DATASET_SPEC, SETUP_GUIDE, TESTING_DOCUMENTATION
├── .github/workflows/            # ci.yml, cd.yml
├── pyproject.toml
└── Makefile                      # loop-fast / verify / eval / bench-* targets
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (production only)
- CUDA-enabled GPU (recommended for training/dev detection; CPU suffices for sim + eval)

### Local Setup (Windows)

```powershell
git clone https://github.com/Bobbymkr/SGP-IV.git
cd SGP-IV

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
Copy-Item .env.example .env

.venv\Scripts\python.exe -m pytest tests/unit tests/integration -q -x --no-header -p no:cacheprovider
```

### Local Setup (Linux/macOS)

```bash
git clone https://github.com/Bobbymkr/SGP-IV.git
cd SGP-IV

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
cp .env.example .env

make loop-fast
```

### Verify, Evaluate, Benchmark

```bash
make verify      # full test suite + lint + type-check (canonical gate)
make eval        # 11-scenario adaptive-vs-fixed matrix
make bench-sim   # simulation throughput (target >= 500 steps/s)
make bench-detect# detection fps/latency against the registry model
```

`make` targets are the only verification interface (see `AGENTS.md`). `docs/BENCHMARKS.md` is updated on every `make bench-*` run; `docs/MASTER_PLAN.md` section 7 (status board) on every phase completion.

### Production Deployment

```bash
make docker-build
make docker-up

# Services:
# - API: http://localhost:8000
# - Dashboard: http://localhost:8501
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
```

---

## Usage

### Dashboard

```bash
make run-demo
# or: streamlit run src/adaptive_traffic/ui/app.py
```

Open `http://localhost:8501`. Pages: System Overview, real-time Dashboard, Live Demo simulation, Algorithm Comparison, Impact Metrics, Settings.

### API Server

```bash
make run-dev
# or: uvicorn adaptive_traffic.api.main:app --reload --host 0.0.0.0 --port 8000
```

Docs: `http://localhost:8000/docs`. Metrics (when `PROMETHEUS_ENABLED=true`): `http://localhost:8000/api/v1/health/metrics`.

#### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Health check (`/ready`, `/live`, `/version`, `/metrics` alongside) |
| `GET /api/v1/signals/` | List signal controllers |
| `POST /api/v1/signals/{id}/timing` | Push timing via STMP |
| `GET /api/v1/signals/{id}/health` | SNMP monitoring status |
| `GET /api/v1/signals/{id}/v2x/queue-refinement` | BSM-based queue refinement |
| `POST /api/v1/signals/{id}/v2x/spat` | SPAT transmit |
| `POST /api/v1/detection/detect` | Detect vehicles in image (`/detect/batch`, `/cameras/*` alongside) |
| `POST /api/v1/analytics/forecast` | Traffic forecast |
| `GET /api/v1/analytics/recommendations/{id}` | Timing recommendations |

### Simulations

```python
from adaptive_traffic.config.city_profiles import get_city_profile
from adaptive_traffic.core.simulation.engine import create_intersection, create_simulation

city = get_city_profile("mumbai")
sim = create_simulation({"time_step": 0.1, "max_time": 3600}, city_profile=city)
sim.add_intersection(create_intersection(
    {"id": "main", "approaches": ["north", "south", "east", "west"]},
    city_profile=city,
))

for _ in range(1000):
    sim.step()
    if _ % 100 == 0:
        print(sim.get_network_stats())
```

### Closed-Loop Run (mock STMP by default)

```bash
python scripts/run_closed_loop.py --help
# aim at real hardware: python scripts/run_closed_loop.py --ntcip-ip <controller-ip>
```

---

## Training Workflow

| Notebook | Purpose |
|----------|---------|
| `notebooks/train_bmd_finale_drive.ipynb` | Canonical finale: 5-epoch polish from loop-8 at lr 0.002, ONNX export, int8 quant, registry packaging |
| `notebooks/train_bmd_loop.ipynb` | 8-loop cumulative chain (`images_000` to `images_007`), 20 + 7x12 epochs from COCO |
| `notebooks/train_trafficcam_loop.ipynb` | TrafficCAM fine-tune (staged candidate, not promoted) |

Flow per loop: prep (COCO to YOLO, PNG to JPG) -> train -> validate on official 10k val -> export ONNX opset17 -> quantize -> package `models/registry/<name>/` (fp32 ONNX + int8 ONNX + metadata JSON) -> update `configs/device.yaml`. Data contract: `docs/DATASET_SPEC.md`.

---

## Configuration

Common environment variables (full list in `.env.example`; schema in `src/adaptive_traffic/config/settings.py`):

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | development / staging / production |
| `API_HOST` / `API_PORT` | `0.0.0.0` / `8000` | API server bind |
| `YOLO_MODEL_PATH` | `yolov8n.pt` | Fallback model; registry via `configs/device.yaml` |
| `YOLO_CONFIDENCE_THRESHOLD` | `0.5` | Base confidence (low tier uses 0.45) |
| `CONTROLLER_TYPE` | `dqn` | Legacy selector; canonical path is the policy pipeline |
| `MIN_GREEN_TIME` / `MAX_GREEN_TIME` | `10` / `60` | Signal bounds (city profiles override) |
| `CITY_PROFILE` | `tier2_default` | mumbai / delhi / bangalore / tier2_default |
| `NTCIP_CONTROLLER_IP` / `NTCIP_STMP_PORT` | `127.0.0.1` / `5000` | STMP actuation target |
| `J2735_BSM_PORT` / `J2735_SPAT_PORT` | `1735` / `1736` | V2X receive / transmit |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache connection |
| `DATABASE_URL` | `sqlite+aiosqlite:///./adaptive_traffic.db` | Database URL |

Environment-specific YAML in `configs/`. City JSONs in `config/city_profiles/` (select with `make set-city CITY=mumbai`).

---

## Testing

```bash
make loop-fast   # unit + integration, <30s target
make verify      # full suite + flake8 + mypy (pre-push gate)
```

Marker subsets (`-m unit|integration|performance|security`) exist for focused runs; the gates above are what CI enforces (`.github/workflows/ci.yml`). Test conventions and the hand-count ground-truth protocol for queue error: `docs/TESTING_DOCUMENTATION.md`.

---

## Monitoring

- Prometheus scrape: `http://localhost:8000/api/v1/health/metrics` (404 when `PROMETHEUS_ENABLED=false`)
- Phase histograms: `traffic_detect_seconds`, `traffic_estimate_seconds`, `traffic_decide_seconds`, `traffic_actuate_seconds`
- Key signals: average wait, throughput, queue-estimation error, cycle length, detection fps, decide-path p50/p95 (budget: under 10 ms)

---

## Security

- JWT-based API auth (`SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Configurable CORS origins; per-endpoint rate limits
- Pydantic schema validation on all inputs
- Bandit + Safety scans in CI; change `SECRET_KEY` before any deployment

---

## Contributing

1. Fork and create a feature branch: `git checkout -b feature/amazing-feature`
2. Run `make loop-fast` early and `make verify` before pushing
3. Follow code standards: Black (line length 100), isort (Black profile), flake8, mypy, Google-style docstrings
4. Update `docs/BENCHMARKS.md` after any `make bench-*` run and `docs/MASTER_PLAN.md` section 7 after any phase
5. Open a Pull Request against `development`

Heavy ML/CV imports (`torch`, `ultralytics`, `onnxruntime`) belong only inside detection adapters. UI/API layers import services and `config.settings` only.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Ultralytics YOLOv8 for object detection
- FastAPI, Streamlit, PyTorch, OpenCV
- BMD-45 and TrafficCAM dataset providers for training and evaluation data

---

## Support

- Issues: [GitHub Issues](https://github.com/Bobbymkr/SGP-IV/issues)
- Discussions: [GitHub Discussions](https://github.com/Bobbymkr/SGP-IV/discussions)
