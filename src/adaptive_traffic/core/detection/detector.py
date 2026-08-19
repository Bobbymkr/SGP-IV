"""
Vehicle Detection Module
YOLOv8-based vehicle detection for traffic monitoring
"""

import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from ultralytics import YOLO
import torch
import logging

logger = logging.getLogger(__name__)


@dataclass
class VehicleDetection:
    """Vehicle detection result"""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    direction: Optional[str] = None
    speed: Optional[float] = None


@dataclass
class DetectionResult:
    """Complete detection result for a frame"""
    frame_id: int
    timestamp: float
    detections: List[VehicleDetection]
    processing_time: float
    image_shape: Tuple[int, int]


class VehicleDetector:
    """YOLOv8-based vehicle detector optimized for traffic monitoring"""
    
    # COCO class IDs for vehicles
    VEHICLE_CLASSES = {
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck',
        1: 'bicycle'
    }
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = "auto",
        image_size: int = 640
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.image_size = image_size
        
        # Setup device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # Load model
        logger.info(f"Loading YOLO model from {model_path} on {self.device}")
        self.model = YOLO(model_path)
        self.model.to(self.device)
        
        # Warm up
        dummy = np.zeros((image_size, image_size, 3), dtype=np.uint8)
        _ = self.model(dummy, verbose=False)
        
        logger.info("Vehicle detector initialized successfully")
    
    def detect(self, image: np.ndarray) -> List[VehicleDetection]:
        """Detect vehicles in a single frame"""
        # Run inference
        results = self.model(
            image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.image_size,
            verbose=False,
            device=self.device
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            
            for box in boxes:
                class_id = int(box.cls[0])
                
                # Filter for vehicle classes only
                if class_id not in self.VEHICLE_CLASSES:
                    continue
                
                confidence = float(box.conf[0])
                if confidence < self.confidence_threshold:
                    continue
                
                # Get bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Calculate center
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                detection = VehicleDetection(
                    class_id=class_id,
                    class_name=self.VEHICLE_CLASSES[class_id],
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                    center=(center_x, center_y)
                )
                
                detections.append(detection)
        
        return detections
    
    def detect_batch(self, images: List[np.ndarray]) -> List[List[VehicleDetection]]:
        """Detect vehicles in multiple frames"""
        results = self.model(
            images,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.image_size,
            verbose=False,
            device=self.device
        )
        
        batch_detections = []
        for i, result in enumerate(results):
            detections = []
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    if class_id not in self.VEHICLE_CLASSES:
                        continue
                    
                    confidence = float(box.conf[0])
                    if confidence < self.confidence_threshold:
                        continue
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    detection = VehicleDetection(
                        class_id=class_id,
                        class_name=self.VEHICLE_CLASSES[class_id],
                        confidence=confidence,
                        bbox=(x1, y1, x2, y2),
                        center=(center_x, center_y)
                    )
                    detections.append(detection)
            
            batch_detections.append(detections)
        
        return batch_detections
    
    def count_by_direction(self, detections: List[VehicleDetection], 
                          roi_polygons: Dict[str, np.ndarray]) -> Dict[str, Dict[str, int]]:
        """Count vehicles by direction using ROI polygons"""
        counts = {direction: {cls: 0 for cls in self.VEHICLE_CLASSES.values()} 
                  for direction in roi_polygons}
        counts['total'] = {direction: 0 for direction in roi_polygons}
        
        for det in detections:
            center = det.center
            for direction, polygon in roi_polygons.items():
                if cv2.pointPolygonTest(polygon, center, False) >= 0:
                    counts[direction][det.class_name] += 1
                    counts['total'][direction] += 1
                    break
        
        return counts
    
    def visualize(self, image: np.ndarray, detections: List[VehicleDetection]) -> np.ndarray:
        """Draw detections on image"""
        vis = image.copy()
        
        colors = {
            'car': (0, 255, 0),
            'truck': (255, 0, 0),
            'bus': (0, 0, 255),
            'motorcycle': (255, 255, 0),
            'bicycle': (0, 255, 255)
        }
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = colors.get(det.class_name, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{det.class_name}: {det.confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(vis, (x1, y1 - label_size[1] - 5), 
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(vis, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Draw center point
            cv2.circle(vis, det.center, 4, color, -1)
        
        return vis


class MultiCameraDetector:
    """Multi-camera vehicle detection with fusion"""
    
    def __init__(self, camera_configs: List[Dict]):
        self.detectors = {}
        for config in camera_configs:
            camera_id = config['camera_id']
            self.detectors[camera_id] = VehicleDetector(
                model_path=config.get('model_path', 'yolov8n.pt'),
                confidence_threshold=config.get('confidence', 0.5),
                iou_threshold=config.get('iou', 0.45),
                device=config.get('device', 'auto')
            )
    
    def detect_all(self, images: Dict[str, np.ndarray]) -> Dict[str, List[VehicleDetection]]:
        """Run detection on all cameras"""
        results = {}
        for camera_id, image in images.items():
            if camera_id in self.detectors:
                results[camera_id] = self.detectors[camera_id].detect(image)
        return results
    
    def count_all_directions(self, detections: Dict[str, List[VehicleDetection]],
                           roi_configs: Dict[str, Dict[str, np.ndarray]]) -> Dict[str, Dict]:
        """Count vehicles across all cameras by direction"""
        all_counts = {}
        for camera_id, camera_detections in detections.items():
            if camera_id in roi_configs:
                all_counts[camera_id] = self.detectors[camera_id].count_by_direction(
                    camera_detections, roi_configs[camera_id]
                )
        return all_counts


def create_detector(config: Dict) -> VehicleDetector:
    """Factory function to create vehicle detector"""
    return VehicleDetector(
        model_path=config.get('model_path', 'yolov8n.pt'),
        confidence_threshold=config.get('confidence_threshold', 0.5),
        iou_threshold=config.get('iou_threshold', 0.45),
        device=config.get('device', 'auto'),
        image_size=config.get('image_size', 640)
    )