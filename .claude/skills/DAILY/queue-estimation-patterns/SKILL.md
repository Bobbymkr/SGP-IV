---
name: queue-estimation-patterns
description: "Project-specific patterns for converting YOLOv8 detections to per-lane queue lengths."
---

# Queue Estimation Patterns

Project-specific patterns for converting YOLOv8 detections to per-lane queue lengths.
Based on `src/utils/config.py` geometry and standard traffic engineering (HCM 6th edition).
**Adapted for Indian traffic systems - expanded lane geometry and vehicle types.**

## Geometry from config.py

```python
# src/utils/config.py - VisualConfig (Indian adaptation)

stop_lines = {
    'right': 590,   # East approach stop line x-coord
    'down': 330,    # South approach stop line y-coord
    'left': 800,    # West approach stop line x-coord
    'up': 535       # North approach stop line y-coord
}

default_stops = {
    'right': 580,   # Vehicle stop position (10px before line)
    'down': 320,
    'left': 810,
    'up': 545
}

# Lanes per approach - Indian intersections often have 3 or 4 lanes
# (vs 2 in Western counterparts)
# Configure per intersection class:
#   INTERSECTION_CLASS_MINOR = 2 lanes per approach
#   INTERSECTION_CLASS_MAIN = 3 lanes per approach
#   INTERSECTION_CLASS_MAJOR = 4 lanes per approach
LANES_PER_APPROACH = 3  # Change to 4 for major intersections like Mumbai/Tolkappan

# x_coords expanded from 2 → 3 or 4 entries per approach
x_coords = {
    'right': [0, 0, 0],           # 3 lanes (minor)
    'down': [755, 727, 697],      # 3 lanes for South approach
    'left': [1400, 1400, 1400],
    'up': [602, 627, 657]
}

# For 4-lane approaches, add another entry:
# 'right': [0, 0, 0, 0],  # 4 lanes
# etc.

y_coords = {
    'right': [348, 370, 398],    # 3 lanes
    'down': [0, 0, 0],
    'left': [498, 466, 436],
    'up': [800, 800, 800]
}
```

**Encroachment buffer** (Indian roads have higher stop-line encroachment):
```python
encroachment_buffer = 5  # px - vehicles often stop beyond stop line
adjusted_stop_line = config.stop_lines[approach] - encroachment_buffer
```

## Detection → Lane Assignment

