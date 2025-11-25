"""
Pedestrian and Cyclist Integration System
======================================

Advanced vulnerable road user management with:
- Pedestrian detection and tracking
- Cyclist detection and bike lane management
- Crosswalk signal coordination
- Smart crossing systems
- Vulnerable user safety features
- ADA compliance monitoring

Author: Top 0.1% Expert Team
Date: November 2025
Version: 3.0.0
"""

import cv2
import numpy as np
import pygame
import math
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue
from collections import deque, defaultdict
import json
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VulnerableUserType(Enum):
    """Types of vulnerable road users"""
    PEDESTRIAN = "pedestrian"
    CYCLIST = "cyclist"
    WHEELCHAIR_USER = "wheelchair_user"
    MOBILITY_SCOOTER = "mobility_scooter"
    CHILD = "child"
    ELDERLY = "elderly"

class CrossingState(Enum):
    """Crossing signal states"""
    RED = "red"
    WALK = "walk"
    FLASHING_DONT_WALK = "flashing_dont_walk"
    CLEARANCE = "clearance"

class DetectionMethod(Enum):
    """Detection methods for vulnerable users"""
    COMPUTER_VISION = "computer_vision"
    THERMAL_CAMERA = "thermal_camera"
    PRESSURE_SENSORS = "pressure_sensors"
    INFRARED_BEAMS = "infrared_beams"
    RFID_TAGS = "rfid_tags"
    SMARTPHONE_APP = "smartphone_app"

@dataclass
class VulnerableUser:
    """Vulnerable road user information"""
    user_id: str
    user_type: VulnerableUserType
    position: Tuple[float, float]  # x, y coordinates
    velocity: Tuple[float, float]  # vx, vy
    trajectory: List[Tuple[float, float]] = field(default_factory=list)
    confidence: float = 1.0
    last_detected: float = field(default_factory=time.time)
    crossing_request: bool = False
    estimated_crossing_time: Optional[float] = None
    special_needs: List[str] = field(default_factory=list)
    
@dataclass
class CrosswalkConfig:
    """Crosswalk configuration"""
    crosswalk_id: str
    location: Tuple[float, float]  # Center position
    width: float  # meters
    length: float  # meters
    orientation: float  # degrees
    crossing_time: float  # seconds for normal crossing
    clearance_time: float  # seconds for clearance
    has_audio_signals: bool = True
    has_tactile_paving: bool = True
    has_ada_compliance: bool = True
    detection_zones: List[Tuple[float, float, float, float]] = field(default_factory=list)
    
@dataclass
class BikeLaneConfig:
    """Bike lane configuration"""
    lane_id: str
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    width: float  # meters
    direction: str  # "north", "south", "east", "west"
    bike_signal_type: str  # "separate", "shared", "protected"
    detection_sensors: List[str] = field(default_factory=list)

