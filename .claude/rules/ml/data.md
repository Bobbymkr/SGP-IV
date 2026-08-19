# ML Data Rules for Adaptive-Traffic-Signal-Timer

## Dataset Structure
```
data/
├── raw/                    # Original footage (gitignored)
│   ├── intersection_001/
│   │   ├── camera_north.mp4
│   │   ├── camera_south.mp4
│   │   ├── camera_east.mp4
│   │   └── camera_west.mp4
├── frames/                 # Extracted frames (gitignored)
│   ├── train/
│   ├── val/
│   └── test/
├── annotations/            # YOLO format labels
│   ├── train/
│   ├── val/
│   └── test/
├── dataset.yaml            # Ultralytics data config
└── dataset_stats.json      # Class distribution, image counts
```

## Frame Extraction
- Sample rate: 2 FPS from 30 FPS source (every 15th frame)
- Resolution: 1920x1080 → 640x640 (letterbox, preserve aspect)
- Minimum 1000 frames per intersection per camera

## Annotation Standards
- Tool: CVAT (preferred) or LabelImg
- Bounding box: tight around vehicle, include wheels
- Occlusion: annotate if >30% visible
- Truncation: annotate if >50% in frame
- Classes: car, bus, truck, bike, rickshaw (exact spelling)
- Difficult: mark if heavy occlusion, extreme weather, night

## Quality Checks
- No overlapping boxes for same class
- IoU > 0.5 with ground truth for validation
- Class balance: no class < 5% of total annotations
- Review 10% random sample per batch

## Data Augmentation (Training Only)
- Mosaic: 4 images combined (probability 1.0)
- MixUp: alpha=0.1 (probability 0.15)
- Copy-Paste: paste objects from other images (probability 0.3)
- HSV: hgain=0.015, sgain=0.7, vgain=0.4
- Geometric: flip_lr=0.5, perspective=0.0, translate=0.1, scale=0.5

## Test Set Integrity
- Never use test set for hyperparameter tuning
- Test set fixed after first creation
- Report metrics on test set only once per model version

## Privacy & Compliance
- Blur license plates in stored frames
- No pedestrian faces in annotations
- GDPR/CCPA: no personal data in dataset
- Government footage: use only for this project, delete after