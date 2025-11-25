"""
Enhanced Simulation with Multi-Intersection Coordination
====================================================

Integration of multi-intersection coordination system with existing simulation
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

# Import existing simulation components
from simulation import Vehicle, TrafficSignal, signals, currentGreen, currentYellow
from multi_intersection_coordinator import (
    NetworkCoordinator, IntersectionController, IntersectionConfig,
    create_network_coordinator, CoordinationMode
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiIntersectionSimulation:
    """Enhanced simulation with multi-intersection coordination"""
    
    def __init__(self):
        # Initialize existing simulation components
        pygame.init()
        self.screen = pygame.display.set_mode((1800, 1200))
        pygame.display.set_caption("Multi-Intersection Traffic Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Multi-intersection setup
        self.network_coordinator = create_network_coordinator()
        self.intersection_controllers = self.network_coordinator.intersections
        
        # Simulation state
        self.running = True
        self.paused = False
        self.simulation_time = 0.0
        self.dt = 1.0 / 60.0
        
        # Visual layout for multiple intersections
        self.intersection_positions = {
            "INT_A": (300, 300),
            "INT_B": (900, 300),
            "INT_C": (900, 900),
            "INT_D": (300, 900)
        }
        
        # Traffic data collection
        self.traffic_data_history = []
        self.performance_metrics = {}
        
        # Start coordination
        self.network_coordinator.start_coordination_loop()
        
        # Initialize vehicles for each intersection
        self.vehicles_by_intersection = {
            "INT_A": [],
            "INT_B": [],
            "INT_C": [],
            "INT_D": []
        }
        
        logger.info("Multi-intersection simulation initialized")
    
    def create_vehicle_for_intersection(self, intersection_id: str):
        """Create a vehicle for specific intersection"""
        if intersection_id not in self.intersection_positions:
            return None
        
        # Get intersection position
        int_x, int_y = self.intersection_positions[intersection_id]
        
        # Random vehicle properties
        vehicle_types = ['car', 'bus', 'truck', 'rickshaw', 'bike']
        vehicle_type = random.choice(vehicle_types)
        
        # Random approach direction
        directions = ['north', 'south', 'east', 'west']
        direction = random.choice(directions)
        
        # Calculate spawn position based on direction
        if direction == 'north':
            spawn_x = int_x + random.randint(-50, 50)
            spawn_y = int_y - 200
        elif direction == 'south':
            spawn_x = int_x + random.randint(-50, 50)
            spawn_y = int_y + 200
        elif direction == 'east':
            spawn_x = int_x + 200
            spawn_y = int_y + random.randint(-50, 50)
        else:  # west
            spawn_x = int_x - 200
            spawn_y = int_y + random.randint(-50, 50)
        
        # Create vehicle (simplified for multi-intersection)
        vehicle = {
            'id': f"{intersection_id}_{len(self.vehicles_by_intersection[intersection_id])}",
            'type': vehicle_type,
            'x': spawn_x,
            'y': spawn_y,
            'direction': direction,
            'speed': random.uniform(20, 40),
            'target_intersection': intersection_id,
            'color': self._get_vehicle_color(vehicle_type)
        }
        
        return vehicle
    
    def _get_vehicle_color(self, vehicle_type: str) -> Tuple[int, int, int]:
        """Get color for vehicle type"""
        colors = {
            'car': (50, 100, 200),
            'bus': (200, 50, 50),
            'truck': (100, 100, 100),
            'rickshaw': (200, 150, 50),
            'bike': (50, 200, 50)
        }
        return colors.get(vehicle_type, (100, 100, 100))
    
    def update_vehicles(self):
        """Update all vehicles in the network"""
        for intersection_id, vehicles in self.vehicles_by_intersection.items():
            # Update existing vehicles
            for vehicle in vehicles[:]:
                self._update_vehicle_movement(vehicle, intersection_id)
                
                # Remove vehicles that have reached their destination
                if self._has_reached_destination(vehicle, intersection_id):
                    vehicles.remove(vehicle)
                    
                    # Update intersection controller
                    if intersection_id in self.intersection_controllers:
                        controller = self.intersection_controllers[intersection_id]
                        controller.total_vehicles_passed += 1
            
            # Spawn new vehicles
            if random.random() < 0.02:  # 2% chance per frame
                new_vehicle = self.create_vehicle_for_intersection(intersection_id)
                if new_vehicle:
                    vehicles.append(new_vehicle)
    
    def _update_vehicle_movement(self, vehicle: Dict, intersection_id: str):
        """Update individual vehicle movement"""
        # Get target position
        target_x, target_y = self.intersection_positions[intersection_id]
        
        # Calculate direction to target
        dx = target_x - vehicle['x']
        dy = target_y - vehicle['y']
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 5:  # Not at intersection yet
            # Move towards intersection
            vehicle['x'] += (dx / distance) * vehicle['speed'] * self.dt
            vehicle['y'] += (dy / distance) * vehicle['speed'] * self.dt
        else:
            # At intersection, move through based on traffic signal
            self._move_through_intersection(vehicle, intersection_id)
    
    def _move_through_intersection(self, vehicle: Dict, intersection_id: str):
        """Move vehicle through intersection based on signal state"""
        if intersection_id not in self.intersection_controllers:
            return
        
        controller = self.intersection_controllers[intersection_id]
        
        # Check if vehicle can proceed based on signal
        can_proceed = self._can_vehicle_proceed(vehicle, controller)
        
        if can_proceed:
            # Continue moving in same direction
            if vehicle['direction'] == 'north':
                vehicle['y'] -= vehicle['speed'] * self.dt
            elif vehicle['direction'] == 'south':
                vehicle['y'] += vehicle['speed'] * self.dt
            elif vehicle['direction'] == 'east':
                vehicle['x'] += vehicle['speed'] * self.dt
            else:  # west
                vehicle['x'] -= vehicle['speed'] * self.dt
    
    def _can_vehicle_proceed(self, vehicle: Dict, controller: IntersectionController) -> bool:
        """Check if vehicle can proceed through intersection"""
        # Simplified signal check
        # In real implementation, would check specific phase for vehicle direction
        
        # Get current signal state
        current_phase = controller.current_phase
        
        # Simplified: allow vehicles during certain phases
        if current_phase == 0:  # NS Green
            return vehicle['direction'] in ['north', 'south']
        elif current_phase == 2:  # EW Green
            return vehicle['direction'] in ['east', 'west']
        else:  # Yellow or Red phases
            return False
    
    def _has_reached_destination(self, vehicle: Dict, intersection_id: str) -> bool:
        """Check if vehicle has reached and passed through intersection"""
        int_x, int_y = self.intersection_positions[intersection_id]
        
        # Check if vehicle has passed the intersection
        if vehicle['direction'] == 'north' and vehicle['y'] < int_y - 100:
            return True
        elif vehicle['direction'] == 'south' and vehicle['y'] > int_y + 100:
            return True
        elif vehicle['direction'] == 'east' and vehicle['x'] > int_x + 100:
            return True
        elif vehicle['direction'] == 'west' and vehicle['x'] < int_x - 100:
            return True
        
        return False
    
    def draw_intersections(self):
        """Draw all intersections and connecting roads"""
        # Draw roads between intersections
        road_color = (64, 64, 64)
        road_width = 40
        
        # Horizontal roads
        pygame.draw.rect(self.screen, road_color, 
                       (self.intersection_positions["INT_A"][0] - 100,
                        self.intersection_positions["INT_A"][1] - road_width//2,
                        self.intersection_positions["INT_B"][0] - self.intersection_positions["INT_A"][0] + 200,
                        road_width))
        
        pygame.draw.rect(self.screen, road_color,
                       (self.intersection_positions["INT_D"][0] - 100,
                        self.intersection_positions["INT_D"][1] - road_width//2,
                        self.intersection_positions["INT_C"][0] - self.intersection_positions["INT_D"][0] + 200,
                        road_width))
        
        # Vertical roads
        pygame.draw.rect(self.screen, road_color,
                       (self.intersection_positions["INT_A"][0] - road_width//2,
                        self.intersection_positions["INT_A"][1] - 100,
                        road_width,
                        self.intersection_positions["INT_D"][1] - self.intersection_positions["INT_A"][1] + 200))
        
        pygame.draw.rect(self.screen, road_color,
                       (self.intersection_positions["INT_B"][0] - road_width//2,
                        self.intersection_positions["INT_B"][1] - 100,
                        road_width,
                        self.intersection_positions["INT_C"][1] - self.intersection_positions["INT_B"][1] + 200))
        
        # Draw intersections
        for intersection_id, (x, y) in self.intersection_positions.items():
            # Draw intersection box
            intersection_size = 80
            pygame.draw.rect(self.screen, (80, 80, 80),
                           (x - intersection_size//2, y - intersection_size//2,
                            intersection_size, intersection_size))
            
            # Draw traffic signals
            self._draw_traffic_signals(x, y, intersection_id)
            
            # Draw intersection label
            label = self.small_font.render(intersection_id, True, (255, 255, 255))
            self.screen.blit(label, (x - 30, y - 60))
    
    def _draw_traffic_signals(self, x: int, y: int, intersection_id: str):
        """Draw traffic signals for intersection"""
        if intersection_id not in self.intersection_controllers:
            return
        
        controller = self.intersection_controllers[intersection_id]
        current_phase = controller.current_phase
        
        # Signal positions (4 corners of intersection)
        signal_positions = [
            (x - 50, y - 50),  # NW
            (x + 50, y - 50),  # NE
            (x + 50, y + 50),  # SE
            (x - 50, y + 50)   # SW
        ]
        
        # Draw signals based on current phase
        for i, (sx, sy) in enumerate(signal_positions):
            if current_phase == 0 and i in [0, 2]:  # NS Green
                color = (0, 255, 0)
            elif current_phase == 2 and i in [1, 3]:  # EW Green
                color = (0, 255, 0)
            elif current_phase in [1, 3]:  # Yellow phases
                color = (255, 255, 0)
            else:  # Red
                color = (255, 0, 0)
            
            pygame.draw.circle(self.screen, color, (sx, sy), 8)
            pygame.draw.circle(self.screen, (0, 0, 0), (sx, sy), 8, 2)
    
    def draw_vehicles(self):
        """Draw all vehicles in the network"""
        for intersection_id, vehicles in self.vehicles_by_intersection.items():
            for vehicle in vehicles:
                # Draw vehicle as rectangle
                vehicle_size = 15
                pygame.draw.rect(self.screen, vehicle['color'],
                               (vehicle['x'] - vehicle_size//2,
                                vehicle['y'] - vehicle_size//2,
                                vehicle_size, vehicle_size))
                
                # Draw vehicle type label
                label = self.small_font.render(vehicle['type'][0].upper(), True, (255, 255, 255))
                self.screen.blit(label, (vehicle['x'] - 5, vehicle['y'] - 5))
    
    def draw_network_info(self):
        """Draw network coordination information"""
        # Create info panel
        info_surface = pygame.Surface((400, 300))
        info_surface.set_alpha(200)
        info_surface.fill((0, 0, 0))
        
        y_offset = 10
        
        # Title
        title = self.font.render("Network Coordination Status", True, (255, 255, 255))
        info_surface.blit(title, (10, y_offset))
        y_offset += 30
        
        # Network metrics
        network_metrics = self.network_coordinator.get_network_metrics()
        
        metrics_to_display = [
            f"Total Intersections: {network_metrics['total_intersections']}",
            f"Coordination Mode: {network_metrics['coordination_mode']}",
            f"Active Incidents: {network_metrics['active_incidents']}",
            f"Network Congestion: {network_metrics['network_congestion_level']:.2f}",
            f"Target Speed: {network_metrics['target_speed']:.1f} km/h",
            f"Total Vehicles Passed: {network_metrics['total_vehicles_passed']}"
        ]
        
        for metric in metrics_to_display:
            text = self.small_font.render(metric, True, (255, 255, 255))
            info_surface.blit(text, (10, y_offset))
            y_offset += 20
        
        # Intersection-specific info
        y_offset += 10
        subtitle = self.font.render("Intersection Status", True, (255, 255, 255))
        info_surface.blit(subtitle, (10, y_offset))
        y_offset += 25
        
        for intersection_id, controller in self.intersection_controllers.items():
            metrics = controller.get_performance_metrics()
            status = f"{intersection_id}: {metrics['average_queue_length']:.1f} avg queue"
            text = self.small_font.render(status, True, (200, 200, 200))
            info_surface.blit(text, (10, y_offset))
            y_offset += 18
        
        # Blit to main screen
        self.screen.blit(info_surface, (10, 10))
    
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
                elif event.key == pygame.K_i:
                    # Trigger incident for testing
                    self._trigger_test_incident()
                elif event.key == pygame.K_c:
                    # Clear incident
                    self._clear_test_incident()
    
    def _trigger_test_incident(self):
        """Trigger a test incident"""
        incident_data = {
            'type': 'accident',
            'location': self.intersection_positions["INT_B"],
            'impact_radius': 500,
            'severity': 'moderate',
            'estimated_duration': 300  # 5 minutes
        }
        
        self.network_coordinator.report_incident("TEST_INCIDENT", incident_data)
        logger.info("Test incident triggered at INT_B")
    
    def _clear_test_incident(self):
        """Clear test incident"""
        self.network_coordinator.clear_incident("TEST_INCIDENT")
        logger.info("Test incident cleared")
    
    def update(self):
        """Update simulation state"""
        if self.paused:
            return
        
        # Update vehicles
        self.update_vehicles()
        
        # Update intersection controllers
        for controller in self.intersection_controllers.values():
            # Update phase timer
            controller.phase_timer += self.dt
            
            # Simple phase progression (simplified)
            if controller.phase_timer >= controller.cycle_length / 4:
                controller.phase_timer = 0
                controller.current_phase = (controller.current_phase + 1) % 4
        
        # Update simulation time
        self.simulation_time += self.dt
    
    def draw(self):
        """Draw everything"""
        # Clear screen
        self.screen.fill((34, 139, 34))  # Forest green background
        
        # Draw components
        self.draw_intersections()
        self.draw_vehicles()
        self.draw_network_info()
        
        # Draw pause overlay
        if self.paused:
            pause_text = self.font.render("PAUSED", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=(900, 600))
            self.screen.blit(pause_text, text_rect)
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Main simulation loop"""
        logger.info("Starting multi-intersection simulation...")
        logger.info("Controls: SPACE=Pause, I=Trigger Incident, C=Clear Incident, ESC=Exit")
        
        while self.running:
            # Handle events
            self.handle_events()
            
            # Update simulation
            self.update()
            
            # Draw everything
            self.draw()
            
            # Control frame rate
            self.clock.tick(60)
        
        # Cleanup
        pygame.quit()
        logger.info("Multi-intersection simulation ended")

def main():
    """Main entry point"""
    try:
        simulation = MultiIntersectionSimulation()
        simulation.run()
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise

if __name__ == "__main__":
    main()