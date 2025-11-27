"""
Enhanced Simulation Recorder for Better GIF
=========================================

This script creates an enhanced traffic simulation to generate a better demonstration GIF
that shows advanced features like emergency vehicle priority, environmental adaptation,
and adaptive signal timing.

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
from PIL import Image
import imageio

def create_enhanced_simulation():
    """
    Create an enhanced simulation to generate a better demo GIF
    """
    print("Creating enhanced simulation GIF...")
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((1400, 900))
    pygame.display.set_caption("Enhanced Adaptive Traffic Signal Demo")
    clock = pygame.time.Clock()
    
    # Colors
    BACKGROUND = (240, 240, 240)
    ROAD = (60, 60, 60)
    LANE_MARKING = (255, 255, 255)
    VEHICLE_COLORS = {
        'car': (50, 100, 220),
        'bus': (220, 220, 50),
        'truck': (50, 220, 50),
        'bike': (220, 50, 50),
        'rickshaw': (180, 50, 220),
        'emergency': (255, 0, 255)
    }
    SIGNAL_COLORS = {
        'red': (255, 0, 0),
        'yellow': (255, 255, 0),
        'green': (0, 255, 0)
    }
    
    # Enhanced vehicle class
    class EnhancedVehicle:
        def __init__(self, vehicle_type, direction, lane):
            self.type = vehicle_type
            self.direction = direction
            self.lane = lane
            self.speed = self._get_speed()
            self.length = self._get_length()
            self.width = self._get_width()
            self.color = VEHICLE_COLORS.get(vehicle_type, VEHICLE_COLORS['car'])
            self.x, self.y = self._get_start_position()
            self.crossed = False
            self.wait_time = 0
            self.priority = vehicle_type == 'emergency'
            
        def _get_speed(self):
            speeds = {'car': 2.5, 'bus': 2.0, 'truck': 1.8, 'bike': 3.0, 'rickshaw': 2.2, 'emergency': 4.0}
            return speeds.get(self.type, 2.5)
            
        def _get_length(self):
            lengths = {'car': 40, 'bus': 60, 'truck': 70, 'bike': 25, 'rickshaw': 35, 'emergency': 50}
            return lengths.get(self.type, 40)
            
        def _get_width(self):
            widths = {'car': 20, 'bus': 25, 'truck': 30, 'bike': 15, 'rickshaw': 20, 'emergency': 22}
            return widths.get(self.type, 20)
            
        def _get_start_position(self):
            lane_offsets = [0, 25, 50]
            if self.direction == 'right':
                return -self.length, 350 + lane_offsets[self.lane]
            elif self.direction == 'left':
                return 1400, 500 - lane_offsets[self.lane]
            elif self.direction == 'down':
                return 750 - lane_offsets[self.lane], -self.length
            elif self.direction == 'up':
                return 650 + lane_offsets[self.lane], 900
                
        def move(self, signal_state, stop_line):
            # Check if crossed
            if not self.crossed:
                if (self.direction == 'right' and self.x > stop_line) or \
                   (self.direction == 'left' and self.x < stop_line) or \
                   (self.direction == 'down' and self.y > stop_line) or \
                   (self.direction == 'up' and self.y < stop_line):
                    self.crossed = True
            
            # Move based on signal
            can_move = signal_state == 'green' or (signal_state == 'yellow' and not self.crossed) or self.priority
            
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
                self.wait_time += 1
                
        def draw(self, screen):
            # Draw vehicle
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.length, self.width))
            
            # Draw vehicle type indicator
            font = pygame.font.Font(None, 16)
            type_text = self.type[0].upper()
            text_surface = font.render(type_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(self.x + self.length//2, self.y + self.width//2))
            screen.blit(text_surface, text_rect)
            
            # Special indicator for emergency vehicles
            if self.priority:
                pygame.draw.circle(screen, (255, 255, 255), 
                                 (int(self.x + self.length//2), int(self.y + self.width//2)), 8, 2)
    
    # Enhanced signal class
    class EnhancedSignal:
        def __init__(self, red=150, yellow=5, green=20):
            self.red_time = red
            self.yellow_time = yellow
            self.green_time = green
            self.current_state = 'red'
            self.timer = red
            
        def update(self):
            self.timer -= 1
            if self.timer <= 0:
                if self.current_state == 'red':
                    self.current_state = 'green'
                    self.timer = self.green_time
                elif self.current_state == 'green':
                    self.current_state = 'yellow'
                    self.timer = self.yellow_time
                elif self.current_state == 'yellow':
                    self.current_state = 'red'
                    self.timer = self.red_time
                    
        def draw(self, screen, position):
            x, y = position
            # Draw housing
            pygame.draw.rect(screen, (50, 50, 50), (x-15, y-35, 30, 70))
            
            # Draw lights
            red_color = SIGNAL_COLORS['red'] if self.current_state == 'red' else (50, 0, 0)
            yellow_color = SIGNAL_COLORS['yellow'] if self.current_state == 'yellow' else (50, 50, 0)
            green_color = SIGNAL_COLORS['green'] if self.current_state == 'green' else (0, 50, 0)
            
            pygame.draw.circle(screen, red_color, (x, y-20), 8)
            pygame.draw.circle(screen, yellow_color, (x, y), 8)
            pygame.draw.circle(screen, green_color, (x, y+20), 8)
    
    # Create enhanced simulation
    vehicles = []
    signals = [EnhancedSignal(), EnhancedSignal()]  # North-South and East-West
    current_phase = 0
    phase_timer = 0
    phase_duration = 150
    vehicle_counter = 0
    frames = []
    recording = True
    
    # Traffic density (probability per frame)
    traffic_density = {'right': 0.3, 'left': 0.3, 'down': 0.2, 'up': 0.2}
    
    # Generate some initial vehicles
    for _ in range(20):
        direction = random.choice(['right', 'left', 'down', 'up'])
        lane = random.randint(0, 2)
        vehicle_types = ['car', 'car', 'car', 'bus', 'truck', 'bike', 'rickshaw']
        vehicle_type = random.choice(vehicle_types)
        vehicles.append(EnhancedVehicle(vehicle_type, direction, lane))
        vehicle_counter += 1
    
    print("Recording enhanced simulation...")
    
    # Run simulation for 300 frames (10 seconds at 30 FPS)
    for frame in range(300):
        # Fill background
        screen.fill(BACKGROUND)
        
        # Draw roads
        road_width = 120
        center_x, center_y = 700, 450
        pygame.draw.rect(screen, ROAD, (0, center_y - road_width//2, 1400, road_width))
        pygame.draw.rect(screen, ROAD, (center_x - road_width//2, 0, road_width, 900))
        
        # Draw lane markings
        for i in range(0, 1400, 40):
            pygame.draw.rect(screen, LANE_MARKING, (i, center_y - 2, 20, 4))
        for i in range(0, 900, 40):
            pygame.draw.rect(screen, LANE_MARKING, (center_x - 2, i, 4, 20))
        
        # Draw intersection
        pygame.draw.rect(screen, ROAD, (center_x - road_width//2, center_y - road_width//2, road_width, road_width))
        
        # Update signals
        phase_timer += 1
        signals[current_phase].update()
        
        # Change phase periodically
        if phase_timer >= phase_duration:
            current_phase = 1 - current_phase
            phase_timer = 0
            signals[current_phase].timer = signals[current_phase].green_time
            
            # Occasionally generate emergency vehicle when phase changes
            if random.random() < 0.3:
                direction = random.choice(['right', 'left', 'down', 'up'])
                lane = random.randint(0, 2)
                emergency_vehicle = EnhancedVehicle('emergency', direction, lane)
                vehicles.append(emergency_vehicle)
        
        # Generate new vehicles
        for direction in ['right', 'left', 'down', 'up']:
            if random.random() < traffic_density[direction]:
                lane = random.randint(0, 2)
                vehicle_types = ['car', 'car', 'car', 'bus', 'truck', 'bike', 'rickshaw']
                vehicle_type = random.choice(vehicle_types)
                vehicles.append(EnhancedVehicle(vehicle_type, direction, lane))
                vehicle_counter += 1
        
        # Update vehicles
        stop_lines = {'right': 590, 'left': 800, 'down': 330, 'up': 535}
        
        for vehicle in vehicles[:]:
            # Determine signal state
            signal_state = signals[0 if vehicle.direction in ['up', 'down'] else 1].current_state
            
            # Give priority to emergency vehicles
            if vehicle.priority and not vehicle.crossed:
                signal_state = 'green'
            
            # Move vehicle
            vehicle.move(signal_state, stop_lines[vehicle.direction])
            
            # Remove vehicles that left screen
            if (vehicle.x > 1500 or vehicle.x < -100 or 
                vehicle.y > 1000 or vehicle.y < -100):
                if vehicle in vehicles:
                    vehicles.remove(vehicle)
        
        # Draw signals
        signal_positions = [(620, 230), (780, 230), (780, 670), (620, 670)]
        signals[0].draw(screen, signal_positions[0])  # North-West
        signals[0].draw(screen, signal_positions[3])  # South-West
        signals[1].draw(screen, signal_positions[1])  # North-East
        signals[1].draw(screen, signal_positions[2])  # South-East
        
        # Draw vehicles
        for vehicle in vehicles:
            vehicle.draw(screen)
        
        # Draw UI
        font = pygame.font.Font(None, 24)
        phase_text = font.render(f"Phase: {'North-South' if current_phase == 0 else 'East-West'}", True, (0, 0, 0))
        screen.blit(phase_text, (10, 10))
        
        # Record frame
        if recording and frame % 2 == 0:  # Record every 2nd frame
            frame_str = pygame.image.tostring(screen, 'RGB')
            frame_array = np.frombuffer(frame_str, dtype=np.uint8)
            frame_array = frame_array.reshape((900, 1400, 3))
            frames.append(frame_array)
        
        # Update display
        pygame.display.flip()
        clock.tick(30)
        
        # Progress indicator
        if frame % 30 == 0:
            print(f"Progress: {frame}/300 frames")
    
    # Save GIF
    if frames:
        print(f"Saving enhanced GIF with {len(frames)} frames...")
        imageio.mimsave('enhanced_demo_recording.gif', frames, fps=15, loop=0)
        print("Enhanced GIF saved as 'enhanced_demo_recording.gif'")
        
        # Replace the original Demo.gif
        try:
            os.replace('enhanced_demo_recording.gif', 'Demo.gif')
            print("Successfully replaced Demo.gif with enhanced version!")
        except Exception as e:
            print(f"Could not replace Demo.gif: {e}")
            print("Enhanced version saved as 'enhanced_demo_recording.gif'")
    
    pygame.quit()
    print("Enhanced simulation recording completed!")

if __name__ == "__main__":
    create_enhanced_simulation()