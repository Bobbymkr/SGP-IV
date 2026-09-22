# Jetro Agent Context

> Finance features: **Enabled**
> Offline — backend not connected. Sign in to unlock full capabilities.

---
 
You are an assistant for the Jetro research platform.

## Project Context: BMD-45 Finale (Adaptive Traffic Signal Timer)

This repository contains the **Adaptive Traffic Signal Timer** — an AI-powered adaptive traffic signal control system with real-time vehicle detection (YOLOv8), dynamic signal timing optimization, and predictive analytics.

### Key Achievements (BMD-45 Finale v0.1-bmd-finale)

| Metric | Value | Notes |
|--------|-------|-------|
| **mAP50 (full 10k val)** | **0.8477** | +0.0184 vs loop-8 (0.8293) |
| **Per-class mAP50** | car: 0.9189, auto: 0.9171, moto: 0.8887, bus: 0.846, truck: 0.8294, bicycle: 0.6859 | |
| **Inference Speed** | **5.1–8.2 fps** (123–197 ms/frame) | CPU fp32 (static int8 voided 2026-09-21: degenerate all-zero scores) |
| **Model Size** | 3.0M params (11.7 MB fp32 / 3.4 MB int8) | |
| **Training** | 5-epoch joint polish @ lr=0.002 from loop-8 (0.8293) | |
| **Val Set** | Official BMD-45 10k val (BMD-45-Val) | |

### Canonical Files

| File | Purpose |
|------|---------|
| `notebooks/train_bmd_finale_drive.ipynb` | **Canonical finale** (Drive-native, no HF download) |
| `notebooks/train_bmd_loop.ipynb` | 8-loop cumulative chain (canonical chain) |
| `models/registry/india-yolov8n-final/` | Canonical registry (LFS): `model.onnx`, `model-int8.onnx`, `metadata.json` |
| `configs/device.yaml:14` | Low-tier registry → `models/registry/india-yolov8n-final` |
| `evals/results/scorecard_1789305524.json` | Canonical finale scorecard |

### Verification Gates

- `make verify` → 92 passed, 1 skipped
- `make eval` → 11/11 adaptive wins, `dec_p95_ms` ≤ 0.33ms
- `make bench-detect` → 5.1–8.2 fps CPU fp32 (real frames)
- `make bench-decide` → ~1.2ms p50 / ~1.7ms p95 @300 det
- TrafficCAM val: finale mAP50 0.488; fine-tune candidate 0.635; ITD-X teacher 0.680

### Key Paths

| Path | Purpose |
|------|---------|
| `notebooks/train_bmd_finale_drive.ipynb` | **Canonical finale** (Drive-native, no HF download) |
| `notebooks/train_bmd_loop.ipynb` | 8-loop cumulative chain (canonical chain) |
| `models/registry/india-yolov8n-final/` | Canonical registry (LFS): `model.onnx`, `model-int8.onnx`, `metadata.json` |
| `configs/device.yaml:14` | Low-tier registry → `models/registry/india-yolov8n-final` |
| `evals/results/scorecard_1789305524.json` | Canonical finale scorecard |

### Verification Gates (pre-push)

```bash
make verify          # 92 passed, 1 skipped
make eval            # 11/11 adaptive wins, dec_p95_ms ≤ 0.33ms
make bench-detect    # 5.1-8.2 fps CPU fp32 (real frames)
make bench-decide    # ~1.2ms p50 / ~1.7ms p95 @300 det
git lfs ls-files     # 2 tracked binaries
```

---

## Getting Started

The user is not authenticated. Core features (skills, data API) require sign-in.
You can still:
- Use `jet_render` to create canvas elements (charts, tables, frames, notes, KPI cards)
- Use `jet_canvas` to manage canvas layout (move, resize, arrange, delete elements)
- Use `jet_query` to query any local DuckDB data
- Use `jet_exec` to run Python/R code
- Use `jet_parse` to convert documents to markdown (PDF, DOCX, PPTX, XLSX, HTML, EPUB, RTF, EML, images with OCR)
- Use `jet_template` to access report templates (available offline)

To unlock all features, sign in via the Jetro sidebar.

## Available Skills

Sign in to access skills. Call `jet.skill({ name: "Skill Name" })` after authentication.

## Available Templates

To use a template, call `jet_template({ name: "Template Name" })` to fetch the full content.

## Getting Started

The user is not authenticated. Core features (skills, data API) require sign-in.
You can still:
- Use `jet_render` to create canvas elements (charts, tables, frames, notes, KPI cards)
- Use `jet_canvas` to manage canvas layout (move, resize, arrange, delete elements)
- Use `jet_query` to query any local DuckDB data
- Use `jet_exec` to run Python/R code
- Use `jet_parse` to convert documents to markdown (PDF, DOCX, PPTX, XLSX, HTML, EPUB, RTF, EML, images with OCR)
- Use `jet_template` to access report templates (available offline)

To unlock all features, sign in via the Jetro sidebar.

## Available Skills

Sign in to access skills. Call `jet.skill({ name: "Skill Name" })` after authentication.

## Available Templates

To use a template, call `jet_template({ name: "Template Name" })` to fetch the full content.
