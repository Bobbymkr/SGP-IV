"""
Optical Flow for Speed Estimation Module

Implements advanced optical flow algorithms for vehicle speed estimation
and motion analysis in traffic scenarios.
"""

import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from collections import defaultdict, deque
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class FlowVector:
    """Optical flow vector"""
    x: float
    y: float
    confidence: float
    magnitude: float
    angle: float


@dataclass
class VehicleSpeed:
    """Vehicle speed estimation result"""
    vehicle_id: int
    bbox: Tuple[int, int, int, int]
    speed_2d: float  # pixels per second
    speed_3d: Optional[float] = None  # meters per second
    direction: Optional[float] = None  # angle in radians
    confidence: float = 0.0
    trajectory: List[Tuple[float, float]] = None


class OpticalFlowCalculator:
    """Base class for optical flow calculation"""
    
    def __init__(self):
        self.prev_gray = None
        self.prev_points = None
        
    def calculate_flow(self, current_frame: np.ndarray, 
                      prev_frame: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate optical flow between frames"""
        raise NotImplementedError


class LKOpticalFlow(OpticalFlowCalculator):
    """Lucas-Kanade optical flow"""
    
    def __init__(self, max_corners: int = 1000, quality_level: float = 0.01, 
                 min_distance: float = 10.0, block_size: int = 3):
        super().__init__()
        self.max_corners = max_corners
        self.quality_level = quality_level
        self.min_distance = min_distance
        self.block_size = block_size
        
        # LK parameters
        self.lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )
    
    def calculate_flow(self, current_frame: np.ndarray, 
                      prev_frame: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate Lucas-Kanade optical flow"""
        current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        
        if prev_frame is not None:
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        elif self.prev_gray is not None:
            prev_gray = self.prev_gray
        else:
            # First frame - detect features
            self.prev_gray = current_gray
            self.prev_points = cv2.goodFeaturesToTrack(
                current_gray, self.max_corners, self.quality_level, self.min_distance, 
                blockSize=self.block_size
            )
            return np.array([]), np.array([])
        
        # Calculate optical flow
        if self.prev_points is not None and len(self.prev_points) > 0:
            current_points, status, err = cv2.calcOpticalFlowPyrLK(
                prev_gray, current_gray, self.prev_points, None, **self.lk_params
            )
            
            # Select good points
            good_current = current_points[status == 1]
            good_prev = self.prev_points[status == 1]
            
            # Update for next iteration
            self.prev_gray = current_gray
            self.prev_points = good_current.reshape(-1, 1, 2)
            
            return good_current, good_prev
        else:
            # Detect new features
            self.prev_gray = current_gray
            self.prev_points = cv2.goodFeaturesToTrack(
                current_gray, self.max_corners, self.quality_level, self.min_distance,
                blockSize=self.block_size
            )
            return np.array([]), np.array([])
    
    def detect_features(self, gray: np.ndarray, 
                       mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Detect good features to track"""
        return cv2.goodFeaturesToTrack(
            gray, self.max_corners, self.quality_level, self.min_distance,
            mask=mask, blockSize=self.block_size
        )


class FarnebackOpticalFlow(OpticalFlowCalculator):
    """Dense Farneback optical flow"""
    
    def __init__(self, pyr_scale: float = 0.5, levels: int = 3, 
                 winsize: int = 15, iterations: int = 3, 
                 poly_n: int = 5, poly_sigma: float = 1.2, 
                 flags: int = 0):
        super().__init__()
        self.pyr_scale = pyr_scale
        self.levels = levels
        self.winsize = winsize
        self.iterations = iterations
        self.poly_n = poly_n
        self.poly_sigma = poly_sigma
        self.flags = flags
    
    def calculate_flow(self, current_frame: np.ndarray, 
                      prev_frame: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate dense Farneback optical flow"""
        current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        
        if prev_frame is not None:
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        elif self.prev_gray is not None:
            prev_gray = self.prev_gray
        else:
            self.prev_gray = current_gray
            return np.array([]), np.array([])
        
        # Calculate dense flow
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, current_gray, None, 
            self.pyr_scale, self.levels, self.winsize, 
            self.iterations, self.poly_n, self.poly_sigma, self.flags
        )
        
        self.prev_gray = current_gray
        
        # Create coordinate grids
        h, w = flow.shape[:2]
        y, x = np.mgrid[0:h, 0:w]
        
        current_points = np.column_stack([x.ravel(), y.ravel()])
        flow_vectors = flow.reshape(-1, 2)
        prev_points = current_points - flow_vectors
        
        return current_points, prev_points


class DeepOpticalFlow(nn.Module):
    """Deep learning based optical flow (RAFT-like)"""
    
    def __init__(self, hidden_dim: int = 128):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        # Feature extractor
        self.feature_extractor = nn.Sequential(
            nn.Conv2d(6, 64, 7, stride=2, padding=3),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 5, stride=2, padding=2),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 256, 5, stride=2, padding=2),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )
        
        # Flow predictor
        self.flow_predictor = nn.Sequential(
            nn.Conv2d(256, hidden_dim, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden_dim, hidden_dim, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden_dim, 2, 1),
        )
        
    def forward(self, img1: torch.Tensor, img2: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # Concatenate images
        x = torch.cat([img1, img2], dim=1)
        
        # Extract features
        features = self.feature_extractor(x)
        
        # Predict flow
        flow = self.flow_predictor(features)
        
        # Upsample to original resolution
        flow = F.interpolate(flow, size=img1.shape[2:], mode='bilinear', align_corners=False)
        
        return flow


class SpeedEstimator:
    """Vehicle speed estimation from optical flow"""
    
    def __init__(self, camera_matrix: np.ndarray, 
                 fps: float = 30.0, 
                 pixel_to_meter: float = 0.1):
        self.camera_matrix = camera_matrix
        self.fps = fps
        self.pixel_to_meter = pixel_to_meter
        
        # Vehicle tracking
        self.vehicle_tracks = defaultdict(lambda: deque(maxlen=10))
        self.vehicle_id_counter = 0
        
        # Speed smoothing
        self.speed_history = defaultdict(lambda: deque(maxlen=5))
        
    def estimate_speed_from_flow(self, 
                                flow_vectors: np.ndarray,
                                bbox: Tuple[int, int, int, int],
                                depth: Optional[float] = None) -> VehicleSpeed:
        """Estimate speed from optical flow vectors within bounding box"""
        x1, y1, x2, y2 = bbox
        
        # Filter flow vectors within bbox
        mask = (flow_vectors[:, 0] >= x1) & (flow_vectors[:, 0] < x2) & \
               (flow_vectors[:, 1] >= y1) & (flow_vectors[:, 1] < y2)
        
        bbox_flow = flow_vectors[mask]
        
        if len(bbox_flow) == 0:
            return VehicleSpeed(vehicle_id=-1, bbox=bbox, speed_2d=0.0)
        
        # Calculate median flow
        median_flow = np.median(bbox_flow, axis=0)
        flow_magnitude = np.linalg.norm(median_flow)
        
        # Convert to speed (pixels per second)
        speed_2d = flow_magnitude * self.fps
        
        # Convert to real-world speed if depth is available
        speed_3d = None
        if depth is not None:
            # Simple perspective correction
            focal_length = self.camera_matrix[0, 0]
            speed_3d = (speed_2d * depth) / focal_length * self.pixel_to_meter
        
        # Calculate direction
        direction = np.arctan2(median_flow[1], median_flow[0])
        
        # Calculate confidence based on flow consistency
        flow_std = np.std(np.linalg.norm(bbox_flow, axis=1))
        confidence = 1.0 / (1.0 + flow_std)
        
        return VehicleSpeed(
            vehicle_id=-1,
            bbox=bbox,
            speed_2d=speed_2d,
            speed_3d=speed_3d,
            direction=direction,
            confidence=confidence
        )
    
    def track_vehicle_speed(self, detections: List[Dict], 
                           flow_data: Tuple[np.ndarray, np.ndarray]) -> List[VehicleSpeed]:
        """Track vehicle speeds across multiple detections"""
        current_points, prev_points = flow_data
        
        if len(current_points) == 0 or len(prev_points) == 0:
            return []
        
        speeds = []
        
        for detection in detections:
            bbox = detection['bbox']
            vehicle_id = detection.get('id', -1)
            
            # Estimate speed for this vehicle
            speed_est = self.estimate_speed_from_flow(current_points, bbox)
            speed_est.vehicle_id = vehicle_id
            
            # Smooth speed using history
            if vehicle_id != -1:
                self.speed_history[vehicle_id].append(speed_est.speed_2d)
                if len(self.speed_history[vehicle_id]) > 1:
                    speed_est.speed_2d = np.mean(self.speed_history[vehicle_id])
            
            speeds.append(speed_est)
            
            # Update trajectory
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            self.vehicle_tracks[vehicle_id].append((center_x, center_y))
        
        return speeds
    
    def calculate_trajectory_speed(self, vehicle_id: int) -> Optional[float]:
        """Calculate speed from vehicle trajectory"""
        if vehicle_id not in self.vehicle_tracks:
            return None
        
        trajectory = list(self.vehicle_tracks[vehicle_id])
        if len(trajectory) < 2:
            return None
        
        # Calculate speed from trajectory points
        total_distance = 0
        for i in range(1, len(trajectory)):
            dx = trajectory[i][0] - trajectory[i-1][0]
            dy = trajectory[i][1] - trajectory[i-1][1]
            distance = np.sqrt(dx**2 + dy**2)
            total_distance += distance
        
        # Average speed
        avg_speed = total_distance / (len(trajectory) - 1) * self.fps
        
        return avg_speed
    
    def get_vehicle_direction(self, vehicle_id: int) -> Optional[float]:
        """Get vehicle direction from trajectory"""
        if vehicle_id not in self.vehicle_tracks:
            return None
        
        trajectory = list(self.vehicle_tracks[vehicle_id])
        if len(trajectory) < 2:
            return None
        
        # Calculate direction from last two points
        p1 = trajectory[-2]
        p2 = trajectory[-1]
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        return np.arctan2(dy, dx)


class FlowVisualizer:
    """Optical flow visualization utilities"""
    
    @staticmethod
    def draw_flow_vectors(image: np.ndarray, 
                         current_points: np.ndarray, 
                         prev_points: np.ndarray,
                         scale: float = 5.0,
                         color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        """Draw optical flow vectors on image"""
        vis_image = image.copy()
        
        for i, (curr_pt, prev_pt) in enumerate(zip(current_points, prev_points)):
            curr_pt = tuple(map(int, curr_pt))
            prev_pt = tuple(map(int, prev_pt))
            
            # Draw arrow
            cv2.arrowedLine(vis_image, prev_pt, curr_pt, color, 1, tipLength=0.3)
        
        return vis_image
    
    @staticmethod
    def draw_flow_hsv(flow: np.ndarray) -> np.ndarray:
        """Visualize dense flow as HSV image"""
        h, w = flow.shape[:2]
        
        # Convert to polar coordinates
        magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        
        # Create HSV image
        hsv = np.zeros((h, w, 3), dtype=np.uint8)
        hsv[..., 0] = angle * 180 / np.pi / 2  # Hue
        hsv[..., 1] = 255  # Saturation
        hsv[..., 2] = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)  # Value
        
        # Convert to BGR
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        return bgr
    
    @staticmethod
    def draw_speed_info(image: np.ndarray, 
                       speeds: List[VehicleSpeed]) -> np.ndarray:
        """Draw speed information on image"""
        vis_image = image.copy()
        
        for speed in speeds:
            x1, y1, x2, y2 = speed.bbox
            
            # Draw speed text
            if speed.speed_3d is not None:
                speed_text = f"{speed.speed_3d:.1f} m/s"
            else:
                speed_text = f"{speed.speed_2d:.1f} px/s"
            
            cv2.putText(vis_image, speed_text, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Draw direction arrow
            if speed.direction is not None:
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                arrow_length = 30
                end_x = int(center_x + arrow_length * np.cos(speed.direction))
                end_y = int(center_y + arrow_length * np.sin(speed.direction))
                
                cv2.arrowedLine(vis_image, (center_x, center_y), 
                              (end_x, end_y), (255, 0, 0), 2)
        
        return vis_image


class TrafficFlowAnalyzer:
    """Advanced traffic flow analysis using optical flow"""
    
    def __init__(self, roi_mask: Optional[np.ndarray] = None):
        self.roi_mask = roi_mask
        self.flow_history = deque(maxlen=100)
        self.density_history = deque(maxlen=100)
        
    def analyze_traffic_density(self, flow: np.ndarray) -> Dict[str, float]:
        """Analyze traffic density from optical flow"""
        if self.roi_mask is not None:
            flow = flow * self.roi_mask[..., np.newaxis]
        
        # Calculate flow magnitude
        magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        
        # Density metrics
        active_pixels = np.sum(magnitude > 1.0)
        total_pixels = np.sum(self.roi_mask) if self.roi_mask is not None else magnitude.size
        density = active_pixels / total_pixels if total_pixels > 0 else 0
        
        # Average flow magnitude
        avg_magnitude = np.mean(magnitude[magnitude > 1.0]) if active_pixels > 0 else 0
        
        # Flow consistency
        flow_consistency = self._calculate_flow_consistency(flow)
        
        return {
            'density': density,
            'avg_magnitude': avg_magnitude,
            'active_pixels': active_pixels,
            'consistency': flow_consistency
        }
    
    def _calculate_flow_consistency(self, flow: np.ndarray) -> float:
        """Calculate flow consistency (how uniform the flow is)"""
        # Calculate flow direction
        angles = np.arctan2(flow[..., 1], flow[..., 0])
        
        # Calculate circular variance
        mean_cos = np.mean(np.cos(angles))
        mean_sin = np.mean(np.sin(angles))
        
        consistency = np.sqrt(mean_cos**2 + mean_sin**2)
        
        return consistency
    
    def detect_congestion(self, flow_metrics: Dict[str, float]) -> bool:
        """Detect traffic congestion from flow metrics"""
        # Congestion criteria
        high_density = flow_metrics['density'] > 0.3
        low_speed = flow_metrics['avg_magnitude'] < 2.0
        low_consistency = flow_metrics['consistency'] < 0.5
        
        return high_density and low_speed and low_consistency
    
    def estimate_queue_length(self, flow: np.ndarray, 
                            direction: np.ndarray) -> float:
        """Estimate vehicle queue length in a given direction"""
        # Project flow onto direction
        direction_normalized = direction / np.linalg.norm(direction)
        projected_flow = np.dot(flow.reshape(-1, 2), direction_normalized).reshape(flow.shape[:2])
        
        # Find regions with flow opposite to direction (stopped/slow vehicles)
        opposite_flow = projected_flow < 0.5
        
        # Calculate queue length as percentage of ROI
        if self.roi_mask is not None:
            queue_pixels = np.sum(opposite_flow & self.roi_mask)
            total_pixels = np.sum(self.roi_mask)
        else:
            queue_pixels = np.sum(opposite_flow)
            total_pixels = opposite_flow.size
        
        queue_length = queue_pixels / total_pixels if total_pixels > 0 else 0
        
        return queue_length


class OpticalFlowSystem:
    """Main optical flow system for traffic analysis"""
    
    def __init__(self, 
                 method: str = 'farneback',
                 camera_matrix: Optional[np.ndarray] = None,
                 fps: float = 30.0):
        self.method = method
        self.fps = fps
        
        # Initialize optical flow calculator
        if method == 'lucas_kanade':
            self.flow_calculator = LKOpticalFlow()
        elif method == 'farneback':
            self.flow_calculator = FarnebackOpticalFlow()
        elif method == 'deep':
            self.flow_calculator = DeepOpticalFlow()
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.flow_calculator.to(self.device)
            self.flow_calculator.eval()
        else:
            raise ValueError(f"Unsupported optical flow method: {method}")
        
        # Initialize speed estimator
        if camera_matrix is not None:
            self.speed_estimator = SpeedEstimator(camera_matrix, fps)
        else:
            self.speed_estimator = None
        
        # Initialize traffic analyzer
        self.traffic_analyzer = TrafficFlowAnalyzer()
        
        # Visualizer
        self.visualizer = FlowVisualizer()
        
        # Frame counter
        self.frame_count = 0
    
    def process_frame(self, current_frame: np.ndarray, 
                      prev_frame: Optional[np.ndarray] = None,
                      detections: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process a single frame for optical flow analysis"""
        self.frame_count += 1
        
        # Calculate optical flow
        if self.method == 'deep':
            flow = self._calculate_deep_flow(current_frame, prev_frame)
            current_points, prev_points = self._dense_flow_to_points(flow)
        else:
            current_points, prev_points = self.flow_calculator.calculate_flow(current_frame, prev_frame)
            flow = self._points_to_dense_flow(current_points, prev_points, current_frame.shape[:2])
        
        results = {
            'flow': flow,
            'current_points': current_points,
            'prev_points': prev_points,
            'frame_count': self.frame_count
        }
        
        # Estimate speeds if detections are available
        if detections is not None and self.speed_estimator is not None:
            speeds = self.speed_estimator.track_vehicle_speed(detections, (current_points, prev_points))
            results['speeds'] = speeds
        
        # Analyze traffic flow
        flow_metrics = self.traffic_analyzer.analyze_traffic_density(flow)
        results['flow_metrics'] = flow_metrics
        results['congestion_detected'] = self.traffic_analyzer.detect_congestion(flow_metrics)
        
        return results
    
    def _calculate_deep_flow(self, current_frame: np.ndarray, 
                           prev_frame: Optional[np.ndarray] = None) -> np.ndarray:
        """Calculate flow using deep learning model"""
        if prev_frame is None:
            return np.zeros((current_frame.shape[0], current_frame.shape[1], 2))
        
        # Preprocess frames
        def preprocess(frame):
            frame_tensor = torch.from_numpy(frame.transpose(2, 0, 1)).float().unsqueeze(0) / 255.0
            return frame_tensor.to(self.device)
        
        current_tensor = preprocess(current_frame)
        prev_tensor = preprocess(prev_frame)
        
        with torch.no_grad():
            flow_tensor = self.flow_calculator(prev_tensor, current_tensor)
        
        flow = flow_tensor.squeeze().cpu().numpy().transpose(1, 2, 0)
        
        return flow
    
    def _dense_flow_to_points(self, flow: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Convert dense flow to point format"""
        h, w = flow.shape[:2]
        y, x = np.mgrid[0:h, 0:w]
        
        current_points = np.column_stack([x.ravel(), y.ravel()])
        flow_vectors = flow.reshape(-1, 2)
        prev_points = current_points - flow_vectors
        
        # Sample points for efficiency
        step = 10
        current_points = current_points[::step]
        prev_points = prev_points[::step]
        
        return current_points, prev_points
    
    def _points_to_dense_flow(self, current_points: np.ndarray, 
                             prev_points: np.ndarray, 
                             shape: Tuple[int, int]) -> np.ndarray:
        """Convert point flow to dense flow"""
        if len(current_points) == 0:
            return np.zeros((shape[0], shape[1], 2))
        
        h, w = shape
        dense_flow = np.zeros((h, w, 2))
        
        # Simple interpolation
        for i, (curr_pt, prev_pt) in enumerate(zip(current_points, prev_points)):
            x, y = int(curr_pt[0]), int(curr_pt[1])
            if 0 <= x < w and 0 <= y < h:
                flow_vector = curr_pt - prev_pt
                dense_flow[y, x] = flow_vector
        
        return dense_flow
    
    def visualize_flow(self, image: np.ndarray, 
                       flow_results: Dict[str, Any],
                       visualization_type: str = 'vectors') -> np.ndarray:
        """Visualize optical flow results"""
        if visualization_type == 'vectors':
            return self.visualizer.draw_flow_vectors(
                image, flow_results['current_points'], flow_results['prev_points']
            )
        elif visualization_type == 'hsv':
            return self.visualizer.draw_flow_hsv(flow_results['flow'])
        elif visualization_type == 'speeds' and 'speeds' in flow_results:
            return self.visualizer.draw_speed_info(image, flow_results['speeds'])
        else:
            return image


# Factory functions
def create_optical_flow_system(config: Dict) -> OpticalFlowSystem:
    """Factory function to create optical flow system"""
    return OpticalFlowSystem(
        method=config.get('method', 'farneback'),
        camera_matrix=np.array(config['camera_matrix']) if 'camera_matrix' in config else None,
        fps=config.get('fps', 30.0)
    )


def create_speed_estimator(config: Dict) -> SpeedEstimator:
    """Factory function to create speed estimator"""
    return SpeedEstimator(
        camera_matrix=np.array(config['camera_matrix']),
        fps=config.get('fps', 30.0),
        pixel_to_meter=config.get('pixel_to_meter', 0.1)
    )