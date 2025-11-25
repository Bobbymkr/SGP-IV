"""
Environmental System Integration - Phase 2 Implementation
======================================================

This module implements:
- Dynamic weather impact system with realistic effects
- Time-of-day traffic patterns
- Environmental condition modeling
- Weather-responsive vehicle behavior
- Day/night cycle with lighting changes

Author: Top 0.1% Industry Expert Team
Date: November 2025
Version: 2.1.0
"""

import numpy as np
import pygame
import math
import random
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta

# Import Phase 1 components
from simulation_phase1 import VehicleType, AdvancedVehicle, TrafficState

logger = logging.getLogger(__name__)

class WeatherCondition(Enum):
    """Comprehensive weather conditions"""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    OVERCAST = "overcast"
    LIGHT_RAIN = "light_rain"
    MODERATE_RAIN = "moderate_rain"
    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    LIGHT_SNOW = "light_snow"
    MODERATE_SNOW = "moderate_snow"
    HEAVY_SNOW = "heavy_snow"
    BLIZZARD = "blizzard"
    FOG_LIGHT = "light_fog"
    FOG_HEAVY = "heavy_fog"
    SMOG = "smog"
    DUST_STORM = "dust_storm"

class TimeOfDay(Enum):
    """Time of day categories with realistic traffic patterns"""
    EARLY_MORNING = "early_morning"    # 00:00 - 06:00
    MORNING_RUSH = "morning_rush"      # 06:00 - 09:00
    MORNING = "morning"                 # 09:00 - 12:00
    AFTERNOON = "afternoon"             # 12:00 - 17:00
    EVENING_RUSH = "evening_rush"      # 17:00 - 20:00
    EVENING = "evening"                 # 20:00 - 23:00
    NIGHT = "night"                     # 23:00 - 00:00

