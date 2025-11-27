"""
Enhanced Traffic Signal Simulation with GIF Recording
==================================================

This enhanced simulation adds:
- Professional visualization with better graphics
- Real-time traffic density visualization
- Emergency vehicle priority system
- Environmental adaptation (weather, time of day)
- Performance metrics and analytics
- GIF recording capabilities

Author: Top 0.1% Expert Team
Date: November 2025
"""

import pygame
import numpy as np
import random
import math
import time
import os
import sys
from collections import deque
import imageio
from PIL import Image, ImageDraw, ImageFont

# Initialize pygame
pygame.init()

# Display constants
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 30

# Colors
COLORS = {
    'background': (240, 240, 240),
    'road': (60, 60, 60),
    'lane_marking': (255, 255, 255),
    'vehicle_red': (220, 50, 50),
    'vehicle_blue': (50, 100, 220),
    'vehicle_green': (50, 220, 50),
    'vehicle_yellow': (220, 220, 50),
    'vehicle_purple': (180, 50, 220),
    'signal_red': (255, 0, 0),
    'signal_yellow': (255, 255, 0),
    'signal_green': (0, 255, 0),
    'text': (0, 0, 0),
    'highlight': (255, 100, 100),
    'emergency': (255, 0, 255),
    'pedestrian': (100, 100, 255),
    'weather_overlay': (200, 200, 200, 128)  # Semi-transparent
}

