"""
Advanced Traffic Simulation Engine - Phase 1 Implementation
==========================================================

This module implements the core simulation engine upgrade with:
- Advanced physics engine with realistic vehicle dynamics
- Intelligent driver behavior models (IDM+, MOBIL)
- Multi-lane highway logic
- Enhanced collision detection and safety systems
- Modular architecture for future enhancements

Author: Top 0.1% Industry Expert Team
Date: November 2025
Version: 2.0.0
"""

import numpy as np
import pygame
import math
import random
import time
import threading
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque, defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Physical constants (real-world values)
GRAVITY = 9.81  # m/s²
SCALE_FACTOR = 2.0  # pixels per meter
FPS = 60  # frames per second
DT = 1.0 / FPS  # time step in seconds

class VehicleType(Enum):
    """Vehicle types with realistic parameters"""
    CAR = "car"
    BUS = "bus"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"
    EMERGENCY = "emergency"

class LaneType(Enum):
    """Lane types"""
    REGULAR = "regular"
    BUS = "bus"
    HOV = "hov"
    EMERGENCY = "emergency"
    TURNING = "turning"

class DrivingState(Enum):
    """Driving states"""
    NORMAL = "normal"
    ACCELERATING = "accelerating"
    BRAKING = "braking"
    CRUISING = "cruising"
    TURNING = "turning"
    CHANGING_LANE = "changing_lane"
    STOPPED = "stopped"

@dataclass
class VehicleParameters:
    """Realistic vehicle parameters based on actual vehicle data"""
    vehicle_type: VehicleType
    length: float  # meters
    width: float   # meters
    height: float  # meters
    mass: float    # kg
    max_acceleration: float  # m/s²
    max_deceleration: float  # m/s² (comfortable braking)
    emergency_deceleration: float  # m/s² (emergency braking)
    max_speed: float  # km/h
    reaction_time: float  # seconds
    safe_following_time: float  # seconds
    turning_radius: float  # meters
    
    @classmethod
    def get_parameters(cls, vehicle_type: VehicleType) -> 'VehicleParameters':
        """Get realistic parameters for each vehicle type"""
        params = {
            VehicleType.CAR: cls(
                vehicle_type=VehicleType.CAR,
                length=4.5, width=1.8, height=1.5, mass=1500,
                max_acceleration=2.5, max_deceleration=4.0, emergency_deceleration=8.0,
                max_speed=50, reaction_time=1.0, safe_following_time=1.5, turning_radius=5.5
            ),
            VehicleType.BUS: cls(
                vehicle_type=VehicleType.BUS,
                length=12.0, width=2.5, height=3.0, mass=12000,
                max_acceleration=1.2, max_deceleration=3.0, emergency_deceleration=6.0,
                max_speed=40, reaction_time=1.2, safe_following_time=2.0, turning_radius=8.0
            ),
            VehicleType.TRUCK: cls(
                vehicle_type=VehicleType.TRUCK,
                length=18.0, width=2.5, height=3.5, mass=40000,
                max_acceleration=0.8, max_deceleration=2.5, emergency_deceleration=5.0,
                max_speed=35, reaction_time=1.3, safe_following_time=2.5, turning_radius=10.0
            ),
            VehicleType.MOTORCYCLE: cls(
                vehicle_type=VehicleType.MOTORCYCLE,
                length=2.2, width=0.8, height=1.2, mass=200,
                max_acceleration=4.0, max_deceleration=5.0, emergency_deceleration=9.0,
                max_speed=60, reaction_time=0.8, safe_following_time=1.2, turning_radius=3.5
            ),
            VehicleType.BICYCLE: cls(
                vehicle_type=VehicleType.BICYCLE,
                length=1.8, width=0.6, height=1.0, mass=80,
                max_acceleration=1.5, max_deceleration=3.0, emergency_deceleration=5.0,
                max_speed=25, reaction_time=0.6, safe_following_time=1.0, turning_radius=2.5
            ),
            VehicleType.EMERGENCY: cls(
                vehicle_type=VehicleType.EMERGENCY,
                length=5.5, width=2.2, height=2.5, mass=2500,
                max_acceleration=4.0, max_deceleration=6.0, emergency_deceleration=10.0,
                max_speed=80, reaction_time=0.5, safe_following_time=1.0, turning_radius=5.0
            )
        }
        return params[vehicle_type]

