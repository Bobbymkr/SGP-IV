#!/usr/bin/env python3
"""
Adaptive Traffic Signal Control - Comprehensive Video Demo
Created for non-technical audience to showcase all system capabilities
"""

import os
import sys
import time
import threading
import random
import numpy as np
import pygame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from datetime import datetime, timedelta
import json
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Code', 'YOLO', 'darkflow'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import existing modules
try:
    from simulation import Vehicle, TrafficSignal, defaultRed, defaultYellow, defaultGreen
except ImportError:
    print("Warning: Could not import from simulation.py, using fallback implementations")

# Video Demo Configuration
@dataclass
class VideoConfig:
    """Configuration for video demonstration"""
    width: int = 1400
    height: int = 900
    fps: int = 30
    duration_seconds: int = 180  # 3 minutes total
    scene_duration: int = 30     # 30 seconds per scene
    
    # Colors for visualization
    COLORS = {
        'background': (240, 240, 240),
        'road': (60, 60, 60),
        'lane_marking': (255, 255, 255),
        'vehicle_red': (220, 50, 50),
        'vehicle_blue': (50, 100, 220),
        'vehicle_green': (50, 220, 50),
        'vehicle_yellow': (220, 220, 50),
        'signal_red': (255, 0, 0),
        'signal_yellow': (255, 255, 0),
        'signal_green': (0, 255, 0),
        'text': (0, 0, 0),
        'highlight': (255, 100, 100),
        'emergency': (255, 0, 255),
        'pedestrian': (100, 100, 255)
    }

class TrafficMetrics:
    """Track and display traffic performance metrics"""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.vehicles_passed = 0
        self.total_wait_time = 0
        self.emergency_vehicles_served = 0
        self.fuel_saved = 0
        self.co2_reduced = 0
        self.efficiency_score = 0
        self.queue_lengths = deque(maxlen=100)
        self.wait_times = deque(maxlen=100)
        self.timestamps = deque(maxlen=100)
        
    def update(self, vehicles_passed, wait_time, queue_length):
        self.vehicles_passed += vehicles_passed
        self.total_wait_time += wait_time
        self.queue_lengths.append(queue_length)
        self.wait_times.append(wait_time)
        self.timestamps.append(time.time())
        
        # Calculate efficiency metrics
        if len(self.queue_lengths) > 10:
            avg_queue = np.mean(self.queue_lengths)
            avg_wait = np.mean(self.wait_times)
            self.efficiency_score = max(0, 100 - (avg_queue * 2 + avg_wait))
            
            # Environmental impact calculations
            self.fuel_saved = max(0, (avg_wait - 10) * 0.1)  # Simplified calculation
            self.co2_reduced = self.fuel_saved * 2.3  # kg CO2 per gallon

class EmergencyVehicleSystem:
    """Emergency vehicle priority system with visual indicators"""
    def __init__(self):
        self.active_emergencies = []
        self.emergency_types = ['ambulance', 'fire_truck', 'police']
        self.emergency_colors = {
            'ambulance': (255, 255, 255),
            'fire_truck': (255, 0, 0),
            'police': (0, 0, 255)
        }
        
    def add_emergency(self, vehicle_type, approach_direction, distance):
        """Add emergency vehicle to system"""
        emergency = {
            'type': vehicle_type,
            'direction': approach_direction,
            'distance': distance,
            'priority': 10,
            'timestamp': time.time(),
            'served': False
        }
        self.active_emergencies.append(emergency)
        return emergency
    
    def get_priority_action(self, current_phase):
        """Get signal priority action for emergency vehicles"""
        if not self.active_emergencies:
            return None
            
        # Find closest emergency vehicle
        closest_emergency = min(self.active_emergencies, 
                              key=lambda x: x['distance'], 
                              default=None)
        
        if closest_emergency and closest_emergency['distance'] < 50:
            # Return phase that gives green light to emergency vehicle
            emergency_phases = {
                'north': 0, 'south': 0,
                'east': 1, 'west': 1
            }
            return emergency_phases.get(closest_emergency['direction'])
        
        return None
    
    def update(self, dt):
        """Update emergency vehicle positions"""
        for emergency in self.active_emergencies[:]:
            emergency['distance'] -= 30 * dt  # Emergency vehicle speed
            if emergency['distance'] <= 0:
                emergency['served'] = True
                self.active_emergencies.remove(emergency)