@dataclass
class WeatherParameters:
    """Realistic weather impact parameters"""
    condition: WeatherCondition
    visibility: float              # 0.0 to 1.0 (1.0 = perfect visibility)
    road_friction: float          # 0.0 to 1.0 (1.0 = dry asphalt)
    wind_speed: float            # m/s
    wind_direction: float         # degrees
    precipitation_intensity: float  # mm/hour
    temperature: float           # celsius
    humidity: float              # 0-100%
    
    # Impact multipliers
    speed_reduction_factor: float = 1.0
    reaction_time_multiplier: float = 1.0
    braking_distance_multiplier: float = 1.0
    accident_probability_multiplier: float = 1.0
    visibility_distance: float = 1000.0  # meters
    
    def __post_init__(self):
        """Calculate impact factors based on weather condition"""
        self._calculate_impact_factors()
    
    def _calculate_impact_factors(self):
        """Calculate realistic impact factors for each weather condition"""
        weather_effects = {
            WeatherCondition.CLEAR: {
                'visibility': 1.0, 'road_friction': 1.0, 'speed': 1.0,
                'reaction': 1.0, 'braking': 1.0, 'accident': 1.0, 'vis_distance': 1000
            },
            WeatherCondition.PARTLY_CLOUDY: {
                'visibility': 0.9, 'road_friction': 0.95, 'speed': 0.95,
                'reaction': 1.0, 'braking': 1.0, 'accident': 1.1, 'vis_distance': 800
            },
            WeatherCondition.OVERCAST: {
                'visibility': 0.8, 'road_friction': 0.9, 'speed': 0.9,
                'reaction': 1.05, 'braking': 1.05, 'accident': 1.2, 'vis_distance': 600
            },
            WeatherCondition.LIGHT_RAIN: {
                'visibility': 0.7, 'road_friction': 0.7, 'speed': 0.8,
                'reaction': 1.2, 'braking': 1.3, 'accident': 1.5, 'vis_distance': 400
            },
            WeatherCondition.MODERATE_RAIN: {
                'visibility': 0.5, 'road_friction': 0.5, 'speed': 0.65,
                'reaction': 1.4, 'braking': 1.6, 'accident': 2.0, 'vis_distance': 200
            },
            WeatherCondition.HEAVY_RAIN: {
                'visibility': 0.3, 'road_friction': 0.4, 'speed': 0.5,
                'reaction': 1.6, 'braking': 2.0, 'accident': 3.0, 'vis_distance': 100
            },
            WeatherCondition.THUNDERSTORM: {
                'visibility': 0.2, 'road_friction': 0.35, 'speed': 0.4,
                'reaction': 1.8, 'braking': 2.2, 'accident': 4.0, 'vis_distance': 50
            },
            WeatherCondition.LIGHT_SNOW: {
                'visibility': 0.6, 'road_friction': 0.6, 'speed': 0.7,
                'reaction': 1.3, 'braking': 1.4, 'accident': 1.8, 'vis_distance': 300
            },
            WeatherCondition.MODERATE_SNOW: {
                'visibility': 0.4, 'road_friction': 0.4, 'speed': 0.55,
                'reaction': 1.5, 'braking': 1.7, 'accident': 2.5, 'vis_distance': 150
            },
            WeatherCondition.HEAVY_SNOW: {
                'visibility': 0.2, 'road_friction': 0.3, 'speed': 0.4,
                'reaction': 1.7, 'braking': 2.0, 'accident': 3.5, 'vis_distance': 80
            },
            WeatherCondition.BLIZZARD: {
                'visibility': 0.1, 'road_friction': 0.2, 'speed': 0.25,
                'reaction': 2.0, 'braking': 2.5, 'accident': 5.0, 'vis_distance': 30
            },
            WeatherCondition.FOG_LIGHT: {
                'visibility': 0.5, 'road_friction': 0.9, 'speed': 0.7,
                'reaction': 1.4, 'braking': 1.2, 'accident': 2.2, 'vis_distance': 200
            },
            WeatherCondition.FOG_HEAVY: {
                'visibility': 0.2, 'road_friction': 0.85, 'speed': 0.45,
                'reaction': 1.8, 'braking': 1.4, 'accident': 3.8, 'vis_distance': 50
            },
            WeatherCondition.SMOG: {
                'visibility': 0.6, 'road_friction': 0.95, 'speed': 0.75,
                'reaction': 1.2, 'braking': 1.1, 'accident': 1.6, 'vis_distance': 350
            },
            WeatherCondition.DUST_STORM: {
                'visibility': 0.3, 'road_friction': 0.8, 'speed': 0.6,
                'reaction': 1.5, 'braking': 1.3, 'accident': 2.8, 'vis_distance': 120
            }
        }
        
        effects = weather_effects.get(self.condition, weather_effects[WeatherCondition.CLEAR])
        
        self.visibility = effects['visibility']
        self.road_friction = effects['road_friction']
        self.speed_reduction_factor = effects['speed']
        self.reaction_time_multiplier = effects['reaction']
        self.braking_distance_multiplier = effects['braking']
        self.accident_probability_multiplier = effects['accident']
        self.visibility_distance = effects['vis_distance']

