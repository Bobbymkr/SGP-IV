# Train YOLOv8 for Traffic Detection

Train YOLOv8n on custom intersection footage.

## Usage
```
/train-yolo [epochs] [batch_size] [img_size]
```

## Examples
```
/train-yolo 100 16 640
/train-yolo 50 8 640 --resume
```

## Implementation
```bash
#!/bin/bash
set -euo pipefail

EPOCHS=${1:-100}
BATCH=${2:-16}
IMG_SIZE=${3:-640}
RESUME=${4:-}

cd /path/to/project

# Activate venv
source .venv/bin/activate

# Train
python -m scripts.train_yolo \
  --config config/train_config.yaml \
  --data data/dataset.yaml \
  --epochs $EPOCHS \
  --batch $BATCH \
  --img-size $IMG_SIZE \
  ${RESUME:+--resume $RESUME}

echo "Training complete. Best model at runs/train/yolov8n-traffic-*/weights/best.pt"
```

## Config
Edit `config/train_config.yaml` for hyperparameters.

## Colab
For GPU training, use `colab/01_yolo_finetune.ipynb`.
