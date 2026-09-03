"""
Shared pytest fixtures for Adaptive Traffic Signal Timer tests
"""

import pytest

collect_ignore_glob = [
    # Legacy tests targeting the removed Code/YOLO/darkflow layout
    # (vehicle_detection_modern.py, run_project.py, simulation.py were
    # deleted in the 2bb10b9 project restructure). Quarantined, not deleted.
    "**/test_vehicle_detection_unit.py",
    "**/test_simulation_unit.py",
    "**/test_edge_cases.py",
    "**/test_enhanced_gif.py",
    "**/test_gif_loading.py",
    "**/test_enhanced_demo.py",
]


import numpy as np

from adaptive_traffic.config.settings import Settings
from adaptive_traffic.core.control.controllers import (
    FixedTimeController,
    FuzzyController,
    TrafficState,
    WebsterController,
)
from adaptive_traffic.core.detection.detector import VehicleDetection
from adaptive_traffic.core.simulation.engine import (
    Direction,
    Intersection,
    Lane,
    TrafficSimulation,
)


@pytest.fixture
def settings():
    """Test settings"""
    return Settings(
        environment="testing", debug=True, yolo_model_path="yolov8n.pt", confidence_threshold=0.5
    )


@pytest.fixture
def mock_detection():
    """Mock vehicle detection"""
    return VehicleDetection(
        class_id=2, class_name="car", confidence=0.95, bbox=(100, 200, 250, 320), center=(175, 260)
    )


@pytest.fixture
def mock_detections():
    """Multiple mock detections"""
    return [
        VehicleDetection(2, "car", 0.95, (100, 200, 250, 320), (175, 260)),
        VehicleDetection(7, "truck", 0.88, (300, 180, 480, 350), (390, 265)),
        VehicleDetection(5, "bus", 0.92, (50, 210, 200, 380), (125, 295)),
    ]


@pytest.fixture
def traffic_state():
    """Sample traffic state"""
    return TrafficState(
        queue_lengths={"north": 10, "south": 8, "east": 15, "west": 12},
        flow_rates={"north": 600, "south": 550, "east": 400, "west": 350},
        occupancy={"north": 0.3, "south": 0.25, "east": 0.4, "west": 0.35},
        phase="NS_green",
        time_in_phase=20.0,
    )


@pytest.fixture
def fixed_controller():
    """Fixed time controller"""
    return FixedTimeController(
        {
            "min_green": 10,
            "max_green": 60,
            "yellow_time": 5,
            "all_red_time": 2,
            "directions": ["north", "south", "east", "west"],
            "timing_plans": {
                "plan_1": {
                    "cycle_length": 120,
                    "green_north": 30,
                    "green_south": 30,
                    "green_east": 30,
                    "green_west": 30,
                }
            },
            "default_plan": "plan_1",
        }
    )


@pytest.fixture
def webster_controller():
    """Webster controller"""
    return WebsterController(
        {
            "min_green": 10,
            "max_green": 60,
            "yellow_time": 5,
            "all_red_time": 2,
            "directions": ["north", "south", "east", "west"],
            "lost_time": 12,
        }
    )


@pytest.fixture
def fuzzy_controller():
    """Fuzzy controller"""
    return FuzzyController(
        {
            "min_green": 10,
            "max_green": 60,
            "yellow_time": 5,
            "all_red_time": 2,
            "directions": ["north", "south", "east", "west"],
        }
    )


@pytest.fixture
def sample_simulation():
    """Sample traffic simulation"""
    sim = TrafficSimulation(
        {
            "time_step": 0.1,
            "max_time": 3600,
            "generation_rates": {
                Direction.NORTH: 600,
                Direction.SOUTH: 600,
                Direction.EAST: 400,
                Direction.WEST: 400,
            },
        }
    )

    intersection = Intersection(
        id="main",
        lanes={
            "north_0": Lane(Direction.NORTH, 0, 200),
            "south_0": Lane(Direction.SOUTH, 0, 200),
            "east_0": Lane(Direction.EAST, 0, 200),
            "west_0": Lane(Direction.WEST, 0, 200),
        },
        signal_timing={"NS_green": 30, "NS_yellow": 5, "EW_green": 30, "EW_yellow": 5},
    )
    sim.add_intersection(intersection)
    return sim


@pytest.fixture
def sample_forecast_data():
    """Sample forecast data"""
    return {
        "north": np.random.randint(300, 600, 24).tolist(),
        "south": np.random.randint(300, 600, 24).tolist(),
        "east": np.random.randint(200, 500, 24).tolist(),
        "west": np.random.randint(200, 500, 24).tolist(),
    }


@pytest.fixture(autouse=True)
def reset_random_seed():
    """Reset random seed for reproducible tests"""
    np.random.seed(42)
    yield
