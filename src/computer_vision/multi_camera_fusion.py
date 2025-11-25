"""
Multi-Camera Fusion System

Implements advanced sensor fusion techniques for combining data
from multiple cameras and sensors in traffic monitoring systems.
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
import json
from scipy.optimize import linear_sum_assignment
from scipy.spatial.transform import Rotation
import open3d as o3d

logger = logging.getLogger(__name__)


@dataclass
class CameraConfig:
    """Camera configuration parameters"""
    id: int
    name: str
    position: np.ndarray  # 3D position [x, y, z]
    rotation: np.ndarray  # Rotation matrix 3x3
    camera_matrix: np.ndarray  # Intrinsic matrix 3x3
    dist_coeffs: np.ndarray  # Distortion coefficients
    fov: float  # Field of view in degrees
    resolution: Tuple[int, int]  # Width, Height
    fps: float
    overlap_regions: List[int]  # IDs of overlapping cameras


@dataclass
class FusedDetection:
    """Fused detection from multiple sensors"""
    object_id: int
    class_name: str
    confidence: float
    position_3d: np.ndarray  # 3D world coordinates
    velocity_3d: Optional[np.ndarray] = None
    dimensions: Optional[np.ndarray] = None  # [length, width, height]
    source_cameras: List[int] = None
    detection_confidences: Dict[int, float] = None
    timestamp: float = 0.0


class CameraCalibrator:
    """Camera calibration and extrinsic estimation"""
    
    def __init__(self, checkerboard_size: Tuple[int, int] = (9, 6)):
        self.checkerboard_size = checkerboard_size
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        self.objp = np.zeros((checkerboard_size[0] * checkerboard_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:checkerboard_size[0], 0:checkerboard_size[1]].T.reshape(-1, 2)
        
    def calibrate_intrinsics(self, images: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray, List[np.ndarray]]:
        """Calibrate camera intrinsics using checkerboard images"""
        objpoints = []
        imgpoints = []
        
        for img in images:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, self.checkerboard_size, None)
            
            if ret:
                objpoints.append(self.objp)
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
                imgpoints.append(corners2)
        
        if len(objpoints) > 0:
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
            return mtx, dist, [rvecs, tvecs]
        else:
            raise ValueError("No checkerboard patterns found in images")
    
    def estimate_extrinsics(self, camera_matrix: np.ndarray, 
                           dist_coeffs: np.ndarray,
                           image: np.ndarray,
                           object_points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Estimate camera extrinsics from known object points"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, self.checkerboard_size, None)
        
        if ret:
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
            ret, rvec, tvec = cv2.solvePnP(object_points, corners2, camera_matrix, dist_coeffs)
            
            if ret:
                R, _ = cv2.Rodrigues(rvec)
                return R, tvec
        
        raise ValueError("Could not estimate extrinsics")
    
    def stereo_calibrate(self, cam1_images: List[np.ndarray], 
                        cam2_images: List[np.ndarray]) -> Dict[str, np.ndarray]:
        """Calibrate stereo camera pair"""
        objpoints = []
        imgpoints1 = []
        imgpoints2 = []
        
        for img1, img2 in zip(cam1_images, cam2_images):
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            ret1, corners1 = cv2.findChessboardCorners(gray1, self.checkerboard_size, None)
            ret2, corners2 = cv2.findChessboardCorners(gray2, self.checkerboard_size, None)
            
            if ret1 and ret2:
                objpoints.append(self.objp)
                corners2_1 = cv2.cornerSubPix(gray1, corners1, (11, 11), (-1, -1), self.criteria)
                corners2_2 = cv2.cornerSubPix(gray2, corners2, (11, 11), (-1, -1), self.criteria)
                imgpoints1.append(corners2_1)
                imgpoints2.append(corners2_2)
        
        if len(objpoints) > 0:
            ret, mtx1, dist1, mtx2, dist2, R, T, E, F = cv2.stereoCalibrate(
                objpoints, imgpoints1, imgpoints2, None, None, None, None,
                gray1.shape[::-1], flags=cv2.CALIB_FIX_INTRINSIC
            )
            
            return {
                'R': R, 'T': T, 'E': E, 'F': F,
                'mtx1': mtx1, 'dist1': dist1,
                'mtx2': mtx2, 'dist2': dist2
            }
        else:
            raise ValueError("No valid stereo pairs found")


class CoordinateTransformer:
    """Coordinate system transformations"""
    
    @staticmethod
    def pixel_to_camera(pixel: np.ndarray, depth: float, 
                       camera_matrix: np.ndarray) -> np.ndarray:
        """Convert pixel coordinates to camera coordinates"""
        fx, fy = camera_matrix[0, 0], camera_matrix[1, 1]
        cx, cy = camera_matrix[0, 2], camera_matrix[1, 2]
        
        x = (pixel[0] - cx) * depth / fx
        y = (pixel[1] - cy) * depth / fy
        z = depth
        
        return np.array([x, y, z])
    
    @staticmethod
    def camera_to_world(camera_coords: np.ndarray, 
                        rotation: np.ndarray, 
                        translation: np.ndarray) -> np.ndarray:
        """Convert camera coordinates to world coordinates"""
        return rotation @ camera_coords + translation
    
    @staticmethod
    def world_to_camera(world_coords: np.ndarray, 
                       rotation: np.ndarray, 
                       translation: np.ndarray) -> np.ndarray:
        """Convert world coordinates to camera coordinates"""
        return rotation.T @ (world_coords - translation)
    
    @staticmethod
    def camera_to_pixel(camera_coords: np.ndarray, 
                        camera_matrix: np.ndarray) -> np.ndarray:
        """Convert camera coordinates to pixel coordinates"""
        fx, fy = camera_matrix[0, 0], camera_matrix[1, 1]
        cx, cy = camera_matrix[0, 2], camera_matrix[1, 2]
        
        x = camera_coords[0] / camera_coords[2] * fx + cx
        y = camera_coords[1] / camera_coords[2] * fy + cy
        
        return np.array([x, y])
    
    @staticmethod
    def create_transformation_matrix(rotation: np.ndarray, 
                                   translation: np.ndarray) -> np.ndarray:
        """Create 4x4 transformation matrix"""
        T = np.eye(4)
        T[:3, :3] = rotation
        T[:3, 3] = translation
        return T


class DetectionAssociator:
    """Associate detections across multiple cameras"""
    
    def __init__(self, distance_threshold: float = 2.0):
        self.distance_threshold = distance_threshold
        
    def associate_detections(self, 
                            detections_by_camera: Dict[int, List[Dict]],
                            camera_configs: Dict[int, CameraConfig]) -> List[List[Dict]]:
        """Associate detections from multiple cameras"""
        # Transform all detections to world coordinates
        world_detections = []
        detection_sources = []
        
        for cam_id, detections in detections_by_camera.items():
            config = camera_configs[cam_id]
            
            for detection in detections:
                # Convert to world coordinates
                world_pos = self._detection_to_world(detection, config)
                if world_pos is not None:
                    world_detections.append({
                        'position': world_pos,
                        'camera_id': cam_id,
                        'detection': detection,
                        'confidence': detection.get('confidence', 1.0)
                    })
                    detection_sources.append(cam_id)
        
        # Cluster detections
        clusters = self._cluster_detections(world_detections)
        
        return clusters
    
    def _detection_to_world(self, detection: Dict, 
                           config: CameraConfig) -> Optional[np.ndarray]:
        """Convert detection to world coordinates"""
        bbox = detection.get('bbox', [0, 0, 0, 0])
        depth = detection.get('depth', 10.0)  # Default depth
        
        # Get center pixel
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        
        # Convert to camera coordinates
        camera_coords = CoordinateTransformer.pixel_to_camera(
            np.array([center_x, center_y]), depth, config.camera_matrix
        )
        
        # Convert to world coordinates
        world_coords = CoordinateTransformer.camera_to_world(
            camera_coords, config.rotation, config.position
        )
        
        return world_coords
    
    def _cluster_detections(self, detections: List[Dict]) -> List[List[Dict]]:
        """Cluster detections that belong to the same object"""
        if not detections:
            return []
        
        clusters = []
        used = set()
        
        for i, det1 in enumerate(detections):
            if i in used:
                continue
            
            cluster = [det1]
            used.add(i)
            
            for j, det2 in enumerate(detections[i+1:], i+1):
                if j in used:
                    continue
                
                distance = np.linalg.norm(det1['position'] - det2['position'])
                if distance < self.distance_threshold:
                    cluster.append(det2)
                    used.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def hungarian_association(self, 
                             detections1: List[Dict], 
                             detections2: List[Dict],
                             cost_matrix: Optional[np.ndarray] = None) -> List[Tuple[int, int]]:
        """Associate detections using Hungarian algorithm"""
        if cost_matrix is None:
            cost_matrix = self._create_cost_matrix(detections1, detections2)
        
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        associations = []
        for r, c in zip(row_indices, col_indices):
            if cost_matrix[r, c] < self.distance_threshold:
                associations.append((r, c))
        
        return associations
    
    def _create_cost_matrix(self, detections1: List[Dict], 
                           detections2: List[Dict]) -> np.ndarray:
        """Create cost matrix for Hungarian algorithm"""
        n1, n2 = len(detections1), len(detections2)
        cost_matrix = np.full((n1, n2), 1e6)  # Large value for impossible matches
        
        for i, det1 in enumerate(detections1):
            for j, det2 in enumerate(detections2):
                pos1 = det1.get('position', np.zeros(3))
                pos2 = det2.get('position', np.zeros(3))
                distance = np.linalg.norm(pos1 - pos2)
                cost_matrix[i, j] = distance
        
        return cost_matrix


class MultiCameraFusion:
    """Main multi-camera fusion system"""
    
    def __init__(self, camera_configs: List[CameraConfig]):
        self.camera_configs = {config.id: config for config in camera_configs}
        self.associator = DetectionAssociator()
        self.transformer = CoordinateTransformer()
        
        # Tracking
        self.object_tracker = defaultdict(lambda: deque(maxlen=10))
        self.object_id_counter = 0
        
        # Fusion history
        self.fusion_history = deque(maxlen=100)
        
    def fuse_detections(self, 
                       detections_by_camera: Dict[int, List[Dict]],
                       timestamp: float = 0.0) -> List[FusedDetection]:
        """Fuse detections from multiple cameras"""
        # Associate detections across cameras
        clusters = self.associator.associate_detections(
            detections_by_camera, self.camera_configs
        )
        
        fused_detections = []
        
        for cluster in clusters:
            fused_det = self._fuse_cluster(cluster, timestamp)
            if fused_det:
                fused_detections.append(fused_det)
        
        # Update tracking
        self._update_tracking(fused_detections)
        
        # Store in history
        self.fusion_history.append((timestamp, fused_detections))
        
        return fused_detections
    
    def _fuse_cluster(self, cluster: List[Dict], timestamp: float) -> Optional[FusedDetection]:
        """Fuse a cluster of detections"""
        if not cluster:
            return None
        
        # Weighted average of positions
        positions = np.array([det['position'] for det in cluster])
        confidences = np.array([det['confidence'] for det in cluster])
        
        # Normalize confidences
        weights = confidences / np.sum(confidences)
        
        # Fused position
        fused_position = np.average(positions, axis=0, weights=weights)
        
        # Get class information (use highest confidence)
        best_detection = max(cluster, key=lambda x: x['confidence'])
        class_name = best_detection['detection'].get('class_name', 'unknown')
        
        # Source cameras
        source_cameras = [det['camera_id'] for det in cluster]
        
        # Detection confidences by camera
        detection_confidences = {det['camera_id']: det['confidence'] for det in cluster}
        
        # Create fused detection
        fused_detection = FusedDetection(
            object_id=self.object_id_counter,
            class_name=class_name,
            confidence=np.max(confidences),
            position_3d=fused_position,
            source_cameras=source_cameras,
            detection_confidences=detection_confidences,
            timestamp=timestamp
        )
        
        self.object_id_counter += 1
        
        return fused_detection
    
    def _update_tracking(self, fused_detections: List[FusedDetection]):
        """Update object tracking"""
        # Simple proximity-based tracking
        current_positions = {det.object_id: det.position_3d for det in fused_detections}
        
        # Match with previous tracks
        if hasattr(self, 'previous_positions'):
            matches = self._match_objects(current_positions, self.previous_positions)
            
            for new_id, old_id in matches.items():
                # Update velocity
                if old_id in self.object_tracker:
                    old_positions = list(self.object_tracker[old_id])
                    if len(old_positions) > 0:
                        velocity = (current_positions[new_id] - old_positions[-1]) / 0.1  # Assuming 100ms
                        # Update detection with velocity
                        for det in fused_detections:
                            if det.object_id == new_id:
                                det.velocity_3d = velocity
        
        # Update tracks
        for det in fused_detections:
            self.object_tracker[det.object_id].append(det.position_3d)
        
        self.previous_positions = current_positions
    
    def _match_objects(self, current_positions: Dict[int, np.ndarray], 
                      previous_positions: Dict[int, np.ndarray]) -> Dict[int, int]:
        """Match current objects with previous ones"""
        matches = {}
        
        for current_id, current_pos in current_positions.items():
            min_distance = float('inf')
            best_match = None
            
            for prev_id, prev_pos in previous_positions.items():
                distance = np.linalg.norm(current_pos - prev_pos)
                if distance < min_distance and distance < 2.0:  # 2 meter threshold
                    min_distance = distance
                    best_match = prev_id
            
            if best_match is not None:
                matches[current_id] = best_match
        
        return matches
    
    def create_birds_eye_view(self, 
                             fused_detections: List[FusedDetection],
                             area_size: Tuple[float, float] = (100.0, 100.0),
                             resolution: Tuple[int, int] = (1000, 1000)) -> np.ndarray:
        """Create bird's eye view visualization"""
        width, height = resolution
        bev_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Scale factors
        scale_x = width / area_size[0]
        scale_y = height / area_size[1]
        
        # Draw detections
        for det in fused_detections:
            x, y, z = det.position_3d
            
            # Convert to BEV coordinates
            bev_x = int(x * scale_x + width // 2)
            bev_y = int(height // 2 - y * scale_y)  # Flip y-axis
            
            if 0 <= bev_x < width and 0 <= bev_y < height:
                # Draw detection
                color = self._get_class_color(det.class_name)
                cv2.circle(bev_image, (bev_x, bev_y), 10, color, -1)
                
                # Draw velocity vector
                if det.velocity_3d is not None:
                    vx, vy, vz = det.velocity_3d
                    end_x = int(bev_x + vx * scale_x * 2)
                    end_y = int(bev_y - vy * scale_y * 2)
                    cv2.arrowedLine(bev_image, (bev_x, bev_y), (end_x, end_y), color, 2)
                
                # Draw label
                label = f"{det.class_name}_{det.object_id}"
                cv2.putText(bev_image, label, (bev_x + 15, bev_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw camera positions
        for cam_id, config in self.camera_configs.items():
            x, y, z = config.position
            bev_x = int(x * scale_x + width // 2)
            bev_y = int(height // 2 - y * scale_y)
            
            if 0 <= bev_x < width and 0 <= bev_y < height:
                cv2.rectangle(bev_image, (bev_x - 5, bev_y - 5), 
                             (bev_x + 5, bev_y + 5), (0, 0, 255), -1)
                cv2.putText(bev_image, f"Cam{cam_id}", (bev_x + 10, bev_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        return bev_image
    
    def _get_class_color(self, class_name: str) -> Tuple[int, int, int]:
        """Get color for object class"""
        colors = {
            'car': (0, 255, 0),
            'truck': (255, 0, 0),
            'bus': (0, 0, 255),
            'motorcycle': (255, 255, 0),
            'bicycle': (255, 0, 255),
            'person': (0, 255, 255),
        }
        return colors.get(class_name, (128, 128, 128))
    
    def get_coverage_map(self, area_size: Tuple[float, float] = (100.0, 100.0),
                        resolution: Tuple[int, int] = (1000, 1000)) -> np.ndarray:
        """Get camera coverage map"""
        width, height = resolution
        coverage_map = np.zeros((height, width), dtype=np.uint8)
        
        scale_x = width / area_size[0]
        scale_y = height / area_size[1]
        
        for cam_id, config in self.camera_configs.items():
            # Project camera FOV onto ground plane
            fov_points = self._project_camera_fov(config, area_size)
            
            # Convert to pixel coordinates
            pixel_points = []
            for point in fov_points:
                px = int(point[0] * scale_x + width // 2)
                py = int(height // 2 - point[1] * scale_y)
                if 0 <= px < width and 0 <= py < height:
                    pixel_points.append((px, py))
            
            # Fill polygon
            if len(pixel_points) >= 3:
                cv2.fillPoly(coverage_map, [np.array(pixel_points)], 255)
        
        return coverage_map
    
    def _project_camera_fov(self, config: CameraConfig, 
                           area_size: Tuple[float, float]) -> List[np.ndarray]:
        """Project camera FOV onto ground plane"""
        # Simplified FOV projection
        fov_rad = np.radians(config.fov)
        max_distance = 50.0  # Maximum detection distance
        
        # Camera position
        cam_pos = config.position
        
        # Create FOV points
        fov_points = []
        
        # Center line
        center_direction = config.rotation @ np.array([0, 0, 1])
        center_point = cam_pos + center_direction * max_distance
        fov_points.append(center_point[:2])  # Only x, y coordinates
        
        # Left edge
        left_angle = fov_rad / 2
        left_rotation = Rotation.from_euler('z', left_angle).as_matrix()
        left_direction = config.rotation @ left_rotation @ np.array([0, 0, 1])
        left_point = cam_pos + left_direction * max_distance
        fov_points.append(left_point[:2])
        
        # Right edge
        right_angle = -fov_rad / 2
        right_rotation = Rotation.from_euler('z', right_angle).as_matrix()
        right_direction = config.rotation @ right_rotation @ np.array([0, 0, 1])
        right_point = cam_pos + right_direction * max_distance
        fov_points.append(right_point[:2])
        
        return fov_points


class SensorFusionNetwork(nn.Module):
    """Deep learning based sensor fusion"""
    
    def __init__(self, num_cameras: int, feature_dim: int = 256):
        super().__init__()
        self.num_cameras = num_cameras
        self.feature_dim = feature_dim
        
        # Feature extractors for each camera
        self.feature_extractors = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(3, 64, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(64, 128, 3, stride=2, padding=1),
                nn.ReLU(inplace=True),
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten(),
                nn.Linear(128, feature_dim)
            ) for _ in range(num_cameras)
        ])
        
        # Fusion layers
        self.fusion = nn.Sequential(
            nn.Linear(feature_dim * num_cameras, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, 10)  # Output classes
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(feature_dim, num_heads=8)
        
    def forward(self, camera_inputs: List[torch.Tensor]) -> torch.Tensor:
        """Forward pass through fusion network"""
        # Extract features from each camera
        features = []
        for i, (input_tensor, extractor) in enumerate(zip(camera_inputs, self.feature_extractors)):
            feat = extractor(input_tensor)
            features.append(feat)
        
        # Stack features
        features_tensor = torch.stack(features, dim=1)  # [batch, num_cameras, feature_dim]
        
        # Apply attention
        attended_features, _ = self.attention(features_tensor, features_tensor, features_tensor)
        
        # Flatten and fuse
        fused_features = attended_features.view(attended_features.size(0), -1)
        
        # Final classification
        output = self.fusion(fused_features)
        
        return output


# Factory functions
def create_camera_config(config_dict: Dict) -> CameraConfig:
    """Create camera configuration from dictionary"""
    return CameraConfig(
        id=config_dict['id'],
        name=config_dict['name'],
        position=np.array(config_dict['position']),
        rotation=np.array(config_dict['rotation']),
        camera_matrix=np.array(config_dict['camera_matrix']),
        dist_coeffs=np.array(config_dict['dist_coeffs']),
        fov=config_dict['fov'],
        resolution=tuple(config_dict['resolution']),
        fps=config_dict['fps'],
        overlap_regions=config_dict.get('overlap_regions', [])
    )


def create_multi_camera_fusion(configs: List[Dict]) -> MultiCameraFusion:
    """Create multi-camera fusion system from configurations"""
    camera_configs = [create_camera_config(config) for config in configs]
    return MultiCameraFusion(camera_configs)


def create_sensor_fusion_network(num_cameras: int, 
                                feature_dim: int = 256) -> SensorFusionNetwork:
    """Create sensor fusion neural network"""
    return SensorFusionNetwork(num_cameras, feature_dim)