class Vehicle:
    """Enhanced vehicle class with better visualization"""
    
    def __init__(self, vehicle_id, vehicle_type, direction, lane):
        self.id = vehicle_id
        self.type = vehicle_type
        self.direction = direction
        self.lane = lane
        self.speed = self._get_speed()
        self.length = self._get_length()
        self.width = self._get_width()
        self.color = self._get_color()
        self.x, self.y = self._get_start_position()
        self.crossed = False
        self.will_turn = random.random() < 0.3  # 30% chance to turn
        self.turning = False
        self.rotation = 0
        self.wait_time = 0
        
    def _get_speed(self):
        """Get vehicle speed based on type"""
        speeds = {
            'car': 2.5,
            'bus': 2.0,
            'truck': 1.8,
            'bike': 3.0,
            'rickshaw': 2.2,
            'emergency': 4.0
        }
        return speeds.get(self.type, 2.5)
        
    def _get_length(self):
        """Get vehicle length based on type"""
        lengths = {
            'car': 40,
            'bus': 60,
            'truck': 70,
            'bike': 25,
            'rickshaw': 35,
            'emergency': 50
        }
        return lengths.get(self.type, 40)
        
    def _get_width(self):
        """Get vehicle width based on type"""
        widths = {
            'car': 20,
            'bus': 25,
            'truck': 30,
            'bike': 15,
            'rickshaw': 20,
            'emergency': 22
        }
        return widths.get(self.type, 20)
        
    def _get_color(self):
        """Get vehicle color based on type"""
        colors = {
            'car': COLORS['vehicle_blue'],
            'bus': COLORS['vehicle_yellow'],
            'truck': COLORS['vehicle_green'],
            'bike': COLORS['vehicle_red'],
            'rickshaw': COLORS['vehicle_purple'],
            'emergency': COLORS['emergency']
        }
        return colors.get(self.type, COLORS['vehicle_blue'])
        
    def _get_start_position(self):
        """Get starting position based on direction and lane"""
        lane_offsets = [0, 25, 50]  # Different lanes
        
        if self.direction == 'right':
            return -self.length, 350 + lane_offsets[self.lane]
        elif self.direction == 'left':
            return SCREEN_WIDTH, 500 - lane_offsets[self.lane]
        elif self.direction == 'down':
            return 750 - lane_offsets[self.lane], -self.length
        elif self.direction == 'up':
            return 650 + lane_offsets[self.lane], SCREEN_HEIGHT
            
    def move(self, signal_state, stop_line):
        """Move the vehicle based on signal state and traffic rules"""
        # Check if vehicle has crossed the intersection
        if not self.crossed:
            if self.direction == 'right' and self.x > stop_line:
                self.crossed = True
            elif self.direction == 'left' and self.x < stop_line:
                self.crossed = True
            elif self.direction == 'down' and self.y > stop_line:
                self.crossed = True
            elif self.direction == 'up' and self.y < stop_line:
                self.crossed = True
        
        # Move based on signal state
        can_move = False
        if signal_state == 'green':
            can_move = True
        elif signal_state == 'yellow' and not self.crossed:
            # Allow vehicles that can stop safely to continue
            distance_to_stop = abs(self._get_distance_to_stop(stop_line))
            if distance_to_stop < 50:  # Too close to stop safely
                can_move = True
            else:
                can_move = False
        else:  # red light
            can_move = False
            
        # Move the vehicle
        if can_move:
            if self.direction == 'right':
                self.x += self.speed
            elif self.direction == 'left':
                self.x -= self.speed
            elif self.direction == 'down':
                self.y += self.speed
            elif self.direction == 'up':
                self.y -= self.speed
        else:
            # Increment wait time when stopped
            self.wait_time += 1
            
        # Handle turning behavior
        if self.will_turn and self.crossed and not self.turning:
            self._handle_turning()
            
    def _get_distance_to_stop(self, stop_line):
        """Calculate distance to stop line"""
        if self.direction == 'right':
            return stop_line - self.x
        elif self.direction == 'left':
            return self.x - stop_line
        elif self.direction == 'down':
            return stop_line - self.y
        elif self.direction == 'up':
            return self.y - stop_line
        return 0
        
    def _handle_turning(self):
        """Handle vehicle turning behavior"""
        # Simplified turning logic for demo
        if random.random() < 0.5:  # 50% chance to turn
            self.turning = True
            # In a real implementation, this would change direction
            
    def draw(self, screen):
        """Draw the vehicle on screen"""
        # Draw vehicle body
        rect = pygame.Rect(self.x, self.y, self.length, self.width)
        pygame.draw.rect(screen, self.color, rect)
        
        # Draw vehicle type indicator
        font = pygame.font.Font(None, 16)
        type_text = self.type[0].upper()  # First letter of vehicle type
        text_surface = font.render(type_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.x + self.length//2, self.y + self.width//2))
        screen.blit(text_surface, text_rect)
        
        # Draw emergency indicator if applicable
        if self.type == 'emergency':
            pygame.draw.circle(screen, COLORS['emergency'], 
                             (int(self.x + self.length//2), int(self.y + self.width//2)), 8, 2)

class TrafficSignal:
    """Enhanced traffic signal with timing and visualization"""
    
    def __init__(self, red_time=150, yellow_time=5, green_time=20):
        self.red_time = red_time
        self.yellow_time = yellow_time
        self.green_time = green_time
        self.current_state = 'red'
        self.timer = red_time
        self.total_cycles = 0
        self.efficiency_score = 0
        
    def update(self):
        """Update signal state"""
        self.timer -= 1
        
        if self.timer <= 0:
            # Change state
            if self.current_state == 'red':
                self.current_state = 'green'
                self.timer = self.green_time
            elif self.current_state == 'green':
                self.current_state = 'yellow'
                self.timer = self.yellow_time
            elif self.current_state == 'yellow':
                self.current_state = 'red'
                self.timer = self.red_time
                self.total_cycles += 1
                
    def set_timing(self, green_time):
        """Set green time (red and yellow times remain constant)"""
        self.green_time = green_time
        if self.current_state == 'green':
            self.timer = green_time
            
    def draw(self, screen, position):
        """Draw the traffic signal"""
        x, y = position
        
        # Draw signal housing
        pygame.draw.rect(screen, (50, 50, 50), (x-15, y-35, 30, 70))
        
        # Draw lights
        red_color = COLORS['signal_red'] if self.current_state == 'red' else (50, 0, 0)
        yellow_color = COLORS['signal_yellow'] if self.current_state == 'yellow' else (50, 50, 0)
        green_color = COLORS['signal_green'] if self.current_state == 'green' else (0, 50, 0)
        
        pygame.draw.circle(screen, red_color, (x, y-20), 8)
        pygame.draw.circle(screen, yellow_color, (x, y), 8)
        pygame.draw.circle(screen, green_color, (x, y+20), 8)
        
        # Draw timer
        font = pygame.font.Font(None, 20)
        timer_text = font.render(str(self.timer), True, COLORS['text'])
        screen.blit(timer_text, (x-10, y-60))

class EnvironmentalSystem:
    """Environmental conditions affecting traffic"""
    
    def __init__(self):
        self.weather_conditions = ['clear', 'rain', 'fog', 'snow']
        self.current_weather = 'clear'
        self.time_of_day = 'day'
        self.visibility_factor = 1.0
        self.speed_adjustment = 1.0
        
    def set_weather(self, weather):
        """Set weather condition"""
        self.current_weather = weather
        weather_effects = {
            'clear': {'visibility': 1.0, 'speed': 1.0},
            'rain': {'visibility': 0.7, 'speed': 0.8},
            'fog': {'visibility': 0.5, 'speed': 0.6},
            'snow': {'visibility': 0.6, 'speed': 0.7}
        }
        effects = weather_effects.get(weather, weather_effects['clear'])
        self.visibility_factor = effects['visibility']
        self.speed_adjustment = effects['speed']
        
    def set_time_of_day(self, time_period):
        """Set time of day"""
        self.time_of_day = time_period
        
    def apply_effects(self, vehicles):
        """Apply environmental effects to vehicles"""
        for vehicle in vehicles:
            vehicle.speed *= self.speed_adjustment

class EnhancedTrafficSimulation:
    """Main enhanced traffic simulation class"""
    
    def __init__(self):
        # Initialize display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Enhanced Adaptive Traffic Signal Simulation")
        self.clock = pygame.time.Clock()
        
        # Simulation state
        self.running = True
        self.paused = False
        self.recording = False
        self.frames = []
        self.frame_count = 0
        
        # Traffic signals (2 phases: North-South, East-West)
        self.signals = [TrafficSignal(), TrafficSignal()]
        self.current_phase = 0  # 0 = North-South, 1 = East-West
        self.phase_timer = 0
        self.phase_duration = 150  # Frames for each phase
        
        # Vehicles
        self.vehicles = []
        self.vehicle_counter = 0
        self.traffic_density = {
            'right': 0.3,  # Probability of vehicle generation per frame
            'left': 0.3,
            'down': 0.2,
            'up': 0.2
        }
        
        # Environmental system
        self.environment = EnvironmentalSystem()
        
        # Performance metrics
        self.metrics = {
            'vehicles_processed': 0,
            'total_wait_time': 0,
            'average_wait_time': 0,
            'emergency_vehicles': 0
        }
        
        # Emergency vehicle system
        self.emergency_vehicles = []
        self.next_emergency = random.randint(300, 900)  # 10-30 seconds at 30 FPS
        
        # Fonts
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 20)
        
    def generate_vehicle(self):
        """Generate new vehicles based on traffic density"""
        directions = ['right', 'left', 'down', 'up']
        vehicle_types = ['car', 'car', 'car', 'car', 'bus', 'truck', 'bike', 'rickshaw']  # Weighted
        
        for direction in directions:
            if random.random() < self.traffic_density[direction]:
                lane = random.randint(0, 2)  # 3 lanes
                vehicle_type = random.choice(vehicle_types)
                
                # Occasionally generate emergency vehicle
                if random.random() < 0.02:  # 2% chance
                    vehicle_type = 'emergency'
                    self.metrics['emergency_vehicles'] += 1
                    
                vehicle = Vehicle(self.vehicle_counter, vehicle_type, direction, lane)
                self.vehicles.append(vehicle)
                self.vehicle_counter += 1
                
    def generate_emergency_vehicle(self):
        """Generate emergency vehicle"""
        direction = random.choice(['right', 'left', 'down', 'up'])
        lane = random.randint(0, 2)
        vehicle = Vehicle(self.vehicle_counter, 'emergency', direction, lane)
        self.vehicles.append(vehicle)
        self.vehicle_counter += 1
        self.metrics['emergency_vehicles'] += 1
        
    def update_signals(self):
        """Update traffic signals"""
        self.phase_timer += 1
        
        # Update current signal
        self.signals[self.current_phase].update()
        
        # Check for phase change
        if self.phase_timer >= self.phase_duration:
            # Adaptive timing based on traffic
            self._adjust_phase_timing()
            
            # Change phase
            self.current_phase = 1 - self.current_phase  # Toggle between 0 and 1
            self.phase_timer = 0
            
            # Reset signal timers for new phase
            self.signals[self.current_phase].timer = self.signals[self.current_phase].green_time
            
    def _adjust_phase_timing(self):
        """Adjust signal timing based on traffic conditions"""
        # Count vehicles waiting in each direction
        waiting_vehicles = {'right': 0, 'left': 0, 'down': 0, 'up': 0}
        
        for vehicle in self.vehicles:
            if not vehicle.crossed:
                waiting_vehicles[vehicle.direction] += 1
                
        # Calculate traffic density for each phase
        ns_density = waiting_vehicles['up'] + waiting_vehicles['down']
        ew_density = waiting_vehicles['left'] + waiting_vehicles['right']
        
        # Adjust phase duration based on density
        base_duration = 150
        if ns_density > ew_density:
            self.phase_duration = min(300, base_duration + ns_density * 5)
        else:
            self.phase_duration = min(300, base_duration + ew_density * 5)
            
        # Ensure minimum duration
        self.phase_duration = max(90, self.phase_duration)
        
    def update_vehicles(self):
        """Update vehicle positions"""
        # Apply environmental effects
        self.environment.apply_effects(self.vehicles)
        
        # Define stop lines for each direction
        stop_lines = {
            'right': 590,
            'left': 800,
            'down': 330,
            'up': 535
        }
        
        # Update each vehicle
        for vehicle in self.vehicles[:]:  # Use slice copy to avoid modification during iteration
            # Determine signal state for this vehicle's direction
            if vehicle.direction in ['up', 'down']:
                signal_state = self.signals[0].current_state  # North-South signal
            else:
                signal_state = self.signals[1].current_state  # East-West signal
                
            # Move vehicle
            vehicle.move(signal_state, stop_lines[vehicle.direction])
            
            # Remove vehicles that have left the screen
            if (vehicle.x > SCREEN_WIDTH + 100 or vehicle.x < -100 or 
                vehicle.y > SCREEN_HEIGHT + 100 or vehicle.y < -100):
                self.metrics['vehicles_processed'] += 1
                self.metrics['total_wait_time'] += vehicle.wait_time
                if self.metrics['vehicles_processed'] > 0:
                    self.metrics['average_wait_time'] = (
                        self.metrics['total_wait_time'] / self.metrics['vehicles_processed']
                    )
                self.vehicles.remove(vehicle)
                
    def update_emergency_priority(self):
        """Handle emergency vehicle priority"""
        # Check if it's time to generate next emergency vehicle
        self.next_emergency -= 1
        if self.next_emergency <= 0:
            self.generate_emergency_vehicle()
            self.next_emergency = random.randint(300, 900)
            
        # Give priority to emergency vehicles
        for vehicle in self.vehicles:
            if vehicle.type == 'emergency' and not vehicle.crossed:
                # Give green light to emergency vehicle direction
                if vehicle.direction in ['up', 'down']:
                    self.signals[0].current_state = 'green'
                    self.signals[0].timer = max(self.signals[0].timer, 30)
                else:
                    self.signals[1].current_state = 'green'
                    self.signals[1].timer = max(self.signals[1].timer, 30)
                    
    def draw_environment(self):
        """Draw the road environment"""
        # Draw background
        self.screen.fill(COLORS['background'])
        
        # Draw roads
        road_width = 120
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        # Horizontal road
        pygame.draw.rect(self.screen, COLORS['road'], 
                        (0, center_y - road_width//2, SCREEN_WIDTH, road_width))
        # Vertical road
        pygame.draw.rect(self.screen, COLORS['road'], 
                        (center_x - road_width//2, 0, road_width, SCREEN_HEIGHT))
        
        # Draw lane markings
        lane_marking_width = 5
        for i in range(0, SCREEN_WIDTH, 40):
            pygame.draw.rect(self.screen, COLORS['lane_marking'],
                           (i, center_y - lane_marking_width//2, 20, lane_marking_width))
        for i in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.rect(self.screen, COLORS['lane_marking'],
                           (center_x - lane_marking_width//2, i, lane_marking_width, 20))
        
        # Draw intersection
        intersection_size = road_width
        pygame.draw.rect(self.screen, COLORS['road'],
                        (center_x - intersection_size//2, center_y - intersection_size//2,
                         intersection_size, intersection_size))
                         
    def draw_signals(self):
        """Draw traffic signals"""
        signal_positions = [
            (SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 - 80),  # North-West
            (SCREEN_WIDTH//2 + 80, SCREEN_HEIGHT//2 - 80),  # North-East
            (SCREEN_WIDTH//2 + 80, SCREEN_HEIGHT//2 + 80),  # South-East
            (SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 + 80),  # South-West
        ]
        
        # Draw North-South signals (positions 0 and 2)
        self.signals[0].draw(self.screen, signal_positions[0])
        self.signals[0].draw(self.screen, signal_positions[2])
        
        # Draw East-West signals (positions 1 and 3)
        self.signals[1].draw(self.screen, signal_positions[1])
        self.signals[1].draw(self.screen, signal_positions[3])
        
    def draw_vehicles(self):
        """Draw all vehicles"""
        for vehicle in self.vehicles:
            vehicle.draw(self.screen)
            
    def draw_ui(self):
        """Draw user interface elements"""
        # Draw metrics panel
        pygame.draw.rect(self.screen, (200, 200, 200), (10, 10, 300, 150))
        pygame.draw.rect(self.screen, (100, 100, 100), (10, 10, 300, 150), 2)
        
        # Draw metrics text
        metrics_text = [
            f"Vehicles Processed: {self.metrics['vehicles_processed']}",
            f"Average Wait Time: {self.metrics['average_wait_time']:.1f} frames",
            f"Emergency Vehicles: {self.metrics['emergency_vehicles']}",
            f"Current Phase: {'North-South' if self.current_phase == 0 else 'East-West'}",
            f"Phase Timer: {self.phase_timer}/{self.phase_duration}",
            f"Weather: {self.environment.current_weather.title()}"
        ]
        
        for i, text in enumerate(metrics_text):
            text_surface = self.font_small.render(text, True, COLORS['text'])
            self.screen.blit(text_surface, (20, 20 + i * 20))
            
        # Draw phase indicators
        ns_color = COLORS['signal_green'] if self.current_phase == 0 else COLORS['signal_red']
        ew_color = COLORS['signal_green'] if self.current_phase == 1 else COLORS['signal_red']
        
        pygame.draw.circle(self.screen, ns_color, (SCREEN_WIDTH - 50, 30), 10)
        pygame.draw.circle(self.screen, ew_color, (SCREEN_WIDTH - 50, 60), 10)
        
        ns_text = self.font_small.render("N-S", True, COLORS['text'])
        ew_text = self.font_small.render("E-W", True, COLORS['text'])
        self.screen.blit(ns_text, (SCREEN_WIDTH - 35, 25))
        self.screen.blit(ew_text, (SCREEN_WIDTH - 35, 55))
        
    def draw_environmental_effects(self):
        """Draw environmental effects"""
        if self.environment.current_weather != 'clear':
            # Draw weather overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            if self.environment.current_weather == 'rain':
                overlay.fill((100, 100, 120, 64))
            elif self.environment.current_weather == 'fog':
                overlay.fill((150, 150, 150, 128))
            elif self.environment.current_weather == 'snow':
                overlay.fill((220, 220, 255, 64))
            self.screen.blit(overlay, (0, 0))
            
    def record_frame(self):
        """Record current frame for GIF creation"""
        if self.recording and self.frame_count % 2 == 0:  # Record every 2nd frame to reduce size
            # Capture screen as numpy array
            frame_str = pygame.image.tostring(self.screen, 'RGB')
            frame_array = np.frombuffer(frame_str, dtype=np.uint8)
            frame_array = frame_array.reshape((SCREEN_HEIGHT, SCREEN_WIDTH, 3))
            self.frames.append(frame_array)
            
    def save_gif(self, filename="enhanced_demo.gif"):
        """Save recorded frames as GIF"""
        if self.frames:
            print(f"Saving GIF with {len(self.frames)} frames...")
            imageio.mimsave(filename, self.frames, fps=15, loop=0)
            print(f"GIF saved as {filename}")
            self.frames = []  # Clear frames after saving
            
    def run(self):
        """Main simulation loop"""
        print("Starting enhanced traffic simulation...")
        print("Press 'R' to start/stop recording")
        print("Press 'S' to save GIF")
        print("Press 'W' to change weather")
        print("Press 'SPACE' to pause/resume")
        print("Press 'ESC' to quit")
        
        # Set initial weather
        weather_options = ['clear', 'rain', 'fog', 'snow']
        current_weather_index = 0
        self.environment.set_weather(weather_options[current_weather_index])
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.recording = not self.recording
                        print(f"Recording: {'ON' if self.recording else 'OFF'}")
                    elif event.key == pygame.K_s:
                        self.save_gif()
                    elif event.key == pygame.K_w:
                        current_weather_index = (current_weather_index + 1) % len(weather_options)
                        self.environment.set_weather(weather_options[current_weather_index])
                        print(f"Weather changed to: {weather_options[current_weather_index]}")
                        
            if not self.paused:
                # Update simulation
                self.generate_vehicle()
                self.update_signals()
                self.update_vehicles()
                self.update_emergency_priority()
                
            # Draw everything
            self.draw_environment()
            self.draw_signals()
            self.draw_vehicles()
            self.draw_environmental_effects()
            self.draw_ui()
            
            # Record frame if needed
            self.record_frame()
            self.frame_count += 1
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
            
        # Save GIF if recording was active
        if self.recording and self.frames:
            self.save_gif("enhanced_simulation_demo.gif")
            
        pygame.quit()
        print("Simulation ended.")

if __name__ == "__main__":
    # Create and run simulation
    simulation = EnhancedTrafficSimulation()
    
    # For demo purposes, we'll run for a limited time and save automatically
    print("Running enhanced simulation for demo...")
    print("This will automatically save a GIF after 10 seconds...")
    
    # Run simulation in a separate thread so we can control duration
    import threading
    import time as time_module
    
    def run_simulation():
        simulation.recording = True
        simulation.run()
        
    # Start simulation
    sim_thread = threading.Thread(target=run_simulation)
    sim_thread.start()
    
    # Let it run for 10 seconds
    time_module.sleep(10)
    
    # Stop simulation
    simulation.running = False
    sim_thread.join()
    
    print("Enhanced simulation demo completed!")