#!/usr/bin/env python3
"""
Synthetic Indian Traffic Dataset Generator
===========================================
Generates unbiased, versatile YOLO-format dataset using the simulation engine.
Covers all 6 classes, 3/4/5-way geometries, 4 weather states, 3 discipline presets.
Designed so real-world data can be dropped in with minimal changes.

Output structure matches DATASET_SPEC.md contract exactly.
"""

import os
import json
import random
import shutil
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adaptive_traffic.core.simulation.engine import (
    create_simulation, create_intersection, TrafficSimulation, Vehicle, VehicleType, Direction, Lane
)
from adaptive_traffic.core.simulation.behavior import BehaviorEngine
from adaptive_traffic.core.simulation.weather import WeatherModel, WeatherState
from adaptive_traffic.core.domain import VehicleDetection


# ============================================================
# CONFIGURATION
# ============================================================

CLASSES = ["car", "motorcycle", "bus", "truck", "bicycle", "auto"]
CLASS_TO_VEHICLE_TYPE = {
    "car": VehicleType.CAR,
    "motorcycle": VehicleType.MOTORCYCLE,
    "bus": VehicleType.BUS,
    "truck": VehicleType.TRUCK,
    "bicycle": VehicleType.BICYCLE,
    "auto": VehicleType.AUTO,
}

# Vehicle visual properties (for rendering)
VEHICLE_RENDER = {
    VehicleType.CAR: {"length": 4.5, "width": 1.8, "color": (70, 130, 180)},
    VehicleType.BUS: {"length": 12.0, "width": 2.5, "color": (220, 20, 60)},
    VehicleType.TRUCK: {"length": 10.0, "width": 2.5, "color": (139, 69, 19)},
    VehicleType.MOTORCYCLE: {"length": 2.0, "width": 0.8, "color": (255, 165, 0)},
    VehicleType.BICYCLE: {"length": 1.8, "width": 0.6, "color": (34, 139, 34)},
    VehicleType.AUTO: {"length": 3.0, "width": 1.4, "color": (255, 215, 0)},
}

# Simulation configurations for dataset generation
GEOMETRIES = {
    "3way": {
        "approaches": [Direction.NORTH, Direction.EAST, Direction.WEST],
        "compatibility_groups": [[Direction.NORTH], [Direction.EAST, Direction.WEST]],
        "lanes_per_direction": 2,
        "lane_length": 200,
    },
    "4way": {
        "approaches": [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST],
        "compatibility_groups": [[Direction.NORTH, Direction.SOUTH], [Direction.EAST, Direction.WEST]],
        "lanes_per_direction": 2,
        "lane_length": 200,
    },
    "5way": {
        "approaches": [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST, Direction.SOUTH_WEST],
        "compatibility_groups": [[Direction.NORTH], [Direction.EAST, Direction.WEST], [Direction.SOUTH], [Direction.SOUTH_WEST]],
        "lanes_per_direction": 2,
        "lane_length": 200,
    },
}

WEATHER_STATES = [WeatherState.CLEAR, WeatherState.LIGHT_RAIN, WeatherState.HEAVY_MONSOON, WeatherState.WATERLOGGED]
DISCIPLINE_PRESETS = ["disciplined", "typical_urban", "aggressive_metro"]

TIMES_OF_DAY = ["morning", "noon", "evening", "night"]

CAMERA_CONFIGS = [
    {"height_m": 7.0, "fov_deg": 60, "pitch_deg": -30},
    {"height_m": 8.5, "fov_deg": 70, "pitch_deg": -25},
    {"height_m": 6.0, "fov_deg": 55, "pitch_deg": -35},
]

IMAGE_SIZE = (640, 640)  # YOLO standard
METERS_PER_PIXEL = 0.3  # ~192m coverage at 640px

# Generation targets
TARGET_TOTAL_IMAGES = 5000
SPLIT_RATIOS = {"train": 0.7, "val": 0.15, "test": 0.15}
CALIBRATION_FRAMES = 200