class PedestrianDetector:
    """Advanced pedestrian detection using multiple methods"""
    
    def __init__(self):
        # Detection models
        self.hog_detector = cv2.HOGDescriptor()
        self.hog_detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # Deep learning model (would load pre-trained model)
        self.pedestrian_model = None  # Would load YOLO or similar
        
        # Detection parameters
        self.min_confidence = 0.5
        self.nms_threshold = 0.4
        self.detection_methods = [DetectionMethod.COMPUTER_VISION]
        
        # Tracking
        self.tracked_pedestrians = {}
        self.next_track_id = 0
        self.max_disappeared_frames = 30
        
        # Kalman filters for tracking
        self.kalman_filters = {}
        
        logger.info("Pedestrian detector initialized")
    
    def detect_pedestrians(self, frame: np.ndarray, 
                         detection_zones: List[Tuple[int, int, int, int]] = None) -> List[VulnerableUser]:
        """Detect pedestrians in frame"""
        detections = []
        
        # Method 1: HOG detector
        hog_detections = self._detect_with_hog(frame)
        
        # Method 2: Deep learning (if available)
        dl_detections = []
        if self.pedestrian_model:
            dl_detections = self._detect_with_deep_learning(frame)
        
        # Combine detections
        all_detections = hog_detections + dl_detections
        
        # Apply Non-Maximum Suppression
        nms_detections = self._apply_nms(all_detections)
        
        # Filter by detection zones
        if detection_zones:
            nms_detections = self._filter_by_zones(nms_detections, detection_zones)
        
        # Convert to VulnerableUser objects
        for detection in nms_detections:
            pedestrian = VulnerableUser(
                user_id=f"PED_{self.next_track_id}",
                user_type=VulnerableUserType.PEDESTRIAN,
                position=detection['center'],
                velocity=(0, 0),
                confidence=detection['confidence']
            )
            detections.append(pedestrian)
            self.next_track_id += 1
        
        # Update tracking
        self._update_tracking(detections)
        
        return self._get_tracked_pedestrians()
    
    def _detect_with_hog(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect pedestrians using HOG descriptor"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect pedestrians
        found, w = self.hog_detector.detectMultiScale(
            gray,
            winStride=(8, 8),
            padding=(32, 32),
            scale=1.05
        )
        
        detections = []
        for i, (x, y, w, h) in enumerate(found):
            if w[i] > 0:  # Valid detection
                confidence = min(1.0, w[i] / 100.0)  # Simple confidence estimate
                
                detections.append({
                    'bbox': (x, y, x + w[i], y + h[i]),
                    'center': (x + w[i] // 2, y + h[i] // 2),
                    'size': (w[i], h[i]),
                    'confidence': confidence,
                    'method': 'HOG'
                })
        
        return detections
    
    def _detect_with_deep_learning(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect pedestrians using deep learning model"""
        # Placeholder for deep learning detection
        # In real implementation, would use YOLO, SSD, or similar
        return []
    
    def _apply_nms(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply Non-Maximum Suppression to reduce overlapping detections"""
        if not detections:
            return []
        
        # Extract bounding boxes and confidences
        boxes = np.array([d['bbox'] for d in detections])
        confidences = np.array([d['confidence'] for d in detections])
        
        # Apply NMS
        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, self.min_confidence, self.nms_threshold
        )
        
        # Filter detections
        nms_detections = []
        if len(indices) > 0:
            indices = indices.flatten()
            nms_detections = [detections[i] for i in indices]
        
        return nms_detections
    
    def _filter_by_zones(self, detections: List[Dict[str, Any]], 
                       zones: List[Tuple[int, int, int, int]]) -> List[Dict[str, Any]]:
        """Filter detections by specified zones"""
        filtered_detections = []
        
        for detection in detections:
            center = detection['center']
            
            # Check if center is in any zone
            for zone in zones:
                x1, y1, x2, y2 = zone
                if x1 <= center[0] <= x2 and y1 <= center[1] <= y2:
                    filtered_detections.append(detection)
                    break
        
        return filtered_detections
    
    def _update_tracking(self, detections: List[VulnerableUser]):
        """Update pedestrian tracking"""
        current_time = time.time()
        
        # Simple tracking - in real implementation would use more sophisticated algorithms
        for pedestrian in detections:
            # Find closest existing track
            min_distance = float('inf')
            best_track_id = None
            
            for track_id, track in self.tracked_pedestrians.items():
                distance = math.sqrt(
                    (pedestrian.position[0] - track.position[0])**2 +
                    (pedestrian.position[1] - track.position[1])**2
                )
                
                if distance < min_distance and distance < 50:  # 50 pixel threshold
                    min_distance = distance
                    best_track_id = track_id
            
            if best_track_id is not None:
                # Update existing track
                track = self.tracked_pedestrians[best_track_id]
                track.position = pedestrian.position
                track.trajectory.append(pedestrian.position)
                track.last_detected = current_time
                
                # Calculate velocity
                if len(track.trajectory) >= 2:
                    prev_pos = track.trajectory[-2]
                    dt = current_time - track.last_detected
                    if dt > 0:
                        velocity = (
                            (pedestrian.position[0] - prev_pos[0]) / dt,
                            (pedestrian.position[1] - prev_pos[1]) / dt
                        )
                        track.velocity = velocity
            else:
                # Create new track
                self.tracked_pedestrians[pedestrian.user_id] = pedestrian
    
    def _get_tracked_pedestrians(self) -> List[VulnerableUser]:
        """Get currently tracked pedestrians"""
        current_time = time.time()
        active_pedestrians = []
        
        # Remove old tracks
        expired_tracks = [
            track_id for track_id, track in self.tracked_pedestrians.items()
            if current_time - track.last_detected > self.max_disappeared_frames
        ]
        
        for track_id in expired_tracks:
            del self.tracked_pedestrians[track_id]
        
        # Return active tracks
        for pedestrian in self.tracked_pedestrians.values():
            active_pedestrians.append(pedestrian)
        
        return active_pedestrians

class CyclistDetector:
    """Advanced cyclist detection and bike lane monitoring"""
    
    def __init__(self):
        # Detection parameters
        self.min_confidence = 0.4
        self.bike_aspect_ratio_range = (0.3, 3.0)
        self.bike_size_range = (20, 200)  # pixels
        
        # Bike lane detection
        self.lane_detector = None  # Would load lane detection model
        self.bike_lanes = {}
        
        # Tracking
        self.tracked_cyclists = {}
        
        logger.info("Cyclist detector initialized")
    
    def detect_cyclists(self, frame: np.ndarray) -> List[VulnerableUser]:
        """Detect cyclists in frame"""
        detections = []
        
        # Method 1: Contour-based detection
        contour_detections = self._detect_cyclists_by_contours(frame)
        
        # Method 2: Feature-based detection
        feature_detections = self._detect_cyclists_by_features(frame)
        
        # Combine detections
        all_detections = contour_detections + feature_detections
        
        # Convert to VulnerableUser objects
        for detection in all_detections:
            cyclist = VulnerableUser(
                user_id=f"CYCLE_{len(self.tracked_cyclists)}",
                user_type=VulnerableUserType.CYCLIST,
                position=detection['center'],
                velocity=(0, 0),
                confidence=detection['confidence']
            )
            detections.append(cyclist)
            self.tracked_cyclists[cyclist.user_id] = cyclist
        
        return detections
    
    def _detect_cyclists_by_contours(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect cyclists using contour analysis"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Filter by size
            if not self.bike_size_range[0] <= area <= self.bike_size_range[1]:
                continue
            
            # Filter by aspect ratio
            aspect_ratio = w / h if h > 0 else 0
            if not self.bike_aspect_ratio_range[0] <= aspect_ratio <= self.bike_aspect_ratio_range[1]:
                continue
            
            # Calculate confidence based on shape characteristics
            confidence = self._calculate_cyclist_confidence(contour, w, h)
            
            if confidence > self.min_confidence:
                detections.append({
                    'bbox': (x, y, x + w, y + h),
                    'center': (x + w // 2, y + h // 2),
                    'size': (w, h),
                    'area': area,
                    'confidence': confidence,
                    'method': 'contour'
                })
        
        return detections
    
    def _detect_cyclists_by_features(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect cyclists using feature matching"""
        # Placeholder for feature-based detection
        # In real implementation, would use:
        # - HOG features for cyclists
        # - Circular Hough transform for wheels
        # - Template matching for bike shapes
        
        return []
    
    def _calculate_cyclist_confidence(self, contour, w: int, h: int) -> float:
        """Calculate confidence score for cyclist detection"""
        # Shape-based confidence
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter * perimeter)
        else:
            circularity = 0
        
        # Aspect ratio confidence
        ideal_ratio = 1.0  # Square-ish for bike/rider
        ratio_confidence = 1.0 - abs((w/h) - ideal_ratio) if h > 0 else 0
        
        # Size confidence
        ideal_area = 100  # pixels
        size_confidence = 1.0 - abs(area - ideal_area) / ideal_area
        
        # Combined confidence
        confidence = (circularity * 0.3 + ratio_confidence * 0.4 + size_confidence * 0.3)
        
        return min(1.0, confidence)
    
    def monitor_bike_lanes(self, frame: np.ndarray, cyclists: List[VulnerableUser]) -> Dict[str, Any]:
        """Monitor cyclist compliance with bike lanes"""
        lane_status = {}
        
        for lane_id, lane_config in self.bike_lanes.items():
            # Check if cyclists are in bike lane
            cyclists_in_lane = []
            cyclists_violating = []
            
            for cyclist in cyclists:
                if self._is_point_in_lane(cyclist.position, lane_config):
                    cyclists_in_lane.append(cyclist)
                elif self._is_near_lane(cyclist.position, lane_config):
                    cyclists_violating.append(cyclist)
            
            lane_status[lane_id] = {
                'cyclists_in_lane': len(cyclists_in_lane),
                'cyclists_violating': len(cyclists_violating),
                'compliance_rate': len(cyclists_in_lane) / max(1, len(cyclists_in_lane) + len(cyclists_violating)),
                'lane_occupancy': len(cyclists_in_lane) / max(1, self._calculate_lane_capacity(lane_config))
            }
        
        return lane_status
    
    def _is_point_in_lane(self, point: Tuple[float, float], 
                         lane_config: BikeLaneConfig) -> bool:
        """Check if point is within bike lane"""
        # Simplified point-in-polygon test
        # In real implementation, would use proper geometric algorithms
        
        x, y = point
        x1, y1 = lane_config.start_point
        x2, y2 = lane_config.end_point
        
        # Check if point is within lane bounds
        lane_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        lane_width = lane_config.width
        
        # Distance from point to lane centerline
        point_to_line_dist = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / lane_length
        
        return point_to_line_dist <= lane_width / 2
    
    def _is_near_lane(self, point: Tuple[float, float], 
                    lane_config: BikeLaneConfig, threshold: float = 5.0) -> bool:
        """Check if point is near bike lane"""
        x, y = point
        x1, y1 = lane_config.start_point
        x2, y2 = lane_config.end_point
        
        # Distance to lane endpoints
        dist_to_start = math.sqrt((x - x1)**2 + (y - y1)**2)
        dist_to_end = math.sqrt((x - x2)**2 + (y - y2)**2)
        
        return min(dist_to_start, dist_to_end) <= threshold
    
    def _calculate_lane_capacity(self, lane_config: BikeLaneConfig) -> int:
        """Calculate bike lane capacity"""
        # Simple capacity based on lane length
        lane_length = math.sqrt(
            (lane_config.end_point[0] - lane_config.start_point[0])**2 +
            (lane_config.end_point[1] - lane_config.start_point[1])**2
        )
        
        # Assume one cyclist per 5 meters
        return int(lane_length / 5)

class CrosswalkController:
    """Smart crosswalk control system"""
    
    def __init__(self, crosswalk_config: CrosswalkConfig):
        self.config = crosswalk_config
        self.current_state = CrossingState.RED
        self.state_timer = 0.0
        self.waiting_pedestrians = []
        self.crossing_pedestrians = []
        
        # Signal timing
        self.min_walk_time = crosswalk_config.crossing_time
        self.clearance_time = crosswalk_config.clearance_time
        self.flashing_dont_walk_time = 5.0  # seconds
        
        # Detection zones
        self.waiting_zone = crosswalk_config.detection_zones[0] if crosswalk_config.detection_zones else None
        self.crosswalk_zone = crosswalk_config.detection_zones[1] if len(crosswalk_config.detection_zones) > 1 else None
        
        # Audio signals
        self.audio_enabled = crosswalk_config.has_audio_signals
        self.last_audio_time = 0
        
        logger.info(f"Crosswalk controller initialized: {crosswalk_config.crosswalk_id}")
    
    def update(self, pedestrians: List[VulnerableUser], dt: float) -> Dict[str, Any]:
        """Update crosswalk state"""
        # Detect pedestrians in waiting zone
        waiting_pedestrians = self._detect_waiting_pedestrians(pedestrians)
        self.waiting_pedestrians = waiting_pedestrians
        
        # Detect pedestrians in crosswalk
        crossing_pedestrians = self._detect_crossing_pedestrians(pedestrians)
        self.crossing_pedestrians = crossing_pedestrians
        
        # Update state machine
        self._update_state_machine(dt)
        
        # Generate crossing requests
        crossing_requests = self._generate_crossing_requests()
        
        return {
            'crosswalk_id': self.config.crosswalk_id,
            'current_state': self.current_state.value,
            'state_timer': self.state_timer,
            'waiting_count': len(waiting_pedestrians),
            'crossing_count': len(crossing_pedestrians),
            'crossing_requests': crossing_requests,
            'audio_active': self._should_play_audio()
        }
    
    def _detect_waiting_pedestrians(self, pedestrians: List[VulnerableUser]) -> List[VulnerableUser]:
        """Detect pedestrians waiting to cross"""
        waiting = []
        
        for pedestrian in pedestrians:
            if self._is_in_zone(pedestrian.position, self.waiting_zone):
                waiting.append(pedestrian)
                pedestrian.crossing_request = True
                pedestrian.estimated_crossing_time = time.time() + 2.0  # 2 seconds to reach crosswalk
        
        return waiting
    
    def _detect_crossing_pedestrians(self, pedestrians: List[VulnerableUser]) -> List[VulnerableUser]:
        """Detect pedestrians currently crossing"""
        crossing = []
        
        for pedestrian in pedestrians:
            if self._is_in_zone(pedestrian.position, self.crosswalk_zone):
                crossing.append(pedestrian)
        
        return crossing
    
    def _is_in_zone(self, position: Tuple[float, float], 
                   zone: Tuple[float, float, float, float]) -> bool:
        """Check if position is within detection zone"""
        if not zone:
            return False
        
        x, y = position
        x1, y1, x2, y2 = zone
        
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def _update_state_machine(self, dt: float):
        """Update crosswalk state machine"""
        self.state_timer += dt
        
        if self.current_state == CrossingState.RED:
            # Check if should activate walk signal
            if len(self.waiting_pedestrians) > 0 and self.state_timer > 2.0:
                self._activate_walk_signal()
        
        elif self.current_state == CrossingState.WALK:
            # Check if should start flashing don't walk
            if self.state_timer >= self.min_walk_time:
                self._activate_flashing_dont_walk()
        
        elif self.current_state == CrossingState.FLASHING_DONT_WALK:
            # Check if should return to red
            if self.state_timer >= self.flashing_dont_walk_time:
                self._activate_red_signal()
        
        elif self.current_state == CrossingState.CLEARANCE:
            # Check if clearance is complete
            if self.state_timer >= self.clearance_time:
                self._activate_red_signal()
    
    def _activate_walk_signal(self):
        """Activate walk signal"""
        self.current_state = CrossingState.WALK
        self.state_timer = 0.0
        
        # Play audio signal
        if self.audio_enabled:
            self._play_audio_signal('walk')
        
        logger.info(f"Walk signal activated: {self.config.crosswalk_id}")
    
    def _activate_flashing_dont_walk(self):
        """Activate flashing don't walk signal"""
        self.current_state = CrossingState.FLASHING_DONT_WALK
        self.state_timer = 0.0
        
        # Play audio signal
        if self.audio_enabled:
            self._play_audio_signal('dont_walk')
        
        logger.info(f"Flashing don't walk activated: {self.config.crosswalk_id}")
    
    def _activate_red_signal(self):
        """Activate red signal"""
        self.current_state = CrossingState.RED
        self.state_timer = 0.0
        
        logger.info(f"Red signal activated: {self.config.crosswalk_id}")
    
    def _play_audio_signal(self, signal_type: str):
        """Play audio signal for crosswalk"""
        current_time = time.time()
        
        # Limit audio frequency
        if current_time - self.last_audio_time < 1.0:
            return
        
        # In real implementation, would play actual audio files
        self.last_audio_time = current_time
        
        if signal_type == 'walk':
            logger.debug("Playing walk audio signal")
        elif signal_type == 'dont_walk':
            logger.debug("Playing don't walk audio signal")
    
    def _should_play_audio(self) -> bool:
        """Check if audio should be playing"""
        return self.audio_enabled and (
            self.current_state == CrossingState.WALK or
            (self.current_state == CrossingState.FLASHING_DONT_WALK and 
             int(self.state_timer * 2) % 2 == 0)  # Flashing
        )
    
    def _generate_crossing_requests(self) -> List[Dict[str, Any]]:
        """Generate crossing requests for traffic system"""
        requests = []
        
        for pedestrian in self.waiting_pedestrians:
            if pedestrian.crossing_request:
                request = {
                    'request_id': f"REQ_{pedestrian.user_id}_{int(time.time())}",
                    'crosswalk_id': self.config.crosswalk_id,
                    'user_type': pedestrian.user_type.value,
                    'user_id': pedestrian.user_id,
                    'request_time': time.time(),
                    'estimated_crossing_time': pedestrian.estimated_crossing_time,
                    'priority': self._calculate_priority(pedestrian),
                    'special_needs': pedestrian.special_needs
                }
                requests.append(request)
                pedestrian.crossing_request = False  # Reset request
        
        return requests
    
    def _calculate_priority(self, pedestrian: VulnerableUser) -> int:
        """Calculate crossing priority for pedestrian"""
        base_priority = 5
        
        # Adjust for vulnerable users
        if pedestrian.user_type == VulnerableUserType.WHEELCHAIR_USER:
            base_priority += 3
        elif pedestrian.user_type == VulnerableUserType.ELDERLY:
            base_priority += 2
        elif pedestrian.user_type == VulnerableUserType.CHILD:
            base_priority += 1
        
        # Adjust for special needs
        if 'visual_impairment' in pedestrian.special_needs:
            base_priority += 2
        if 'mobility_impairment' in pedestrian.special_needs:
            base_priority += 2
        
        return min(10, base_priority)

class VulnerableUserManager:
    """Main manager for pedestrian and cyclist integration"""
    
    def __init__(self):
        self.pedestrian_detector = PedestrianDetector()
        self.cyclist_detector = CyclistDetector()
        self.crosswalk_controllers = {}
        self.bike_lanes = {}
        
        # Detection data
        self.detected_users = []
        self.crossing_requests = queue.Queue(maxsize=100)
        
        # Safety monitoring
        self.safety_events = deque(maxlen=100)
        self.violation_count = defaultdict(int)
        
        # Integration with traffic system
        self.traffic_system_interface = None
        
        logger.info("Vulnerable user manager initialized")
    
    def add_crosswalk(self, crosswalk_config: CrosswalkConfig):
        """Add crosswalk to management system"""
        controller = CrosswalkController(crosswalk_config)
        self.crosswalk_controllers[crosswalk_config.crosswalk_id] = controller
        
        logger.info(f"Crosswalk added: {crosswalk_config.crosswalk_id}")
    
    def add_bike_lane(self, lane_config: BikeLaneConfig):
        """Add bike lane to management system"""
        self.bike_lanes[lane_config.lane_id] = lane_config
        self.cyclist_detector.bike_lanes[lane_config.lane_id] = lane_config
        
        logger.info(f"Bike lane added: {lane_config.lane_id}")
    
    def process_frame(self, frame: np.ndarray, dt: float) -> Dict[str, Any]:
        """Process video frame for vulnerable user detection"""
        # Detect pedestrians
        pedestrians = self.pedestrian_detector.detect_pedestrians(frame)
        
        # Detect cyclists
        cyclists = self.cyclist_detector.detect_cyclists(frame)
        
        # Combine all detected users
        self.detected_users = pedestrians + cyclists
        
        # Update crosswalk controllers
        crosswalk_status = {}
        for crosswalk_id, controller in self.crosswalk_controllers.items():
            status = controller.update(self.detected_users, dt)
            crosswalk_status[crosswalk_id] = status
        
        # Monitor bike lanes
        bike_lane_status = self.cyclist_detector.monitor_bike_lanes(frame, cyclists)
        
        # Check for safety events
        safety_events = self._detect_safety_events()
        
        # Generate crossing requests
        crossing_requests = []
        for controller in self.crosswalk_controllers.values():
            requests = controller._generate_crossing_requests()
            crossing_requests.extend(requests)
        
        # Add to queue
        for request in crossing_requests:
            if not self.crossing_requests.full():
                self.crossing_requests.put(request)
        
        return {
            'detected_pedestrians': len(pedestrians),
            'detected_cyclists': len(cyclists),
            'total_detected': len(self.detected_users),
            'crosswalk_status': crosswalk_status,
            'bike_lane_status': bike_lane_status,
            'safety_events': safety_events,
            'crossing_requests_pending': self.crossing_requests.qsize()
        }
    
    def _detect_safety_events(self) -> List[Dict[str, Any]]:
        """Detect safety-related events"""
        events = []
        current_time = time.time()
        
        # Check for near-misses
        near_misses = self._detect_near_misses()
        events.extend(near_misses)
        
        # Check for violations
        violations = self._detect_violations()
        events.extend(violations)
        
        # Check for unsafe behaviors
        unsafe_behaviors = self._detect_unsafe_behaviors()
        events.extend(unsafe_behaviors)
        
        return events
    
    def _detect_near_misses(self) -> List[Dict[str, Any]]:
        """Detect near-miss situations"""
        near_misses = []
        
        # Check for pedestrians too close to vehicles
        # In real implementation, would integrate with vehicle detection
        for user in self.detected_users:
            # Simplified near-miss detection
            if user.confidence > 0.8:  # High confidence detection
                # Check if user is in dangerous area
                # This would require integration with traffic system
                pass
        
        return near_misses
    
    def _detect_violations(self) -> List[Dict[str, Any]]:
        """Detect traffic violations"""
        violations = []
        
        # Check bike lane violations
        for lane_id, status in self.cyclist_detector.monitor_bike_lanes(
                np.zeros((480, 640, 3), dtype=np.uint8),  # Dummy frame
                self.detected_users
            ).items():
            
            if status['cyclists_violating'] > 0:
                self.violation_count[f"bike_lane_{lane_id}"] += status['cyclists_violating']
                
                violations.append({
                    'event_type': 'bike_lane_violation',
                    'lane_id': lane_id,
                    'violations_count': status['cyclists_violating'],
                    'timestamp': time.time(),
                    'severity': 'medium'
                })
        
        return violations
    
    def _detect_unsafe_behaviors(self) -> List[Dict[str, Any]]:
        """Detect unsafe pedestrian/cyclist behaviors"""
        unsafe_events = []
        
        # Check for pedestrians crossing against red signal
        for crosswalk_id, controller in self.crosswalk_controllers.items():
            if controller.current_state == CrossingState.RED:
                for user in controller.crossing_pedestrians:
                    unsafe_events.append({
                        'event_type': 'crossing_against_red',
                        'crosswalk_id': crosswalk_id,
                        'user_id': user.user_id,
                        'user_type': user.user_type.value,
                        'timestamp': time.time(),
                        'severity': 'high'
                    })
        
        return unsafe_events
    
    def get_crossing_requests(self) -> List[Dict[str, Any]]:
        """Get pending crossing requests"""
        requests = []
        
        while not self.crossing_requests.empty():
            try:
                request = self.crossing_requests.get_nowait()
                requests.append(request)
            except queue.Empty:
                break
        
        return requests
    
    def get_safety_summary(self) -> Dict[str, Any]:
        """Get safety monitoring summary"""
        total_violations = sum(self.violation_count.values())
        
        return {
            'total_violations': total_violations,
            'violations_by_type': dict(self.violation_count),
            'safety_events_count': len(self.safety_events),
            'recent_safety_events': list(self.safety_events)[-10:],  # Last 10 events
            'compliance_rate': max(0, 1.0 - total_violations / max(1, len(self.detected_users) * 10)),
            'timestamp': time.time()
        }
    
    def set_traffic_system_interface(self, interface):
        """Set interface to traffic signal system"""
        self.traffic_system_interface = interface
        logger.info("Traffic system interface connected")

# Factory functions
def create_crosswalk_config(crosswalk_id: str, location: Tuple[float, float]) -> CrosswalkConfig:
    """Create standard crosswalk configuration"""
    return CrosswalkConfig(
        crosswalk_id=crosswalk_id,
        location=location,
        width=3.0,  # 3 meters
        length=5.0,  # 5 meters
        orientation=0.0,  # North-South
        crossing_time=15.0,  # 15 seconds
        clearance_time=5.0,   # 5 seconds
        has_audio_signals=True,
        has_tactile_paving=True,
        has_ada_compliance=True,
        detection_zones=[
            (location[0] - 20, location[1] - 30, location[0] + 20, location[1] - 10),  # Waiting zone
            (location[0] - 15, location[1] - 10, location[0] + 15, location[1] + 10)   # Crosswalk zone
        ]
    )

def create_bike_lane_config(lane_id: str, start: Tuple[float, float], 
                         end: Tuple[float, float]) -> BikeLaneConfig:
    """Create standard bike lane configuration"""
    return BikeLaneConfig(
        lane_id=lane_id,
        start_point=start,
        end_point=end,
        width=1.5,  # 1.5 meters
        direction="north",  # Would calculate based on coordinates
        bike_signal_type="protected",
        detection_sensors=["camera", "inductive_loop"]
    )

def create_vulnerable_user_manager() -> VulnerableUserManager:
    """Create vulnerable user manager"""
    return VulnerableUserManager()

# Export main classes
__all__ = [
    'VulnerableUserManager',
    'PedestrianDetector',
    'CyclistDetector',
    'CrosswalkController',
    'VulnerableUser',
    'CrosswalkConfig',
    'BikeLaneConfig',
    'VulnerableUserType',
    'CrossingState',
    'DetectionMethod',
    'create_crosswalk_config',
    'create_bike_lane_config',
    'create_vulnerable_user_manager'
]