@dataclass
class TimeOfDayParameters:
    """Time-of-day traffic pattern parameters"""
    time_of_day: TimeOfDay
    traffic_density_multiplier: float = 1.0
    speed_multiplier: float = 1.0
    vehicle_type_distribution: Dict[VehicleType, float] = field(default_factory=dict)
    lighting_level: float = 1.0  # 0.0 to 1.0
    accident_probability_multiplier: float = 1.0
    
    def __post_init__(self):
        """Calculate time-of-day parameters"""
        self._calculate_parameters()
    
    def _calculate_parameters(self):
        """Calculate realistic parameters for each time period"""
        time_patterns = {
            TimeOfDay.EARLY_MORNING: {
                'density': 0.3, 'speed': 1.1, 'lighting': 0.2, 'accident': 0.8,
                'distribution': {VehicleType.CAR: 0.8, VehicleType.TRUCK: 0.15, 
                               VehicleType.BUS: 0.02, VehicleType.MOTORCYCLE: 0.03}
            },
            TimeOfDay.MORNING_RUSH: {
                'density': 1.0, 'speed': 0.7, 'lighting': 0.8, 'accident': 1.5,
                'distribution': {VehicleType.CAR: 0.75, VehicleType.TRUCK: 0.1, 
                               VehicleType.BUS: 0.1, VehicleType.MOTORCYCLE: 0.05}
            },
            TimeOfDay.MORNING: {
                'density': 0.6, 'speed': 0.9, 'lighting': 1.0, 'accident': 1.0,
                'distribution': {VehicleType.CAR: 0.7, VehicleType.TRUCK: 0.12, 
                               VehicleType.BUS: 0.08, VehicleType.MOTORCYCLE: 0.1}
            },
            TimeOfDay.AFTERNOON: {
                'density': 0.5, 'speed': 0.95, 'lighting': 1.0, 'accident': 1.0,
                'distribution': {VehicleType.CAR: 0.72, VehicleType.TRUCK: 0.13, 
                               VehicleType.BUS: 0.07, VehicleType.MOTORCYCLE: 0.08}
            },
            TimeOfDay.EVENING_RUSH: {
                'density': 0.9, 'speed': 0.75, 'lighting': 0.6, 'accident': 1.3,
                'distribution': {VehicleType.CAR: 0.8, VehicleType.TRUCK: 0.08, 
                               VehicleType.BUS: 0.07, VehicleType.MOTORCYCLE: 0.05}
            },
            TimeOfDay.EVENING: {
                'density': 0.7, 'speed': 0.85, 'lighting': 0.4, 'accident': 1.2,
                'distribution': {VehicleType.CAR: 0.78, VehicleType.TRUCK: 0.1, 
                               VehicleType.BUS: 0.07, VehicleType.MOTORCYCLE: 0.05}
            },
            TimeOfDay.NIGHT: {
                'density': 0.4, 'speed': 1.05, 'lighting': 0.1, 'accident': 1.8,
                'distribution': {VehicleType.CAR: 0.85, VehicleType.TRUCK: 0.05, 
                               VehicleType.BUS: 0.02, VehicleType.MOTORCYCLE: 0.08}
            }
        }
        
        pattern = time_patterns.get(self.time_of_day, time_patterns[TimeOfDay.MORNING])
        
        self.traffic_density_multiplier = pattern['density']
        self.speed_multiplier = pattern['speed']
        self.lighting_level = pattern['lighting']
        self.accident_probability_multiplier = pattern['accident']
        self.vehicle_type_distribution = pattern['distribution']