# Junction-day combinations for split hygiene
JUNCTION_DAYS = [
    (f"j{i:02d}", (datetime(2026, 1, 1) + timedelta(days=d)).strftime("%Y-%m-%d"))
    for i in range(1, 21) for d in range(7)  # 20 junctions, 7 days each = 140 combinations
]


# ============================================================
# RENDERING ENGINE
# ============================================================

class TrafficRenderer:
    """Renders simulation state to image with YOLO bounding boxes."""
    
    def __init__(self, image_size: Tuple[int, int] = IMAGE_SIZE, meters_per_pixel: float = METERS_PER_PIXEL):
        self.image_size = image_size
        self.mpp = meters_per_pixel
        self.width, self.height = image_size
        self.cx, self.cy = self.width // 2, self.height // 2
        
        # Camera position in world coordinates (meters from intersection center)
        self.cam_world_x = 0.0
        self.cam_world_y = -50.0  # 50m south of intersection
        
    def world_to_image(self, wx: float, wy: float) -> Tuple[float, float]:
        """Convert world coordinates (meters) to image pixels."""
        # Camera at (0, -50), looking north
        rel_x = wx - self.cam_world_x
        rel_y = -(wy - self.cam_world_y)  # Flip Y for image coordinates
        
        # Perspective projection (simplified)
        scale = 1.0 / (1.0 + abs(rel_y) * 0.01)
        px = self.cx + rel_x / self.mpp * scale
        py = self.cy + rel_y / self.mpp * scale
        return px, py
    
    def render_frame(self, sim: TrafficSimulation, intersection_id: str = "main") -> Tuple[np.ndarray, List[VehicleDetection]]:
        """Render a simulation frame and return image + detections."""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        draw = ImageDraw.Draw(Image.fromarray(img))
        detections = []
        
        # Draw road surface
        self._draw_roads(img, sim, intersection_id)
        
        # Draw vehicles and collect detections
        if intersection_id in sim.intersections:
            intersection = sim.intersections[intersection_id]
            for lane in intersection.lanes.values():
                for vehicle in lane.vehicles:
                    det = self._draw_vehicle(img, vehicle, lane)
                    if det:
                        detections.append(det)
        
        # Add weather effects
        weather = sim.weather_model.current()
        self._apply_weather_effects(img, weather)
        
        # Add time-of-day lighting
        self._apply_lighting(img)
        
        return np.array(img), detections
    
    def _draw_roads(self, img: np.ndarray, sim: TrafficSimulation, intersection_id: str):
        """Draw road network."""
        if intersection_id not in sim.intersections:
            return
            
        intersection = sim.intersections[intersection_id]
        
        # Draw lanes as rectangles
        for lane in intersection.lanes.values():
            # Lane centerline in world coordinates
            direction = lane.direction
            lane_idx = lane.lane_index
            
            # Calculate lane offset from center
            lane_width = 3.5  # meters
            offset = (lane_idx - 0.5) * lane_width  # Center of lane
            
            # Draw lane segment approaching intersection
            start_dist = 150  # meters from intersection
            end_dist = 0
            
            if direction == Direction.NORTH:
                wx1, wy1 = -offset, -start_dist
                wx2, wy2 = -offset, -end_dist
            elif direction == Direction.SOUTH:
                wx1, wy1 = offset, start_dist
                wx2, wy2 = offset, end_dist
            elif direction == Direction.EAST:
                wx1, wy1 = start_dist, offset
                wx2, wy2 = end_dist, offset
            elif direction == Direction.WEST:
                wx1, wy1 = -start_dist, -offset
                wx2, wy2 = -end_dist, -offset
            elif direction == Direction.SOUTH_WEST:
                wx1, wy1 = -start_dist * 0.7, start_dist * 0.7
                wx2, wy2 = 0, 0
            else:
                continue
                
            p1 = self.world_to_image(wx1, wy1)
            p2 = self.world_to_image(wx2, wy2)
            
            # Draw lane as polygon (two edges)
            perp = 1.8  # half width in meters
            # Left edge
            if direction in (Direction.NORTH, Direction.SOUTH):
                lx1, ly1 = self.world_to_image(wx1 - perp, wy1)
                lx2, ly2 = self.world_to_image(wx2 - perp, wy2)
            else:
                lx1, ly1 = self.world_to_image(wx1, wy1 - perp)
                lx2, ly2 = self.world_to_image(wx2, wy2 - perp)
            # Right edge
            if direction in (Direction.NORTH, Direction.SOUTH):
                rx1, ry1 = self.world_to_image(wx1 + perp, wy1)
                rx2, ry2 = self.world_to_image(wx2 + perp, wy2)
            else:
                rx1, ry1 = self.world_to_image(wx1, wy1 + perp)
                rx2, ry2 = self.world_to_image(wx2, wy2 + perp)
            
            # Draw as filled polygon
            pts = np.array([[lx1, ly1], [lx2, ly2], [rx2, ry2], [rx1, ry1]], dtype=np.int32)
            cv2.fillPoly(img, [pts], (50, 50, 50))
            
            # Lane markings
            cv2.line(img, (int(lx1), int(ly1)), (int(lx2), int(ly2)), (100, 100, 100), 1)
            cv2.line(img, (int(rx1), int(ry1)), (int(rx2), int(ry2)), (100, 100, 100), 1)
        
        # Draw stop lines
        for lane in intersection.lanes.values():
            direction = lane.direction
            if direction == Direction.NORTH:
                wx, wy = 0, -2
            elif direction == Direction.SOUTH:
                wx, wy = 0, 2
            elif direction == Direction.EAST:
                wx, wy = 2, 0
            elif direction == Direction.WEST:
                wx, wy = -2, 0
            else:
                continue
            p1 = self.world_to_image(wx - 1.8, wy)
            p2 = self.world_to_image(wx + 1.8, wy)
            cv2.line(img, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (255, 255, 255), 2)
    
    def _draw_vehicle(self, img: np.ndarray, vehicle: Vehicle, lane: Lane) -> Optional[VehicleDetection]:
        """Draw vehicle and return YOLO detection."""
        props = VEHICLE_RENDER[vehicle.vehicle_type]
        length_m = props["length"]
        width_m = props["width"]
        color = props["color"]
        
        # Vehicle position in world coordinates (meters from stop line, negative = approaching)
        wx = -vehicle.position
        wy = 0
        
        # Lane lateral offset
        lane_width = 3.5
        lane_offset = (lane.lane_index - 0.5) * lane_width
        
        if lane.direction == Direction.NORTH:
            wx, wy = -lane_offset, -vehicle.position
        elif lane.direction == Direction.SOUTH:
            wx, wy = lane_offset, vehicle.position
        elif lane.direction == Direction.EAST:
            wx, wy = vehicle.position, lane_offset
        elif lane.direction == Direction.WEST:
            wx, wy = -vehicle.position, -lane_offset
        elif lane.direction == Direction.SOUTH_WEST:
            wx, wy = -vehicle.position * 0.7, vehicle.position * 0.7
        
        # Convert to image coordinates
        cx, cy = self.world_to_image(wx, wy)
        
        # Vehicle orientation
        if lane.direction in (Direction.NORTH, Direction.SOUTH):
            angle = 0 if lane.direction == Direction.NORTH else 180
            vlen_px = length_m / self.mpp
            vwid_px = width_m / self.mpp
        else:
            angle = 90 if lane.direction == Direction.EAST else -90
            vlen_px = length_m / self.mpp
            vwid_px = width_m / self.mpp
        
        # Apply perspective scaling
        scale = 1.0 / (1.0 + abs(vehicle.position) * 0.01)
        vlen_px *= scale
        vwid_px *= scale
        
        # Skip if off-screen
        if cx < -vwid_px or cx > self.width + vwid_px or cy < -vlen_px or cy > self.height + vlen_px:
            return None
        
        # Draw vehicle as rotated rectangle
        rect = ((cx, cy), (vwid_px, vlen_px), angle)
        box = cv2.boxPoints(rect).astype(np.int32)
        cv2.fillPoly(img, [box], color)
        cv2.polylines(img, [box], True, (255, 255, 255), 1)
        
        # Calculate YOLO bounding box (axis-aligned)
        x_coords = box[:, 0]
        y_coords = box[:, 1]
        x1, x2 = max(0, x_coords.min()), min(self.width, x_coords.max())
        y1, y2 = max(0, y_coords.min()), min(self.height, y_coords.max())
        
        if x2 <= x1 or y2 <= y1:
            return None
            
        # Normalize to [0, 1]
        x_center = (x1 + x2) / 2 / self.width
        y_center = (y1 + y2) / 2 / self.height
        w = (x2 - x1) / self.width
        h = (y2 - y1) / self.height
        
        # Validate bounds
        if not (0 < x_center < 1 and 0 < y_center < 1 and 0 < w < 1 and 0 < h < 1):
            return None
        
        class_id = CLASSES.index(vehicle.vehicle_type.value)
        
        return VehicleDetection(
            class_id=class_id,
            class_name=vehicle.vehicle_type.value,
            confidence=0.95,
            bbox=(int(x1), int(y1), int(x2), int(y2)),
            center=(int(cx), int(cy)),
            direction=lane.direction.value,
            speed=vehicle.speed
        )
    
    def _apply_weather_effects(self, img: np.ndarray, weather):
        """Apply weather visual effects."""
        if weather.state == WeatherState.LIGHT_RAIN:
            # Add rain streaks
            for _ in range(200):
                x = random.randint(0, self.width)
                y = random.randint(0, self.height)
                length = random.randint(5, 15)
                cv2.line(img, (x, y), (x + 1, y + length), (200, 200, 200), 1)
            # Slight brightness reduction
            img[:] = (img * 0.85).astype(np.uint8)
            
        elif weather.state == WeatherState.HEAVY_MONSOON:
            # Heavy rain
            for _ in range(500):
                x = random.randint(0, self.width)
                y = random.randint(0, self.height)
                length = random.randint(10, 25)
                cv2.line(img, (x, y), (x + 2, y + length), (180, 180, 180), 1)
            # Fog/brightness
            img[:] = (img * 0.7).astype(np.uint8)
            # Water spray
            for _ in range(100):
                x = random.randint(0, self.width)
                y = random.randint(self.height // 2, self.height)
                cv2.circle(img, (x, y), random.randint(1, 3), (200, 200, 200), -1)
            
        elif weather.state == WeatherState.WATERLOGGED:
            # Waterlogged - reflections, heavy rain, low visibility
            for _ in range(600):
                x = random.randint(0, self.width)
                y = random.randint(0, self.height)
                length = random.randint(15, 30)
                cv2.line(img, (x, y), (x + 3, y + length), (150, 150, 150), 1)
            img[:] = (img * 0.5).astype(np.uint8)
            # Standing water reflections
            for _ in range(50):
                x = random.randint(0, self.width)
                y = random.randint(self.height // 2, self.height)
                cv2.ellipse(img, (x, y), (random.randint(20, 50), random.randint(5, 15)), 0, 0, 360, (80, 80, 100), -1)
    
    def _apply_lighting(self, img: np.ndarray):
        """Apply time-of-day lighting (simplified)."""
        # Add vignette for night
        pass  # Could add based on time


# ============================================================
# DATASET GENERATOR
# ============================================================

@dataclass
class CaptureMeta:
    clip_id: str
    junction_type: str
    camera_height_m: float
    weather: str
    time_of_day: str
    discipline: str = "typical_urban"
    city: str = "synthetic"


class SyntheticDatasetGenerator:
    def __init__(self, output_dir: Path, seed: int = 42):
        self.output_dir = Path(output_dir)
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        
        self.renderer = TrafficRenderer()
        self.captures_meta: List[CaptureMeta] = []
        self.image_counter = 0
        
        # Setup directories
        self._setup_dirs()
        
    def _setup_dirs(self):
        dirs = [
            self.output_dir / "images" / "train",
            self.output_dir / "images" / "val",
            self.output_dir / "images" / "test",
            self.output_dir / "labels" / "train",
            self.output_dir / "labels" / "val",
            self.output_dir / "labels" / "test",
            self.output_dir / "calibration" / "frames",
            self.output_dir / "meta",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def _get_split(self, junction_idx: int, day_idx: int) -> str:
        """Deterministic split by junction-day index (no random frame splitting)."""
        # Combine junction and day into a single index
        junction_day_idx = junction_idx * 7 + day_idx  # 7 days per junction
        total = len(JUNCTION_DAYS)
        train_end = int(total * SPLIT_RATIOS["train"])
        val_end = train_end + int(total * SPLIT_RATIOS["val"])
        
        if junction_day_idx < train_end:
            return "train"
        elif junction_day_idx < val_end:
            return "val"
        return "test"
    
    def _create_simulation(self, geometry: str, weather: WeatherState, discipline: str) -> TrafficSimulation:
        """Create simulation with specified configuration."""
        geo = GEOMETRIES[geometry]
        
        config = {
            "time_step": 0.1,
            "max_time": 3600,
            "seed": self.seed + self.image_counter,
            "weather_state": weather.value,
            "behavior_preset": discipline,
            "generation_rates": {
                Direction.NORTH: 600,
                Direction.SOUTH: 600,
                Direction.EAST: 400,
                Direction.WEST: 400,
                Direction.SOUTH_WEST: 300,
            },
            "adaptive_scheduling": True,
        }
        
        sim = create_simulation(config)
        intersection = create_intersection({
            "id": "main",
            "approaches": [d.value for d in geo["approaches"]],
            "compatibility_groups": [[d.value for d in g] for g in geo["compatibility_groups"]],
            "lanes_per_direction": geo["lanes_per_direction"],
            "lane_length": geo["lane_length"],
        })
        sim.add_intersection(intersection)
        return sim
    
    def _generate_frames_for_config(
        self,
        geometry: str,
        weather: WeatherState,
        discipline: str,
        junction_idx: int,
        day_idx: int,
        num_frames: int
    ) -> List[Tuple[np.ndarray, List[VehicleDetection], str, Dict]]:
        """Generate frames for a specific configuration."""
        sim = self._create_simulation(geometry, weather, discipline)
        
        # Camera config variation
        cam_config = CAMERA_CONFIGS[junction_idx % len(CAMERA_CONFIGS)]
        time_of_day = TIMES_OF_DAY[day_idx % len(TIMES_OF_DAY)]
        
        frames = []
        clip_id = f"j{junction_idx:02d}_{datetime(2026,1,1)+timedelta(days=day_idx):%Y-%m-%d}_{time_of_day}_{geometry}_{weather.value}_{discipline}"
        
        for frame_idx in range(num_frames * 10):  # Run more steps, save more frames
            # Step simulation
            sim.step()
            
            # Render every 5th step to reduce temporal correlation
            if frame_idx % 5 == 0:
                img, detections = self.renderer.render_frame(sim)
                
                # Add noise/augmentation
                img = self._augment_image(img, weather)
                
                meta = {
                    "clip_id": clip_id,
                    "junction_type": geometry,
                    "camera_height_m": cam_config["height_m"],
                    "weather": weather.value,
                    "time_of_day": time_of_day,
                    "city": "synthetic",
                    "discipline": discipline,
                    "frame_idx": frame_idx,
                }
                
                frames.append((img, detections, clip_id, meta))
                
                if len(frames) >= num_frames:
                    break
        
        return frames
    
    def _augment_image(self, img: np.ndarray, weather) -> np.ndarray:
        """Apply realistic augmentations."""
        # Brightness/contrast
        alpha = random.uniform(0.8, 1.2)
        beta = random.randint(-20, 20)
        img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        
        # Gaussian noise
        if random.random() < 0.3:
            noise = np.random.normal(0, 5, img.shape).astype(np.uint8)
            img = cv2.add(img, noise)
        
        # Motion blur (occasionally)
        if random.random() < 0.1:
            k = random.randint(3, 7)
            kernel = np.zeros((k, k))
            kernel[k//2, :] = 1.0 / k
            img = cv2.filter2D(img, -1, kernel)
        
        # JPEG compression artifacts
        if random.random() < 0.2:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), random.randint(70, 95)]
            _, enc = cv2.imencode('.jpg', img, encode_param)
            img = cv2.imdecode(enc, 1)
        
        return img
    
    def _save_frame(
        self,
        img: np.ndarray,
        detections: List[VehicleDetection],
        split: str,
        clip_id: str,
        meta: Dict,
        is_calibration: bool = False
    ):
        """Save image and label file."""
        filename = f"{clip_id}_f{self.image_counter:06d}.jpg"
        
        if is_calibration:
            img_path = self.output_dir / "calibration" / "frames" / filename
        else:
            img_path = self.output_dir / "images" / split / filename
            label_path = self.output_dir / "labels" / split / filename.replace(".jpg", ".txt")
            
            # Write YOLO labels
            with open(label_path, "w") as f:
                for det in detections:
                    x1, y1, x2, y2 = det.bbox
                    x_center = (x1 + x2) / 2 / self.renderer.width
                    y_center = (y1 + y2) / 2 / self.renderer.height
                    w = (x2 - x1) / self.renderer.width
                    h = (y2 - y1) / self.renderer.height
                    f.write(f"{det.class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
        
        cv2.imwrite(str(img_path), img)
        self.image_counter += 1
        
        if not is_calibration:
            self.captures_meta.append(CaptureMeta(
                clip_id=clip_id,
                junction_type=meta["junction_type"],
                camera_height_m=meta["camera_height_m"],
                weather=meta["weather"],
                time_of_day=meta["time_of_day"],
                discipline=meta["discipline"],
                city=meta["city"]
            ))
    
    def generate(self, target_images: int = TARGET_TOTAL_IMAGES, calibration_frames: int = CALIBRATION_FRAMES):
        """Main generation loop."""
        print(f"Generating synthetic dataset in {self.output_dir}")
        print(f"Target: {target_images} images across {len(GEOMETRIES)} geometries, "
              f"{len(WEATHER_STATES)} weather states, {len(DISCIPLINE_PRESETS)} discipline presets")
        
        frames_per_config = max(1, target_images // (len(GEOMETRIES) * len(WEATHER_STATES) * len(DISCIPLINE_PRESETS) * 10))
        
        config_count = 0
        for geom_name in GEOMETRIES:
            for weather in WEATHER_STATES:
                for discipline in DISCIPLINE_PRESETS:
                    config_count += 1
                    print(f"\n[{config_count}/{len(GEOMETRIES)*len(WEATHER_STATES)*len(DISCIPLINE_PRESETS)}] "
                          f"Generating: {geom_name} | {weather.value} | {discipline}")
                    
                    # Use multiple junction-day combos per config for split diversity
                    # Spread across all junction-days to get proper train/val/test splits
                    for spread_idx in range(0, 140, 10):  # 14 combinations spread across all 140
                        junction_idx, day_idx = divmod(spread_idx, 7)
                        split = self._get_split(junction_idx, day_idx)
                        
                        frames = self._generate_frames_for_config(
                            geom_name, weather, discipline, junction_idx, day_idx, frames_per_config
                        )
                        
                        for img, detections, clip_id, meta in frames:
                            self._save_frame(img, detections, split, clip_id, meta)
        
        # Generate calibration set (stratified sampling)
        print("\nGenerating calibration frames...")
        self._generate_calibration_set(calibration_frames)
        
        # Write data.yaml
        self._write_data_yaml()
        
        # Write captures.json
        self._write_captures_json()
        
        # Print summary
        self._print_summary()
    
    def _generate_calibration_set(self, target_calibration: int = CALIBRATION_FRAMES):
        """Generate calibration frames meeting §6 coverage requirements."""
        # We need: ≥30% rain-affected, ≥20% night/dusk, ≥30% dense two-wheeler
        cal_configs = [
            # Rain-affected (30%+)
            (["light_rain", "heavy_monsoon", "waterlogged"], ["morning", "noon", "evening"], int(target_calibration * 0.4)),
            # Night/dusk (20%+)
            (["clear"], ["night", "evening"], int(target_calibration * 0.25)),
            # Dense two-wheeler (30%+)
            (["clear"], ["morning", "noon"], int(target_calibration * 0.35)),
        ]
        
        cal_frames = 0
        for weathers, times, count in cal_configs:
            for _ in range(count):
                weather_str = random.choice(weathers)
                time_str = random.choice(times)
                weather = WeatherState(weather_str)
                discipline = random.choice(DISCIPLINE_PRESETS)
                geometry = random.choice(list(GEOMETRIES.keys()))
                
                sim = self._create_simulation(geometry, weather, discipline)
                
                # Run for a bit to get vehicles
                for _ in range(50):
                    sim.step()
                
                img, detections = self.renderer.render_frame(sim)
                img = self._augment_image(img, sim.weather_model.current())
                
                clip_id = f"cal_{weather_str}_{time_str}_{geometry}_{cal_frames:04d}"
                meta = {
                    "clip_id": clip_id,
                    "junction_type": geometry,
                    "camera_height_m": 7.5,
                    "weather": weather_str,
                    "time_of_day": time_str,
                    "city": "synthetic",
                    "discipline": discipline,
                }
                
                self._save_frame(img, detections, "train", clip_id, meta, is_calibration=True)
                cal_frames += 1
        
        print(f"Generated {cal_frames} calibration frames")
    
    def _write_data_yaml(self):
        """Write data.yaml in YOLO format."""
        abs_path = self.output_dir.resolve().as_posix()
        yaml_content = f"""path: {abs_path}
train: images/train
val: images/val
test: images/test
names:
"""
        for i, name in enumerate(CLASSES):
            yaml_content += f"  {i}: {name}\n"
        
        yaml_path = self.output_dir / "data.yaml"
        yaml_path.write_text(yaml_content)
        print(f"Written {yaml_path}")
    
    def _write_captures_json(self):
        """Write meta/captures.json."""
        # Deduplicate by clip_id
        seen = set()
        unique_captures = []
        for cap in self.captures_meta:
            if cap.clip_id not in seen:
                seen.add(cap.clip_id)
                unique_captures.append(asdict(cap))
        
        json_path = self.output_dir / "meta" / "captures.json"
        json_path.write_text(json.dumps(unique_captures, indent=2))
        print(f"Written {json_path} ({len(unique_captures)} unique clips)")
    
    def _print_summary(self):
        """Print dataset statistics."""
        print("\n" + "="*60)
        print("DATASET GENERATION COMPLETE")
        print("="*60)
        
        for split in ["train", "val", "test"]:
            img_dir = self.output_dir / "images" / split
            lbl_dir = self.output_dir / "labels" / split
            n_img = len(list(img_dir.glob("*.jpg")))
            n_lbl = len(list(lbl_dir.glob("*.txt")))
            print(f"  {split:5s}: {n_img:5d} images, {n_lbl:5d} labels")
        
        cal_dir = self.output_dir / "calibration" / "frames"
        n_cal = len(list(cal_dir.glob("*.jpg")))
        print(f"  calibration: {n_cal:5d} frames")
        
        print(f"\nTotal images: {self.image_counter}")
        print(f"Unique clips: {len(set(c.clip_id for c in self.captures_meta))}")
        print(f"\nOutput: {self.output_dir}")
        print("Ready for: python scripts/prepare_dataset.py --check")
        print("           python notebooks/train_india_yolo.ipynb")


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Indian traffic dataset")
    parser.add_argument("--output", "-o", default="data/synthetic_india_yolo",
                        help="Output directory (default: data/synthetic_india_yolo)")
    parser.add_argument("--images", "-n", type=int, default=TARGET_TOTAL_IMAGES,
                        help=f"Total images to generate (default: {TARGET_TOTAL_IMAGES})")
    parser.add_argument("--seed", "-s", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--calibration", "-c", type=int, default=CALIBRATION_FRAMES,
                        help=f"Calibration frames (default: {CALIBRATION_FRAMES})")
    args = parser.parse_args()
    
    output_dir = Path(args.output).resolve()
    if output_dir.exists():
        print(f"Output directory {output_dir} exists. Overwriting...")
        shutil.rmtree(output_dir)
    
    generator = SyntheticDatasetGenerator(output_dir, seed=args.seed)
    generator.generate(target_images=args.images, calibration_frames=args.calibration)


if __name__ == "__main__":
    main()