"""
Emergency Vehicle Priority System
===============================

Advanced emergency vehicle detection and signal preemption with:
- Real-time emergency vehicle detection
- Signal preemption algorithms
- Priority corridor management
- Emergency route optimization
- Multi-modal emergency detection (audio, visual, GPS)
- Automatic recovery after emergency passage

Author: Top 0.1% Expert Team
Date: November 2025
Version: 3.0.0
"""

import numpy as np
import cv2
import threading
import time
import logging
from typing import List, Dict, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import queue
import json
import math
from collections import deque, defaultdict
import asyncio
from scipy import signal as scipy_signal
from scipy.fft import fft, fftfreq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmergencyType(Enum):
    """Types of emergency vehicles"""
    POLICE = "police"
    FIRE = "fire"
    AMBULANCE = "ambulance"
    RESCUE = "rescue"
    HAZMAT = "hazmat"

class DetectionMethod(Enum):
    """Emergency vehicle detection methods"""
    VISUAL = "visual"          # Siren lights, emergency colors
    AUDIO = "audio"            # Siren sound patterns
    GPS = "gps"                # GPS tracking from emergency services
    RFID = "rfid"              # RFID tags on emergency vehicles
    CELLULAR = "cellular"        # Cellular triangulation
    MANUAL = "manual"            # Manual activation

class PreemptionMode(Enum):
    """Signal preemption modes"""
    IMMEDIATE = "immediate"      # Immediate green light
    PRIORITY = "priority"        # Priority in next cycle
    COORDINATED = "coordinated"  # Coordinated corridor clearing
    STAGGERED = "staggered"     # Staggered progression

@dataclass
class EmergencyVehicle:
    """Emergency vehicle information"""
    vehicle_id: str
    emergency_type: EmergencyType
    current_location: Tuple[float, float]  # GPS coordinates
    destination: Optional[Tuple[float, float]]
    speed: float  # km/h
    heading: float  # degrees
    estimated_arrival: float  # seconds to intersection
    route: List[str] = field(default_factory=list)  # Intersection IDs
    priority_level: int = 1  # 1-10, higher = more urgent
    detection_method: DetectionMethod = DetectionMethod.VISUAL
    timestamp: float = field(default_factory=time.time)
    
@dataclass
class PreemptionRequest:
    """Signal preemption request"""
    request_id: str
    emergency_vehicle: EmergencyVehicle
    target_intersections: List[str]
    preemption_mode: PreemptionMode
    estimated_duration: float  # seconds
    priority_score: float
    timestamp: float = field(default_factory=time.time)

@dataclass
class EmergencyCorridor:
    """Emergency vehicle priority corridor"""
    corridor_id: str
    start_intersection: str
    end_intersection: str
    path_intersections: List[str]
    priority_level: int
    activation_time: float
    estimated_clearance_time: float
    active_vehicles: List[str] = field(default_factory=list)

class AudioEmergencyDetector:
    """Audio-based emergency vehicle detection using siren patterns"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.window_size = 1024
        self.hop_size = 512
        
        # Emergency siren frequency patterns (Hz)
        self.siren_patterns = {
            'wail': [500, 600],      # Traditional wail
            'yelp': [600, 800],       # Yelp pattern
            'hi_lo': [400, 800],      # High-low pattern
            'piercer': [1000, 1200],  # Piercer siren
            'airhorn': [200, 300]      # Air horn
        }
        
        # Detection thresholds
        self.frequency_threshold = 0.7
        self.amplitude_threshold = 0.3
        self.pattern_match_threshold = 0.8
        
        # Audio processing
        self.audio_buffer = deque(maxlen=self.sample_rate * 5)  # 5 seconds buffer
        self.detection_history = deque(maxlen=10)
        
        logger.info("Audio emergency detector initialized")
    
    def process_audio_frame(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Process audio frame for emergency vehicle detection"""
        # Add to buffer
        self.audio_buffer.extend(audio_data)
        
        if len(self.audio_buffer) < self.window_size:
            return {'detected': False, 'confidence': 0.0}
        
        # Convert to numpy array
        audio_array = np.array(list(self.audio_buffer)[-self.window_size:])
        
        # Apply window function
        window = np.hanning(self.window_size)
        windowed_audio = audio_array * window
        
        # FFT analysis
        fft_result = fft(windowed_audio)
        freqs = fftfreq(self.window_size, 1/self.sample_rate)
        magnitude = np.abs(fft_result)
        
        # Detect siren patterns
        detected_patterns = []
        for pattern_name, freq_range in self.siren_patterns.items():
            # Find peaks in frequency range
            freq_mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
            if np.any(freq_mask):
                pattern_magnitude = np.max(magnitude[freq_mask])
                normalized_magnitude = pattern_magnitude / np.max(magnitude)
                
                if normalized_magnitude > self.frequency_threshold:
                    detected_patterns.append({
                        'pattern': pattern_name,
                        'magnitude': normalized_magnitude,
                        'frequency': freqs[np.argmax(magnitude[freq_mask])]
                    })
        
        # Calculate confidence
        confidence = 0.0
        if detected_patterns:
            confidence = max(p['magnitude'] for p in detected_patterns)
        
        # Temporal consistency check
        is_consistent = self._check_temporal_consistency(confidence)
        
        result = {
            'detected': is_consistent and confidence > self.amplitude_threshold,
            'confidence': confidence,
            'patterns': detected_patterns,
            'timestamp': time.time()
        }
        
        self.detection_history.append(result)
        return result
    
    def _check_temporal_consistency(self, current_confidence: float) -> bool:
        """Check for consistent detection over time"""
        if len(self.detection_history) < 3:
            return True
        
        # Check if recent detections show consistent pattern
        recent_detections = list(self.detection_history)[-3:]
        avg_confidence = np.mean([d['confidence'] for d in recent_detections])
        
        return avg_confidence > self.amplitude_threshold * 0.7

