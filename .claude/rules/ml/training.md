# ML Training Pipeline Rules

## Training Script Template
All training scripts must follow this structure:

```python
#!/usr/bin/env python3
"""
Train {model_name} for {task}
Usage: python train.py --config config.yaml --data data.yaml
"""
import argparse
import yaml
from pathlib import Path
import torch
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Training config YAML')
    parser.add_argument('--data', required=True, help='Dataset config YAML')
    parser.add_argument('--device', default='auto', help='cuda, cpu, or auto')
    parser.add_argument('--resume', help='Resume from checkpoint')
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    device = torch.device('cuda' if torch.cuda.is_available() and args.device != 'cpu' else 'cpu')
    model = YOLO(config['model']['pretrained'])

    results = model.train(
        data=args.data,
        epochs=config['training']['epochs'],
        batch=config['training']['batch_size'],
        imgsz=config['training']['img_size'],
        device=device,
        patience=config['training']['patience'],
        lr0=config['training']['lr0'],
        momentum=config['training']['momentum'],
        weight_decay=config['training']['weight_decay'],
        warmup_epochs=config['training']['warmup_epochs'],
        cos_lr=config['training']['cos_lr'],
        augment=config['training']['augment'],
        mosaic=config['training']['mosaic'],
        mixup=config['training']['mixup'],
        copy_paste=config['training']['copy_paste'],
        project=config['output']['project'],
        name=config['output']['name'],
        exist_ok=True,
        resume=args.resume,
    )

    # Export best model
    model.export(format='onnx', opset=12, simplify=True)

if __name__ == '__main__':
    main()
```

## Config Schema (config.yaml)
```yaml
model:
  name: "yolov8n"
  pretrained: "yolov8n.pt"
  num_classes: 5

training:
  epochs: 100
  batch_size: 16
  img_size: 640
  patience: 20
  lr0: 0.01
  momentum: 0.937
  weight_decay: 0.0005
  warmup_epochs: 3
  cos_lr: true
  augment: true
  mosaic: 1.0
  mixup: 0.1
  copy_paste: 0.3

output:
  project: "runs/train"
  name: "yolov8n-traffic-v1"

logging:
  tensorboard: true
  wandb: false  # Set true if WANDB_API_KEY configured
```

## Reproducibility
- Set seeds: `torch.manual_seed(42)`, `np.random.seed(42)`, `random.seed(42)`
- `torch.backends.cudnn.deterministic = True`
- `torch.backends.cudnn.benchmark = False`
- Log git commit hash with every run

## Distributed Training (Multi-GPU)
- Use `torch.nn.DataParallel` or `torch.distributed`
- Adjust batch size: `effective_batch = batch_size * num_gpus`
- LR scaling: `lr = base_lr * sqrt(num_gpus)` (linear scaling rule)

## Checkpoint Management
- Save every epoch: `last.pt`
- Save best mAP: `best.pt`
- Keep last 5 checkpoints only
- Resume: `model.train(resume='last.pt')`

## Validation During Training
- Validate every epoch
- Metrics: mAP@0.5, mAP@0.5:0.95, precision, recall, per-class AP
- Log to TensorBoard + CSV

## Colab-Specific
```python
# Mount Drive
from google.colab import drive
drive.mount('/content/drive')

# Dataset path
DATA_ROOT = '/content/drive/MyDrive/traffic_dataset'

# Use T4 GPU (free tier)
!nvidia-smi
```

## Hyperparameter Tuning
- Use Optuna or Ray Tune for HPO
- Search space: lr0, momentum, weight_decay, augment params
- Budget: 20-50 trials
- Pruner: MedianPruner