"""
License Plate Recognition System

Implements advanced license plate detection and recognition using
deep learning and traditional computer vision techniques.
"""

import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import re
import logging
from collections import defaultdict
import easyocr
import pytesseract

logger = logging.getLogger(__name__)


@dataclass
class LicensePlate:
    """License plate detection and recognition result"""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    text: str
    confidence_text: float
    country_code: Optional[str] = None
    plate_type: Optional[str] = None
    corners: Optional[np.ndarray] = None  # 4 corner points
    perspective_corrected: Optional[np.ndarray] = None


class PlateDetector(nn.Module):
    """Deep learning license plate detector"""
    
    def __init__(self, input_size: Tuple[int, int] = (640, 640)):
        super().__init__()
        self.input_size = input_size
        
        # Backbone (simplified ResNet-like)
        self.backbone = nn.Sequential(
            # Initial conv
            nn.Conv2d(3, 64, 7, stride=2, padding=3),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(3, stride=2, padding=1),
            
            # Stage 1
            nn.Conv2d(64, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            
            # Stage 2
            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            
            # Stage 3
            nn.Conv2d(128, 256, 3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )
        
        # Detection head
        self.detection_head = nn.Sequential(
            nn.Conv2d(256, 128, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 64, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 5, 1),  # 4 bbox coords + 1 confidence
            nn.Sigmoid()
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        detections = self.detection_head(features)
        return detections


class TraditionalPlateDetector:
    """Traditional computer vision plate detection"""
    
    def __init__(self):
        # Cascade classifier for plate detection
        self.plate_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_license_plate_rus_16stages.xml')
        
    def detect_plates(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect license plates using traditional methods"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Method 1: Cascade classifier
        plates_cascade = self.plate_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Method 2: Morphological operations
        plates_morph = self._detect_with_morphology(gray)
        
        # Method 3: Edge detection
        plates_edge = self._detect_with_edges(gray)
        
        # Combine all detections
        all_plates = list(plates_cascade) + plates_morph + plates_edge
        
        # Remove duplicates
        filtered_plates = self._filter_overlapping_boxes(all_plates)
        
        return filtered_plates
    
    def _detect_with_morphology(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect plates using morphological operations"""
        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        plates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Aspect ratio filter
            aspect_ratio = w / h
            if 2.0 < aspect_ratio < 6.0 and w > 80 and h > 20:
                plates.append((x, y, x + w, y + h))
        
        return plates
    
    def _detect_with_edges(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect plates using edge detection"""
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        plates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Aspect ratio and area filter
            aspect_ratio = w / h
            area = w * h
            if 2.0 < aspect_ratio < 6.0 and area > 2000:
                plates.append((x, y, x + w, y + h))
        
        return plates
    
    def _filter_overlapping_boxes(self, boxes: List[Tuple[int, int, int, int]], 
                                 iou_threshold: float = 0.3) -> List[Tuple[int, int, int, int]]:
        """Filter overlapping bounding boxes"""
        if not boxes:
            return []
        
        # Convert to numpy array
        boxes = np.array(boxes)
        
        # Calculate areas
        areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        
        # Sort by confidence (area in this case)
        indices = np.argsort(areas)[::-1]
        
        keep = []
        while len(indices) > 0:
            current = indices[0]
            keep.append(current)
            
            if len(indices) == 1:
                break
            
            # Calculate IoU
            current_box = boxes[current]
            remaining_boxes = boxes[indices[1:]]
            
            xx1 = np.maximum(current_box[0], remaining_boxes[:, 0])
            yy1 = np.maximum(current_box[1], remaining_boxes[:, 1])
            xx2 = np.minimum(current_box[2], remaining_boxes[:, 2])
            yy2 = np.minimum(current_box[3], remaining_boxes[:, 3])
            
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            
            intersection = w * h
            union = areas[current] + areas[indices[1:]] - intersection
            
            iou = intersection / union
            
            indices = indices[1:][iou < iou_threshold]
        
        return [tuple(boxes[i]) for i in keep]


class PlateRecognizer:
    """License plate text recognition"""
    
    def __init__(self, method: str = 'easyocr'):
        self.method = method
        
        if method == 'easyocr':
            self.reader = easyocr.Reader(['en'])
        elif method == 'tesseract':
            # Configure Tesseract for license plates
            self.tesseract_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        else:
            raise ValueError(f"Unsupported OCR method: {method}")
    
    def recognize_plate(self, plate_image: np.ndarray) -> Tuple[str, float]:
        """Recognize text from license plate image"""
        # Preprocess plate image
        processed_image = self._preprocess_plate(plate_image)
        
        if self.method == 'easyocr':
            result = self.reader.readtext(processed_image)
            if result:
                text = result[0][1]
                confidence = result[0][2]
            else:
                text = ""
                confidence = 0.0
        
        elif self.method == 'tesseract':
            text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)
            text = text.strip().replace(' ', '')
            confidence = 0.8  # Tesseract doesn't provide reliable confidence
        
        # Post-process text
        text = self._postprocess_text(text)
        
        return text, confidence
    
    def _preprocess_plate(self, image: np.ndarray) -> np.ndarray:
        """Preprocess license plate image for OCR"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize
        height, width = gray.shape
        if height < 50:
            scale = 50 / height
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Apply threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return binary
    
    def _postprocess_text(self, text: str) -> str:
        """Post-process recognized text"""
        # Remove non-alphanumeric characters
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Common corrections
        corrections = {
            'O': '0',  # O to 0
            'I': '1',  # I to 1
            'S': '5',  # S to 5
            'Z': '2',  # Z to 2
            'G': '6',  # G to 6
            'B': '8',  # B to 8
        }
        
        # Apply corrections based on context
        corrected_text = ""
        for i, char in enumerate(text):
            if char in corrections and i > 0 and i < len(text) - 1:
                # Check if it's likely a number based on position
                if i in [2, 3]:  # Common positions for numbers
                    corrected_text += corrections[char]
                else:
                    corrected_text += char
            else:
                corrected_text += char
        
        return corrected_text


class PlateValidator:
    """License plate format validation"""
    
    def __init__(self, country_code: str = 'US'):
        self.country_code = country_code
        
        # Define plate patterns for different countries
        self.patterns = {
            'US': r'^[A-Z]{2}\d{4,6}$',  # 2 letters + 4-6 digits
            'UK': r'^[A-Z]{2}\d{2}[A-Z]{3}$',  # 2 letters + 2 digits + 3 letters
            'DE': r'^[A-Z]{1,3}-[A-Z]{1,2}-\d{1,4}$',  # German format
            'FR': r'^[A-Z]{2}-\d{3}-[A-Z]{2}$',  # French format
            'CN': r'^[A-Z]{1}[A-Z0-9]{5,6}$',  # Chinese format
        }
    
    def validate_plate(self, plate_text: str, country_code: Optional[str] = None) -> bool:
        """Validate license plate format"""
        if not plate_text:
            return False
        
        country = country_code or self.country_code
        
        if country in self.patterns:
            pattern = self.patterns[country]
            return bool(re.match(pattern, plate_text))
        
        # Default validation: at least 5 characters, mix of letters and numbers
        return len(plate_text) >= 5 and any(c.isdigit() for c in plate_text) and any(c.isalpha() for c in plate_text)
    
    def detect_country(self, plate_text: str) -> Optional[str]:
        """Detect country based on plate format"""
        for country, pattern in self.patterns.items():
            if re.match(pattern, plate_text):
                return country
        return None


class LicensePlateRecognizer:
    """Main license plate recognition system"""
    
    def __init__(self, 
                 detection_method: str = 'traditional',
                 recognition_method: str = 'easyocr',
                 country_code: str = 'US'):
        self.detection_method = detection_method
        self.recognition_method = recognition_method
        self.country_code = country_code
        
        # Initialize components
        if detection_method == 'deep_learning':
            self.detector = PlateDetector()
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.detector.to(self.device)
            self.detector.eval()
        else:
            self.detector = TraditionalPlateDetector()
        
        self.recognizer = PlateRecognizer(recognition_method)
        self.validator = PlateValidator(country_code)
        
        # Tracking for multiple frames
        self.plate_history = defaultdict(list)
        self.frame_count = 0
    
    def detect_plates(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect license plates in image"""
        if self.detection_method == 'deep_learning':
            return self._detect_with_dl(image)
        else:
            return self.detector.detect_plates(image)
    
    def _detect_with_dl(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect plates using deep learning"""
        # Preprocess image
        h, w = image.shape[:2]
        input_size = self.detector.input_size
        
        # Resize and normalize
        img_resized = cv2.resize(image, input_size)
        img_tensor = torch.from_numpy(img_resized.transpose(2, 0, 1)).float().unsqueeze(0) / 255.0
        img_tensor = img_tensor.to(self.device)
        
        with torch.no_grad():
            detections = self.detector(img_tensor)
        
        # Post-process detections
        detections = detections.squeeze().cpu().numpy()
        
        # Convert to original image size
        plates = []
        for i in range(0, detections.shape[0], 5):
            if i + 4 < detections.shape[0]:
                confidence = detections[i + 4]
                if confidence > 0.5:
                    # Normalize coordinates
                    x1 = int(detections[i] * w)
                    y1 = int(detections[i + 1] * h)
                    x2 = int(detections[i + 2] * w)
                    y2 = int(detections[i + 3] * h)
                    
                    plates.append((x1, y1, x2, y2))
        
        return plates
    
    def recognize_plates(self, image: np.ndarray, 
                        plate_boxes: List[Tuple[int, int, int, int]]) -> List[LicensePlate]:
        """Recognize text from detected license plates"""
        plates = []
        
        for bbox in plate_boxes:
            x1, y1, x2, y2 = bbox
            
            # Extract plate region
            plate_region = image[y1:y2, x1:x2]
            
            if plate_region.size == 0:
                continue
            
            # Perspective correction if needed
            corrected_plate = self._correct_perspective(plate_region)
            
            # Recognize text
            text, confidence = self.recognizer.recognize_plate(corrected_plate)
            
            # Validate plate
            is_valid = self.validator.validate_plate(text)
            detected_country = self.validator.detect_country(text)
            
            if is_valid or confidence > 0.7:  # Accept high confidence even if format is unusual
                plate = LicensePlate(
                    bbox=bbox,
                    confidence=1.0,  # Detection confidence
                    text=text,
                    confidence_text=confidence,
                    country_code=detected_country,
                    perspective_corrected=corrected_plate
                )
                plates.append(plate)
        
        return plates
    
    def _correct_perspective(self, plate_image: np.ndarray) -> np.ndarray:
        """Correct perspective distortion in license plate"""
        gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        
        # Find corners
        corners = cv2.goodFeaturesToTrack(gray, 4, 0.01, 10)
        
        if corners is not None and len(corners) == 4:
            corners = np.float32(corners).reshape(-1, 2)
            
            # Order corners
            corners = self._order_corners(corners)
            
            # Define destination corners
            h, w = plate_image.shape[:2]
            dst_corners = np.array([
                [0, 0],
                [w, 0],
                [w, h],
                [0, h]
            ], dtype=np.float32)
            
            # Calculate perspective transform
            M = cv2.getPerspectiveTransform(corners, dst_corners)
            
            # Apply transform
            corrected = cv2.warpPerspective(plate_image, M, (w, h))
            return corrected
        
        return plate_image
    
    def _order_corners(self, corners: np.ndarray) -> np.ndarray:
        """Order corners for perspective transform"""
        # Calculate centroid
        center = np.mean(corners, axis=0)
        
        # Sort by angle from center
        def angle_from_center(point):
            return np.arctan2(point[1] - center[1], point[0] - center[0])
        
        corners_sorted = sorted(corners, key=angle_from_center)
        
        # Reorder to: top-left, top-right, bottom-right, bottom-left
        ordered = np.array([
            corners_sorted[1],  # top-left
            corners_sorted[0],  # top-right
            corners_sorted[2],  # bottom-right
            corners_sorted[3]   # bottom-left
        ], dtype=np.float32)
        
        return ordered
    
    def track_plates(self, plates: List[LicensePlate]) -> List[LicensePlate]:
        """Track license plates across frames"""
        self.frame_count += 1
        
        # Add current plates to history
        for plate in plates:
            self.plate_history[plate.text].append((self.frame_count, plate))
        
        # Remove old entries (older than 30 frames)
        for text in list(self.plate_history.keys()):
            self.plate_history[text] = [
                (frame, plate) for frame, plate in self.plate_history[text]
                if self.frame_count - frame < 30
            ]
            
            if not self.plate_history[text]:
                del self.plate_history[text]
        
        return plates
    
    def get_stable_plates(self, min_appearances: int = 3) -> List[LicensePlate]:
        """Get plates that appear consistently across frames"""
        stable_plates = []
        
        for text, history in self.plate_history.items():
            if len(history) >= min_appearances:
                # Get the most recent detection
                latest_frame, latest_plate = max(history, key=lambda x: x[0])
                stable_plates.append(latest_plate)
        
        return stable_plates
    
    def process_image(self, image: np.ndarray) -> List[LicensePlate]:
        """Complete license plate recognition pipeline"""
        # Detect plates
        plate_boxes = self.detect_plates(image)
        
        # Recognize text
        plates = self.recognize_plates(image, plate_boxes)
        
        # Track plates
        plates = self.track_plates(plates)
        
        return plates
    
    def visualize_results(self, image: np.ndarray, 
                         plates: List[LicensePlate]) -> np.ndarray:
        """Visualize license plate recognition results"""
        vis_image = image.copy()
        
        for plate in plates:
            x1, y1, x2, y2 = plate.bbox
            
            # Draw bounding box
            color = (0, 255, 0) if plate.confidence_text > 0.7 else (0, 0, 255)
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
            
            # Draw text
            label = f"{plate.text} ({plate.confidence_text:.2f})"
            if plate.country_code:
                label += f" [{plate.country_code}]"
            
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(vis_image, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(vis_image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return vis_image


# Factory functions
def create_plate_recognizer(config: Dict) -> LicensePlateRecognizer:
    """Factory function to create license plate recognizer"""
    return LicensePlateRecognizer(
        detection_method=config.get('detection_method', 'traditional'),
        recognition_method=config.get('recognition_method', 'easyocr'),
        country_code=config.get('country_code', 'US')
    )


def create_batch_processor(config: Dict):
    """Create batch processor for multiple images"""
    recognizer = create_plate_recognizer(config)
    
    def process_batch(images: List[np.ndarray]) -> List[List[LicensePlate]]:
        results = []
        for image in images:
            plates = recognizer.process_image(image)
            results.append(plates)
        return results
    
    return process_batch