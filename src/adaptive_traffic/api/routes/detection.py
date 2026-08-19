"""
Vehicle detection endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import base64
import numpy as np

router = APIRouter()


class DetectionResult(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]
    center: List[int]
    track_id: Optional[int] = None


class DetectionResponse(BaseModel):
    frame_id: int
    timestamp: str
    detections: List[DetectionResult]
    processing_time: float
    counts_by_class: Dict[str, int]
    counts_by_direction: Optional[Dict[str, Dict[str, int]]] = None


class CameraConfig(BaseModel):
    camera_id: str
    intersection_id: str
    direction: str
    roi_polygons: Optional[Dict[str, List[List[int]]]] = None
    enabled: bool = True


# In-memory storage
cameras_db: Dict[str, CameraConfig] = {}
detection_history: List[DetectionResponse] = []


@router.post("/detect", response_model=DetectionResponse)
async def detect_vehicles(
    file: UploadFile = File(...),
    camera_id: str = Form(...),
    frame_id: int = Form(...),
    roi_config: Optional[str] = Form(None)
):
    """Detect vehicles in uploaded image"""
    # Read image
    contents = await file.read()
    
    # In real implementation, decode image and run detection
    # For now, return mock response
    mock_detections = [
        DetectionResult(
            class_id=2,
            class_name="car",
            confidence=0.95,
            bbox=[100, 200, 250, 320],
            center=[175, 260]
        ),
        DetectionResult(
            class_id=7,
            class_name="truck",
            confidence=0.88,
            bbox=[300, 180, 480, 350],
            center=[390, 265]
        )
    ]
    
    response = DetectionResponse(
        frame_id=frame_id,
        timestamp=datetime.utcnow().isoformat(),
        detections=mock_detections,
        processing_time=0.045,
        counts_by_class={"car": 1, "truck": 1}
    )
    
    # Store in history
    detection_history.append(response)
    if len(detection_history) > 1000:
        detection_history.pop(0)
    
    return response


@router.post("/detect/batch", response_model=List[DetectionResponse])
async def detect_batch(
    files: List[UploadFile] = File(...),
    camera_id: str = Form(...)
):
    """Detect vehicles in batch of images"""
    results = []
    for i, file in enumerate(files):
        contents = await file.read()
        # Process each image
        results.append(DetectionResponse(
            frame_id=i,
            timestamp=datetime.utcnow().isoformat(),
            detections=[],
            processing_time=0.04,
            counts_by_class={}
        ))
    return results


@router.get("/history", response_model=List[DetectionResponse])
async def get_detection_history(
    camera_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get detection history"""
    history = detection_history[::-1]  # Most recent first
    
    if camera_id:
        # Filter by camera (would need camera_id in response)
        pass
    
    return history[offset:offset+limit]


@router.get("/counts/{camera_id}")
async def get_vehicle_counts(camera_id: str, window_minutes: int = 5):
    """Get aggregated vehicle counts for time window"""
    # Mock response
    return {
        "camera_id": camera_id,
        "window_minutes": window_minutes,
        "counts_by_class": {
            "car": 142,
            "truck": 23,
            "bus": 8,
            "motorcycle": 15,
            "bicycle": 31
        },
        "counts_by_direction": {
            "north": {"car": 45, "truck": 5, "total": 50},
            "south": {"car": 38, "truck": 8, "total": 46},
            "east": {"car": 32, "truck": 4, "total": 36},
            "west": {"car": 27, "truck": 6, "total": 33}
        },
        "total": 165,
        "timestamp": datetime.utcnow().isoformat()
    }


# Camera management
@router.post("/cameras/", response_model=CameraConfig)
async def register_camera(camera: CameraConfig):
    """Register a new camera"""
    cameras_db[camera.camera_id] = camera
    return camera


@router.get("/cameras/", response_model=List[CameraConfig])
async def list_cameras():
    """List all registered cameras"""
    return list(cameras_db.values())


@router.get("/cameras/{camera_id}", response_model=CameraConfig)
async def get_camera(camera_id: str):
    """Get camera configuration"""
    if camera_id not in cameras_db:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cameras_db[camera_id]


@router.put("/cameras/{camera_id}", response_model=CameraConfig)
async def update_camera(camera_id: str, camera: CameraConfig):
    """Update camera configuration"""
    if camera_id not in cameras_db:
        raise HTTPException(status_code=404, detail="Camera not found")
    cameras_db[camera_id] = camera
    return camera


@router.delete("/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """Delete camera"""
    if camera_id not in cameras_db:
        raise HTTPException(status_code=404, detail="Camera not found")
    del cameras_db[camera_id]
    return {"message": "Camera deleted"}