```python
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple

@dataclass
class LaneQueue:
    approach: str      # 'north', 'south', 'east', 'west'
    lane_idx: int      # 0, 1, or 2 (for 3-lane) or 0,1,2,3 (for 4-lane)
    vehicle_count: int
    queue_length_m: float
    occupancy: float   # 0-1
    vehicle_types: Dict[str, int]  # car: 5, bus: 2, two_wheeler: 8, etc.

class QueueEstimator:
    def __init__(self, config, lanes_per_approach=3):
        self.stop_lines = config.stop_lines
        self.default_stops = config.default_stops
        self.lanes_per_approach = lanes_per_approach  # 3 or 4 for India
        self.lane_coords = self._compute_lane_polygons(config)

        # Vehicle lengths (meters) for queue length calc - Indian adaptation
        self.vehicle_lengths = {
            'car': 4.5, 'bus': 12.0, 'truck': 10.0,
            'two_wheeler': 1.8, 'autorickshaw': 2.8,
            'cycle': 1.9, 'tractor': 3.5
        }

        # Pixel to meter calibration (approach-specific)
        # Indian calibrations typically: 0.04-0.06 px/m (denser traffic = smaller px/m)
        self.px_to_m = {
            'north': 0.05,   # ~20 px/m (calibrate per camera)
            'south': 0.05,
            'east': 0.05,
            'west': 0.05
        }

        # EWMA alpha adjusted for noisier Indian traffic (more smoothing)
        self.ewma_alpha = 0.25  # vs 0.3 for Western traffic

    def _compute_lane_polygons(self, config):
        """Create lane polygons from x_coords/y_coords and stop lines"""
        polys = {}
        for approach in ['right', 'down', 'left', 'up']:
            polys[approach] = []
            for lane in range(self.lanes_per_approach):
                x = config.x_coords[approach][lane]
                y = config.y_coords[approach][lane]
                polys[approach].append({
                    'x_range': (min(x, config.stop_lines[approach]),
                               max(x, config.stop_lines[approach])),
                    'y_range': (min(y, config.stop_lines[approach]),
                               max(y, config.stop_lines[approach]))
                })
        return polys

    def estimate(self, detections: List[Dict]) -> Dict[str, LaneQueue]:
        """Convert detections to per-lane queues"""

        # Initialize counters - now lanes_per_approach instead of hardcoded 2
        counts = {app: {lane: 0 for lane in range(self.lanes_per_approach)}
                  for app in ['north', 'south', 'east', 'west']}
        types = {app: {lane: {} for lane in range(self.lanes_per_approach)}
                 for app in ['north', 'south', 'east', 'west']}

        # Map detection bbox to lane
        for det in detections:
            bbox = det['bbox']  # [x1, y1, x2, y2]
            cls = det['class']  # Now supports 8 classes from yolov8-tensorrt-patterns
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2

            # Find which approach+lane (using Indian geometry)
            approach, lane = self._point_to_lane(cx, cy, self.lanes_per_approach)
            if approach:
                counts[approach][lane] += 1
                types[approach][lane][cls] = types[approach][lane].get(cls, 0) + 1

        # Build result
        result = {}
        for approach in ['north', 'south', 'east', 'west']:
            for lane in range(self.lanes_per_approach):
                count = counts[approach][lane]
                veh_types = types[approach][lane]

                # Queue length in meters - using Indian vehicle lengths
                queue_m = sum(self.vehicle_lengths.get(t, 4.5) * c
                             for t, c in veh_types.items())
                queue_m += count * 2.0  # gap between vehicles (smaller in India)

                # Occupancy (0-1) based on max queue length for this lane count
                # More lanes = longer max queue before spillback
                max_queue_m = 120.0  # ~20 vehicles * 6m (Indian: longer queues possible)
                occupancy = min(queue_m / max_queue_m, 1.0)

                result[f"{approach}_{lane}"] = LaneQueue(
                    approach=approach,
                    lane_idx=lane,
                    vehicle_count=count,
                    queue_length_m=queue_m,
                    occupancy=occupancy,
                    vehicle_types=veh_types
                )

        return result

    def _point_to_lane(self, x, y, lanes_per_approach):
        """Map pixel coordinate to approach+lane using Indian config geometry"""
        # Simplified - real version uses lane polygons
        # Check which stop line region the point is in

        # Determine approach first
        if y < 400:  # North (up)
            approach = 'north'
        elif y > 500:  # South (down)
            approach = 'south'
        elif x < 650:  # West (left)
            approach = 'west'
        else:  # East (right)
            approach = 'east'

        if not approach:
            return None, None

        # Now determine lane within approach (0 to lanes_per_average-1)
        # Indian intersections often have vehicles distributed across lanes
        # Lane 0 = nearest stop line, Lane 2 = furthest back

        # Simplified lane assignment based on x or y position within approach
        if approach in ['north', 'south']:
            # For north-south: use x coordinate to determine lane
            if lanes_per_approach == 3:
                if x < 630: lane = 0  # far lane
                elif x < 680: lane = 1  # middle lane
                else: lane = 2  # near stop line
            elif lanes_per_approach == 4:
                # 4-lane: divide x range into 4
                x_ranges = [0, 630, 680, 750, 800]  # example boundaries
                for i in range(4):
                    if x < x_ranges[i+1]:
                        lane = i
                        break
                else:
                    lane = 3
            else:
                lane = 0
        elif approach in ['east', 'west']:
            # For east-west: use y coordinate
            if lanes_per_approach == 3:
                if y < 380: lane = 0  # far lane
                elif y < 430: lane = 1  # middle lane
                else: lane = 2  # near stop line
            elif lanes_per_approach == 4:
                y_ranges = [0, 380, 430, 480, 535]
                for i in range(4):
                    if y < y_ranges[i+1]:
                        lane = i
                        break
                else:
                    lane = 3
            else:
                lane = 0
        else:
            lane = 0

        return approach, lane

    def _compute_ewma(self, current_queues: Dict[str, LaneQueue]) -> Dict[str, LaneQueue]:
        """EWMA smoothing adapted for Indian traffic noise"""
        smoothed = {}
        for key, q in current_queues.items():
            if key in self.prev_queues:
                prev_q = self.prev_queues[key]
                # Indian: alpha=0.25 means more smoothing, more stable but slower to respond
                smoothed_q = LaneQueue(
                    approach=q.approach,
                    lane_idx=q.lane_idx,
                    vehicle_count=int(self.ewma_alpha * q.vehicle_count +
                                      (1-self.ewma_alpha) * prev_q.vehicle_count),
                    queue_length_m=self.ewma_alpha * q.queue_length_m +
                                   (1-self.ewma_alpha) * prev_q.queue_length_m,
                    occupancy=self.ewma_alpha * q.occupancy +
                              (1-self.ewma_alpha) * prev_q.occupancy,
                    vehicle_types=q.vehicle_types
                )
            else:
                smoothed_q = q
            smoothed[key] = smoothed_q
        self.prev_queues = smoothed
        return smoothed

# EWMA Smoothing for stable queue estimates
class EWMAQueueFilter:
    def __init__(self, alpha=0.25):  # Indian: 0.25 vs 0.3
        self.alpha = alpha
        self.prev_queues = {}

    def update(self, current_queues: Dict[str, LaneQueue]) -> Dict[str, LaneQueue]:
        smoothed = {}
        for key, q in current_queues.items():
            if key in self.prev_queues:
                prev_q = self.prev_queues[key]
                smoothed_q = LaneQueue(
                    approach=q.approach,
                    lane_idx=q.lane_idx,
                    vehicle_count=int(self.alpha * q.vehicle_count +
                                      (1-self.alpha) * prev_q.vehicle_count),
                    queue_length_m=self.alpha * q.queue_length_m +
                                   (1-self.alpha) * prev_q.queue_length_m,
                    occupancy=self.alpha * q.occupancy +
                              (1-self.alpha) * prev_q.occupancy,
                    vehicle_types=q.vehicle_types
                )
            else:
                smoothed_q = q
            smoothed[key] = smoothed_q
        self.prev_queues = smoothed
        return smoothed
```

## Rules
- Use `config.py` VisualConfig as single source of truth for geometry
- Map approaches: `right`=East, `down`=South, `left`=West, `up`=North
- **LANES_PER_APPROACH = 3** (default for Indian) or **4** (for major intersections)
- EWMA alpha=0.25 (Indian: more smoothing for noisier traffic vs 0.3 Western)
- Calibrate px_to_m per camera using known lane length (Indian: 0.04-0.06 typical)
- Handle occlusion: if detection confidence < 0.4, weight by 0.5
- **Encroachment buffer**: Indian roads have 5px higher encroachment → adjust stop line
- Vehicle types supported: car, bus, truck, two_wheeler, autorickshaw, cycle, tractor
- Queue length gap: 2.0m between vehicles (Indian: smaller gaps tolerated)
- Max queue before spillback: 120m for 3-lane, 160m for 4-lane Indian intersections
