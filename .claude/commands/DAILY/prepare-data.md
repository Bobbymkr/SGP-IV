# Prepare Dataset for Training

Extract frames from video, run annotation tool, create YOLO dataset.

## Usage
```
/prepare-data [video_dir] [output_dir] [fps]
```

## Examples
```
/prepare-data data/raw/intersection_001 data/traffic_dataset 2
/prepare-data /mnt/government_footage data/traffic_dataset 1
```

## Implementation
```bash
#!/bin/bash
set -euo pipefail

VIDEO_DIR=${1:-"data/raw"}
OUTPUT_DIR=${2:-"data/traffic_dataset"}
FPS=${3:-2}

cd /path/to/project
source .venv/bin/activate

# Create directory structure
mkdir -p $OUTPUT_DIR/{train,val,test}/{images,labels}

# Extract frames from all videos
python -c "
import cv2
import os
from pathlib import Path

video_dir = Path('$VIDEO_DIR')
output_dir = Path('$OUTPUT_DIR')
fps = $FPS

frame_count = 0
for video_path in video_dir.rglob('*.mp4'):
    cap = cv2.VideoCapture(str(video_path))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps / fps)
    
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            # Resize to 640x640 with letterbox
            h, w = frame.shape[:2]
            scale = min(640/w, 640/h)
            new_w, new_h = int(w*scale), int(h*scale)
            resized = cv2.resize(frame, (new_w, new_h))
            
            # Letterbox
            canvas = np.full((640, 640, 3), 114, dtype=np.uint8)
            x_off = (640 - new_w) // 2
            y_off = (640 - new_h) // 2
            canvas[y_off:y_off+new_h, x_off:x_off+new_w] = resized
            
            # Save
            split = 'train' if frame_count % 10 < 7 else ('val' if frame_count % 10 < 9 else 'test')
            out_path = output_dir / split / 'images' / f'{video_path.stem}_{frame_count:06d}.jpg'
            cv2.imwrite(str(out_path), canvas)
            frame_count += 1
        frame_idx += 1
    cap.release()

print(f'Extracted {frame_count} frames')
"

echo "Frame extraction complete. Next: annotate with CVAT."
echo "Import $OUTPUT_DIR into CVAT, annotate, export YOLO format to same directory."
```

## Next Steps
1. Run this command to extract frames
2. Import `data/traffic_dataset` into CVAT (localhost:8080)
3. Annotate all frames (car, bus, truck, bike, rickshaw)
4. Export as YOLO 1.1 format to same directory
5. Run `/train-yolo`