class IntelligentDriverModel:
    """
    Intelligent Driver Model Plus (IDM+) for realistic car-following behavior
    Based on real traffic flow research and human driver behavior
    """
    
    def __init__(self, vehicle_params: VehicleParameters):
        self.params = vehicle_params
        self.desired_speed = vehicle_params.max_speed / 3.6  # Convert km/h to m/s
        self.min_spacing = 2.0  # meters
        self.desired_time_headway = vehicle_params.safe_following_time
        self.acceleration_exponent = 4
        self.comfortable_deceleration = vehicle_params.max_deceleration
        
    def calculate_acceleration(self, current_speed: float, lead_vehicle_distance: float, 
                           lead_vehicle_speed: float, desired_speed: float = None) -> float:
        """
        Calculate acceleration using IDM+ formula
        Returns acceleration in m/s²
        """
        if desired_speed is None:
            desired_speed = self.desired_speed
            
        # Convert to m/s for calculations
        v = current_speed
        v_lead = lead_vehicle_speed
        s = lead_vehicle_distance
        v0 = desired_speed
        
        # Calculate desired spacing
        s_star = self.min_spacing + max(0, v * self.desired_time_headway + 
                                     (v * (v - v_lead)) / (2 * math.sqrt(self.comfortable_deceleration * self.acceleration_exponent)))
        
        # Free road acceleration
        free_acc = self.params.max_acceleration * (1 - (v / v0) ** self.acceleration_exponent)
        
        # Interaction acceleration
        if s > 0:
            interaction_acc = -self.comfortable_deceleration * (s_star / s) ** 2
        else:
            interaction_acc = -self.emergency_braking_acceleration(v)
            
        # Total acceleration
        acceleration = free_acc + interaction_acc
        
        # Clamp to physical limits
        return max(-self.params.emergency_deceleration, 
                  min(self.params.max_acceleration, acceleration))
    
    def emergency_braking_acceleration(self, speed: float) -> float:
        """Calculate emergency braking acceleration"""
        return -self.params.emergency_deceleration * (1 + speed / 10.0)

class MOBILLaneChangeModel:
    """
    Minimizing Overall Braking Induced by Lane Changes (MOBIL) model
    For realistic and safe lane changing behavior
    """
    
    def __init__(self, vehicle_params: VehicleParameters):
        self.params = vehicle_params
        self.politeness_factor = 0.5  # How considerate the driver is
        self.acceleration_threshold = 0.2  # m/s² minimum advantage for lane change
        self.min_safe_distance = 1.0  # meters
        
    def should_change_lane(self, current_lane_acceleration: float,
                        new_lane_front_distance: float, new_lane_front_speed: float,
                        new_lane_rear_distance: float, new_lane_rear_speed: float,
                        current_speed: float) -> Tuple[bool, float]:
        """
        Determine if lane change is safe and beneficial
        Returns (should_change, advantage)
        """
        # Safety check - ensure safe distances
        if new_lane_front_distance < self.min_safe_distance or new_lane_rear_distance < self.min_safe_distance:
            return False, 0.0
            
        # Calculate acceleration in new lane using IDM
        idm = IntelligentDriverModel(self.params)
        
        # Acceleration if we change to new lane (following front vehicle)
        new_lane_acc = idm.calculate_acceleration(current_speed, new_lane_front_distance, new_lane_front_speed)
        
        # Acceleration of rear vehicle in new lane after we change
        rear_vehicle_new_acc = idm.calculate_acceleration(new_lane_rear_speed, 
                                                      new_lane_rear_distance, current_speed)
        
        # Current acceleration of rear vehicle in its lane
        rear_vehicle_current_acc = 0.0  # Would need to track this
        
        # Calculate advantage (MOBIL formula)
        advantage = new_lane_acc - current_lane_acceleration
        disadvantage_to_rear = self.politeness_factor * (rear_vehicle_current_acc - rear_vehicle_new_acc)
        total_advantage = advantage - disadvantage_to_rear
        
        # Lane change is beneficial if total advantage exceeds threshold
        should_change = total_advantage > self.acceleration_threshold
        
        return should_change, total_advantage

