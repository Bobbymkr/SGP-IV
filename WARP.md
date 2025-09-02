# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- Python project implementing an adaptive traffic signal controller using YOLO (Darkflow/TensorFlow 1.x) for vehicle detection and a Pygame-based intersection simulation.
- Core code lives under Code/YOLO/darkflow/.
- Key entry points:
  - vehicle_detection.py: runs object detection on images in test_images/ and writes annotated outputs to output_images/.
  - simulation.py: runs a visual traffic intersection simulation and adaptive signal timing loop.

Prerequisites
- Python 3.8+ (successfully tested with Python 3.13)
- Modern TensorFlow 2.x, OpenCV, Pygame, and supporting libraries
- Note: Original project required Python 3.7 + TensorFlow 1.13.1, but this has been modernized

Environment setup
- Create and activate a virtual environment (examples below use PowerShell on Windows):
  - python -m venv .venv
  - . .venv/Scripts/Activate.ps1
- Install modern dependencies from the darkflow directory:
  - cd Code/YOLO/darkflow
  - pip install tensorflow opencv-python pygame matplotlib Pillow Cython numpy

Common commands
- Run complete project demo (detection + simulation):
  - cd Code/YOLO/darkflow
  - python run_project.py --demo
- Run vehicle detection only (modernized version with mock YOLO):
  - cd Code/YOLO/darkflow
  - python vehicle_detection_modern.py
- Run traffic simulation only (opens Pygame window):
  - cd Code/YOLO/darkflow
  - python simulation.py
- Show project information:
  - cd Code/YOLO/darkflow
  - python run_project.py --info
- Clean compiled artifacts:
  - cd Code/YOLO/darkflow
  - Remove-Item -Recurse -Force build, *.pyd, **\__pycache__ 2>$null

Notes on linting/tests
- No formal test suite or linter configuration is present. There are no pytest/unittest configs or CI workflows in the repo root. Development is manual and script-driven.

High-level architecture
- Modules (as also summarized in README):
  1) Vehicle Detection Module (vehicle_detection.py)
     - Uses darkflow (a TensorFlow 1.x-based reimplementation of YOLO) to load YOLOv2 config/weights and run detections.
     - Configuration is provided via options dict:
       - model: ./cfg/yolo.cfg
       - load: ./bin/yolov2.weights
       - threshold: 0.3
     - Reads images from ./test_images/, writes annotated outputs to ./output_images/.
     - Entry point at bottom iterates files and calls detectVehicles(filename).
  2) Signal Switching Algorithm (embedded in simulation.py)
     - TrafficSignal class stores red/yellow/green and min/max parameters.
     - Global state: signals[], currentGreen/nextGreen/currentYellow, counts per direction, per-lane vehicle queues.
     - setTime() computes next green duration based on estimated queue composition using per-class service times (carTime, busTime, etc.), bounded by defaultMinimum/defaultMaximum. Detection via YOLO is stubbed out (commented), and current implementation infers counts from simulated queue objects.
     - repeat() drives a cyclic state machine: counts down green, triggers detection window at detectionTime of the upcoming signal, transitions through yellow, resets defaults, and advances to the next signal. Runs continuously using time.sleep(1) ticks.
  3) Simulation Module (simulation.py)
     - Pygame visualization of a 4-way intersection with three lanes per approach and discrete vehicle sprites per class and direction.
     - Vehicle objects have per-class speeds and follow car-following gaps (gap/gap2). Turning behavior is modeled for a subset of vehicles on the inner lane via rotation of the sprite around a mid intersection.
     - Threads:
       - initialization: initializes signals and starts the repeat() loop.
       - generateVehicles: continuously spawns vehicles with randomized class, lane, direction, and turn intent.
       - simulationTime: tracks wall time, prints per-lane throughput and exits after simTime seconds.
     - Main loop draws background, signals (with current timer text), vehicle counts per approach (vehicles[direction]['crossed']), and advances vehicle motion.

Assets and required paths
- Code/YOLO/darkflow/bin/yolov2.weights: required at runtime for vehicle_detection (and for any future live detection integration).
- Code/YOLO/darkflow/cfg/*.cfg and data files: model configuration files used by darkflow/TFNet.
- Code/YOLO/darkflow/images/: sprites for vehicles, signals, and intersection background required by simulation.py.
- Code/YOLO/darkflow/test_images/ and output_images/: image input/output folders for vehicle_detection.py. Create them if missing.

Platform considerations
- Windows: Works with modern Python versions (3.8+). No special build tools required for the modernized version.
- macOS/Linux: Should work with the modernized dependencies and Python 3.8+.
- Note: Original darkflow framework is incompatible with TensorFlow 2.x, so a modernized mock detection system is provided.

Modernization notes
- Original vehicle_detection.py requires TensorFlow 1.x and darkflow framework
- Created vehicle_detection_modern.py that works with TensorFlow 2.x and modern Python
- Mock detection system simulates YOLO results for demonstration purposes
- Fixed Windows compatibility issues in simulation.py (replaced 'say' command with print)
- Added run_project.py as a comprehensive launcher script
- All core functionality preserved while updating dependencies

Repository documentation highlights
- readme.md provides a step-by-step setup and run guide, demo images/GIF, and a PDF with deeper implementation details. Follow its Step II (weights placement) and Step III (requirements + build) closely before running scripts.