class WeatherSystem:
    """Dynamic weather system with realistic transitions"""
    
    def __init__(self):
        self.current_weather = WeatherParameters(WeatherCondition.CLEAR, 1.0, 1.0, 0, 0, 0, 20, 50)
        self.target_weather = self.current_weather
        self.transition_progress = 0.0
        self.transition_duration = 300.0  # 5 minutes for weather change
        self.weather_change_timer = 0.0
        
        # Weather patterns for realistic simulation
        self.weather_patterns = self._generate_weather_patterns()
        self.current_pattern_index = 0
        
        # Particle effects for visualization
        self.particles = []
        self.max_particles = 200
        
    def _generate_weather_patterns(self) -> List[Tuple[WeatherCondition, float]]:
            """Generate realistic weather sequence"""
            # 24-hour weather pattern with realistic transitions
            patterns = [
                (WeatherCondition.CLEAR, 6.0),      # 00:00 - 06:00
                (WeatherCondition.PARTLY_CLOUDY, 3.0),  # 06:00 - 09:00
                (WeatherCondition.CLEAR, 3.0),         # 09:00 - 12:00
                (WeatherCondition.OVERCAST, 2.0),       # 12:00 - 14:00
                (WeatherCondition.LIGHT_RAIN, 1.5),     # 14:00 - 15:30
                (WeatherCondition.MODERATE_RAIN, 2.0),  # 15:30 - 17:30
                (WeatherCondition.LIGHT_RAIN, 1.0),     # 17:30 - 18:30
                (WeatherCondition.PARTLY_CLOUDY, 2.5),  # 18:30 - 21:00
                (WeatherCondition.CLEAR, 3.0),         # 21:00 - 00:00
            ]
            return patterns
    
    def update(self, dt: float, simulation_time: float):
        """Update weather system with realistic transitions"""
        # Check for weather pattern change
        self.weather_change_timer += dt
        current_pattern_time = sum(p[1] for p in self.weather_patterns[:self.current_pattern_index])
        
        if self.weather_change_timer > current_pattern_time:
            self.current_pattern_index = (self.current_pattern_index + 1) % len(self.weather_patterns)
            self._initiate_weather_change()
            self.weather_change_timer = 0.0
        
        # Update weather transition
        if self.transition_progress < 1.0:
            self.transition_progress += dt / self.transition_duration
            self.transition_progress = min(1.0, self.transition_progress)
            
            # Smooth interpolation between weather states
            self._interpolate_weather()
        
        # Update particle effects
        self._update_particles(dt)
    
    def _initiate_weather_change(self):
        """Start transition to new weather"""
        next_weather_condition = self.weather_patterns[self.current_pattern_index][0]
        self.target_weather = WeatherParameters(next_weather_condition, 1.0, 1.0, 0, 0, 0, 20, 50)
        self.transition_progress = 0.0
        
        logger.info(f"Weather changing to: {next_weather_condition.value}")
    
    def _interpolate_weather(self):
        """Smoothly interpolate between current and target weather"""
        t = self.transition_progress
        # Use smooth easing function
        t = t * t * (3.0 - 2.0 * t)
        
        self.current_weather.visibility = (1 - t) * self.current_weather.visibility + t * self.target_weather.visibility
        self.current_weather.road_friction = (1 - t) * self.current_weather.road_friction + t * self.target_weather.road_friction
        self.current_weather.speed_reduction_factor = (1 - t) * self.current_weather.speed_reduction_factor + t * self.target_weather.speed_reduction_factor
        self.current_weather.reaction_time_multiplier = (1 - t) * self.current_weather.reaction_time_multiplier + t * self.target_weather.reaction_time_multiplier
        self.current_weather.visibility_distance = (1 - t) * self.current_weather.visibility_distance + t * self.target_weather.visibility_distance
    
    def _update_particles(self, dt: float):
        """Update weather particle effects"""
        # Remove old particles
        self.particles = [p for p in self.particles if p['life'] > 0]
        
        # Generate new particles based on weather
        particle_rate = self._get_particle_generation_rate()
        
        if random.random() < particle_rate * dt and len(self.particles) < self.max_particles:
            self._generate_particle()
        
        # Update existing particles
        for particle in self.particles:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['life'] -= dt
            particle['vy'] += particle['gravity'] * dt  # Apply gravity
    
    def _get_particle_generation_rate(self) -> float:
        """Get particle generation rate based on weather"""
        rates = {
            WeatherCondition.CLEAR: 0.0,
            WeatherCondition.PARTLY_CLOUDY: 0.5,
            WeatherCondition.OVERCAST: 1.0,
            WeatherCondition.LIGHT_RAIN: 10.0,
            WeatherCondition.MODERATE_RAIN: 20.0,
            WeatherCondition.HEAVY_RAIN: 40.0,
            WeatherCondition.THUNDERSTORM: 50.0,
            WeatherCondition.LIGHT_SNOW: 5.0,
            WeatherCondition.MODERATE_SNOW: 15.0,
            WeatherCondition.HEAVY_SNOW: 30.0,
            WeatherCondition.BLIZZARD: 45.0,
            WeatherCondition.FOG_LIGHT: 2.0,
            WeatherCondition.FOG_HEAVY: 8.0,
            WeatherCondition.SMOG: 3.0,
            WeatherCondition.DUST_STORM: 25.0
        }
        return rates.get(self.current_weather.condition, 0.0)
    
    def _generate_particle(self):
        """Generate a single weather particle"""
        particle = {
            'x': random.uniform(-100, 1600),
            'y': random.uniform(-50, -10),
            'vx': random.uniform(20, 50),  # Horizontal velocity (wind effect)
            'vy': random.uniform(50, 150), # Vertical velocity
            'life': random.uniform(3, 8),
            'size': random.uniform(1, 3),
            'color': self._get_particle_color(),
            'gravity': 9.81,
            'type': self.current_weather.condition
        }
        self.particles.append(particle)
    
    def _get_particle_color(self) -> Tuple[int, int, int]:
        """Get particle color based on weather condition"""
        colors = {
            WeatherCondition.LIGHT_RAIN: (150, 150, 255),
            WeatherCondition.MODERATE_RAIN: (100, 100, 255),
            WeatherCondition.HEAVY_RAIN: (50, 50, 255),
            WeatherCondition.THUNDERSTORM: (80, 80, 200),
            WeatherCondition.LIGHT_SNOW: (255, 255, 255),
            WeatherCondition.MODERATE_SNOW: (240, 240, 255),
            WeatherCondition.HEAVY_SNOW: (220, 220, 255),
            WeatherCondition.BLIZZARD: (200, 200, 255),
            WeatherCondition.FOG_LIGHT: (200, 200, 200),
            WeatherCondition.FOG_HEAVY: (180, 180, 180),
            WeatherCondition.SMOG: (150, 150, 150),
            WeatherCondition.DUST_STORM: (180, 160, 140)
        }
        return colors.get(self.current_weather.condition, (255, 255, 255))
    
    def apply_weather_effects_to_vehicle(self, vehicle: AdvancedVehicle):
        """Apply weather effects to vehicle behavior"""
        # Modify vehicle parameters based on weather
        weather = self.current_weather
        
        # Speed reduction
        vehicle.desired_speed = (vehicle.params.max_speed / 3.6) * weather.speed_reduction_factor
        
        # Reaction time increase
        vehicle.params.reaction_time *= weather.reaction_time_multiplier
        
        # Braking distance increase
        vehicle.params.safe_following_time *= weather.braking_distance_multiplier
        
        # Visibility-based speed adjustment
        if weather.visibility_distance < 100:
            # Reduce speed further in low visibility
            visibility_factor = weather.visibility_distance / 100.0
            vehicle.desired_speed *= visibility_factor

