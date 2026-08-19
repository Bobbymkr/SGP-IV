"""
Traffic Simulation Engine
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)


class VehicleType(Enum):
    CAR = "car"
    BUS = "bus"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


@dataclass
class Vehicle:
    """Vehicle in simulation"""
    id: int
    vehicle_type: VehicleType
    direction: Direction
    lane: int
    position: float  # Distance from stop line (meters)
    speed: float     # m/s
    target_speed: float
    acceleration: float = 0.0
    waiting_time: float = 0.0
    route: List[Direction] = field(default_factory=list)
    current_target: Optional[Direction] = None


@dataclass
class Lane:
    """Lane in simulation"""
    direction: Direction
    lane_index: int
    length: float  # meters
    vehicles: List[Vehicle] = field(default_factory=list)
    stop_line: float = 0.0
    signal_state: str = "red"  # red, yellow, green


@dataclass
class Intersection:
    """Intersection with lanes and signal control"""
    id: str
    lanes: Dict[str, Lane]  # key: "direction_laneIndex"
    signal_timing: Dict[str, float]  # phase -> duration
    current_phase: str = "NS_green"
    phase_timer: float = 0.0
    phase_sequence: List[str] = field(default_factory=lambda: ["NS_green", "NS_yellow", "EW_green", "EW_yellow"])


class TrafficSimulation:
    """Microscopic traffic simulation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.dt = config.get('time_step', 0.1)  # seconds
        self.simulation_time = 0.0
        self.max_time = config.get('max_time', 3600)  # seconds
        
        # Vehicle properties by type
        self.vehicle_properties = {
            VehicleType.CAR: {'length': 4.5, 'max_speed': 16.7, 'accel': 2.5, 'decel': 4.5},
            VehicleType.BUS: {'length': 12.0, 'max_speed': 13.9, 'accel': 1.5, 'decel': 3.5},
            VehicleType.TRUCK: {'length': 10.0, 'max_speed': 11.1, 'accel': 1.2, 'decel': 3.0},
            VehicleType.MOTORCYCLE: {'length': 2.0, 'max_speed': 22.2, 'accel': 3.5, 'decel': 5.0},
            VehicleType.BICYCLE: {'length': 1.8, 'max_speed': 5.6, 'accel': 1.0, 'decel': 2.5},
        }
        
        # Generation rates (vehicles/hour per lane)
        self.generation_rates = config.get('generation_rates', {
            Direction.NORTH: 600,
            Direction.SOUTH: 600,
            Direction.EAST: 400,
            Direction.WEST: 400
        })
        
        self.intersections: Dict[str, Intersection] = {}
        self.vehicles: List[Vehicle] = []
        self.vehicle_counter = 0
        self.vehicle_id_map: Dict[int, Vehicle] = {}
        
        # Statistics
        self.stats = {
            'total_generated': 0,
            'total_completed': 0,
            'total_waiting_time': 0.0,
            'total_travel_time': 0.0,
            'avg_speed': 0.0
        }
    
    def add_intersection(self, intersection: Intersection):
        """Add intersection to simulation"""
        self.intersections[intersection.id] = intersection
        
        # Initialize lanes
        for lane_key, lane in intersection.lanes.items():
            lane.vehicles = []
            lane.signal_state = "red"
    
    def step(self):
        """Advance simulation by one time step"""
        self.simulation_time += self.dt
        
        # Update signal states
        self._update_signals()
        
        # Generate new vehicles
        self._generate_vehicles()
        
        # Update vehicle positions
        self._update_vehicles()
        
        # Remove vehicles that have left the network
        self._remove_completed_vehicles()
        
        # Update statistics
        self._update_statistics()
    
    def _update_signals(self):
        """Update traffic signal states"""
        for intersection in self.intersections.values():
            intersection.phase_timer += self.dt
            
            # Get current phase duration
            phase_duration = intersection.signal_timing.get(
                intersection.current_phase, 30
            )
            
            # Check for phase change
            if intersection.phase_timer >= phase_duration:
                # Move to next phase
                current_idx = intersection.phase_sequence.index(intersection.current_phase)
                next_idx = (current_idx + 1) % len(intersection.phase_sequence)
                intersection.current_phase = intersection.phase_sequence[next_idx]
                intersection.phase_timer = 0.0
                
                # Update lane signal states
                self._update_lane_signals(intersection)
    
    def _update_lane_signals(self, intersection: Intersection):
        """Update lane signal states based on current phase"""
        phase = intersection.current_phase
        
        for lane_key, lane in intersection.lanes.items():
            direction = lane.direction.value
            
            if "NS" in phase and direction in ["north", "south"]:
                lane.signal_state = phase.replace("NS_", "").lower()
            elif "EW" in phase and direction in ["east", "west"]:
                lane.signal_state = phase.replace("EW_", "").lower()
            else:
                lane.signal_state = "red"
    
    def _generate_vehicles(self):
        """Generate new vehicles based on rates"""
        for direction, rate_per_hour in self.generation_rates.items():
            # Convert to per time step
            rate_per_step = rate_per_hour * self.dt / 3600
            
            # Poisson arrival
            if random.random() < rate_per_step:
                self._create_vehicle(direction)
    
    def _create_vehicle(self, direction: Direction):
        """Create a new vehicle"""
        # Choose vehicle type (weighted)
        vtype = random.choices(
            list(VehicleType),
            weights=[0.6, 0.05, 0.1, 0.1, 0.15]
        )[0]
        
        props = self.vehicle_properties[vtype]
        
        # Find available lane
        for intersection in self.intersections.values():
            for lane_key, lane in intersection.lanes.items():
                if lane.direction == direction and lane.lane_index == 0:
                    # Check if space at entry
                    entry_pos = lane.length
                    can_spawn = True
                    for veh in lane.vehicles:
                        if veh.position > entry_pos - props['length'] - 2:
                            can_spawn = False
                            break
                    
                    if can_spawn:
                        vehicle = Vehicle(
                            id=self.vehicle_counter,
                            vehicle_type=vtype,
                            direction=direction,
                            lane=lane.lane_index,
                            position=entry_pos,
                            speed=0.0,
                            target_speed=props['max_speed'],
                            current_target=direction
                        )
                        
                        lane.vehicles.append(vehicle)
                        self.vehicles.append(vehicle)
                        self.vehicle_id_map[vehicle.id] = vehicle
                        self.vehicle_counter += 1
                        self.stats['total_generated'] += 1
                        return
    
    def _update_vehicles(self):
        """Update all vehicle positions and states"""
        for intersection in self.intersections.values():
            for lane_key, lane in intersection.lanes.items():
                self._update_lane_vehicles(lane, intersection)
    
    def _update_lane_vehicles(self, lane: Lane, intersection: Intersection):
        """Update vehicles in a single lane"""
        # Sort vehicles by position (closest to stop line first)
        lane.vehicles.sort(key=lambda v: v.position)
        
        for i, vehicle in enumerate(lane.vehicles):
            props = self.vehicle_properties[vehicle.vehicle_type]
            
            # Determine target speed based on signal and leading vehicle
            target_speed = self._calculate_target_speed(vehicle, lane, i, intersection)
            
            # Calculate acceleration
            if vehicle.speed < target_speed:
                vehicle.acceleration = min(props['accel'], (target_speed - vehicle.speed) / self.dt)
            else:
                vehicle.acceleration = max(-props['decel'], (target_speed - vehicle.speed) / self.dt)
            
            # Update speed
            vehicle.speed = max(0, vehicle.speed + vehicle.acceleration * self.dt)
            
            # Update position (vehicles move toward stop line at position 0)
            vehicle.position -= vehicle.speed * self.dt
            
            # Update waiting time
            if vehicle.speed < 0.5:
                vehicle.waiting_time += self.dt
                self.stats['total_waiting_time'] += self.dt
            
            # Check if vehicle passed stop line
            if vehicle.position <= 0:
                vehicle.position = 0
                # Vehicle will be removed in _remove_completed_vehicles
    
    def _calculate_target_speed(self, vehicle: Vehicle, lane: Lane, 
                               index: int, intersection: Intersection) -> float:
        """Calculate target speed for a vehicle"""
        props = self.vehicle_properties[vehicle.vehicle_type]
        max_speed = props['max_speed']
        
        # Check signal
        if lane.signal_state == "red" and vehicle.position < 30:
            # Must stop at stop line
            stopping_distance = vehicle.position
            if stopping_distance > 0:
                # Decelerate to stop
                required_decel = (vehicle.speed ** 2) / (2 * stopping_distance)
                if required_decel > props['decel']:
                    return 0.0
            return 0.0
        
        elif lane.signal_state == "yellow" and vehicle.position < 20:
            # Prepare to stop if can't clear intersection
            return min(vehicle.speed, max_speed * 0.5)
        
        # Check leading vehicle
        if index > 0:
            leader = lane.vehicles[index - 1]
            gap = leader.position - vehicle.position - props['length']
            
            if gap < 10:  # Too close
                return min(vehicle.speed, leader.speed * 0.9)
            elif gap < 20:
                return min(vehicle.speed, leader.speed * 1.1)
        
        # Free flow
        return max_speed
    
    def _remove_completed_vehicles(self):
        """Remove vehicles that have passed through the intersection"""
        for intersection in self.intersections.values():
            for lane_key, lane in intersection.lanes.items():
                # Vehicles with position <= 0 have passed
                completed = [v for v in lane.vehicles if v.position <= 0]
                for v in completed:
                    lane.vehicles.remove(v)
                    self.vehicles.remove(v)
                    del self.vehicle_id_map[v.id]
                    self.stats['total_completed'] += 1
    
    def _update_statistics(self):
        """Update simulation statistics"""
        if self.vehicles:
            self.stats['avg_speed'] = np.mean([v.speed for v in self.vehicles])
    
    def get_intersection_state(self, intersection_id: str) -> Dict:
        """Get current state of an intersection"""
        if intersection_id not in self.intersections:
            return {}
        
        intersection = self.intersections[intersection_id]
        
        queues = {}
        flows = {}
        
        for lane_key, lane in intersection.lanes.items():
            direction = lane.direction.value
            # Count vehicles waiting (speed < 1 m/s)
            waiting = sum(1 for v in lane.vehicles if v.speed < 1.0 and v.position < 50)
            queues[direction] = waiting
            
            # Flow rate (vehicles/hour that passed recently)
            # Simplified: count vehicles near stop line moving
            moving = sum(1 for v in lane.vehicles if v.speed > 1.0 and v.position < 30)
            flows[direction] = moving * 3600  # rough estimate
        
        return {
            'queues': queues,
            'flows': flows,
            'signal_phase': intersection.current_phase,
            'phase_timer': intersection.phase_timer
        }
    
    def get_network_stats(self) -> Dict:
        """Get overall network statistics"""
        return {
            'simulation_time': self.simulation_time,
            'active_vehicles': len(self.vehicles),
            'total_generated': self.stats['total_generated'],
            'total_completed': self.stats['total_completed'],
            'avg_waiting_time': self.stats['total_waiting_time'] / max(self.stats['total_completed'], 1),
            'avg_speed': self.stats['avg_speed'],
            'throughput': self.stats['total_completed'] / max(self.simulation_time / 3600, 1/3600)
        }


def create_intersection(config: Dict) -> Intersection:
    """Factory function to create intersection"""
    lanes = {}
    
    for direction in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
        for lane_idx in range(config.get('lanes_per_direction', 2)):
            lane_key = f"{direction.value}_{lane_idx}"
            lanes[lane_key] = Lane(
                direction=direction,
                lane_index=lane_idx,
                length=config.get('lane_length', 200),
                stop_line=0.0
            )
    
    return Intersection(
        id=config.get('id', 'main'),
        lanes=lanes,
        signal_timing=config.get('signal_timing', {
            'NS_green': 30,
            'NS_yellow': 5,
            'EW_green': 30,
            'EW_yellow': 5
        }),
        current_phase="NS_green",
        phase_sequence=["NS_green", "NS_yellow", "EW_green", "EW_yellow"]
    )


def create_simulation(config: Dict) -> TrafficSimulation:
    """Factory function to create simulation"""
    return TrafficSimulation(config)