class AdvancedVehicle:
    """
    Advanced vehicle class with realistic physics and behavior
    Incorporates IDM+, MOBIL, and enhanced vehicle dynamics
    """
    
    def __init__(self, vehicle_id: int, vehicle_type: VehicleType, 
                 lane: int, position: np.ndarray, velocity: float = 0.0):
        self.id = vehicle_id
        self.type = vehicle_type
        self.params = VehicleParameters.get_parameters(vehicle_type)
        
        # Position and dynamics
        self.position = position.astype(float)  # [x, y] in meters
        self.velocity = velocity  # m/s
        self.acceleration = 0.0  # m/s²
        self.heading = 0.0  # radians
        self.angular_velocity = 0.0  # rad/s
        
        # Lane management
        self.current_lane = lane
        self.target_lane = lane
        self.lane_change_progress = 0.0
        self.lane_change_cooldown = 0.0
        
        # Behavior models
        self.idm = IntelligentDriverModel(self.params)
        self.mobil = MOBILLaneChangeModel(self.params)
        self.driving_state = DrivingState.NORMAL
        
        # Vehicle state
        self.turning_indicator = False
        self.emergency_mode = False
        self.desired_speed = self.params.max_speed / 3.6  # Convert to m/s
        self.brake_lights_on = False
        
        # Tracking
        self.trajectory = deque(maxlen=100)
        self.waiting_time = 0.0
        self.total_distance_traveled = 0.0
        
        # Visual properties
        self.color = self._get_vehicle_color()
        self.length_pixels = int(self.params.length * SCALE_FACTOR)
        self.width_pixels = int(self.params.width * SCALE_FACTOR)
        
    def _get_vehicle_color(self) -> Tuple[int, int, int]:
        """Get vehicle color based on type"""
        colors = {
            VehicleType.CAR: (50, 100, 200),      # Blue
            VehicleType.BUS: (200, 50, 50),       # Red
            VehicleType.TRUCK: (100, 100, 100),    # Gray
            VehicleType.MOTORCYCLE: (200, 150, 50), # Orange
            VehicleType.BICYCLE: (50, 200, 50),     # Green
            VehicleType.EMERGENCY: (255, 0, 0)      # Bright Red
        }
        return colors[self.type]
    
    def update(self, dt: float, traffic_state: 'TrafficState'):
        """Update vehicle state for one time step"""
        #感知周围环境
        nearby_vehicles = traffic_state.get_nearby_vehicles(self)
        front_vehicle = traffic_state.get_front_vehicle(self.current_lane, self.position[0])
        
        # Calculate desired acceleration using IDM
        if front_vehicle:
            distance = front_vehicle.position[0] - self.position[0] - self.params.length
            if distance < 0:
                distance = 0.1  # Prevent collision
            self.acceleration = self.idm.calculate_acceleration(
                self.velocity, distance, front_vehicle.velocity, self.desired_speed
            )
        else:
            # Free road acceleration
            self.acceleration = self.idm.calculate_acceleration(self.velocity, float('inf'), 0, self.desired_speed)
        
        # Check for lane change opportunities
        if self.lane_change_cooldown <= 0 and self.driving_state != DrivingState.TURNING:
            self._evaluate_lane_change(traffic_state)
        
        # Update velocity and position
        self.velocity += self.acceleration * dt
        self.velocity = max(0, min(self.velocity, self.params.max_speed / 3.6))
        
        # Update position based on current state
        if self.driving_state == DrivingState.CHANGING_LANE:
            self._perform_lane_change(dt)
        else:
            self.position[0] += self.velocity * dt
        
        # Update visual state
        self._update_visual_state()
        
        # Update tracking
        self.trajectory.append(self.position.copy())
        self.total_distance_traveled += self.velocity * dt
        self.waiting_time += dt if self.velocity < 0.1 else 0
        
        # Update cooldowns
        self.lane_change_cooldown = max(0, self.lane_change_cooldown - dt)
    
    def _evaluate_lane_change(self, traffic_state: 'TrafficState'):
        """Evaluate if lane change is beneficial using MOBIL"""
        # Get vehicles in adjacent lanes
        left_lane = self.current_lane - 1
        right_lane = self.current_lane + 1
        
        # Check right lane
        if right_lane < traffic_state.num_lanes:
            front_right = traffic_state.get_front_vehicle(right_lane, self.position[0])
            rear_right = traffic_state.get_rear_vehicle(right_lane, self.position[0])
            
            if front_right and rear_right:
                should_change, advantage = self.mobil.should_change_lane(
                    self.acceleration,
                    front_right.position[0] - self.position[0] - self.params.length,
                    front_right.velocity,
                    self.position[0] - rear_right.position[0] - rear_right.params.length,
                    rear_right.velocity,
                    self.velocity
                )
                
                if should_change:
                    self._initiate_lane_change(right_lane)
                    return
        
        # Check left lane
        if left_lane >= 0:
            front_left = traffic_state.get_front_vehicle(left_lane, self.position[0])
            rear_left = traffic_state.get_rear_vehicle(left_lane, self.position[0])
            
            if front_left and rear_left:
                should_change, advantage = self.mobil.should_change_lane(
                    self.acceleration,
                    front_left.position[0] - self.position[0] - self.params.length,
                    front_left.velocity,
                    self.position[0] - rear_left.position[0] - rear_left.params.length,
                    rear_left.velocity,
                    self.velocity
                )
                
                if should_change:
                    self._initiate_lane_change(left_lane)
    
    def _initiate_lane_change(self, target_lane: int):
        """Initiate lane change maneuver"""
        self.target_lane = target_lane
        self.driving_state = DrivingState.CHANGING_LANE
        self.lane_change_progress = 0.0
        self.lane_change_cooldown = 3.0  # 3 second cooldown
        self.turning_indicator = True
    
    def _perform_lane_change(self, dt: float):
        """Execute smooth lane change"""
        lane_change_duration = 2.0  # seconds for complete lane change
        self.lane_change_progress += dt / lane_change_duration
        
        if self.lane_change_progress >= 1.0:
            # Complete lane change
            self.current_lane = self.target_lane
            self.driving_state = DrivingState.NORMAL
            self.lane_change_progress = 0.0
            self.turning_indicator = False
        else:
            # Smooth lateral movement
            lateral_offset = math.sin(self.lane_change_progress * math.pi) * 3.5  # 3.5m lane width
            self.position[1] = self.current_lane * 3.5 + lateral_offset
    
    def _update_visual_state(self):
        """Update visual indicators"""
        # Brake lights
        self.brake_lights_on = self.acceleration < -1.0
        
        # Update heading based on lane change
        if self.driving_state == DrivingState.CHANGING_LANE:
            self.heading = math.sin(self.lane_change_progress * math.pi) * 0.1
        else:
            self.heading *= 0.9  # Return to straight
    
    def get_rect(self) -> pygame.Rect:
        """Get vehicle rectangle for collision detection"""
        x_pixels = int(self.position[0] * SCALE_FACTOR)
        y_pixels = int(self.position[1] * SCALE_FACTOR)
        return pygame.Rect(x_pixels - self.length_pixels // 2,
                         y_pixels - self.width_pixels // 2,
                         self.length_pixels, self.width_pixels)
    
    def draw(self, screen: pygame.Surface, camera_offset: np.ndarray):
        """Draw vehicle on screen"""
        # Calculate screen position
        screen_x = int(self.position[0] * SCALE_FACTOR - camera_offset[0])
        screen_y = int(self.position[1] * SCALE_FACTOR - camera_offset[1])
        
        # Create vehicle rectangle
        vehicle_rect = pygame.Rect(screen_x - self.length_pixels // 2,
                                screen_y - self.width_pixels // 2,
                                self.length_pixels, self.width_pixels)
        
        # Draw vehicle body
        pygame.draw.rect(screen, self.color, vehicle_rect)
        pygame.draw.rect(screen, (0, 0, 0), vehicle_rect, 1)  # Outline
        
        # Draw brake lights if on
        if self.brake_lights_on:
            brake_light_rect = pygame.Rect(screen_x - self.length_pixels // 2 + 2,
                                      screen_y - self.width_pixels // 4,
                                      4, self.width_pixels // 2)
            pygame.draw.rect(screen, (255, 0, 0), brake_light_rect)
        
        # Draw turning indicator if on
        if self.turning_indicator:
            indicator_color = (255, 200, 0)  # Yellow
            if self.target_lane > self.current_lane:  # Right turn
                pygame.draw.circle(screen, indicator_color,
                               (screen_x + self.length_pixels // 2 - 5,
                                screen_y + self.width_pixels // 2 - 5), 3)
            else:  # Left turn
                pygame.draw.circle(screen, indicator_color,
                               (screen_x + self.length_pixels // 2 - 5,
                                screen_y - self.width_pixels // 2 + 5), 3)
        
        # Draw vehicle ID for debugging
        font = pygame.font.Font(None, 12)
        id_text = font.render(str(self.id), True, (255, 255, 255))
        screen.blit(id_text, (screen_x - 5, screen_y - 15))

class TrafficState:
    """Manages the overall traffic state and vehicle interactions"""
    
    def __init__(self, num_lanes: int, road_length: float):
        self.num_lanes = num_lanes
        self.road_length = road_length
        self.vehicles: List[AdvancedVehicle] = []
        self.vehicle_counter = 0
        self.spawn_timer = 0.0
        self.spawn_rate = 2.0  # Average vehicles per second
        
        # Performance tracking
        self.total_vehicles_spawned = 0
        self.total_vehicles_passed = 0
        self.average_speed = 0.0
        self.density = 0.0
        
    def add_vehicle(self, vehicle_type: VehicleType = None, lane: int = None) -> AdvancedVehicle:
        """Add a new vehicle to the simulation"""
        if vehicle_type is None:
            # Weighted random selection based on real traffic composition
            weights = [0.7, 0.05, 0.1, 0.05, 0.05, 0.05]  # Car, Bus, Truck, Motorcycle, Bicycle, Emergency
            vehicle_type = np.random.choice(list(VehicleType), p=weights)
        
        if lane is None:
            lane = random.randint(0, self.num_lanes - 1)
        
        # Check if spawn position is clear
        spawn_position = np.array([10.0, lane * 3.5])  # 3.5m lane width
        if not self._is_position_clear(spawn_position, lane):
            return None  # Cannot spawn, position occupied
        
        # Create vehicle
        vehicle = AdvancedVehicle(self.vehicle_counter, vehicle_type, lane, spawn_position)
        self.vehicle_counter += 1
        self.vehicles.append(vehicle)
        self.total_vehicles_spawned += 1
        
        return vehicle
    
    def _is_position_clear(self, position: np.ndarray, lane: int, min_distance: float = 10.0) -> bool:
        """Check if a position is clear for spawning"""
        for vehicle in self.vehicles:
            if vehicle.current_lane == lane:
                distance = abs(vehicle.position[0] - position[0])
                if distance < min_distance:
                    return False
        return True
    
    def get_nearby_vehicles(self, vehicle: AdvancedVehicle, radius: float = 50.0) -> List[AdvancedVehicle]:
        """Get all vehicles within radius of given vehicle"""
        nearby = []
        for other in self.vehicles:
            if other.id != vehicle.id:
                distance = np.linalg.norm(other.position - vehicle.position)
                if distance < radius:
                    nearby.append(other)
        return nearby
    
    def get_front_vehicle(self, lane: int, position: float) -> Optional[AdvancedVehicle]:
        """Get the front vehicle in a given lane"""
        front_vehicle = None
        min_distance = float('inf')
        
        for vehicle in self.vehicles:
            if vehicle.current_lane == lane and vehicle.position[0] > position:
                distance = vehicle.position[0] - position
                if distance < min_distance:
                    min_distance = distance
                    front_vehicle = vehicle
        
        return front_vehicle
    
    def get_rear_vehicle(self, lane: int, position: float) -> Optional[AdvancedVehicle]:
        """Get the rear vehicle in a given lane"""
        rear_vehicle = None
        min_distance = float('inf')
        
        for vehicle in self.vehicles:
            if vehicle.current_lane == lane and vehicle.position[0] < position:
                distance = position - vehicle.position[0]
                if distance < min_distance:
                    min_distance = distance
                    rear_vehicle = vehicle
        
        return rear_vehicle
    
    def update(self, dt: float):
        """Update all vehicles and traffic state"""
        # Update vehicles
        for vehicle in self.vehicles[:]:  # Copy list to allow removal during iteration
            vehicle.update(dt, self)
            
            # Remove vehicles that have left the simulation area
            if vehicle.position[0] > self.road_length:
                self.vehicles.remove(vehicle)
                self.total_vehicles_passed += 1
        
        # Spawn new vehicles
        self.spawn_timer += dt
        if self.spawn_timer > 1.0 / self.spawn_rate:
            self.spawn_timer = 0.0
            self.add_vehicle()
        
        # Update performance metrics
        self._update_metrics()
    
    def _update_metrics(self):
        """Update traffic performance metrics"""
        if not self.vehicles:
            return
        
        # Average speed
        total_speed = sum(v.velocity for v in self.vehicles)
        self.average_speed = total_speed / len(self.vehicles)
        
        # Density (vehicles per km)
        self.density = len(self.vehicles) / (self.road_length / 1000.0)
    
    def get_metrics(self) -> Dict[str, float]:
        """Get current traffic metrics"""
        return {
            'vehicle_count': len(self.vehicles),
            'average_speed_kmh': self.average_speed * 3.6,
            'density_vehicles_per_km': self.density,
            'total_spawned': self.total_vehicles_spawned,
            'total_passed': self.total_vehicles_passed,
            'flow_rate': self.total_vehicles_passed / max(1, time.time() - getattr(self, 'start_time', time.time()))
        }

class PhysicsEngine:
    """Advanced physics engine for vehicle dynamics"""
    
    def __init__(self):
        self.gravity = GRAVITY
        self.air_resistance_coefficient = 0.3
        self.rolling_resistance_coefficient = 0.015
        self.dt = DT
        
    def update_vehicle_physics(self, vehicle: AdvancedVehicle, dt: float):
        """Update vehicle physics with realistic forces"""
        # Calculate forces acting on vehicle
        # 1. Engine/braking force (from acceleration)
        engine_force = vehicle.params.mass * vehicle.acceleration
        
        # 2. Air resistance (proportional to velocity squared)
        air_resistance = -0.5 * self.air_resistance_coefficient * 1.2 * \
                        (vehicle.params.width * vehicle.params.height) * vehicle.velocity * abs(vehicle.velocity)
        
        # 3. Rolling resistance
        rolling_resistance = -self.rolling_resistance_coefficient * vehicle.params.mass * self.gravity
        
        # Total force
        total_force = engine_force + air_resistance + rolling_resistance
        
        # Update velocity and position
        actual_acceleration = total_force / vehicle.params.mass
        vehicle.velocity += actual_acceleration * dt
        vehicle.position[0] += vehicle.velocity * dt
        
        # Ensure physical constraints
        vehicle.velocity = max(0, vehicle.velocity)
        vehicle.acceleration = actual_acceleration

# Export main classes for use in simulation
__all__ = [
    'AdvancedVehicle',
    'TrafficState', 
    'PhysicsEngine',
    'VehicleType',
    'VehicleParameters',
    'IntelligentDriverModel',
    'MOBILLaneChangeModel',
    'DrivingState',
    'LaneType'
]