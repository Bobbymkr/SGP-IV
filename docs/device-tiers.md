# Device Tiers & Supported Hardware Matrix

> **MASTER_PLAN D5 / Phase 6** — This document defines the three hardware tiers used by
> `configs/device.yaml`. The goal is **device-versatile** operation across the fragmented
> Indian ATCS deployment landscape (Bengaluru BATCS runs mixed hardware across 165+
> junctions). Never Orin-specific — tiers are defined by *available compute*, not device SKU.

Run `make profile-device` to auto-detect and write `active_tier`.

---

## Tier Definitions

| Tier | Typical Hardware | Detection Backend | Expected FPS (baseline) | Queue-Estimation Notes |
|------|------------------|-------------------|------------------------|------------------------|
| **low** | x86 IPC, ARM SBC, legacy boxes — CPU only, no GPU | ONNX Runtime int8 (CPUExecutionProvider) | ~4.98 fps on india-yolov8n-final (int8) | Interpolation-only (D6). Frames skipped when inference > time-step; queue estimates interpolated from last two frames. |
| **mid** | Jetson TX2 / Xavier NX, RK3588 NPU boxes — GPU/NPU present | ONNX Runtime fp32 (CUDAExecutionProvider or NPU provider if available) | ~10–25 fps on yolov8n-final (fp32) | Full-frame detection each step. Confidence threshold standard (0.5). |
| **high** | Jetson Orin NX / AGX, discrete GPU boxes — TensorRT-capable | TensorRT fp16 (engine built+cached on-device at first boot in `models/trt_cache/`) | fp16 path TBD; until then same as mid on `-final` fp32 | Same as mid, but with fp16 speed. **Adapter pending Phase 5** — currently falls back to ONNX fp32 with a warning. |

> **Note on "mid" NPU providers:** onnxruntime 1.16+ supports `QNNExecutionProvider` (Snapdragon) and vendor-specific NPU providers. If present, `profile-device` detects them as CUDA-equivalent and selects `mid`.

---

## Device Matrix (Indian deployments)

| Device / Platform | Tier | Rationale | Notes |
|-------------------|------|-----------|-------|
| Generic x86 IPC (Intel i5/i7, 8–16GB) | low | CPU only | Common in legacy fixed-time cabinets upgraded to adaptive |
| RK3588 SBC (8-core A76/A55, Mali-G610, 6 TOPS NPU) | mid | NPU → onnxruntime QNN/NPU provider when available | Emerging in municipal tenders |
| NVIDIA Jetson TX2 (Pascal 256 CUDA) | mid | GPU present, fp32 only | Bengaluru BATCS installed base |
| NVIDIA Jetson Xavier NX (Volta 384 CUDA) | mid | GPU present, fp32/int8 | |
| NVIDIA Jetson Orin NX / AGX (Ampere, Tensor Cores) | high | TensorRT fp16 engine builds on-device | Highest tier; same code via `device.yaml` |
| Generic x86 IPC (Intel i5/i7, 8–16GB) | low | CPU only | Common in legacy fixed-time cabinets upgraded to adaptive |
| RK3588 SBC (8-core A76/A55, Mali-G610, 6 TOPS NPU) | mid | NPU → onnxruntime QNN/NPU provider when available | Emerging in municipal tenders |
| NVIDIA Jetson TX2 (Pascal 256 CUDA) | mid | GPU present, fp32 only | Bengaluru BATCS installed base |
| NVIDIA Jetson Xavier NX (Volta 384 CUDA) | mid | GPU present, fp32/int8 | |
| NVIDIA Jetson Orin NX / AGX (Ampere, Tensor Cores) | high | TensorRT fp16 engine builds on-device | Highest tier; same code via `device.yaml` |
| Generic ARM SBC (Pi 4, Khadas VIM, etc.) | low | No GPU/NPU onnx providers | Fallback tier |
| Generic ARM SBC (Pi 4, Khadas VIM, etc.) | low | No GPU/NPU onnx providers | Fallback tier |

---

## Tier Selection Logic (`scripts/profile_device.py`)

1. Probe `onnxruntime.get_available_providers()`:
   - `TensorrtExecutionProvider` present → **high**
   - `CUDAExecutionProvider` (or NPU provider) present → **mid**
   - Only `CPUExecutionProvider` → **low**
2. Write `active_tier: <tier>` into `configs/device.yaml` (or print with `--write` flag).

---

## Upgrade Trigger: Tier-Low Hybrid Detector (Future)

**When to build the tier-low hybrid detector (Phase 5 D6):**

> `make eval` queue-estimation error on **tier-low** exceeds tolerance (configurable; default 0.5 RMSE vs ground-truth queue length).

If breached: implement frame-skip + background-subtraction hybrid (cheap motion areas + interpolation) in a new adapter behind `DetectorPort`. Until then, interpolation-only is the baseline — simpler, works on every generation.

---

## New Finale Model (v0.1-bmd-finale)

The **india-yolov8n-final** model is the canonical low-tier detector for production deployments:

| Property | Value |
|----------|-------|
| **Model** | india-yolov8n-final (static int8, ONNX) |
| **mAP50 (full 10k val)** | **0.8477** |
| **Per-class mAP50** | car: 0.9189, auto: 0.9171, motorcycle: 0.8887, bus: 0.8460, truck: 0.8294, bicycle: 0.6859 |
| **Inference Speed** | 4.98 fps (200.6 ms/frame) on CPU (int8) |
| **Model Size** | 3.0M params (11.7 MB fp32 / 3.4 MB int8) |
| **Training** | 5-epoch joint polish @ lr=0.002 from loop-8 (0.8293) |
| **Validation** | Official BMD-45 10k val split (BMD-45-Val) |
| **Registry Path** | `models/registry/india-yolov8n-final/` (LFS-tracked) |

---

## Reproducing a Tier Baseline

```bash
# Detect & write active_tier
make profile-device

# Sim throughput (tier-independent)
make bench-sim

# Detection throughput (tier-dependent)
make bench-detect --backend=ultralytics  # CPU baseline
make bench-detect --backend=onnx         # requires onnxruntime + registry models
```

Tier baselines (registry models live in `models/registry/india-yolov8n-final/`):
```bash
# ONNX int8 (low tier)
make bench-detect --backend=onnx --registry=models/registry/india-yolov8n-final

# TensorRT fp16 (high tier, after adapter lands)
make bench-detect --backend=tensorrt --registry=models/registry/india-yolov8n-final
```

Results append to `docs/BENCHMARKS.md` → update the Detection table.