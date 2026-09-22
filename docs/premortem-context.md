# Premortem Context — Adaptive Traffic Signal Timer

*Input brief for the premortem run of 2026-09-03. Sources: `docs/MASTER_PLAN.md` (locked decisions D1–D10, phase status board), `docs/BENCHMARKS.md`, `configs/device.yaml`, `configs/evals/scenarios.yaml`, `docs/DATASET_SPEC.md`, `orca-pipeline.yaml`, `vault/`.*

## What is it?

An AI-powered adaptive traffic-signal control system for Indian intersections (3/4/5-way), engineered around loop engineering (Makefile-gated verification: `loop-fast` / `verify` / `eval` / `bench-sim`) and graph engineering (graphify knowledge graph), with India-specific edge cases (driver-discipline presets, monsoon weather states, autorickshaws) and device-versatile deployment (ONNX int8 / TensorRT tiering selected by `configs/device.yaml`).

## Who is it for?

Indian Adaptive Traffic Control System (ATCS) deployments — BATCS-style programs running mixed edge hardware (Jetson TX2→Orin NX, RK3588 NPU boxes, legacy x86 IPCs) across many junctions — plus the solo developer maintaining the project.

## What does success look like?

`MASTER_PLAN` §5: loop-fast <30s PASS · eval matrix covering geometry × discipline × weather × incident × tier PASS (synthetic) · queue error demonstrably distorted by edge cases PASS (0.00→1.32) · sim ≥500 steps/s PASS (28,503 = 57×) · same codebase serves CPU-only box → Jetson via `device.yaml` alone PENDING · N-way scheduler 3/4/5-way from config PASS · graphify current PASS. Ultimate goal: adaptive control beating fixed-time on **real** deployments.

## Remaining work (the plan under test)

- **Phase 5 (partial):** speed ladder NumPy→Numba→(Rust only if walled); PyTorch→ONNX export + int8 static quantization calibrated on Indian frames; TensorRT adapter; pipeline (uvloop, ring buffer); Prometheus histograms.
- **Phase 6 (continuous):** `docs/device-tiers.md`; tier/device matrix; hybrid-detector trigger log.
- **Phase T (ready, blocked on data):** awaiting authority footage → `prepare_dataset.py` convert → `--check` → Colab T4 training (yolov8n @70ep) → int8 export → registry zip → rerun eval matrix.
- **Orca autobuild (wired):** 5-phase pipeline, `resume.ps1` power-cut resume, vault mirror, freelm 6-pool.

## Locked decisions shaping the remaining path

D3 synthetic weather (pluggable IMD port later) · D5 ONNX tiering, never Orin-specific · D6 tier-low = interpolation-only queue estimation, hybrid upgrade only "if eval shows queue error above tolerance" (**tolerance value never defined**) · D8 Python stays · D1 legacy runners deleted.

## Current evidence base

- Eval matrix: 11 **synthetic** scenarios ×2 modes, 22.4s wall; adaptive −76.5% avg wait on 5-way, −31% on 3-way; queue_error gradient 0.00→1.32 across weather/discipline axes.
- `BENCHMARKS.md`: one sim row (28,503 steps/s); **zero** bench-detect rows; test suite 1.1–1.5s.
- `DATASET_SPEC.md` v1: 6 classes, PROVISIONAL flag (tempos/e-rickshaws/tractors expected); calibration set ~200 frames (≥30% rain-affected).
- All validation to date is synthetic: no real footage, no hardware-in-the-loop run, no real detector fps measurement anywhere.
