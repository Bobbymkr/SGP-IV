"""
3D Vehicle Detection with Depth Estimation Module

Implements state-of-the-art 3D object detection and depth estimation
for traffic monitoring and vehicle analysis.
"""

import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import open3d as o3d
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Detection3D:
    """3D detection result"""
    class_id: int
    class_name: str
    confidence: float
    bbox_2d: Tuple[int, int, int, int]  # x1, y1, x2, y2
    bbox_3d: np.ndarray  # 8x3 array of 3D corners
    center_3d: np.ndarray  # 3D center point
    dimensions: np.ndarray  # (length, width, height)
    rotation_y: float  # Yaw angle
    depth: float  # Depth to center
    velocity: Optional[np.ndarray] = None  # 3D velocity vector


class DepthEstimator(nn.Module):
    """Monocular depth estimation network"""
    
    def __init__(self, backbone: str = 'resnet50'):
        super().__init__()
        
        if backbone == 'resnet50':
            self.backbone = torch.hub.load('pytorch/vision:v0.10.0', 'resnet50', pretrained=True)
            self.backbone = nn.Sequential(*list(self.backbone.children())[:-2])
            feature_dim = 2048
        else:
            raise ValueError(f"Unsupported backbone: {backbone}")
        
        # Depth prediction head
        self.depth_head = nn.Sequential(
            nn.Conv2d(feature_dim, 512, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=False),
            nn.Conv2d(512, 256, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=False),
            nn.Conv2d(256, 128, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=False),
            nn.Conv2d(128, 64, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 1, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        depth = self.depth_head(features)
        return depth


class StereoDepthEstimator:
    """Stereo depth estimation using rectified image pairs"""
    
    def __init__(self, baseline: float = 0.1, focal_length: float = 1000.0):
        self.baseline = baseline
        self.focal_length = focal_length
        self.stereo_matcher = cv2.StereoSGBM_create(
            minDisparity=0,
            numDisparities=16*6,
            blockSize=11,
            P1=8*3*11**2,
            P2=32*3*11**2,
            disp12MaxDiff=1,
            uniquenessRatio=10,
            speckleWindowSize=100,
            speckleRange=32
        )
        
    def compute_depth(self, left_img: np.ndarray, right_img: np.ndarray) -> np.ndarray:
        """Compute depth map from stereo image pair"""
        # Convert to grayscale
        left_gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
        right_gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)
        
        # Compute disparity
        disparity = self.stereo_matcher.compute(left_gray, right_gray)
        disparity = disparity.astype(np.float32) / 16.0
        
        # Convert disparity to depth
        with np.errstate(divide='ignore'):
            depth = (self.baseline * self.focal_length) / disparity
            depth[disparity <= 0] = 0
            
        return depth


class PointCloudProcessor:
    """3D point cloud processing utilities"""
    
    @staticmethod
    def depth_to_point_cloud(depth: np.ndarray, 
                           camera_matrix: np.ndarray,
                           color_image: Optional[np.ndarray] = None) -> o3d.geometry.PointCloud:
        """Convert depth map to 3D point cloud"""
        height, width = depth.shape
        
        # Create coordinate grids
        u, v = np.meshgrid(np.arange(width), np.arange(height))
        
        # Convert to homogeneous coordinates
        ones = np.ones_like(u)
        coords_2d = np.stack([u.flatten(), v.flatten(), ones], axis=1)
        
        # Get camera intrinsics
        fx, fy = camera_matrix[0, 0], camera_matrix[1, 1]
        cx, cy = camera_matrix[0, 2], camera_matrix[1, 2]
        
        # Convert to 3D coordinates
        depth_flat = depth.flatten()
        valid = depth_flat > 0
        
        x = (coords_2d[valid, 0] - cx) * depth_flat[valid] / fx
        y = (coords_2d[valid, 1] - cy) * depth_flat[valid] / fy
        z = depth_flat[valid]
        
        points = np.stack([x, y, z], axis=1)
        
        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        
        # Add colors if available
        if color_image is not None:
            colors = color_image.reshape(-1, 3)[valid] / 255.0
            pcd.colors = o3d.utility.Vector3dVector(colors)
            
        return pcd
    
    @staticmethod
    def cluster_vehicles(pcd: o3d.geometry.PointCloud,
                        distance_threshold: float = 0.5,
                        min_points: int = 100) -> List[o3d.geometry.PointCloud]:
        """Cluster point cloud to separate vehicles"""
        # DBSCAN clustering
        labels = np.array(pcd.cluster_dbscan(eps=distance_threshold, min_points=min_points))
        
        clusters = []
        max_label = labels.max()
        
        for i in range(max_label + 1):
            cluster_indices = np.where(labels == i)[0]
            if len(cluster_indices) >= min_points:
                cluster_pcd = pcd.select_by_index(cluster_indices)
                clusters.append(cluster_pcd)
                
        return clusters
    
    @staticmethod
    def fit_bounding_box(pcd: o3d.geometry.PointCloud) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Fit oriented bounding box to point cloud"""
        obb = pcd.get_oriented_bounding_box()
        
        center = np.array(obb.center)
        extent = np.array(obb.extent)  # (length, width, height)
        
        # Get rotation matrix
        rotation = np.array(obb.R)
        
        return center, extent, rotation


class Vehicle3DDetector:
    """Main 3D vehicle detection system"""
    
    def __init__(self, 
                 camera_matrix: np.ndarray,
                 dist_coeffs: np.ndarray,
                 use_stereo: bool = False,
                 baseline: float = 0.1):
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        self.use_stereo = use_stereo
        
        # Initialize depth estimator
        if use_stereo:
            self.depth_estimator = StereoDepthEstimator(baseline=baseline)
        else:
            self.depth_estimator = DepthEstimator()
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.depth_estimator.to(self.device)
            self.depth_estimator.eval()
        
        # Point cloud processor
        self.pc_processor = PointCloudProcessor()
        
        # Vehicle dimensions (average values in meters)
        self.vehicle_dims = {
            'car': np.array([4.5, 1.8, 1.5]),
            'truck': np.array([8.0, 2.5, 3.0]),
            'bus': np.array([12.0, 2.5, 3.5]),
            'motorcycle': np.array([2.0, 0.8, 1.2]),
            'bicycle': np.array([1.8, 0.6, 1.0])
        }
        
        # Class names
        self.class_names = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
        
    def estimate_depth(self, image: np.ndarray, 
                      right_image: Optional[np.ndarray] = None) -> np.ndarray:
        """Estimate depth from image(s)"""
        if self.use_stereo and right_image is not None:
            return self.depth_estimator.compute_depth(image, right_image)
        else:
            # Monocular depth estimation
            # Preprocess image
            img_tensor = torch.from_numpy(image.transpose(2, 0, 1)).float().unsqueeze(0) / 255.0
            img_tensor = img_tensor.to(self.device)
            
            with torch.no_grad():
                depth_pred = self.depth_estimator(img_tensor)
                depth = depth_pred.squeeze().cpu().numpy()
                
            # Scale depth to reasonable range (0-100 meters)
            depth = depth * 100.0
            return depth
    
    def detect_2d_objects(self, image: np.ndarray) -> List[Dict]:
        """Detect 2D bounding boxes (placeholder for actual detector)"""
        # This would integrate with YOLO, Faster R-CNN, etc.
        # For now, return dummy detections
        detections = []
        
        # Simulate some detections
        h, w = image.shape[:2]
        
        # Car detection
        detections.append({
            'bbox': [w//4, h//3, 3*w//4, 2*h//3],
            'class_id': 0,
            'class_name': 'car',
            'confidence': 0.95
        })
        
        return detections
    
    def project_to_3d(self, bbox: Tuple[int, int, int, int], 
                     depth: np.ndarray) -> Tuple[np.ndarray, float]:
        """Project 2D bbox to 3D using depth information"""
        x1, y1, x2, y2 = bbox
        
        # Get center point
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        # Get depth at center
        center_depth = depth[center_y, center_x]
        
        if center_depth <= 0:
            # Use median depth in bbox if center depth is invalid
            roi_depth = depth[y1:y2, x1:x2]
            valid_depths = roi_depth[roi_depth > 0]
            if len(valid_depths) > 0:
                center_depth = np.median(valid_depths)
            else:
                center_depth = 10.0  # Default depth
        
        # Convert to 3D coordinates
        fx, fy = self.camera_matrix[0, 0], self.camera_matrix[1, 1]
        cx, cy = self.camera_matrix[0, 2], self.camera_matrix[1, 2]
        
        x_3d = (center_x - cx) * center_depth / fx
        y_3d = (center_y - cy) * center_depth / fy
        z_3d = center_depth
        
        center_3d = np.array([x_3d, y_3d, z_3d])
        
        return center_3d, center_depth
    
    def estimate_3d_bbox(self, center_3d: np.ndarray, 
                       class_name: str,
                       bbox_2d: Tuple[int, int, int, int]) -> Tuple[np.ndarray, np.ndarray, float]:
        """Estimate 3D bounding box from center and class"""
        # Get average dimensions for this class
        dims = self.vehicle_dims.get(class_name, self.vehicle_dims['car'])
        
        # Calculate rotation based on 2D bbox aspect ratio
        x1, y1, x2, y2 = bbox_2d
        width_2d = x2 - x1
        height_2d = y2 - y1
        
        # Simple heuristic for rotation
        if width_2d > height_2d * 1.5:
            rotation_y = np.pi / 2  # Side view
        else:
            rotation_y = 0  # Front/rear view
        
        # Generate 3D bbox corners
        l, w, h = dims
        corners = np.array([
            [-l/2, -w/2, 0], [l/2, -w/2, 0], [l/2, w/2, 0], [-l/2, w/2, 0],  # Bottom
            [-l/2, -w/2, h], [l/2, -w/2, h], [l/2, w/2, h], [-l/2, w/2, h]   # Top
        ])
        
        # Apply rotation
        cos_r = np.cos(rotation_y)
        sin_r = np.sin(rotation_y)
        rotation_matrix = np.array([
            [cos_r, 0, sin_r],
            [0, 1, 0],
            [-sin_r, 0, cos_r]
        ])
        
        corners = corners @ rotation_matrix.T
        corners += center_3d
        
        return corners, dims, rotation_y
    
    def detect_3d_vehicles(self, 
                          image: np.ndarray,
                          right_image: Optional[np.ndarray] = None) -> List[Detection3D]:
        """Main 3D vehicle detection pipeline"""
        # Estimate depth
        depth = self.estimate_depth(image, right_image)
        
        # Detect 2D objects
        detections_2d = self.detect_2d_objects(image)
        
        detections_3d = []
        
        for det in detections_2d:
            bbox = tuple(det['bbox'])
            class_name = det['class_name']
            confidence = det['confidence']
            class_id = det['class_id']
            
            # Project to 3D
            center_3d, depth_val = self.project_to_3d(bbox, depth)
            
            # Estimate 3D bbox
            bbox_3d, dimensions, rotation = self.estimate_3d_bbox(center_3d, class_name, bbox)
            
            # Create detection
            detection = Detection3D(
                class_id=class_id,
                class_name=class_name,
                confidence=confidence,
                bbox_2d=bbox,
                bbox_3d=bbox_3d,
                center_3d=center_3d,
                dimensions=dimensions,
                rotation_y=rotation,
                depth=depth_val
            )
            
            detections_3d.append(detection)
        
        return detections_3d
    
    def track_vehicles(self, detections: List[Detection3D], 
                      previous_detections: List[Detection3D]) -> List[Detection3D]:
        """Simple tracking based on proximity"""
        if not previous_detections:
            return detections
        
        tracked_detections = []
        
        for det in detections:
            # Find closest previous detection
            min_distance = float('inf')
            best_match = None
            
            for prev_det in previous_detections:
                distance = np.linalg.norm(det.center_3d - prev_det.center_3d)
                if distance < min_distance and distance < 5.0:  # 5 meter threshold
                    min_distance = distance
                    best_match = prev_det
            
            if best_match:
                # Estimate velocity
                dt = 1.0  # Assume 1 second between frames
                velocity = (det.center_3d - best_match.center_3d) / dt
                det.velocity = velocity
            
            tracked_detections.append(det)
        
        return tracked_detections
    
    def visualize_detections(self, 
                           image: np.ndarray,
                           detections: List[Detection3D]) -> np.ndarray:
        """Visualize 3D detections on image"""
        vis_image = image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox_2d
            
            # Draw 2D bbox
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{det.class_name}: {det.confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(vis_image, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            cv2.putText(vis_image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Draw depth info
            depth_text = f"Depth: {det.depth:.1f}m"
            cv2.putText(vis_image, depth_text, (x1, y2 + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Draw velocity if available
            if det.velocity is not None:
                speed = np.linalg.norm(det.velocity[:2])  # Horizontal speed
                vel_text = f"Speed: {speed:.1f}m/s"
                cv2.putText(vis_image, vel_text, (x1, y2 + 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return vis_image


class MultiViewDetector:
    """Multi-view 3D detection using multiple cameras"""
    
    def __init__(self, camera_configs: List[Dict]):
        self.camera_configs = camera_configs
        self.detectors = []
        
        for config in camera_configs:
            detector = Vehicle3DDetector(
                camera_matrix=config['camera_matrix'],
                dist_coeffs=config['dist_coeffs'],
                use_stereo=config.get('use_stereo', False),
                baseline=config.get('baseline', 0.1)
            )
            self.detectors.append(detector)
    
    def detect_multi_view(self, images: List[np.ndarray]) -> List[Detection3D]:
        """Detect vehicles from multiple camera views"""
        all_detections = []
        
        for i, (image, detector) in enumerate(zip(images, self.detectors)):
            detections = detector.detect_3d_vehicles(image)
            
            # Transform to world coordinates if extrinsics provided
            if 'extrinsics' in self.camera_configs[i]:
                extrinsics = self.camera_configs[i]['extrinsics']
                for det in detections:
                    # Transform center and bbox to world coordinates
                    det.center_3d = self.transform_to_world(det.center_3d, extrinsics)
                    det.bbox_3d = self.transform_points_to_world(det.bbox_3d, extrinsics)
            
            all_detections.extend(detections)
        
        # Merge detections from different views
        merged_detections = self.merge_detections(all_detections)
        
        return merged_detections
    
    def transform_to_world(self, point: np.ndarray, extrinsics: np.ndarray) -> np.ndarray:
        """Transform point from camera to world coordinates"""
        # Convert to homogeneous coordinates
        point_homo = np.append(point, 1)
        # Apply transformation
        world_point_homo = extrinsics @ point_homo
        return world_point_homo[:3]
    
    def transform_points_to_world(self, points: np.ndarray, extrinsics: np.ndarray) -> np.ndarray:
        """Transform multiple points to world coordinates"""
        points_homo = np.hstack([points, np.ones((points.shape[0], 1))])
        world_points_homo = (extrinsics @ points_homo.T).T
        return world_points_homo[:, :3]
    
    def merge_detections(self, detections: List[Detection3D], 
                        distance_threshold: float = 2.0) -> List[Detection3D]:
        """Merge detections from multiple views"""
        if not detections:
            return []
        
        merged = []
        used = set()
        
        for i, det1 in enumerate(detections):
            if i in used:
                continue
            
            # Find nearby detections
            cluster = [det1]
            used.add(i)
            
            for j, det2 in enumerate(detections[i+1:], i+1):
                if j in used:
                    continue
                
                distance = np.linalg.norm(det1.center_3d - det2.center_3d)
                if distance < distance_threshold:
                    cluster.append(det2)
                    used.add(j)
            
            # Merge cluster
            if len(cluster) == 1:
                merged.append(cluster[0])
            else:
                merged_det = self.merge_cluster(cluster)
                merged.append(merged_det)
        
        return merged
    
    def merge_cluster(self, detections: List[Detection3D]) -> Detection3D:
        """Merge a cluster of detections"""
        # Average center position
        centers = np.array([det.center_3d for det in detections])
        avg_center = np.mean(centers, axis=0)
        
        # Use detection with highest confidence as base
        base_det = max(detections, key=lambda d: d.confidence)
        
        # Update center
        merged_det = Detection3D(
            class_id=base_det.class_id,
            class_name=base_det.class_name,
            confidence=base_det.confidence,
            bbox_2d=base_det.bbox_2d,
            bbox_3d=base_det.bbox_3d,
            center_3d=avg_center,
            dimensions=base_det.dimensions,
            rotation_y=base_det.rotation_y,
            depth=np.linalg.norm(avg_center),
            velocity=base_det.velocity
        )
        
        return merged_det


# Factory function
def create_3d_detector(config: Dict) -> Vehicle3DDetector:
    """Factory function to create 3D detector"""
    return Vehicle3DDetector(
        camera_matrix=np.array(config['camera_matrix']),
        dist_coeffs=np.array(config['dist_coeffs']),
        use_stereo=config.get('use_stereo', False),
        baseline=config.get('baseline', 0.1)
    )


def create_multi_view_detector(configs: List[Dict]) -> MultiViewDetector:
    """Factory function to create multi-view detector"""
    return MultiViewDetector(configs)