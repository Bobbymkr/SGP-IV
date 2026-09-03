# Python Style Rules for Adaptive-Traffic-Signal-Timer

## Formatting (black + ruff)
- Line length: 100 characters
- Target version: py313
- Use double quotes for strings
- Trailing commas in multi-line structures

## Type Hints (mypy strict)
- All functions must have type annotations
- Use `from __future__ import annotations` for forward refs
- Prefer `list[T]` over `List[T]` (Python 3.9+)
- Use `dict[K, V]` over `Dict[K, V]`
- Avoid `Any` - use `object` or protocol instead

## Imports
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import cv2
import numpy as np
import torch
from ultralytics import YOLO

# Local
from src.utils.config import SimulationConfig
```

## Naming Conventions
- Classes: `PascalCase` (e.g., `VehicleDetector`, `SignalController`)
- Functions/Methods: `snake_case` (e.g., `detect_vehicles`, `calculate_green_time`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_GREEN_TIME`, `MAX_QUEUE_LENGTH`)
- Private: `_leading_underscore`
- Type variables: `T`, `K`, `V` or descriptive (`VehicleT`)

## Error Handling
- Use custom exceptions for domain errors
- Never bare `except:` - always specify exception type
- Log errors with context before re-raising
- Use `try/except/else/finally` for resource management

## Async/Await
- Use `asyncio` for I/O-bound operations (camera streams, API calls)
- CPU-bound ML inference: run in thread pool via `asyncio.to_thread()`
- Avoid blocking calls in async functions

## ML-Specific
- Models loaded once at startup, not per-request
- Use `torch.no_grad()` for inference
- Batch inference when possible
- Device management: `device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')`