class EnvironmentalSystem:
    """Environmental adaptation system (weather, time of day)"""
    def __init__(self):
        self.weather_conditions = ['clear', 'rain', 'fog', 'snow']
        self.current_weather = 'clear'
        self.time_of_day = 'morning_rush'
        self.visibility_factor = 1.0
        self.speed_adjustment = 1.0
        
    def set_weather(self, weather):
        """Set weather condition and adjust parameters"""
        self.current_weather = weather
        
        weather_effects = {
            'clear': {'visibility': 1.0, 'speed': 1.0, 'color': (135, 206, 235)},
            'rain': {'visibility': 0.7, 'speed': 0.8, 'color': (100, 100, 120)},
            'fog': {'visibility': 0.5, 'speed': 0.6, 'color': (150, 150, 150)},
            'snow': {'visibility': 0.6, 'speed': 0.7, 'color': (220, 220, 255)}
        }
        
        effects = weather_effects.get(weather, weather_effects['clear'])
        self.visibility_factor = effects['visibility']
        self.speed_adjustment = effects['speed']
        return effects['color']
    
    def set_time_of_day(self, time_period):
        """Set time of day and adjust traffic patterns"""
        self.time_of_day = time_period
        
        traffic_multipliers = {
            'morning_rush': 1.5,
            'midday': 1.0,
            'evening_rush': 1.8,
            'night': 0.3
        }
        
        return traffic_multipliers.get(time_period, 1.0)

