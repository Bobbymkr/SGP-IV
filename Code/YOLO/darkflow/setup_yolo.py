"""
YOLO Model Auto-Downloader and Setup
==================================

Automated YOLOv8 model download and setup system
"""

import os
import sys
import urllib.request
import hashlib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# YOLOv8 model URLs and checksums
YOLO_MODELS = {
    'yolov8n.pt': {
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt',
        'size': 6.2,  # MB
        'checksum': 'e8c8f4c1b8c8e4c8b8c8e4c8b8c8e4c8b'  # Example checksum
    },
    'yolov8s.pt': {
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt',
        'size': 21.5,  # MB
        'checksum': 'f8c8f4c1b8c8e4c8b8c8e4c8b8c8e4c8b'
    },
    'yolov8m.pt': {
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt',
        'size': 49.7,  # MB
        'checksum': 'a8c8f4c1b8c8e4c8b8c8e4c8b8c8e4c8b'
    }
}

def download_file(url: str, filepath: Path, expected_size: float = None) -> bool:
    """Download file with progress tracking"""
    try:
        def progress_hook(block_num, block_size, total_size):
            if expected_size:
                percent = min(100, (block_num * block_size) / (expected_size * 1024 * 1024) * 100)
                print(f"\rDownloading: {percent:.1f}%", end='', flush=True)
        
        urllib.request.urlretrieve(url, filepath, progress_hook)
        print()  # New line after progress
        return True
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

def verify_file(filepath: Path, expected_checksum: str) -> bool:
    """Verify file integrity"""
    try:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest() == expected_checksum
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

def setup_yolo_models():
    """Download and setup YOLO models"""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    print("Setting up YOLOv8 models...")
    
    # Download nano model (fastest, good for real-time)
    model_name = 'yolov8n.pt'
    model_info = YOLO_MODELS[model_name]
    model_path = models_dir / model_name
    
    if not model_path.exists():
        print(f"Downloading {model_name} ({model_info['size']} MB)...")
        if download_file(model_info['url'], model_path, model_info['size']):
            print(f"✓ {model_name} downloaded successfully")
        else:
            print(f"✗ Failed to download {model_name}")
            return False
    else:
        print(f"✓ {model_name} already exists")
    
    return True

if __name__ == "__main__":
    setup_yolo_models()