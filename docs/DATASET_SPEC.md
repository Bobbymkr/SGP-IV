# Dataset Specification — India-YOLO Training Data

*Status: CONTRACT v1 · Classes provisional (see §2 flag)*

This document defines the exact format authorities'/annotators' data must be
converted into before training. `scripts/prepare_dataset.py` validates and
normalizes into this contract.

## 1. Layout

```
DATASET_ROOT/
  data.yaml                  # YOLO dataset config
  images/train/*.jpg         # training frames
  images/val/*.jpg
  images/test/*.jpg
  labels/train/*.txt         # YOLO detection labels, one per image
  labels/val/*.txt
  labels/test/*.txt
  calibration/frames/*.jpg   # ~200 frames for int8 quantization sampling
  meta/captures.json         # capture metadata (§5)
```

`data.yaml` shape:

```yaml
path: .
train: images/train
val: images/val
test: images/test
names:
  0: car
  1: motorcycle
  2: bus
  3: truck
  4: bicycle
  5: auto
```

## 2. Class schema

| id | name | maps to `VehicleType` |
|----|------|-----------------------|
| 0 | car | CAR |
| 1 | motorcycle | MOTORCYCLE |
| 2 | bus | BUS |
| 3 | truck | TRUCK |
| 4 | bicycle | BICYCLE |
| 5 | auto | AUTO |

> ⚠️ **PROVISIONAL FLAG**: more classes are expected (tempos, e-rickshaws,
> tractors, etc.). The schema is deliberately cheap to extend: append new ids
> at the END (never reorder existing ones), update `data.yaml`,
> `core/domain.py::VehicleType`, and retrain. All downstream code reads class
> lists from model `metadata.json`, never hardcoded.

## 3. Label format

One `.txt` per image, lines: `class_id center_x center_y width height`
(all coordinates normalized 0–1 relative to image size).

## 4. Split hygiene (non-negotiable)

Splits are cut by **junction × day**, never by random frame. Consecutive
video frames are near-duplicates; random splitting leaks them across splits
and inflates val mAP. `prepare_dataset.py --check-splits` enforces this when
`meta/captures.json` provides junction/day per clip.

## 5. Capture metadata (`meta/captures.json`)

Requested alongside footage because it feeds the eval matrix axes directly:

```json
[
  {
    "clip_id": "j12_2026-07-14_morning",
    "junction_type": "4way",
    "camera_height_m": 7.5,
    "weather": "heavy_rain",
    "time_of_day": "morning",
    "city": "<anonymized>"
  }
]
```

`weather` values align with `WeatherState`: clear | light_rain | heavy_rain |
waterlogged. `junction_type`: 3way | 4way | 5way | other.

## 6. Quantization calibration set

~200 frames sampled to cover the degradation axes: ≥30% rain-affected,
≥20% night/dusk, ≥30% dense two-wheeler frames, remainder clear-day.
`prepare_dataset.py --make-calibration` samples accordingly when metadata
allows, else warns.

## 7. Acceptance checklist (run automatically)

- [ ] every image has exactly one label file (warn otherwise)
- [ ] class ids ⊆ {0..5}
- [ ] boxes within [0,1]
- [ ] val/test junctions disjoint from train (when captures.json present)
- [ ] calibration set exists and meets §6 coverage (best-effort)
