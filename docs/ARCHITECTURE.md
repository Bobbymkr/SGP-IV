# Architecture Overview

**Last Updated:** 2026-09-03

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Adaptive Traffic Signal System                    │
├─────────────────────────────────────────────────────────────────────────┤
│  UI/API Layer (FastAPI + Streamlit)                                     │
│  ├── /api/v1/signals/*       → Signal control & NTCIP/J2735 endpoints   │
│  ├── /api/v1/detection/*     → Detection inference endpoints            │
│  ├── /api/v1/analytics/*     → Queue estimation, forecasting            │
│  └── /api/v1/health          → System health                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Services Layer (config.settings only)                                  │
│  ├── SignalControlService    → Controller factory, timing plans         │
│  ├── DetectionService        → DetectorPort factory, backends           │
│  ├── SimulationService       → TrafficSimulation, behavior, weather     │
│  ├── AnalyticsService        → QueueEstimator, RobustnessEvaluator      │
│  └── CityProfileService      → Profile registry, loader                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Core Domain (core/domain.py)                                           │
│  ├── VehicleType (8 classes)                                            │
│  ├── Direction (N/S/E/W + diagonals)                                    │
│  ├── VehicleDetection / DetectionResult                                 │
│  ├── SignalTiming / TrafficState                                        │
│  └── NTCIP/J2735 dataclasses (PhaseTiming, CycleConfig, BSM, SPAT, MAP) │
├─────────────────────────────────────────────────────────────────────────┤
│  Ports Layer (core/ports/)                                              │
│  ├── DetectorPort (base.py)     → detect(frame) → DetectionResult       │
│  ├── NTCIPPort (ntcip_port.py)  → STMP actuation + SNMP monitoring     │
│  └── J2735Port (ntcip_port.py)  → BSM receive + SPAT transmit          │
├─────────────────────────────────────────────────────────────────────────┤
│  Adapters Layer (adapters/ + core/detection/)                           │
│  ├── UltralyticsDetector      → YOLOv8 (dev, GPU)                       │
│  ├── OnnxDetector             → ONNX Runtime int8/fp32 (edge CPU/NPU)   │
│  ├── NTCIP1202STMPAdapter     → UDP STMP SET/GET (actuation)            │
│  ├── NTCIPSNMPAdapter         → SNMP GET/GETNEXT (monitoring)           │
│  ├── J2735Adapter             → UDP BSM rx + SPAT tx (V2X)              │
│  └── Mock adapters            → Testing without hardware                │
├─────────────────────────────────────────────────────────────────────────┤
│  Engine Layer                                                            │
│  ├── TrafficSimulation        → Microscopic sim, N-way scheduler        │
│  ├── BehaviorEngine           → 3 India presets (disciplined/urban/agg) │
│  ├── WeatherModel             → 4 states (clear/rain/monsoon/waterlog)  │
│  ├── Controllers (Fixed/Webster/Fuzzy/DQN)                             │
│  ├── QueueEstimator           → px_to_m, vehicle lengths, BSM fusion    │
│  └── RobustnessEvaluator      → Incident scenarios with city weights    │
├─────────────────────────────────────────────────────────────────────────┤
│  Configuration (config/)                                                 │
│  ├── settings.py              → Pydantic Settings + env vars            │
│  ├── city_profile.py          → CityProfile Pydantic schema             │
│  ├── city_profiles.py         → JSON loader + registry                  │
│  ├── city_profiles/*.json     → mumbai, delhi, bangalore, tier2_default │
│  └── device.yaml              → Hardware tier → backend/model mapping   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Dependency Rule

```
core/domain.py ← ports ← adapters
```

- **domain.py**: Pure dataclasses, no external deps
- **ports/*.py**: Abstract interfaces (ABCs)
- **adapters/*.py**: Concrete implementations
  - Heavy libs (torch, ultralytics, onnxruntime) ONLY inside adapters
  - UI/API import services and `config.settings` only
  - No cross-imports between UI/API/engine internals

## City Profile System

Single source of truth for city-specific parameters:

| Parameter | Mumbai | Delhi | Bangalore | Tier2 Default |
|-----------|--------|-------|-----------|---------------|
| Lanes/Approach | 4 | 4 | 3 | 3 |
| Behavior Preset | aggressive_metro | typical_urban | typical_urban | typical_urban |
| Weather Profile | heavy_monsoon | clear | light_rain | clear |
| Vehicle Mix | 2W heavy | 2W + Auto | 2W dominant | balanced |
| Signal Bounds | 15-90s | 15-80s | 10-70s | 10-60s |

**Runtime Selection**: `CITY_PROFILE` env var → `settings.city` → `get_city_profile(name)`

**Wiring Points**:
- QueueEstimator: vehicle lengths, detector calibration, px_to_m
- Controllers: min/max green, yellow, all-red, directions
- Simulation: behavior preset, weather state, vehicle properties, generation rates
- RobustnessEvaluator: incident weights
- Detectors: class mapping, per-class confidence thresholds

## NTCIP 1202 / J2735 V2X Integration

### STMP (Actuation) - UDP Port 5000
- **SET**: phase timing (green/yellow/red per phase), cycle length, offset
- **GET**: current phase timing state
- OIDs: phaseGreen, phaseYellow, phaseRed, cycleLength, offset
- Graceful degradation: logs failure → local simulation mode

### SNMP (Monitoring) - UDP Port 161
- Detector status: volume, occupancy, fault
- Fault table: code, description, severity
- Cycle counters: cycle number, phase, green elapsed
- Non-blocking: failures logged but don't block control loop

### J2735 V2X - UDP Ports 1735/1736
- **BSM Receive (1735)**: Vehicle position/speed/heading → queue refinement
- **SPAT Transmit (1736)**: Signal phase/timing → connected vehicles (10Hz)
- **MAP**: Static intersection geometry loaded from city profile
- Best-effort broadcast

## Detection Pipeline

```
Camera Frame → DetectorPort.create(backend, city_profile) 
    → UltralyticsDetector / OnnxDetector 
    → detect(frame) → DetectionResult[VehicleDetection]
        → QueueEstimator.estimate_from_detections()
            → LaneQueue / QueueEstimate (per-direction)
                → Controller.compute_timing(TrafficState)
                    → SignalTiming → NTCIP STMP SET → Controller
                    → J2735 SPAT → Connected Vehicles
```

**Backends**:
- `ultralytics` (default): YOLOv8, PyTorch, GPU/CPU
- `onnx`: ONNX Runtime int8/fp32, CPU/CUDA/NPU
- `tensorrt`: Falls back to ONNX (Phase 5)

## Simulation & Evaluation

### TrafficSimulation
- N-way intersection via compatibility graph scheduler
- Adaptive scheduling: max-demand group served
- 3 behavior presets × 4 weather states × incidents
- True vs observed queue (detection degradation modeled)

### Eval Matrix (make eval)
- 11 scenarios × 2 modes (adaptive vs fixed)
- Dimensions: geometry × discipline × weather × incident
- Metrics: avg wait, throughput, queue_error
- Regression flag vs previous scorecard

## Hardware Tiers (configs/device.yaml)

| Tier | Backend | Model | Quantization | Target FPS |
|------|---------|-------|--------------|------------|
| low  | onnx    | india-yolov8n | int8  | 5  |
| mid  | onnx    | india-yolov8s | fp32  | 15 |
| high | tensorrt| india-yolov8s | fp16  | 30+ |

## Verification Commands

| Command | Purpose |
|---------|---------|
| `make loop-fast` | Unit + integration tests (<30s) |
| `make verify` | Full test suite + lint + type-check |
| `make bench-sim` | Simulation throughput (steps/sec) |
| `make bench-detect` | Detection FPS/latency |
| `make eval` | Scenario matrix adaptive vs fixed |
| `make graph-update` | Refresh knowledge graph |

## Key Files

| File | Purpose |
|------|---------|
| `core/domain.py` | Shared domain types |
| `core/ports/ntcip_port.py` | NTCIP + J2735 port interfaces |
| `core/ports/detector.py` | DetectorPort ABC |
| `adapters/__init__.py` | Adapter factories |
| `config/city_profile.py` | CityProfile schema |
| `config/city_profiles.py` | Profile registry + JSON loader |
| `config/city_profiles/*.json` | 4 city profiles |
| `core/analytics/queue_estimator.py` | Queue length estimation |
| `core/analytics/robustness_eval.py` | Robustness evaluation |
| `core/control/controllers.py` | Signal controllers |
| `core/simulation/engine.py` | Microscopic traffic simulation |
| `core/detection/adapters_*.py` | Detection backends |
| `api/routes/signals.py` | REST + NTCIP/J2735 endpoints |
| `evals/runner.py` | Eval matrix runner |