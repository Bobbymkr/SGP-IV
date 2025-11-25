"""
Enhanced Traffic Simulation - Phase 1 Implementation
==================================================

Advanced traffic simulation with:
- Realistic vehicle physics and dynamics
- Intelligent driver behavior (IDM+, MOBIL)
- Multi-lane highway logic
- Advanced collision detection
- Performance metrics and analytics

This replaces the basic simulation.py with industry-standard traffic flow modeling.
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

# Import our advanced simulation components
from simulation_phase1 import (
    AdvancedVehicle, TrafficState, PhysicsEngine, VehicleType,
    VehicleParameters, IntelligentDriverModel, MOBILLaneChangeModel,
    DrivingState, LaneType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Display constants
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 60
SCALE_FACTOR = 2.0  # pixels per meter

# Road configuration
NUM_LANES = 4
ROAD_LENGTH = 500.0  # meters
LANE_WIDTH = 3.5  # meters

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 100, 255)
ORANGE = (255, 165, 0)

class AdvancedTrafficSimulation:
    """Main simulation class with enhanced features"""
    
    def __init__(self):
        pygame.init()
        
        # Display setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Advanced Traffic Simulation - Phase 1")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Simulation components
        self.traffic_state = TrafficState(NUM_LANES, ROAD_LENGTH)
        self.physics_engine = PhysicsEngine()
        
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
        self.selected_vehicle = None
        
        # Statistics
        self.metrics_history = []
        self.max_history_length = 300  # Keep 5 minutes at 60 FPS
        
        # Initialize with some vehicles
        self._initialize_traffic()
        
    def _initialize_traffic(self):
        """Initialize simulation with some vehicles"""
        # Create initial traffic
        for i in range(15):
            lane = random.randint(0, NUM_LANES - 1)
            position = np.array([random.uniform(20, 200), lane * LANE_WIDTH])
            
            # Random vehicle type with realistic distribution
            weights = [0.7, 0.05, 0.1, 0.05, 0.05, 0.05]  # Car, Bus, Truck, Motorcycle, Bicycle, Emergency
            vehicle_type = np.random.choice(list(VehicleType), p=weights)
            
            vehicle = AdvancedVehicle(i, vehicle_type, lane, position, 
                                  random.uniform(0, 15))
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
                elif event.key == pygame.K_r:
                    self._reset_simulation()
                elif event.key == pygame.K_v:
                    self._add_random_vehicle()
                elif event.key == pygame.K_c:
                    self._clear_vehicles()
            
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
        """Add a random vehicle to the simulation"""
        vehicle = self.traffic_state.add_vehicle()
        if vehicle:
            logger.info(f"Added vehicle {vehicle.id} of type {vehicle.type.value}")
    
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
        self._initialize_traffic()
        logger.info("Reset simulation")
    
    def update(self):
        """Update simulation state"""
        if self.paused:
            return
        
        # Update traffic state
        self.traffic_state.update(self.dt)
        
        # Update simulation time
        self.simulation_time += self.dt
        
        # Collect metrics
        metrics = self.traffic_state.get_metrics()
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
    
    def draw_road(self):
        """Draw the road and lane markings"""
        # Clear screen
        self.screen.fill(GREEN)
        
        # Draw road surface
        road_y_start = 50
        road_height = NUM_LANES * LANE_WIDTH * SCALE_FACTOR
        road_rect = pygame.Rect(0, road_y_start, SCREEN_WIDTH, road_height)
        pygame.draw.rect(self.screen, DARK_GRAY, road_rect)
        
        # Draw lane markings
        for lane in range(NUM_LANES + 1):
            y = road_y_start + lane * LANE_WIDTH * SCALE_FACTOR
            if lane == 0 or lane == NUM_LANES:
                # Edge lines - solid
                pygame.draw.line(self.screen, WHITE, (0, y), (SCREEN_WIDTH, y), 3)
            else:
                # Lane dividers - dashed
                for x in range(0, SCREEN_WIDTH, 40):
                    pygame.draw.line(self.screen, WHITE, (x, y), (x + 20, y), 2)
        
        # Draw shoulder markings
        shoulder_width = 20
        pygame.draw.rect(self.screen, GRAY, (0, road_y_start - shoulder_width, 
                                         SCREEN_WIDTH, shoulder_width))
        pygame.draw.rect(self.screen, GRAY, (0, road_y_start + road_height, 
                                         SCREEN_WIDTH, shoulder_width))
    
    def draw_vehicles(self):
        """Draw all vehicles with enhanced graphics"""
        for vehicle in self.traffic_state.vehicles:
            # Calculate screen position
            screen_x = int(vehicle.position[0] * SCALE_FACTOR - self.camera_offset[0])
            screen_y = int(vehicle.position[1] * SCALE_FACTOR - self.camera_offset[1])
            
            # Skip if outside screen
            if screen_x < -100 or screen_x > SCREEN_WIDTH + 100:
                continue
            if screen_y < -100 or screen_y > SCREEN_HEIGHT + 100:
                continue
            
            # Draw vehicle
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
        """Draw performance metrics and information"""
        if not self.show_metrics:
            return
        
        # Create semi-transparent background for metrics
        metrics_surface = pygame.Surface((400, 300))
        metrics_surface.set_alpha(200)
        metrics_surface.fill(BLACK)
        
        y_offset = 10
        
        # Title
        title_text = self.font.render("Traffic Metrics", True, WHITE)
        metrics_surface.blit(title_text, (10, y_offset))
        y_offset += 30
        
        # Current metrics
        if self.metrics_history:
            current_metrics = self.metrics_history[-1]
            
            metrics_to_display = [
                f"Vehicles: {current_metrics['vehicle_count']}",
                f"Avg Speed: {current_metrics['average_speed_kmh']:.1f} km/h",
                f"Density: {current_metrics['density_vehicles_per_km']:.1f} veh/km",
                f"Total Spawned: {current_metrics['total_spawned']}",
                f"Total Passed: {current_metrics['total_passed']}",
                f"Flow Rate: {current_metrics['flow_rate']:.1f} veh/s",
                f"Sim Time: {self.simulation_time:.1f}s"
            ]
            
            for metric in metrics_to_display:
                metric_text = self.small_font.render(metric, True, WHITE)
                metrics_surface.blit(metric_text, (10, y_offset))
                y_offset += 20
        
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
            "V: Add Vehicle",
            "C: Clear Vehicles",
            "R: Reset Simulation",
            "Arrow Keys: Move Camera",
            "Mouse Wheel: Zoom",
            "Click: Select Vehicle",
            "ESC: Exit"
        ]
        
        for control in controls:
            control_text = self.small_font.render(control, True, WHITE)
            metrics_surface.blit(control_text, (10, y_offset))
            y_offset += 18
        
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
                f"Acceleration: {vehicle.acceleration:.2f} m/s²",
                f"Lane: {vehicle.current_lane}",
                f"State: {vehicle.driving_state.value}",
                f"Position: ({vehicle.position[0]:.1f}, {vehicle.position[1]:.1f})"
            ]
            
            for info in selected_info:
                info_text = self.small_font.render(info, True, YELLOW)
                metrics_surface.blit(info_text, (10, y_offset))
                y_offset += 18
        
        # Blit metrics surface to screen
        self.screen.blit(metrics_surface, (SCREEN_WIDTH - 410, 10))
    
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
        logger.info("Starting Advanced Traffic Simulation - Phase 1")
        logger.info("Controls: SPACE=Pause, M=Metrics, I=IDs, V=Add Vehicle, R=Reset, ESC=Exit")
        
        while self.running:
            # Handle events
            self.handle_events()
            
            # Update simulation
            self.update()
            
            # Draw everything
            self.draw_road()
            self.draw_vehicles()
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
        simulation = AdvancedTrafficSimulation()
        simulation.run()
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise

if __name__ == "__main__":
    main()