class TimeSystem:
    """Time-of-day system with realistic traffic patterns"""
    
    def __init__(self):
        self.current_time = 6.0  # Start at 6:00 AM
        self.time_scale = 60.0  # 1 real second = 1 simulation minute
        self.current_time_of_day = TimeOfDay.MORNING_RUSH
        self.time_params = TimeOfDayParameters(TimeOfDay.MORNING_RUSH)
        
    def update(self, dt: float):
        """Update time system"""
        # Advance simulation time
        self.current_time += (dt * self.time_scale) / 3600.0  # Convert to hours
        
        # Wrap around 24 hours
        if self.current_time >= 24.0:
            self.current_time -= 24.0
        
        # Update time of day
        self._update_time_of_day()
    
    def _update_time_of_day(self):
        """Update current time of day based on simulation time"""
        hour = int(self.current_time)
        
        if 0 <= hour < 6:
            new_time_of_day = TimeOfDay.EARLY_MORNING
        elif 6 <= hour < 9:
            new_time_of_day = TimeOfDay.MORNING_RUSH
        elif 9 <= hour < 12:
            new_time_of_day = TimeOfDay.MORNING
        elif 12 <= hour < 17:
            new_time_of_day = TimeOfDay.AFTERNOON
        elif 17 <= hour < 20:
            new_time_of_day = TimeOfDay.EVENING_RUSH
        elif 20 <= hour < 23:
            new_time_of_day = TimeOfDay.EVENING
        else:
            new_time_of_day = TimeOfDay.NIGHT
        
        if new_time_of_day != self.current_time_of_day:
            self.current_time_of_day = new_time_of_day
            self.time_params = TimeOfDayParameters(new_time_of_day)
            logger.info(f"Time of day changed to: {new_time_of_day.value}")
    
    def get_time_string(self) -> str:
        """Get formatted time string"""
        hours = int(self.current_time)
        minutes = int((self.current_time - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
    
    def get_vehicle_spawn_probability(self) -> float:
        """Get vehicle spawn probability based on time of day"""
        base_probability = 0.1  # Base 10% chance per frame
        return base_probability * self.time_params.traffic_density_multiplier
    
    def get_vehicle_type_for_time(self) -> VehicleType:
        """Get vehicle type based on time-of-day distribution"""
        distribution = self.time_params.vehicle_type_distribution
        vehicle_types = list(distribution.keys())
        weights = list(distribution.values())
        return np.random.choice(vehicle_types, p=weights)

class EnvironmentalRenderer:
    """Renderer for environmental effects"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.lighting_surface = pygame.Surface((screen_width, screen_height))
        self.lighting_surface.set_alpha(128)
        
    def render_weather_effects(self, screen: pygame.Surface, weather_system: WeatherSystem):
        """Render weather particle effects"""
        for particle in weather_system.particles:
            if 0 <= particle['x'] < self.screen_width and 0 <= particle['y'] < self.screen_height:
                pygame.draw.circle(screen, particle['color'], 
                               (int(particle['x']), int(particle['y'])), 
                               int(particle['size']))
    
    def render_time_of_day_lighting(self, screen: pygame.Surface, time_system: TimeSystem):
        """Render lighting effects based on time of day"""
        lighting_level = time_system.time_params.lighting_level
        
        # Create lighting overlay
        if lighting_level < 1.0:
            # Darken screen for night/evening
            darkness = int((1.0 - lighting_level) * 150)
            overlay = pygame.Surface((self.screen_width, self.screen_height))
            overlay.set_alpha(darkness)
            overlay.fill((0, 0, 50))  # Slight blue tint for night
            screen.blit(overlay, (0, 0))
        
        # Add streetlights for night time
        if lighting_level < 0.5:
            self._render_streetlights(screen)
    
    def _render_streetlights(self, screen: pygame.Surface):
        """Render streetlights for night time"""
        # Streetlight positions along the road
        streetlight_positions = [(200, 150), (400, 150), (600, 150), (800, 150), (1000, 150), (1200, 150), (1400, 150)]
        
        for pos in streetlight_positions:
            # Light pole
            pygame.draw.rect(screen, (100, 100, 100), (pos[0] - 2, pos[1] - 20, 4, 20))
            
            # Light glow
            for radius in range(30, 5, -5):
                alpha = 20 - radius // 2
                color = (255, 255, 200, alpha) if alpha > 0 else (255, 255, 200)
                pygame.draw.circle(screen, color[:3], pos, radius)
    
    def render_weather_info(self, screen: pygame.Surface, weather_system: WeatherSystem, 
                         time_system: TimeSystem, font: pygame.font.Font):
        """Render weather and time information"""
        info_surface = pygame.Surface((350, 120))
        info_surface.set_alpha(200)
        info_surface.fill((0, 0, 0))
        
        y_offset = 10
        
        # Time
        time_text = font.render(f"Time: {time_system.get_time_string()}", True, (255, 255, 255))
        info_surface.blit(time_text, (10, y_offset))
        y_offset += 25
        
        # Time of day
        tod_text = font.render(f"Period: {time_system.current_time_of_day.value}", True, (255, 255, 255))
        info_surface.blit(tod_text, (10, y_offset))
        y_offset += 25
        
        # Weather
        weather_text = font.render(f"Weather: {weather_system.current_weather.condition.value}", True, (255, 255, 255))
        info_surface.blit(weather_text, (10, y_offset))
        y_offset += 25
        
        # Visibility
        visibility_text = font.render(f"Visibility: {weather_system.current_weather.visibility_distance:.0f}m", True, (255, 255, 255))
        info_surface.blit(visibility_text, (10, y_offset))
        y_offset += 25
        
        # Temperature
        temp_text = font.render(f"Temperature: {weather_system.current_weather.temperature:.0f}°C", True, (255, 255, 255))
        info_surface.blit(temp_text, (10, y_offset))
        
        # Blit to main screen
        screen.blit(info_surface, (10, 10))

# Export main classes
__all__ = [
    'WeatherSystem',
    'TimeSystem', 
    'EnvironmentalRenderer',
    'WeatherCondition',
    'TimeOfDay',
    'WeatherParameters',
    'TimeOfDayParameters'
]