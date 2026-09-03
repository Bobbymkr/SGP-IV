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
| **low** | x86 IPC, ARM SBC, legacy boxes — CPU only, no GPU | ONNX Runtime int8 (CPUExecutionProvider) | ~2–5 fps on yolov8n-int8 | Interpolation-only (D6). Frames skipped when inference > time-step; queue estimates interpolated from last two frames. |
| **mid** | Jetson TX2 / Xavier NX, RK3588 NPU boxes — GPU/NPU present | ONNX Runtime fp32 (CUDAExecutionProvider or NPU provider if available) | ~10–25 fps on yolov8s | Full-frame detection each step. Confidence threshold standard (0.5). |
| **high** | Jetson Orin NX / AGX, discrete GPU boxes — TensorRT-capable | TensorRT fp16 (engine built+cached on-device at first boot in `models/trt_cache/`) | ~30–60+ fps on yolov8s-trt | Same as mid, but with fp16 speed. **Adapter pending Phase 5** — currently falls back to ONNX fp32 with a warning. |

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

When Phase T data arrives and registry models exist (`models/registry/india-yolov8n/`):
```bash
# ONNX int8 (low tier)
make bench-detect --backend=onnx --registry=models/registry/india-yolov8n

# TensorRT fp16 (high tier, after adapter lands)
make bench-detect --backend=tensorrt --registry=models/registry/india-yolov8s
```

Results append to `docs/BENCHMARKS.md` → update the Detection table.