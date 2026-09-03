#!/usr/bin/env python3
"""
Test script to verify GIF loading functionality
"""

import os

from PIL import Image


def test_gif_loading():
    """Test that the Demo.gif file can be loaded correctly"""

    gif_path = "Demo.gif"

    # Check if file exists
    if not os.path.exists(gif_path):
        print("ERROR: Demo.gif not found")
        return False

    # Check file size
    file_size = os.path.getsize(gif_path)
    print(f"Demo.gif file size: {file_size / (1024*1024):.1f} MB")

    # Try to load the image
    try:
        img = Image.open(gif_path)
        print("SUCCESS: Demo.gif loaded successfully")
        print(f"Image format: {img.format}")
        print(f"Image size: {img.size}")
        print(f"Image mode: {img.mode}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to load Demo.gif: {e}")
        return False


if __name__ == "__main__":
    test_gif_loading()
