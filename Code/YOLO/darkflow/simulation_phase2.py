"""
Enhanced Traffic Simulation with Environmental Integration - Phase 2
================================================================

Advanced traffic simulation featuring:
- Weather impact system with dynamic conditions
- Time-of-day traffic patterns
- Environmental particle effects
- Day/night lighting cycles
- Weather-responsive vehicle behavior

This builds upon Phase 1 with comprehensive environmental modeling.
"""

import pygame
import numpy as np
import math
import random
import time
import threading
import sys
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

# Import Phase 1 components
from simulation_phase1 import (
    AdvancedVehicle, TrafficState, PhysicsEngine, VehicleType,
    VehicleParameters, IntelligentDriverModel, MOBILLaneChangeModel,
    DrivingState, LaneType
)

# Import Phase 2 environmental systems
from environmental_system import (
    WeatherSystem, TimeSystem, EnvironmentalRenderer,
    WeatherCondition, TimeOfDay, WeatherParameters, TimeOfDayParameters
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced display constants
SCREEN_WIDTH = 1800
SCREEN_HEIGHT = 1000
FPS = 60
SCALE_FACTOR = 2.0

# Road configuration
NUM_LANES = 4
ROAD_LENGTH = 600.0  # meters
LANE_WIDTH = 3.5  # meters

# Enhanced colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 100, 255)
ORANGE = (255, 165, 0)
NIGHT_BLUE = (10, 20, 40)
STREETLIGHT_YELLOW = (255, 220, 100)

class EnvironmentallyAwareVehicle(AdvancedVehicle):
    """Enhanced vehicle class that responds to environmental conditions"""
    
    def __init__(self, vehicle_id: int, vehicle_type: VehicleType, 
                 lane: int, position: np.ndarray, velocity: float = 0.0,
                 weather_system: WeatherSystem = None, time_system: TimeSystem = None):
        super().__init__(vehicle_id, vehicle_type, lane, position, velocity)
        
        # Environmental awareness
        self.weather_system = weather_system
        self.time_system = time_system
        self.headlights_on = False
        self.wipers_on = False
        self.hazard_lights = False
        
        # Weather-specific behavior
        self.base_max_speed = self.params.max_speed
        self.base_reaction_time = self.params.reaction_time
        self.base_safe_following_time = self.params.safe_following_time
    
    def update(self, dt: float, traffic_state: 'TrafficState'):
        """Update vehicle with environmental effects"""
        # Apply environmental effects
        if self.weather_system:
            self.weather_system.apply_weather_effects_to_vehicle(self)
        
        # Update headlights based on time of day
        if self.time_system:
            self._update_lighting()
        
        # Call parent update
        super().update(dt, traffic_state)
    
    def _update_lighting(self):
        """Update vehicle lighting based on time of day"""
        lighting_level = self.time_system.time_params.lighting_level
        
        # Turn on headlights in low light conditions
        self.headlights_on = lighting_level < 0.7
        
        # Turn on wipers in rain/snow
        if self.weather_system:
            weather_condition = self.weather_system.current_weather.condition
            self.wipers_on = weather_condition in [
                WeatherCondition.LIGHT_RAIN, WeatherCondition.MODERATE_RAIN,
                WeatherCondition.HEAVY_RAIN, WeatherCondition.THUNDERSTORM,
                WeatherCondition.LIGHT_SNOW, WeatherCondition.MODERATE_SNOW,
                WeatherCondition.HEAVY_SNOW, WeatherCondition.BLIZZARD
            ]
    
    def draw(self, screen: pygame.Surface, camera_offset: np.ndarray):
        """Draw vehicle with environmental effects"""
        # Call parent draw method
        super().draw(screen, camera_offset)
        
        # Draw environmental effects
        self._draw_environmental_effects(screen, camera_offset)
    
    def _draw_environmental_effects(self, screen: pygame.Surface, camera_offset: np.ndarray):
        """Draw weather and time-specific vehicle effects"""
        screen_x = int(self.position[0] * SCALE_FACTOR - camera_offset[0])
        screen_y = int(self.position[1] * SCALE_FACTOR - camera_offset[1])
        
        # Draw headlights
        if self.headlights_on:
            headlight_color = (255, 255, 200, 100)  # Yellowish white with transparency
            headlight_length = 40
            headlight_width = 15
            
            # Left headlight beam
            left_beam_points = [
                (screen_x - 5, screen_y - 2),
                (screen_x + headlight_length, screen_y - headlight_width)
            ]
            pygame.draw.polygon(screen, headlight_color[:3], left_beam_points)
            
            # Right headlight beam
            right_beam_points = [
                (screen_x - 5, screen_y + 2),
                (screen_x + headlight_length, screen_y + headlight_width)
            ]
            pygame.draw.polygon(screen, headlight_color[:3], right_beam_points)
        
        # Draw wipers in rain
        if self.wipers_on and random.random() < 0.1:  # Intermittent wiper motion
            wiper_color = (50, 50, 50)
            pygame.draw.arc(screen, wiper_color, 
                         (screen_x - 10, screen_y - 10, 20, 20), 
                         0, math.pi/2, 2)

class EnhancedTrafficSimulation:
    """Main simulation class with environmental integration"""
    
    def __init__(self):
        pygame.init()
        
        # Display setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Advanced Traffic Simulation - Phase 2 (Environmental Integration)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Simulation components
        self.traffic_state = TrafficState(NUM_LANES, ROAD_LENGTH)
        self.physics_engine = PhysicsEngine()
        
        # Environmental systems
        self.weather_system = WeatherSystem()
        self.time_system = TimeSystem()
        self.environmental_renderer = EnvironmentalRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Camera and view
        self.camera_offset = np.array([0.0, 0.0])
        self.zoom_level = 1.0
        
        # Simulation state
        self.running = True
        self.paused = False
        self.simulation_time = 0.0
        self.dt = 1.0 / FPS
        
        # Performance tracking
        self.frame_count = 0
        self.fps_history = []
        self.last_fps_update = time.time()
        
        # UI state
        self.show_metrics = True
        self.show_vehicle_ids = False
        self.show_weather_info = True
        self.selected_vehicle = None
        
        # Statistics
        self.metrics_history = []
        self.max_history_length = 300
        
        # Environmental event tracking
        self.weather_events = []
        self.accident_history = []
        
        # Initialize with some vehicles
        self._initialize_traffic()
        
    def _initialize_traffic(self):
        """Initialize simulation with time-appropriate vehicles"""
        # Create initial traffic based on time of day
        for i in range(20):
            lane = random.randint(0, NUM_LANES - 1)
            position = np.array([random.uniform(20, 300), lane * LANE_WIDTH])
            
            # Get vehicle type based on time of day distribution
            vehicle_type = self.time_system.get_vehicle_type_for_time()
            
            vehicle = EnvironmentallyAwareVehicle(
                i, vehicle_type, lane, position, 
                random.uniform(0, 15),
                self.weather_system, self.time_system
            )
            self.traffic_state.vehicles.append(vehicle)
    
    def handle_events(self):
        """Handle user input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_m:
                    self.show_metrics = not self.show_metrics
                elif event.key == pygame.K_i:
                    self.show_vehicle_ids = not self.show_vehicle_ids
                elif event.key == pygame.K_w:
                    self.show_weather_info = not self.show_weather_info
                elif event.key == pygame.K_r:
                    self._reset_simulation()
                elif event.key == pygame.K_v:
                    self._add_random_vehicle()
                elif event.key == pygame.K_c:
                    self._clear_vehicles()
                elif event.key == pygame.K_t:
                    self._trigger_weather_change()
                elif event.key == pygame.K_n:
                    self._advance_time(1.0)  # Advance 1 hour
                elif event.key == pygame.K_d:
                    self._trigger_accident()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self._handle_vehicle_selection(event.pos)
                elif event.button == 4:  # Scroll up
                    self.zoom_level = min(2.0, self.zoom_level * 1.1)
                elif event.button == 5:  # Scroll down
                    self.zoom_level = max(0.5, self.zoom_level / 1.1)
        
        # Handle continuous key presses
        keys = pygame.key.get_pressed()
        camera_speed = 5.0
        
        if keys[pygame.K_LEFT]:
            self.camera_offset[0] -= camera_speed
        if keys[pygame.K_RIGHT]:
            self.camera_offset[0] += camera_speed
        if keys[pygame.K_UP]:
            self.camera_offset[1] -= camera_speed
        if keys[pygame.K_DOWN]:
            self.camera_offset[1] += camera_speed
    
    def _handle_vehicle_selection(self, mouse_pos):
        """Handle vehicle selection with mouse"""
        # Convert mouse position to world coordinates
        world_x = (mouse_pos[0] + self.camera_offset[0]) / SCALE_FACTOR
        world_y = (mouse_pos[1] + self.camera_offset[1]) / SCALE_FACTOR
        
        # Find closest vehicle
        min_distance = float('inf')
        selected = None
        
        for vehicle in self.traffic_state.vehicles:
            distance = math.sqrt((vehicle.position[0] - world_x)**2 + 
                              (vehicle.position[1] - world_y)**2)
            if distance < min_distance and distance < 10.0:  # 10 meter selection radius
                min_distance = distance
                selected = vehicle
        
        self.selected_vehicle = selected
    
    def _add_random_vehicle(self):
        """Add a time-appropriate random vehicle"""
        vehicle_type = self.time_system.get_vehicle_type_for_time()
        lane = random.randint(0, NUM_LANES - 1)
        position = np.array([10.0, lane * LANE_WIDTH])
        
        if self.traffic_state._is_position_clear(position, lane):
            vehicle = EnvironmentallyAwareVehicle(
                self.traffic_state.vehicle_counter, vehicle_type, lane, position,
                random.uniform(0, 15), self.weather_system, self.time_system
            )
            self.traffic_state.vehicles.append(vehicle)
            self.traffic_state.vehicle_counter += 1
            self.traffic_state.total_vehicles_spawned += 1
            logger.info(f"Added {vehicle_type.value} vehicle at {self.time_system.get_time_string()}")
    
    def _clear_vehicles(self):
        """Clear all vehicles from simulation"""
        self.traffic_state.vehicles.clear()
        logger.info("Cleared all vehicles")
    
    def _reset_simulation(self):
        """Reset the entire simulation"""
        self.traffic_state.vehicles.clear()
        self.traffic_state.vehicle_counter = 0
        self.traffic_state.total_vehicles_spawned = 0
        self.traffic_state.total_vehicles_passed = 0
        self.simulation_time = 0.0
        self.time_system.current_time = 6.0
        self.time_system.current_time_of_day = TimeOfDay.MORNING_RUSH
        self.weather_system.current_pattern_index = 0
        self.weather_system.current_weather = WeatherParameters(WeatherCondition.CLEAR, 1.0, 1.0, 0, 0, 0, 20, 50)
        self._initialize_traffic()
        logger.info("Reset simulation")
    
    def _trigger_weather_change(self):
        """Trigger immediate weather change"""
        self.weather_system._initiate_weather_change()
        logger.info("Manual weather change triggered")
    
    def _advance_time(self, hours: float):
        """Advance simulation time"""
        self.time_system.current_time += hours
        self.time_system._update_time_of_day()
        logger.info(f"Time advanced to: {self.time_system.get_time_string()}")
    
    def _trigger_accident(self):
        """Trigger an accident event"""
        if len(self.traffic_state.vehicles) >= 2:
            # Select random vehicles for accident
            vehicles = random.sample(self.traffic_state.vehicles, min(2, len(self.traffic_state.vehicles)))
            
            accident = {
                'time': self.simulation_time,
                'vehicles': [v.id for v in vehicles],
                'location': np.mean([v.position for v in vehicles], axis=0),
                'severity': random.choice(['minor', 'moderate', 'major'])
            }
            
            self.accident_history.append(accident)
            
            # Stop accident vehicles
            for vehicle in vehicles:
                vehicle.velocity = 0
                vehicle.acceleration = 0
                vehicle.hazard_lights = True
            
            logger.info(f"Accident triggered: {accident['severity']} severity at {accident['location']}")
    
    def update(self):
        """Update simulation state with environmental systems"""
        if self.paused:
            return
        
        # Update environmental systems
        self.weather_system.update(self.dt, self.simulation_time)
        self.time_system.update(self.dt)
        
        # Update traffic state with environmentally-aware spawning
        self._update_traffic_with_environment()
        
        # Update simulation time
        self.simulation_time += self.dt
        
        # Collect metrics
        metrics = self.traffic_state.get_metrics()
        metrics.update({
            'weather_condition': self.weather_system.current_weather.condition.value,
            'visibility': self.weather_system.current_weather.visibility_distance,
            'time_of_day': self.time_system.current_time_of_day.value,
            'lighting_level': self.time_system.time_params.lighting_level
        })
        self.metrics_history.append(metrics)
        
        # Limit history length
        if len(self.metrics_history) > self.max_history_length:
            self.metrics_history.pop(0)
        
        # Update FPS tracking
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_update > 1.0:
            fps = self.frame_count / (current_time - self.last_fps_update)
            self.fps_history.append(fps)
            if len(self.fps_history) > 60:
                self.fps_history.pop(0)
            self.frame_count = 0
            self.last_fps_update = current_time
    
    def _update_traffic_with_environment(self):
        """Update traffic with environmental considerations"""
        # Update vehicles
        for vehicle in self.traffic_state.vehicles[:]:
            vehicle.update(self.dt, self.traffic_state)
            
            # Remove vehicles that have left the simulation area
            if vehicle.position[0] > ROAD_LENGTH:
                self.traffic_state.vehicles.remove(vehicle)
                self.traffic_state.total_vehicles_passed += 1
        
        # Environmentally-aware vehicle spawning
        spawn_probability = self.time_system.get_vehicle_spawn_probability()
        
        # Reduce spawn rate in bad weather
        weather_factor = self.weather_system.current_weather.speed_reduction_factor
        spawn_probability *= weather_factor
        
        if random.random() < spawn_probability * self.dt:
            self._add_random_vehicle()
        
        # Update performance metrics
        self.traffic_state._update_metrics()
    
    def draw_road(self):
        """Draw the road with environmental effects"""
        # Get lighting level for time-of-day rendering
        lighting_level = self.time_system.time_params.lighting_level
        
        # Base road color changes with time
        if lighting_level > 0.7:  # Daytime
            road_color = DARK_GRAY
            line_color = WHITE
        elif lighting_level > 0.3:  # Evening/morning
            road_color = (50, 50, 60)
            line_color = (200, 200, 200)
        else:  # Night
            road_color = (30, 30, 40)
            line_color = (150, 150, 150)
        
        # Clear screen with sky color
        if lighting_level > 0.7:
            self.screen.fill((135, 206, 235))  # Sky blue
        elif lighting_level > 0.3:
            self.screen.fill((255, 150, 100))  # Sunset/sunrise orange
        else:
            self.screen.fill(NIGHT_BLUE)  # Night blue
        
        # Draw road surface
        road_y_start = 100
        road_height = NUM_LANES * LANE_WIDTH * SCALE_FACTOR
        road_rect = pygame.Rect(0, road_y_start, SCREEN_WIDTH, road_height)
        pygame.draw.rect(self.screen, road_color, road_rect)
        
        # Draw lane markings
        for lane in range(NUM_LANES + 1):
            y = road_y_start + lane * LANE_WIDTH * SCALE_FACTOR
            if lane == 0 or lane == NUM_LANES:
                # Edge lines - solid
                pygame.draw.line(self.screen, line_color, (0, y), (SCREEN_WIDTH, y), 3)
            else:
                # Lane dividers - dashed (less visible at night)
                dash_length = 20 if lighting_level > 0.5 else 10
                for x in range(0, SCREEN_WIDTH, dash_length * 2):
                    pygame.draw.line(self.screen, line_color, (x, y), (x + dash_length, y), 2)
        
        # Draw weather-affected road surface
        self._draw_weather_effects_on_road(road_y_start, road_height)
    
    def _draw_weather_effects_on_road(self, road_y_start: int, road_height: int):
        """Draw weather effects on road surface"""
        weather = self.weather_system.current_weather
        
        # Wet road effect in rain
        if weather.condition in [WeatherCondition.LIGHT_RAIN, WeatherCondition.MODERATE_RAIN, 
                               WeatherCondition.HEAVY_RAIN, WeatherCondition.THUNDERSTORM]:
            wet_surface = pygame.Surface((SCREEN_WIDTH, road_height))
            wet_surface.set_alpha(30)
            wet_surface.fill((50, 50, 100))  # Blueish tint
            self.screen.blit(wet_surface, (0, road_y_start))
        
        # Snow coverage
        if weather.condition in [WeatherCondition.LIGHT_SNOW, WeatherCondition.MODERATE_SNOW,
                               WeatherCondition.HEAVY_SNOW, WeatherCondition.BLIZZARD]:
            snow_coverage = pygame.Surface((SCREEN_WIDTH, road_height))
            snow_coverage.set_alpha(60)
            snow_coverage.fill((240, 240, 250))  # White tint
            self.screen.blit(snow_coverage, (0, road_y_start))
    
    def draw_vehicles(self):
        """Draw all vehicles with enhanced environmental effects"""
        for vehicle in self.traffic_state.vehicles:
            # Calculate screen position
            screen_x = int(vehicle.position[0] * SCALE_FACTOR - self.camera_offset[0])
            screen_y = int(vehicle.position[1] * SCALE_FACTOR - self.camera_offset[1])
            
            # Skip if outside screen
            if screen_x < -100 or screen_x > SCREEN_WIDTH + 100:
                continue
            if screen_y < -100 or screen_y > SCREEN_HEIGHT + 100:
                continue
            
            # Draw vehicle with environmental effects
            vehicle.draw(self.screen, self.camera_offset)
            
            # Draw selection highlight
            if vehicle == self.selected_vehicle:
                highlight_rect = pygame.Rect(screen_x - vehicle.length_pixels // 2 - 5,
                                        screen_y - vehicle.width_pixels // 2 - 5,
                                        vehicle.length_pixels + 10,
                                        vehicle.width_pixels + 10)
                pygame.draw.rect(self.screen, YELLOW, highlight_rect, 2)
            
            # Draw vehicle ID if enabled
            if self.show_vehicle_ids:
                id_text = self.small_font.render(str(vehicle.id), True, WHITE)
                self.screen.blit(id_text, (screen_x - 10, screen_y - 25))
    
    def draw_metrics(self):
        """Draw performance metrics and environmental information"""
        if not self.show_metrics:
            return
        
        # Create semi-transparent background for metrics
        metrics_surface = pygame.Surface((450, 400))
        metrics_surface.set_alpha(200)
        metrics_surface.fill(BLACK)
        
        y_offset = 10
        
        # Title
        title_text = self.font.render("Traffic & Environmental Metrics", True, WHITE)
        metrics_surface.blit(title_text, (10, y_offset))
        y_offset += 30
        
        # Current metrics
        if self.metrics_history:
            current_metrics = self.metrics_history[-1]
            
            traffic_metrics = [
                f"Vehicles: {current_metrics['vehicle_count']}",
                f"Avg Speed: {current_metrics['average_speed_kmh']:.1f} km/h",
                f"Density: {current_metrics['density_vehicles_per_km']:.1f} veh/km",
                f"Total Spawned: {current_metrics['total_spawned']}",
                f"Total Passed: {current_metrics['total_passed']}",
                f"Flow Rate: {current_metrics['flow_rate']:.1f} veh/s"
            ]
            
            for metric in traffic_metrics:
                metric_text = self.small_font.render(metric, True, WHITE)
                metrics_surface.blit(metric_text, (10, y_offset))
                y_offset += 18
            
            y_offset += 10
            
            # Environmental metrics
            env_metrics = [
                f"Weather: {current_metrics['weather_condition']}",
                f"Visibility: {current_metrics['visibility']:.0f}m",
                f"Time: {self.time_system.get_time_string()}",
                f"Period: {current_metrics['time_of_day']}",
                f"Lighting: {current_metrics['lighting_level']:.1f}"
            ]
            
            for metric in env_metrics:
                metric_text = self.small_font.render(metric, True, (100, 255, 100))
                metrics_surface.blit(metric_text, (10, y_offset))
                y_offset += 18
        
        # FPS
        if self.fps_history:
            current_fps = self.fps_history[-1]
            fps_text = self.small_font.render(f"FPS: {current_fps:.1f}", True, GREEN)
            metrics_surface.blit(fps_text, (10, y_offset))
            y_offset += 20
        
        # Controls
        y_offset += 10
        controls_title = self.font.render("Controls", True, WHITE)
        metrics_surface.blit(controls_title, (10, y_offset))
        y_offset += 25
        
        controls = [
            "SPACE: Pause/Resume",
            "M: Toggle Metrics",
            "I: Toggle Vehicle IDs",
            "W: Toggle Weather Info",
            "V: Add Vehicle",
            "C: Clear Vehicles",
            "R: Reset Simulation",
            "T: Change Weather",
            "N: Advance Time (1hr)",
            "D: Trigger Accident",
            "Arrow Keys: Move Camera",
            "Mouse Wheel: Zoom",
            "Click: Select Vehicle",
            "ESC: Exit"
        ]
        
        for control in controls:
            control_text = self.small_font.render(control, True, WHITE)
            metrics_surface.blit(control_text, (10, y_offset))
            y_offset += 16
        
        # Draw selected vehicle info
        if self.selected_vehicle:
            y_offset += 10
            selected_title = self.font.render("Selected Vehicle", True, YELLOW)
            metrics_surface.blit(selected_title, (10, y_offset))
            y_offset += 25
            
            vehicle = self.selected_vehicle
            selected_info = [
                f"ID: {vehicle.id}",
                f"Type: {vehicle.type.value}",
                f"Speed: {vehicle.velocity * 3.6:.1f} km/h",
                f"Max Speed: {vehicle.base_max_speed * vehicle.desired_speed / (vehicle.params.max_speed / 3.6):.1f} km/h",
                f"Lane: {vehicle.current_lane}",
                f"State: {vehicle.driving_state.value}",
                f"Headlights: {'On' if vehicle.headlights_on else 'Off'}",
                f"Wipers: {'On' if vehicle.wipers_on else 'Off'}"
            ]
            
            for info in selected_info:
                info_text = self.small_font.render(info, True, YELLOW)
                metrics_surface.blit(info_text, (10, y_offset))
                y_offset += 16
        
        # Blit metrics surface to screen
        self.screen.blit(metrics_surface, (SCREEN_WIDTH - 460, 10))
    
    def draw_pause_overlay(self):
        """Draw pause overlay"""
        if not self.paused:
            return
        
        # Create semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause text
        pause_text = self.font.render("PAUSED", True, WHITE)
        text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(pause_text, text_rect)
        
        resume_text = self.small_font.render("Press SPACE to resume", True, WHITE)
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(resume_text, resume_rect)
    
    def run(self):
        """Main simulation loop"""
        logger.info("Starting Advanced Traffic Simulation - Phase 2 (Environmental Integration)")
        logger.info("New Controls: T=Weather Change, N=Advance Time, D=Trigger Accident, W=Weather Info")
        
        while self.running:
            # Handle events
            self.handle_events()
            
            # Update simulation
            self.update()
            
            # Draw everything
            self.draw_road()
            self.draw_vehicles()
            
            # Render environmental effects
            self.environmental_renderer.render_weather_effects(self.screen, self.weather_system)
            self.environmental_renderer.render_time_of_day_lighting(self.screen, self.time_system)
            
            if self.show_weather_info:
                self.environmental_renderer.render_weather_info(
                    self.screen, self.weather_system, self.time_system, self.small_font
                )
            
            self.draw_metrics()
            self.draw_pause_overlay()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # Cleanup
        pygame.quit()
        logger.info("Simulation ended")

def main():
    """Main entry point"""
    try:
        simulation = EnhancedTrafficSimulation()
        simulation.run()
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise

if __name__ == "__main__":
    main()