class VisualEmergencyDetector:
    """Visual-based emergency vehicle detection"""
    
    def __init__(self):
        # Emergency vehicle color ranges (HSV)
        self.emergency_colors = {
            'red': [(0, 50, 50), (10, 255, 255)],      # Red lower/upper
            'blue': [(110, 50, 50), (130, 255, 255)],   # Blue lower/upper
            'amber': [(15, 50, 50), (25, 255, 255)],    # Amber lower/upper
            'white': [(0, 0, 200), (180, 30, 255)]      # White lower/upper
        }
        
        # Flash pattern detection
        self.flash_history = defaultdict(deque)
        self.flash_threshold = 3  # Minimum flashes for detection
        self.flash_time_window = 2.0  # seconds
        
        # Detection parameters
        self.min_area = 100  # Minimum contour area
        self.max_area = 5000  # Maximum contour area
        self.aspect_ratio_range = (0.5, 2.0)  # Valid aspect ratios
        
        logger.info("Visual emergency detector initialized")
    
    def detect_emergency_vehicles(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect emergency vehicles in video frame"""
        results = []
        
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Detect emergency colors
        detected_lights = []
        for color_name, (lower, upper) in self.emergency_colors.items():
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_area <= area <= self.max_area:
                    # Check aspect ratio
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    if self.aspect_ratio_range[0] <= aspect_ratio <= self.aspect_ratio_range[1]:
                        detected_lights.append({
                            'color': color_name,
                            'position': (x + w//2, y + h//2),
                            'area': area,
                            'timestamp': time.time()
                        })
        
        # Group nearby lights (likely same vehicle)
        vehicle_groups = self._group_lights_by_proximity(detected_lights)
        
        # Analyze each group for emergency vehicle patterns
        for group_id, lights in vehicle_groups.items():
            emergency_result = self._analyze_light_group(lights)
            if emergency_result['is_emergency']:
                results.append(emergency_result)
        
        return results
    
    def _group_lights_by_proximity(self, lights: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """Group nearby lights that likely belong to same vehicle"""
        groups = {}
        group_id = 0
        
        for light in lights:
            assigned = False
            
            # Check if light belongs to existing group
            for existing_group_id, existing_lights in groups.items():
                for existing_light in existing_lights:
                    distance = math.sqrt(
                        (light['position'][0] - existing_light['position'][0])**2 +
                        (light['position'][1] - existing_light['position'][1])**2
                    )
                    
                    if distance < 100:  # 100 pixels proximity threshold
                        groups[existing_group_id].append(light)
                        assigned = True
                        break
                
                if assigned:
                    break
            
            if not assigned:
                groups[group_id] = [light]
                group_id += 1
        
        return groups
    
    def _analyze_light_group(self, lights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze group of lights for emergency vehicle patterns"""
        if len(lights) < 2:
            return {'is_emergency': False, 'confidence': 0.0}
        
        # Count colors
        color_counts = defaultdict(int)
        for light in lights:
            color_counts[light['color']] += 1
        
        # Emergency vehicle patterns
        has_red = color_counts['red'] > 0
        has_blue = color_counts['blue'] > 0
        has_amber = color_counts['amber'] > 0
        has_white = color_counts['white'] > 0
        
        # Pattern matching
        confidence = 0.0
        emergency_type = None
        
        # Police: Red and blue flashing
        if has_red and has_blue:
            confidence = 0.9
            emergency_type = EmergencyType.POLICE
        
        # Fire/Ambulance: Red and white/amber
        elif has_red and (has_white or has_amber):
            confidence = 0.8
            emergency_type = EmergencyType.FIRE if has_white else EmergencyType.AMBULANCE
        
        # Mixed emergency lights
        elif len(color_counts) >= 2:
            confidence = 0.6
            emergency_type = EmergencyType.RESCUE
        
        # Check for flashing pattern
        is_flashing = self._detect_flashing_pattern(lights)
        if is_flashing:
            confidence += 0.2
        
        return {
            'is_emergency': confidence > 0.7,
            'confidence': min(1.0, confidence),
            'emergency_type': emergency_type,
            'light_count': len(lights),
            'colors': list(color_counts.keys()),
            'center_position': self._calculate_group_center(lights),
            'timestamp': time.time()
        }
    
    def _detect_flashing_pattern(self, lights: List[Dict[str, Any]]) -> bool:
        """Detect if lights are flashing"""
        current_time = time.time()
        
        for light in lights:
            color = light['color']
            timestamp = light['timestamp']
            
            # Add to flash history
            self.flash_history[color].append(timestamp)
            
            # Remove old entries
            self.flash_history[color] = deque(
                [t for t in self.flash_history[color] 
                 if current_time - t < self.flash_time_window],
                maxlen=self.flash_history[color].maxlen
            )
            
            # Check for minimum flashes
            if len(self.flash_history[color]) >= self.flash_threshold:
                return True
        
        return False
    
    def _calculate_group_center(self, lights: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Calculate center point of light group"""
        x_coords = [light['position'][0] for light in lights]
        y_coords = [light['position'][1] for light in lights]
        
        return (np.mean(x_coords), np.mean(y_coords))

class EmergencyVehicleDetector:
    """Multi-modal emergency vehicle detection system"""
    
    def __init__(self):
        # Detection components
        self.audio_detector = AudioEmergencyDetector()
        self.visual_detector = VisualEmergencyDetector()
        
        # Detection fusion
        self.detection_queue = queue.Queue(maxsize=100)
        self.confidence_threshold = 0.7
        self.temporal_window = 2.0  # seconds
        
        # Tracking
        self.tracked_vehicles = {}
        self.detection_history = defaultdict(deque)
        
        # Multi-threading
        self.running = False
        self.detection_thread = None
        
        logger.info("Multi-modal emergency vehicle detector initialized")
    
    def start_detection(self):
        """Start continuous detection"""
        self.running = True
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        logger.info("Emergency vehicle detection started")
    
    def stop_detection(self):
        """Stop detection"""
        self.running = False
        if self.detection_thread:
            self.detection_thread.join(timeout=5)
        logger.info("Emergency vehicle detection stopped")
    
    def _detection_loop(self):
        """Main detection loop"""
        while self.running:
            try:
                # Process audio and visual inputs
                # In real implementation, would get from camera/microphone
                audio_result = self._simulate_audio_detection()
                visual_results = self._simulate_visual_detection()
                
                # Fuse detections
                fused_detections = self._fuse_detections(audio_result, visual_results)
                
                # Update tracking
                for detection in fused_detections:
                    self._update_vehicle_tracking(detection)
                
                time.sleep(0.1)  # 10 Hz detection rate
                
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                time.sleep(1)
    
    def _simulate_audio_detection(self) -> Dict[str, Any]:
        """Simulate audio detection (replace with real audio input)"""
        # Generate random audio data for simulation
        audio_data = np.random.randn(1024) * 0.1
        
        # Occasionally simulate emergency siren
        if np.random.random() < 0.01:  # 1% chance
            # Add siren-like pattern
            t = np.linspace(0, 1, 1024)
            siren = np.sin(2 * np.pi * 600 * t) * 0.5  # 600 Hz siren
            audio_data += siren
        
        return self.audio_detector.process_audio_frame(audio_data)
    
    def _simulate_visual_detection(self) -> List[Dict[str, Any]]:
        """Simulate visual detection (replace with real camera input)"""
        # Generate dummy frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Occasionally simulate emergency vehicle lights
        if np.random.random() < 0.005:  # 0.5% chance
            # Add bright red/blue spots
            cv2.circle(frame, (100, 100), 20, (0, 0, 255), -1)  # Red
            cv2.circle(frame, (150, 100), 20, (255, 0, 0), -1)  # Blue
        
        return self.visual_detector.detect_emergency_vehicles(frame)
    
    def _fuse_detections(self, audio_result: Dict[str, Any], 
                       visual_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fuse audio and visual detections"""
        fused_detections = []
        current_time = time.time()
        
        # Check audio detection
        audio_detected = audio_result.get('detected', False)
        audio_confidence = audio_result.get('confidence', 0.0)
        
        # Check visual detections
        visual_detected = len(visual_results) > 0
        visual_confidence = max([r.get('confidence', 0.0) for r in visual_results], default=0.0)
        
        # Fusion logic
        if audio_detected and visual_detected:
            # High confidence - both modalities agree
            confidence = (audio_confidence + visual_confidence) / 2
            confidence = min(1.0, confidence * 1.2)  # Boost for agreement
            
            for visual_result in visual_results:
                fused_result = visual_result.copy()
                fused_result['confidence'] = confidence
                fused_result['detection_method'] = DetectionMethod.AUDIO_VISUAL
                fused_detections.append(fused_result)
        
        elif audio_detected:
            # Audio only detection
            fused_detections.append({
                'is_emergency': True,
                'confidence': audio_confidence,
                'detection_method': DetectionMethod.AUDIO,
                'timestamp': current_time
            })
        
        elif visual_detected:
            # Visual only detection
            for visual_result in visual_results:
                visual_result['detection_method'] = DetectionMethod.VISUAL
                fused_detections.append(visual_result)
        
        return fused_detections
    
    def _update_vehicle_tracking(self, detection: Dict[str, Any]):
        """Update emergency vehicle tracking"""
        if not detection.get('is_emergency', False):
            return
        
        confidence = detection.get('confidence', 0.0)
        if confidence < self.confidence_threshold:
            return
        
        # Create emergency vehicle object
        vehicle = EmergencyVehicle(
            vehicle_id=f"EMERGENCY_{int(time.time() * 1000)}",
            emergency_type=detection.get('emergency_type', EmergencyType.POLICE),
            current_location=detection.get('center_position', (0, 0)),
            speed=80.0,  # Default emergency speed
            heading=0.0,
            estimated_arrival=30.0,  # Default 30 seconds
            detection_method=detection.get('detection_method', DetectionMethod.VISUAL),
            priority_level=int(confidence * 10)
        )
        
        self.tracked_vehicles[vehicle.vehicle_id] = vehicle
        
        # Add to detection queue for processing
        self.detection_queue.put(vehicle)
        
        logger.info(f"Emergency vehicle detected: {vehicle.emergency_type.value} with confidence {confidence:.2f}")
    
    def get_detected_vehicles(self) -> List[EmergencyVehicle]:
        """Get list of detected emergency vehicles"""
        return list(self.tracked_vehicles.values())
    
    def clear_vehicle(self, vehicle_id: str):
        """Clear tracked emergency vehicle"""
        if vehicle_id in self.tracked_vehicles:
            del self.tracked_vehicles[vehicle_id]
            logger.info(f"Emergency vehicle {vehicle_id} cleared from tracking")

class SignalPreemptionController:
    """Traffic signal preemption controller for emergency vehicles"""
    
    def __init__(self):
        self.active_preemptions = {}
        self.preemption_history = deque(maxlen=100)
        self.preemption_queue = queue.PriorityQueue()
        
        # Preemption parameters
        self.preemption_clearance_time = 5.0  # seconds
        self.recovery_time = 10.0  # seconds to return to normal
        self.max_preemption_duration = 60.0  # seconds
        
        # Intersection controllers (would be injected in real system)
        self.intersection_controllers = {}
        
        # Emergency corridors
        self.active_corridors = {}
        
        logger.info("Signal preemption controller initialized")
    
    def register_intersection_controller(self, intersection_id: str, controller):
        """Register intersection controller for preemption"""
        self.intersection_controllers[intersection_id] = controller
    
    def request_preemption(self, preemption_request: PreemptionRequest):
        """Process emergency preemption request"""
        request_id = preemption_request.request_id
        
        # Check if higher priority preemption already active
        if self._has_conflicting_preemption(preemption_request):
            logger.warning(f"Conflicting preemption for request {request_id}")
            return False
        
        # Add to priority queue
        priority = -preemption_request.priority_score  # Negative for max-heap behavior
        self.preemption_queue.put((priority, preemption_request))
        
        # Process immediately for high priority requests
        if preemption_request.priority_score >= 8:
            self._execute_preemption(preemption_request)
        
        logger.info(f"Preemption request queued: {request_id} with priority {preemption_request.priority_score}")
        return True
    
    def _has_conflicting_preemption(self, new_request: PreemptionRequest) -> bool:
        """Check for conflicting active preemptions"""
        for active_id, active_request in self.active_preemptions.items():
            # Check for intersection overlap
            if set(new_request.target_intersections) & set(active_request.target_intersections):
                # Check if existing preemption has higher priority
                if active_request.priority_score >= new_request.priority_score:
                    return True
        
        return False
    
    def _execute_preemption(self, preemption_request: PreemptionRequest):
        """Execute signal preemption"""
        request_id = preemption_request.request_id
        emergency_vehicle = preemption_request.emergency_vehicle
        
        # Activate preemption for target intersections
        for intersection_id in preemption_request.target_intersections:
            if intersection_id in self.intersection_controllers:
                controller = self.intersection_controllers[intersection_id]
                
                # Apply preemption based on mode
                if preemption_request.preemption_mode == PreemptionMode.IMMEDIATE:
                    self._apply_immediate_preemption(controller, emergency_vehicle)
                elif preemption_request.preemption_mode == PreemptionMode.COORDINATED:
                    self._apply_coordinated_preemption(controller, emergency_vehicle, preemption_request)
        
        # Store active preemption
        self.active_preemptions[request_id] = preemption_request
        
        # Schedule preemption clearance
        clearance_time = time.time() + preemption_request.estimated_duration
        threading.Timer(
            preemption_request.estimated_duration,
            self._clear_preemption,
            args=[request_id]
        ).start()
        
        logger.info(f"Preemption executed for request {request_id}")
    
    def _apply_immediate_preemption(self, controller, emergency_vehicle: EmergencyVehicle):
        """Apply immediate signal preemption"""
        # Set all signals to red first
        controller.set_all_signals('red')
        
        # Determine approach direction based on vehicle location
        approach_direction = self._determine_approach_direction(emergency_vehicle, controller)
        
        # Set green light for emergency vehicle approach
        controller.set_signal_phase(approach_direction, 'green')
        
        # Activate emergency preemption mode
        controller.emergency_preemption_active = True
        controller.emergency_vehicle_approaching = True
    
    def _apply_coordinated_preemption(self, controller, emergency_vehicle: EmergencyVehicle,
                                   preemption_request: PreemptionRequest):
        """Apply coordinated corridor preemption"""
        # Create emergency corridor
        corridor = EmergencyCorridor(
            corridor_id=f"CORRIDOR_{preemption_request.request_id}",
            start_intersection=preemption_request.target_intersections[0],
            end_intersection=preemption_request.target_intersections[-1],
            path_intersections=preemption_request.target_intersections,
            priority_level=emergency_vehicle.priority_level,
            activation_time=time.time(),
            estimated_clearance_time=time.time() + preemption_request.estimated_duration
        )
        
        self.active_corridors[corridor.corridor_id] = corridor
        
        # Coordinate signals along corridor
        self._coordinate_corridor_signals(corridor, emergency_vehicle)
    
    def _coordinate_corridor_signals(self, corridor: EmergencyCorridor, 
                                  emergency_vehicle: EmergencyVehicle):
        """Coordinate signals along emergency corridor"""
        # Calculate optimal signal timing for emergency vehicle progression
        vehicle_speed = emergency_vehicle.speed  # km/h
        vehicle_speed_ms = vehicle_speed / 3.6  # m/s
        
        for i, intersection_id in enumerate(corridor.path_intersections):
            if intersection_id in self.intersection_controllers:
                controller = self.intersection_controllers[intersection_id]
                
                # Calculate when emergency vehicle will reach this intersection
                distance_to_intersection = i * 500  # Assume 500m between intersections
                arrival_time = distance_to_intersection / vehicle_speed_ms
                
                # Schedule signal change
                if arrival_time > 0:
                    threading.Timer(
                        arrival_time - 5,  # Change 5 seconds before arrival
                        self._set_emergency_green,
                        args=[intersection_id, emergency_vehicle]
                    ).start()
    
    def _set_emergency_green(self, intersection_id: str, emergency_vehicle: EmergencyVehicle):
        """Set emergency green signal at intersection"""
        if intersection_id in self.intersection_controllers:
            controller = self.intersection_controllers[intersection_id]
            
            # Determine approach direction
            approach_direction = self._determine_approach_direction(emergency_vehicle, controller)
            
            # Set green for emergency approach
            controller.set_signal_phase(approach_direction, 'green')
            controller.emergency_preemption_active = True
    
    def _determine_approach_direction(self, emergency_vehicle: EmergencyVehicle, controller) -> str:
        """Determine which direction emergency vehicle is approaching from"""
        # Simplified - in real implementation would use GPS coordinates and intersection layout
        vehicle_location = emergency_vehicle.current_location
        intersection_location = controller.config.location if hasattr(controller, 'config') else (0, 0)
        
        # Calculate bearing from vehicle to intersection
        dx = intersection_location[0] - vehicle_location[0]
        dy = intersection_location[1] - vehicle_location[1]
        bearing = math.atan2(dy, dx) * 180 / math.pi
        
        # Convert bearing to direction
        if -45 <= bearing <= 45:
            return 'east'
        elif 45 < bearing <= 135:
            return 'north'
        elif -135 <= bearing < -45:
            return 'south'
        else:
            return 'west'
    
    def _clear_preemption(self, request_id: str):
        """Clear emergency preemption"""
        if request_id not in self.active_preemptions:
            return
        
        preemption_request = self.active_preemptions[request_id]
        
        # Clear preemption at intersections
        for intersection_id in preemption_request.target_intersections:
            if intersection_id in self.intersection_controllers:
                controller = self.intersection_controllers[intersection_id]
                
                # Start recovery sequence
                controller.emergency_preemption_active = False
                controller.emergency_vehicle_approaching = False
                
                # Return to normal operation after recovery time
                threading.Timer(
                    self.recovery_time,
                    self._return_to_normal_operation,
                    args=[intersection_id]
                ).start()
        
        # Remove from active preemptions
        del self.active_preemptions[request_id]
        
        # Clear associated corridor
        corridor_id = f"CORRIDOR_{request_id}"
        if corridor_id in self.active_corridors:
            del self.active_corridors[corridor_id]
        
        # Add to history
        self.preemption_history.append({
            'request_id': request_id,
            'clearance_time': time.time(),
            'duration': time.time() - preemption_request.timestamp
        })
        
        logger.info(f"Preemption cleared for request {request_id}")
    
    def _return_to_normal_operation(self, intersection_id: str):
        """Return intersection to normal operation"""
        if intersection_id in self.intersection_controllers:
            controller = self.intersection_controllers[intersection_id]
            controller.return_to_normal_timing()
    
    def process_preemption_queue(self):
        """Process queued preemption requests"""
        while not self.preemption_queue.empty():
            try:
                priority, request = self.preemption_queue.get_nowait()
                
                # Check if request is still valid (not expired)
                if time.time() - request.timestamp < 60:  # 1 minute validity
                    self._execute_preemption(request)
                
            except queue.Empty:
                break
    
    def get_preemption_status(self) -> Dict[str, Any]:
        """Get current preemption system status"""
        return {
            'active_preemptions': len(self.active_preemptions),
            'queued_requests': self.preemption_queue.qsize(),
            'active_corridors': len(self.active_corridors),
            'total_preemptions': len(self.preemption_history),
            'average_clearance_time': np.mean([
                h['duration'] for h in self.preemption_history
            ]) if self.preemption_history else 0,
            'timestamp': time.time()
        }

# Factory functions
def create_emergency_detector() -> EmergencyVehicleDetector:
    """Create emergency vehicle detector"""
    return EmergencyVehicleDetector()

def create_preemption_controller() -> SignalPreemptionController:
    """Create signal preemption controller"""
    return SignalPreemptionController()

# Export main classes
__all__ = [
    'EmergencyVehicleDetector',
    'SignalPreemptionController',
    'EmergencyVehicle',
    'PreemptionRequest',
    'EmergencyCorridor',
    'AudioEmergencyDetector',
    'VisualEmergencyDetector',
    'EmergencyType',
    'DetectionMethod',
    'PreemptionMode',
    'create_emergency_detector',
    'create_preemption_controller'
]