class VulnerableUserProtection:
    """Pedestrian and cyclist protection system"""
    def __init__(self):
        self.pedestrians_waiting = {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        self.cyclists_detected = {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        self.crossing_active = False
        self.crossing_direction = None
        
    def add_pedestrians(self, direction, count):
        """Add pedestrians waiting to cross"""
        self.pedestrians_waiting[direction] += count
        
    def add_cyclists(self, direction, count):
        """Add cyclists detected"""
        self.cyclists_detected[direction] += count
        
    def request_crossing(self, direction):
        """Request pedestrian crossing"""
        if self.pedestrians_waiting[direction] > 0:
            return True, self.pedestrians_waiting[direction]
        return False, 0
    
    def activate_crossing(self, direction):
        """Activate pedestrian crossing phase"""
        self.crossing_active = True
        self.crossing_direction = direction
        self.pedestrians_waiting[direction] = 0

class VideoSceneManager:
    """Manages different scenes for the video demonstration"""
    def __init__(self, screen, config):
        self.screen = screen
        self.config = config
        self.current_scene = 0
        self.scene_timer = 0
        self.scenes = [
            'intro',
            'problem_demonstration',
            'ai_detection_showcase',
            'adaptive_signal_control',
            'emergency_vehicle_priority',
            'environmental_adaptation',
            'multi_intersection_coordination',
            'results_and_impact'
        ]
        
    def get_current_scene(self):
        """Get current scene name"""
        if self.current_scene < len(self.scenes):
            return self.scenes[self.current_scene]
        return 'results_and_impact'
    
    def advance_scene(self):
        """Move to next scene"""
        self.current_scene += 1
        self.scene_timer = 0
        
    def update(self, dt):
        """Update scene timer"""
        self.scene_timer += dt
        if self.scene_timer >= self.config.scene_duration:
            self.advance_scene()

class AdaptiveTrafficVideoDemo:
    """Main video demonstration class"""
    def __init__(self):
        pygame.init()
        self.config = VideoConfig()
        self.screen = pygame.display.set_mode((self.config.width, self.config.height))
        pygame.display.set_caption("Adaptive Traffic Signal Control - Video Demo")
        self.clock = pygame.time.Clock()
        
        # Initialize systems
        self.metrics = TrafficMetrics()
        self.emergency_system = EmergencyVehicleSystem()
        self.environmental_system = EnvironmentalSystem()
        self.vulnerable_protection = VulnerableUserProtection()
        self.scene_manager = VideoSceneManager(self.screen, self.config)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.subtitle_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Demo state
        self.running = True
        self.paused = False
        self.demo_time = 0
        self.vehicles = []
        self.signals = []
        self.current_phase = 0
        self.phase_timer = 0
        
        # Performance tracking
        self.fps_history = deque(maxlen=60)
        
    def create_intersection_background(self):
        """Create realistic intersection background"""
        background = pygame.Surface((self.config.width, self.config.height))
        background.fill(self.config.COLORS['background'])
        
        # Draw roads
        road_width = 120
        center_x, center_y = self.config.width // 2, self.config.height // 2
        
        # Horizontal road
        pygame.draw.rect(background, self.config.COLORS['road'], 
                        (0, center_y - road_width//2, self.config.width, road_width))
        # Vertical road
        pygame.draw.rect(background, self.config.COLORS['road'], 
                        (center_x - road_width//2, 0, road_width, self.config.height))
        
        # Lane markings
        lane_marking_width = 5
        for i in range(0, self.config.width, 40):
            pygame.draw.rect(background, self.config.COLORS['lane_marking'],
                           (i, center_y - lane_marking_width//2, 20, lane_marking_width))
        for i in range(0, self.config.height, 40):
            pygame.draw.rect(background, self.config.COLORS['lane_marking'],
                           (center_x - lane_marking_width//2, i, lane_marking_width, 20))
        
        # Intersection box
        intersection_size = road_width
        pygame.draw.rect(background, self.config.COLORS['road'],
                        (center_x - intersection_size//2, center_y - intersection_size//2,
                         intersection_size, intersection_size))
        
        return background
    
    def draw_traffic_signals(self):
        """Draw traffic signals at intersection"""
        signal_positions = [
            (self.config.width//2 - 80, self.config.height//2 - 80),  # North-West
            (self.config.width//2 + 80, self.config.height//2 - 80),  # North-East
            (self.config.width//2 + 80, self.config.height//2 + 80),  # South-East
            (self.config.width//2 - 80, self.config.height//2 + 80),  # South-West
        ]
        
        for i, pos in enumerate(signal_positions):
            # Draw signal box
            pygame.draw.rect(self.screen, (50, 50, 50), 
                           (pos[0] - 15, pos[1] - 35, 30, 70))
            
            # Determine signal color based on phase
            if i // 2 == self.current_phase:  # North-South or East-West
                signal_color = self.config.COLORS['signal_green']
            else:
                signal_color = self.config.COLORS['signal_red']
            
            # Draw signal lights
            pygame.draw.circle(self.screen, self.config.COLORS['signal_red'], 
                             (pos[0], pos[1] - 20), 8)
            pygame.draw.circle(self.screen, self.config.COLORS['signal_yellow'], 
                             (pos[0], pos[1]), 8)
            pygame.draw.circle(self.screen, signal_color, 
                             (pos[0], pos[1] + 20), 8)
    
    def draw_vehicles(self):
        """Draw vehicles on roads"""
        for vehicle in self.vehicles:
            # Simple vehicle representation
            color = self.config.COLORS['vehicle_blue']
            if vehicle.get('type') == 'emergency':
                color = self.config.COLORS['emergency']
            elif vehicle.get('type') == 'bus':
                color = self.config.COLORS['vehicle_yellow']
                
            pygame.draw.rect(self.screen, color,
                           (vehicle['x'], vehicle['y'], 30, 20))
    
    def draw_metrics_panel(self):
        """Draw performance metrics panel"""
        panel_x, panel_y = 20, 20
        panel_width, panel_height = 350, 200
        
        # Draw panel background
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(230)
        panel_surface.fill((255, 255, 255))
        self.screen.blit(panel_surface, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (0, 0, 0), 
                        (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Draw metrics
        metrics_data = [
            f"Vehicles Passed: {self.metrics.vehicles_passed}",
            f"Avg Wait Time: {self.metrics.total_wait_time / max(1, self.metrics.vehicles_passed):.1f}s",
            f"Efficiency Score: {self.metrics.efficiency_score:.1f}%",
            f"Fuel Saved: {self.metrics.fuel_saved:.1f} gallons",
            f"CO₂ Reduced: {self.metrics.co2_reduced:.1f} kg",
            f"Emergencies Served: {self.emergency_system.active_emergencies}"
        ]
        
        y_offset = panel_y + 10
        for metric in metrics_data:
            text = self.small_font.render(metric, True, self.config.COLORS['text'])
            self.screen.blit(text, (panel_x + 10, y_offset))
            y_offset += 25
    
    def draw_scene_title(self):
        """Draw current scene title and description"""
        scene_titles = {
            'intro': ("Adaptive Traffic Signal Control", "Revolutionizing Urban Transportation"),
            'problem_demonstration': ("The Traffic Problem", "Congestion costs cities billions annually"),
            'ai_detection_showcase': ("AI-Powered Detection", "Our system sees and counts every vehicle"),
            'adaptive_signal_control': ("Intelligent Signal Control", "Signals that think and adapt in real-time"),
            'emergency_vehicle_priority': ("Emergency Vehicle Priority", "Saving lives with smart signal preemption"),
            'environmental_adaptation': ("Environmental Adaptation", "Adjusting to weather and conditions"),
            'multi_intersection_coordination': ("Network Coordination", "Optimizing traffic across the city"),
            'results_and_impact': ("Results & Impact", "Measurable improvements for everyone")
        }
        
        current_scene = self.scene_manager.get_current_scene()
        if current_scene in scene_titles:
            title, subtitle = scene_titles[current_scene]
            
            # Draw title
            title_text = self.title_font.render(title, True, self.config.COLORS['text'])
            title_rect = title_text.get_rect(center=(self.config.width // 2, 50))
            self.screen.blit(title_text, title_rect)
            
            # Draw subtitle
            subtitle_text = self.subtitle_font.render(subtitle, True, (100, 100, 100))
            subtitle_rect = subtitle_text.get_rect(center=(self.config.width // 2, 90))
            self.screen.blit(subtitle_text, subtitle_rect)
    
    def simulate_scene_content(self):
        """Simulate content specific to current scene"""
        current_scene = self.scene_manager.get_current_scene()
        
        if current_scene == 'intro':
            # Show system overview
            pass
            
        elif current_scene == 'problem_demonstration':
            # Show congested traffic
            if random.random() < 0.1:
                self.add_vehicle('car', random.choice(['north', 'south', 'east', 'west']))
                
        elif current_scene == 'ai_detection_showcase':
            # Show vehicle detection in action
            if random.random() < 0.15:
                vehicle_type = random.choice(['car', 'truck', 'bus', 'motorcycle'])
                direction = random.choice(['north', 'south', 'east', 'west'])
                self.add_vehicle(vehicle_type, direction)
                
        elif current_scene == 'adaptive_signal_control':
            # Show adaptive signal timing
            self.phase_timer += 1
            if self.phase_timer > 120:  # Change phase every 4 seconds at 30 FPS
                self.current_phase = 1 - self.current_phase
                self.phase_timer = 0
                
        elif current_scene == 'emergency_vehicle_priority':
            # Show emergency vehicle preemption
            if random.random() < 0.02:
                self.emergency_system.add_emergency(
                    random.choice(['ambulance', 'fire_truck', 'police']),
                    random.choice(['north', 'south', 'east', 'west']),
                    100
                )
                
        elif current_scene == 'environmental_adaptation':
            # Show weather adaptation
            if random.random() < 0.01:
                weather = random.choice(self.environmental_system.weather_conditions)
                self.environmental_system.set_weather(weather)
                
        elif current_scene == 'multi_intersection_coordination':
            # Show network coordination
            pass
            
        elif current_scene == 'results_and_impact':
            # Show final results
            pass
    
    def add_vehicle(self, vehicle_type, direction):
        """Add a vehicle to the simulation"""
        vehicle = {
            'type': vehicle_type,
            'direction': direction,
            'x': 0,
            'y': 0,
            'speed': 2,
            'wait_time': 0
        }
        
        # Set starting position based on direction
        center_x, center_y = self.config.width // 2, self.config.height // 2
        if direction == 'north':
            vehicle['x'] = center_x + 30
            vehicle['y'] = self.config.height
        elif direction == 'south':
            vehicle['x'] = center_x - 30
            vehicle['y'] = 0
        elif direction == 'east':
            vehicle['x'] = 0
            vehicle['y'] = center_y - 30
        elif direction == 'west':
            vehicle['x'] = self.config.width
            vehicle['y'] = center_y + 30
            
        self.vehicles.append(vehicle)
    
    def update_vehicles(self, dt):
        """Update vehicle positions"""
        center_x, center_y = self.config.width // 2, self.config.height // 2
        
        for vehicle in self.vehicles[:]:
            # Check if vehicle should stop at red light
            should_stop = False
            distance_to_intersection = abs(vehicle['x'] - center_x) + abs(vehicle['y'] - center_y)
            
            if distance_to_intersection < 150 and distance_to_intersection > 50:
                # Check signal phase
                if vehicle['direction'] in ['north', 'south'] and self.current_phase == 1:
                    should_stop = True
                elif vehicle['direction'] in ['east', 'west'] and self.current_phase == 0:
                    should_stop = True
            
            if not should_stop:
                # Move vehicle
                if vehicle['direction'] == 'north':
                    vehicle['y'] -= vehicle['speed']
                elif vehicle['direction'] == 'south':
                    vehicle['y'] += vehicle['speed']
                elif vehicle['direction'] == 'east':
                    vehicle['x'] += vehicle['speed']
                elif vehicle['direction'] == 'west':
                    vehicle['x'] -= vehicle['speed']
            else:
                vehicle['wait_time'] += dt
            
            # Remove vehicles that have left the screen
            if (vehicle['x'] < -50 or vehicle['x'] > self.config.width + 50 or
                vehicle['y'] < -50 or vehicle['y'] > self.config.height + 50):
                self.vehicles.remove(vehicle)
                self.metrics.vehicles_passed += 1
                self.metrics.total_wait_time += vehicle['wait_time']
    
    def draw_weather_effects(self):
        """Draw weather effects on screen"""
        if self.environmental_system.current_weather == 'rain':
            # Draw rain drops
            for _ in range(50):
                x = random.randint(0, self.config.width)
                y = random.randint(0, self.config.height)
                pygame.draw.line(self.screen, (100, 100, 200), (x, y), (x - 2, y + 10), 1)
                
        elif self.environmental_system.current_weather == 'fog':
            # Draw fog overlay
            fog_surface = pygame.Surface((self.config.width, self.config.height))
            fog_surface.set_alpha(100)
            fog_surface.fill((200, 200, 200))
            self.screen.blit(fog_surface, (0, 0))
            
        elif self.environmental_system.current_weather == 'snow':
            # Draw snowflakes
            for _ in range(30):
                x = random.randint(0, self.config.width)
                y = random.randint(0, self.config.height)
                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), 2)
    
    def run(self):
        """Main video demonstration loop"""
        background = self.create_intersection_background()
        
        while self.running and self.demo_time < self.config.duration_seconds:
            dt = self.clock.tick(self.config.fps) / 1000.0
            self.demo_time += dt
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_RIGHT:
                        self.scene_manager.advance_scene()
            
            if not self.paused:
                # Update systems
                self.scene_manager.update(dt)
                self.emergency_system.update(dt)
                self.update_vehicles(dt)
                self.simulate_scene_content()
                self.metrics.update(0, 0, len(self.vehicles))
            
            # Draw everything
            self.screen.blit(background, (0, 0))
            self.draw_weather_effects()
            self.draw_traffic_signals()
            self.draw_vehicles()
            self.draw_metrics_panel()
            self.draw_scene_title()
            
            # Draw progress bar
            progress = self.demo_time / self.config.duration_seconds
            pygame.draw.rect(self.screen, (200, 200, 200), 
                           (10, self.config.height - 30, self.config.width - 20, 20))
            pygame.draw.rect(self.screen, (0, 200, 0), 
                           (10, self.config.height - 30, 
                            int((self.config.width - 20) * progress), 20))
            
            # Draw FPS
            fps = self.clock.get_fps()
            self.fps_history.append(fps)
            avg_fps = np.mean(self.fps_history) if self.fps_history else 0
            fps_text = self.small_font.render(f"FPS: {avg_fps:.1f}", True, (0, 0, 0))
            self.screen.blit(fps_text, (self.config.width - 100, 10))
            
            # Draw instructions
            instructions = "SPACE: Pause/Resume | RIGHT: Next Scene | ESC: Exit"
            inst_text = self.small_font.render(instructions, True, (100, 100, 100))
            self.screen.blit(inst_text, (10, self.config.height - 50))
            
            pygame.display.flip()
        
        # Show completion screen
        self.show_completion_screen()
    
    def show_completion_screen(self):
        """Show video completion screen"""
        self.screen.fill(self.config.COLORS['background'])
        
        # Draw completion message
        title = self.title_font.render("Video Demo Complete", True, self.config.COLORS['text'])
        title_rect = title.get_rect(center=(self.config.width // 2, self.config.height // 2 - 50))
        self.screen.blit(title, title_rect)
        
        subtitle = self.subtitle_font.render("Thank you for watching!", True, (100, 100, 100))
        subtitle_rect = subtitle.get_rect(center=(self.config.width // 2, self.config.height // 2 + 20))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Draw final metrics
        metrics_text = [
            f"Total Vehicles Processed: {self.metrics.vehicles_passed}",
            f"Average Efficiency: {self.metrics.efficiency_score:.1f}%",
            f"Environmental Impact: {self.metrics.co2_reduced:.1f} kg CO₂ reduced"
        ]
        
        y_offset = self.config.height // 2 + 80
        for metric in metrics_text:
            text = self.text_font.render(metric, True, self.config.COLORS['text'])
            text_rect = text.get_rect(center=(self.config.width // 2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 30
        
        pygame.display.flip()
        
        # Wait for user to close
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    waiting = False
        
        pygame.quit()

def main():
    """Main entry point"""
    print("🚦 Adaptive Traffic Signal Control - Video Demo")
    print("=" * 60)
    print("This demo showcases all system capabilities for non-technical audience")
    print("Features demonstrated:")
    print("  • AI-powered vehicle detection")
    print("  • Adaptive signal control")
    print("  • Emergency vehicle priority")
    print("  • Environmental adaptation")
    print("  • Multi-intersection coordination")
    print("  • Performance metrics and impact")
    print("\nControls:")
    print("  SPACE: Pause/Resume")
    print("  RIGHT: Skip to next scene")
    print("  ESC: Exit demo")
    print("=" * 60)
    
    try:
        demo = AdaptiveTrafficVideoDemo()
        demo.run()
    except Exception as e:
        print(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()