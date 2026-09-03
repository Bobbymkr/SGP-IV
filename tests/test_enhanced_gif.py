#!/usr/bin/env python3
"""
Test script to verify the enhanced Demo.gif functionality
"""

import os

from PIL import Image


def test_enhanced_gif():
    """Test that the enhanced Demo.gif file works correctly"""

    gif_path = "Demo.gif"

    # Check if file exists
    if not os.path.exists(gif_path):
        print("ERROR: Demo.gif not found")
        return False

    # Check file size
    file_size = os.path.getsize(gif_path)
    print(f"Demo.gif file size: {file_size / 1024:.1f} KB")

    # Try to load the image
    try:
        img = Image.open(gif_path)
        print("SUCCESS: Demo.gif loaded successfully")
        print(f"Image format: {img.format}")
        print(f"Image size: {img.size}")
        print(f"Image mode: {img.mode}")
        print(f"Number of frames: {getattr(img, 'n_frames', 1)}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to load Demo.gif: {e}")
        return False


if __name__ == "__main__":
    test_enhanced_gif()
