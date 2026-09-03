"""
Shared Domain Types
Single source of truth for cross-module dataclasses and enums
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class VehicleType(Enum):
    CAR = "car"
    BUS = "bus"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"
    AUTO = "auto"


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTH_EAST = "north_east"
    NORTH_WEST = "north_west"
    SOUTH_EAST = "south_east"
    SOUTH_WEST = "south_west"


@dataclass
class VehicleDetection:
    """Vehicle detection result"""

    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    direction: Optional[str] = None
    speed: Optional[float] = None


@dataclass
class DetectionResult:
    """Complete detection result for a frame"""

    frame_id: int
    timestamp: float
    detections: List[VehicleDetection]
    processing_time: float
    image_shape: Tuple[int, int]


@dataclass
class SignalTiming:
    """Signal timing plan for one intersection"""

    cycle_length: float
    green_times: Dict[str, float]  # direction -> green time
    yellow_time: float
    all_red_time: float
    offset: float = 0.0


@dataclass
class TrafficState:
    """Current traffic state at intersection"""

    queue_lengths: Dict[str, float]  # vehicles per direction
    flow_rates: Dict[str, float]  # vehicles/hour per direction
    occupancy: Dict[str, float]  # detector occupancy per direction
    phase: str  # current signal phase
    time_in_phase: float  # seconds in current phase
