# Adaptive Traffic Signal Timer - Setup Guide

## Overview

This document provides instructions for setting up and running the Adaptive Traffic Signal Timer: FastAPI control plane + Streamlit operations dashboard + YOLOv8 detection + microscopic simulation.

## Quick Setup and Run (Windows)

```bash
cd C:\Users\Admin\OneDrive\Desktop\IDEA\Adaptive-Traffic-Signal-Timer
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Verify the install (canonical gates — these are the ONLY verification entry points):

```bash
.venv\Scripts\python.exe -m pytest tests/unit tests/integration -q -x --no-header -p no:cacheprovider
.venv\Scripts\python.exe evals/runner.py
```

Start the services (two terminals, venv activated):

```bash
# Terminal 1 - API on http://localhost:8000 (docs at /docs)
.venv\Scripts\python.exe -m uvicorn adaptive_traffic.api.main:app --port 8000

# Terminal 2 - dashboard on http://localhost:8503
.venv\Scripts\python.exe -m streamlit run src/adaptive_traffic/ui/app.py --server.port 8503
```

> Use the venv interpreter (`.venv\Scripts\python.exe -m ...`). A bare `streamlit` or
> `uvicorn` resolves the system install, which does not have this package.

Or via Make on Linux/macOS: `make run-dev` and `make run-demo`.

## Drive-Native Training (Colab T4)

For the training pipeline, see the notebooks (no local GPU needed):

1. `notebooks/train_bmd_loop.ipynb` - 8-loop cumulative chain (canonical BMD-45 training)
2. `notebooks/train_bmd_finale_drive.ipynb` - 5-epoch joint polish from loop-8 best
3. `notebooks/eval_trafficcam_drive.ipynb` - TrafficCAM eval (CPU-friendly)
4. `notebooks/train_trafficcam_loop.ipynb` - TrafficCAM fine-tune (T4) + registry candidate
5. `notebooks/pseudo_itd_x.ipynb` - ITD-X reference eval + pseudo-labels (T4)
6. `notebooks/val_int8_drive.ipynb` - fp32 vs int8 full-val anchor, no training (CPU-friendly)
6. Hand-back zips go in `notebooks/training_output_zips/` (gitignored, local-only)

## Required Packages (Already Installed)

All required packages are already present in your Python environment:
- **streamlit** - For the web interface
- **numpy** - For numerical computations
- **pandas** - For data handling
- **altair** - For data visualization
- **Pillow** - For image handling
- **opencv-python** - For computer vision (if needed)

## WARNING Installation Notes

You may see warnings about matplotlib during installation. These can be safely ignored as:
1. The enhanced demo doesn't directly use matplotlib
2. All required functionality is provided by other packages (altair for visualization)
3. The warnings don't affect demo performance

## Demo Features

Six pages in the sidebar. Every number on screen is labelled **MEASURED** (read from disk),
**ILLUSTRATION** (modelled) or **SPEC** (not built in this release) - so you always know
which is which.

### 1. **System Overview**
- What the system does, in plain English (4 steps: watch -> analyse -> optimise -> adapt)
- Proof cards read from the registry and the eval scorecards (11/11 scenes, 84.8% mAP50)
- City configuration for the selected city, and a glossary of the jargon used

### 2. **Dashboard** (simulated city)
- Traffic volumes, signal states and alerts for a modelled city - all marked ILLUSTRATION
- Tabs: Traffic Metrics, Signal Status, Performance, Alerts
- The Performance tab carries the measured strip (wait-time cut, mAP50, decide p95, CPU fps)

### 3. **Live Demo**
- **Real pipeline**: runs the detector on real Indian CCTV frames (TrafficCAM val), real
  queue estimate, real signal plan, on a mock signal box. Cancellable, with the last run and
  the session run history shown. Frame source is printed from the run itself.
- **Simulated junction**: sliders that re-plan green time instantly - marked ILLUSTRATION
  and walled off from the real run (the sliders never touch it)

### 4. **Algorithm Comparison**
- The measured eval matrix: adaptive vs fixed timing per scene, read from the scorecards
- The Surat 15-scene card, and an honest note that DQN / Webster / Fuzzy are dormant backups

### 5. **Impact Metrics**
- Measured strip first, then modelled projections priced with dated Indian rates
- Your city inputs (intersections, traffic per intersection) drive every projection
- Breakdowns (pollutants, money split, 5-year view) sit behind a disclosure

### 6. **Settings**
- **Configuration**: the knobs that really feed the pipeline run (city, confidence, model
  registry, backend, frame counts) plus the engine defaults, read-only
- **API & Integration**: every route the FastAPI app really serves (35 of them) - and the
  honest note that this build has no authentication, so do not expose it publicly
- **Emergency Priority / Weather Adaptation / Pedestrian**: specification only, with the
  reason each is not in this build (for example, the detector has no emergency class)

## Key Benefits Demonstrated

### Performance Improvements
- **Wait time cut 19-75%** vs fixed timing, measured in 11/11 eval scenes
- **Decide p95 0.10 ms** (budget 10 ms), measured
- **30% faster emergency response** - *not implemented in this build* (see Settings)

### Environmental Impact (modelled, ILLUSTRATION)
- **47,128 litres of fuel saved** per intersection per year
- **124 tonnes of CO2 reduction** per intersection per year (~80 cars' worth of emissions)
- **15,333 vehicle-hours** of waiting saved per intersection per year

### Economic Value (modelled, priced with dated Indian rates)
- **Rs 15.3 lakh per intersection per year** in fuel + time value
- **Rs 111.21/L petrol** (Mumbai, 21 Oct 2026); the rate follows the city you pick
- Rates used: petrol/diesel per city, 1 USD = Rs 94.77, carbon Rs 8,150/t (IISD social cost)
- Source of truth: `src/adaptive_traffic/ui/_india.py` (every constant dated and attributed)

## For Non-Technical Audiences

The demo is specifically designed to be accessible to all users:
- **Plain Language**: glossary on the Overview page, plain-English taglines on every block
- **Visual Learning**: Charts and diagrams explain concepts
- **Interactive Elements**: Hands-on experimentation
- **Immediate Feedback**: the pipeline run refreshes every second and can be cancelled
- **Contextual Help**: explanations when you need them

## Navigation Tips

1. Use the sidebar to switch between the six pages
2. Start with "System Overview" for context
3. "Live Demo" runs the real pipeline - press the button and watch the output
4. Compare approaches in "Algorithm Comparison" (this is the measured proof)
5. "Impact Metrics" shows what the impact could be worth, in rupees, with today's rates
6. "Settings" shows what is actually configurable

## Troubleshooting

### If the demo doesn't start:
1. Make sure you're in the correct directory
2. Use the venv interpreter: `.venv\Scripts\python.exe -m streamlit run src/adaptive_traffic/ui/app.py --server.port 8503`
3. If you get `ModuleNotFoundError: adaptive_traffic`, you launched the system Streamlit
   instead of the venv one - use the command above

### If the port is busy:
- Pick another one: `--server.port 8504` (the app works on any port)

### If you see matplotlib warnings:
- These can be safely ignored
- They don't affect demo functionality
- The demo uses altair for visualization instead

### If the browser doesn't open automatically:
- Go to http://localhost:8503 in your browser
- The port number may change (8501, 8502, 8503, etc.)

## Support

For questions about this demo or the underlying technology:
- Contact the development team
- Check the main README files for technical details
- Refer to `docs/ARCHITECTURE.md` for how the system is wired, and
  `sgp-ppt-handoff/01-PROJECT-FACTS.md` for the exact verified numbers

---
*What works today: the detector, the queue estimate, the adaptive plan and the closed loop,
measured on the eval matrix and on real traffic photos. What is not connected yet: a live
camera feed and a real signal box. The dashboard labels every number accordingly.*
