# 02 — Dataset procedure + reasoning

## Contract first
`docs/DATASET_SPEC.md:9-30` + `scripts/prepare_dataset.py`: every source normalized to `images/{train,val,test}/*.jpg` + `labels/**/*.txt` + `data.yaml` (abs path) + `calibration/frames` (~200 for int8) + `meta/captures.json`. This is why BMD-45 / TrafficCAM / HeTra / synthetic are interchangeable in training.

## Chain (say this order)
1. 8-loop cumulative `notebooks/train_bmd_loop.ipynb`: images_000→007, loop1 20ep from COCO, loops 2-8 12ep from prev best, double-prep rehearsal base (no forgetting). Result 0.7949→0.8293.
2. Finale polish `notebooks/train_bmd_finale_drive.ipynb` (canonical, Drive-native): init loop-8 best, 5ep lr=0.002 batch 32, OptionB 13→6 merge, COCO→YOLO + PNG→JPG q92. Result **0.8477 full 10k**.
3. `train_bmd_finale.ipynb` = legacy HF-fallback, keep for reference only.

## Reasoning behind choices
- 6 classes (car/motorcycle/bus/truck/bicycle/auto): matches Indian heterogeneous mix; auto/motorcycle kept separate (high share, distinct headways).
- Rehearsal + low-lr polish: preserve loop gains, squeeze +0.0184 without drift.
- Full-10k val anchor (`val: official-full-10k` in metadata): no cherry-picked split.
- TrafficCAM 180-frame check: finale 0.488 vs candidate 0.635 mAP50, F1 tie → finale stays canonical (generalization over peak).

## Demo frames
Training images ARE valid demo input: `data/synthetic_india_yolo/images/` (4032 files) and `data/trafficcam/images/` (2340 files). Filenames carry weather/behavior tags, e.g. `j17_2026-01-02_noon_3way_clear_aggressive_metro_f000320.jpg`. Use val split for honesty.

## Trace
`notebooks/train_bmd_loop.ipynb`, `train_bmd_finale_drive.ipynb`; `data/synthetic_india_yolo/data.yaml:1-11`; `evals/results/queue_proxy_conf045.csv`; `docs/BENCHMARKS.md`; `notebooks/probe_bmd45_annotations.ipynb`, `profile_hetra_eda.ipynb`, `pseudo_itd_x.ipynb`.
