"""
Enhanced Traffic Signal Configuration
Combines original simulation settings with AI capabilities
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class SimulationConfig:
    """Core simulation parameters"""
    # Screen settings
    screen_width: int = 1400
    screen_height: int = 800
    
    # Signal settings
    num_signals: int = 4
    default_red: int = 150
    default_yellow: int = 5
    default_green: int = 20
    default_minimum: int = 10
    default_maximum: int = 60
    
    # Simulation settings
    sim_time: int = 300  # Total simulation time in seconds
    detection_time: int = 5  # Time before green to detect vehicles
    
    # Vehicle settings
    num_lanes: int = 2
    gap: int = 15  # stopping gap
    gap2: int = 15  # moving gap
    rotation_angle: int = 3
    
    # Vehicle speeds (pixels per frame)
    speeds: Dict[str, float] = None
    
    # Vehicle service times (seconds to cross intersection)
    service_times: Dict[str, float] = None
    
    def __post_init__(self):
        if self.speeds is None:
            self.speeds = {
                'car': 2.25,
                'bus': 1.8,
                'truck': 1.8,
                'rickshaw': 2.0,
                'bike': 2.5
            }
        
        if self.service_times is None:
            self.service_times = {
                'car': 2.0,
                'bike': 1.0,
                'rickshaw': 2.25,
                'bus': 2.5,
                'truck': 2.5
            }


@dataclass
class AIConfig:
    """AI/RL agent configuration"""
    # DQN settings
    state_dim: int = 4  # Queue lengths for 4 directions
    action_dim: int = 12  # Green durations 5-60s in 5s steps
    hidden_dim: int = 128
    learning_rate: float = 0.001
    gamma: float = 0.95
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    batch_size: int = 64
    memory_size: int = 10000
    target_update_freq: int = 100
    
    # Training settings
    training_episodes: int = 1000
    max_steps_per_episode: int = 500
    
    # Controller mode
    controller_type: str = 'dqn'  # 'dqn', 'fuzzy', 'ga', 'pso', 'webster', 'fixed'


@dataclass
class VisualConfig:
    """Visual rendering configuration"""
    # Colors
    black: Tuple[int, int, int] = (0, 0, 0)
    white: Tuple[int, int, int] = (255, 255, 255)
    
    # Coordinates
    signal_coords: List[Tuple[int, int]] = None
    signal_timer_coords: List[Tuple[int, int]] = None
    vehicle_count_coords: List[Tuple[int, int]] = None
    
    # Stop lines
    stop_lines: Dict[str, int] = None
    default_stops: Dict[str, int] = None
    
    # Vehicle starting positions
    x_coords: Dict[str, List[int]] = None
    y_coords: Dict[str, List[int]] = None
    
    # Intersection mid points for turns
    mid_points: Dict[str, Dict[str, int]] = None
    
    def __post_init__(self):
        if self.signal_coords is None:
            self.signal_coords = [
                (530, 230),  # right
                (810, 230),  # down
                (810, 570),  # left
                (530, 570)   # up
            ]
        
        if self.signal_timer_coords is None:
            self.signal_timer_coords = [
                (530, 210),
                (810, 210),
                (810, 550),
                (530, 550)
            ]
        
        if self.vehicle_count_coords is None:
            self.vehicle_count_coords = [
                (480, 210),
                (880, 210),
                (880, 550),
                (480, 550)
            ]
        
        if self.stop_lines is None:
            self.stop_lines = {
                'right': 590,
                'down': 330,
                'left': 800,
                'up': 535
            }
        
        if self.default_stops is None:
            self.default_stops = {
                'right': 580,
                'down': 320,
                'left': 810,
                'up': 545
            }
        
        if self.x_coords is None:
            self.x_coords = {
                'right': [0, 0, 0],
                'down': [755, 727, 697],
                'left': [1400, 1400, 1400],
                'up': [602, 627, 657]
            }
        
        if self.y_coords is None:
            self.y_coords = {
                'right': [348, 370, 398],
                'down': [0, 0, 0],
                'left': [498, 466, 436],
                'up': [800, 800, 800]
            }
        
        if self.mid_points is None:
            self.mid_points = {
                'right': {'x': 705, 'y': 445},
                'down': {'x': 695, 'y': 450},
                'left': {'x': 695, 'y': 425},
                'up': {'x': 695, 'y': 400}
            }


# Global mappings
VEHICLE_TYPES = {0: 'car', 1: 'bus', 2: 'truck', 3: 'rickshaw', 4: 'bike'}
DIRECTION_NUMBERS = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}
DIRECTION_NAMES = {'right': 0, 'down': 1, 'left': 2, 'up': 3}


def get_default_config() -> Tuple[SimulationConfig, AIConfig, VisualConfig]:
    """Get default configuration objects"""
    return SimulationConfig(), AIConfig(), VisualConfig()
