"""
Queue Length Estimator
Converts vehicle detections to per-lane queue lengths using city profile parameters
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from adaptive_traffic.config.city_profile import CityProfile
from adaptive_traffic.core.control.policies import normalize_class
from adaptive_traffic.core.domain import VehicleDetection, VehicleType
from adaptive_traffic.core.monitoring import observe

logger = logging.getLogger(__name__)


@dataclass
class LaneQueue:
    """Queue length estimate for a single lane"""

    lane_id: str
    direction: str
    vehicle_count: int
    total_length_m: float
    avg_spacing_m: float
    confidence: float


@dataclass
class QueueEstimate:
    """Complete queue estimate for an intersection"""

    intersection_id: str
    timestamp: float
    lanes: List[LaneQueue]
    by_direction: Dict[str, LaneQueue]
    total_vehicles: int
    total_length_m: float
    # Queued vehicles per direction per normalized class (headway-table keys);
    # feeds the weighted green policy. Empty when estimated from BSM-only paths
    # that carry no class info (never None — callers sum it directly).
    by_class: Dict[str, Dict[str, int]] = field(default_factory=dict)


class QueueEstimator:
    """Estimates queue lengths from vehicle detections using city profile"""

    def __init__(self, city_profile: CityProfile):
        self.profile = city_profile
        self.vehicle_lengths = self._get_vehicle_lengths()
        self.class_mapping = self._get_class_mapping()
        self.detector_calibration = city_profile.detector_calibration
        self.queue_params = city_profile.queue_estimation

        # Camera geometry parameters (would come from calibration in production)
        self.camera_height_m = 8.0
        self.camera_fov_deg = 90.0
        self.image_width_px = 640
        self.image_height_px = 480

    def _get_vehicle_lengths(self) -> Dict[str, float]:
        """Get vehicle lengths from profile"""
        return {
            "car": self.profile.vehicle_lengths.car,
            "bus": self.profile.vehicle_lengths.bus,
            "truck": self.profile.vehicle_lengths.truck,
            "two_wheeler": self.profile.vehicle_lengths.two_wheeler,
            "autorickshaw": self.profile.vehicle_lengths.autorickshaw,
            "cycle": self.profile.vehicle_lengths.cycle,
            "tractor": self.profile.vehicle_lengths.tractor,
            "bus_pedigree": self.profile.vehicle_lengths.bus_pedigree,
        }

    def _get_class_mapping(self) -> Dict[int, str]:
        """Get class ID to name mapping from profile"""
        # Handle both int keys (from JSON) and string keys
        mapping = {}
        for k, v in self.profile.class_mapping.items():
            if isinstance(k, str):
                mapping[int(k)] = v
            else:
                mapping[k] = v
        return mapping

    @observe("estimate")
    def estimate_from_detections(
        self,
        detections: List[VehicleDetection],
        intersection_id: str = "main",
        timestamp: float = 0.0,
    ) -> QueueEstimate:
        """Estimate queue lengths from vehicle detections"""

        # Group detections by direction/lane
        lane_detections = self._group_by_lane(detections)

        # Estimate queue per lane
        lane_queues = []
        lane_class_counts: Dict[str, Dict[str, int]] = {}
        for lane_key, lane_dets in lane_detections.items():
            queue, class_counts = self._estimate_lane_queue(lane_key, lane_dets)
            lane_queues.append(queue)
            lane_class_counts[lane_key] = class_counts

        # Aggregate by direction
        by_direction = {}
        for queue in lane_queues:
            if queue.direction in by_direction:
                # Combine lanes in same direction
                existing = by_direction[queue.direction]
                by_direction[queue.direction] = LaneQueue(
                    lane_id=f"{queue.direction}_combined",
                    direction=queue.direction,
                    vehicle_count=existing.vehicle_count + queue.vehicle_count,
                    total_length_m=existing.total_length_m + queue.total_length_m,
                    avg_spacing_m=(existing.avg_spacing_m + queue.avg_spacing_m) / 2,
                    confidence=min(existing.confidence, queue.confidence),
                )
            else:
                by_direction[queue.direction] = queue

        # Aggregate per-class queue counts by direction (single pass: lane keys
        # are f"{direction}_{lane_idx}", same split as _estimate_lane_queue).
        by_class: Dict[str, Dict[str, int]] = {}
        for lane_key, counts in lane_class_counts.items():
            direction = lane_key.split("_", 1)[0]
            direction_counts = by_class.setdefault(direction, {})
            for cls, n in counts.items():
                direction_counts[cls] = direction_counts.get(cls, 0) + n

        total_vehicles = sum(q.vehicle_count for q in lane_queues)
        total_length = sum(q.total_length_m for q in lane_queues)

        return QueueEstimate(
            intersection_id=intersection_id,
            timestamp=timestamp,
            lanes=lane_queues,
            by_direction=by_direction,
            total_vehicles=total_vehicles,
            total_length_m=total_length,
            by_class=by_class,
        )

    def _group_by_lane(
        self, detections: List[VehicleDetection]
    ) -> Dict[str, List[VehicleDetection]]:
        """Group detections by lane using bbox position and calibration"""
        lane_groups = {}

        for det in detections:
            # Get vehicle class name
            class_name = self.class_mapping.get(det.class_id, "car")

            # Get lane from detection (if available) or estimate from bbox
            lane_id = getattr(det, "lane_id", None)
            if lane_id is None:
                lane_id = self._estimate_lane_from_bbox(det.bbox)

            direction = getattr(det, "direction", None)
            if direction is None:
                direction = self._estimate_direction_from_bbox(det.bbox)

            lane_key = f"{direction}_{lane_id}"

            if lane_key not in lane_groups:
                lane_groups[lane_key] = []
            lane_groups[lane_key].append(det)

        return lane_groups

    def _estimate_lane_from_bbox(self, bbox: Tuple[int, int, int, int]) -> int:
        """Estimate lane index from bounding box horizontal position"""
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2

        # Simple lane estimation based on horizontal position
        # In production, this would use homography matrix
        lane_width_px = self.image_width_px / self.profile.lanes_per_approach
        lane_idx = int(center_x / lane_width_px)
        return min(lane_idx, self.profile.lanes_per_approach - 1)

    def _estimate_direction_from_bbox(self, bbox: Tuple[int, int, int, int]) -> str:
        """Estimate approach direction from bounding box vertical position"""
        x1, y1, x2, y2 = bbox
        center_y = (y1 + y2) / 2

        # Simple direction estimation based on vertical position
        # Top of image = north, bottom = south, left = west, right = east
        # This is a simplified heuristic
        if center_y < self.image_height_px / 3:
            return "north"
        elif center_y > 2 * self.image_height_px / 3:
            return "south"
        elif x1 < self.image_width_px / 2:
            return "west"
        else:
            return "east"

    def _estimate_lane_queue(
        self, lane_key: str, detections: List[VehicleDetection]
    ) -> Tuple[LaneQueue, Dict[str, int]]:
        """Estimate queue length for a single lane.

        Returns the lane queue plus per-class counts of queue-zone vehicles
        (normalized headway-table keys) for the weighted green policy.
        """
        direction, lane_idx = lane_key.split("_", 1)
        lane_idx = int(lane_idx)

        # Filter detections in queue zone
        queue_detections = []
        for det in detections:
            class_name = self.class_mapping.get(det.class_id, "car")
            distance = self._estimate_distance_to_stop_line(det.bbox, direction)

            if distance is not None and distance <= self.queue_params["queue_zone_distance"]:
                queue_detections.append((det, class_name, distance))

        if not queue_detections:
            return (
                LaneQueue(
                    lane_id=lane_key,
                    direction=direction,
                    vehicle_count=0,
                    total_length_m=0.0,
                    avg_spacing_m=0.0,
                    confidence=1.0,
                ),
                {},
            )

        # Sort by distance to stop line (closest first)
        queue_detections.sort(key=lambda x: x[2])

        # Calculate total queue length
        total_length = 0.0
        for i, (det, class_name, distance) in enumerate(queue_detections):
            vehicle_len = self.vehicle_lengths.get(class_name, 4.5)
            total_length += vehicle_len + self.queue_params["vehicle_length_buffer"]

            # Add gap between vehicles (except for last vehicle)
            if i < len(queue_detections) - 1:
                next_distance = queue_detections[i + 1][2]
                gap = next_distance - distance - vehicle_len
                total_length += max(gap, self.queue_params["min_gap"])

        avg_spacing = total_length / len(queue_detections) if queue_detections else 0

        # Confidence based on detection count and calibration
        calibration_factor = self.detector_calibration.__dict__.get(direction, 0.05)
        confidence = min(1.0, len(queue_detections) * calibration_factor * 10)

        class_counts: Dict[str, int] = {}
        for _, class_name, _ in queue_detections:
            key = normalize_class(class_name)
            class_counts[key] = class_counts.get(key, 0) + 1

        return (
            LaneQueue(
                lane_id=lane_key,
                direction=direction,
                vehicle_count=len(queue_detections),
                total_length_m=total_length,
                avg_spacing_m=avg_spacing,
                confidence=confidence,
            ),
            class_counts,
        )

    def _estimate_distance_to_stop_line(
        self, bbox: Tuple[int, int, int, int], direction: str
    ) -> Optional[float]:
        """Estimate distance from vehicle to stop line using camera calibration"""
        x1, y1, x2, y2 = bbox

        # Use bottom of bbox (closest to camera) for distance estimation
        vehicle_bottom_y = y2

        # Get calibration factor for this approach
        px_to_m = self.detector_calibration.__dict__.get(direction, 0.05)

        # Simple perspective projection: distance proportional to vertical position
        # In production, use full homography matrix from camera calibration
        normalized_y = vehicle_bottom_y / self.image_height_px

        # Distance increases as vehicle is higher in image (further from camera)
        # This is inverted: bottom of image = close, top = far
        max_distance = 100.0  # meters
        distance = max_distance * (1.0 - normalized_y)

        return distance

    def estimate_from_bsm(
        self, bsm_vehicles: List[Dict], intersection_id: str = "main", timestamp: float = 0.0
    ) -> QueueEstimate:
        """Estimate queue lengths from BSM (J2735) vehicle data"""

        lane_groups = {}
        for vehicle in bsm_vehicles:
            lane_id = vehicle.get("lane_id", 0)
            direction = vehicle.get("direction", "north")
            distance = vehicle.get("distance_to_stop_line", 0)

            lane_key = f"{direction}_{lane_id}"
            if lane_key not in lane_groups:
                lane_groups[lane_key] = []
            lane_groups[lane_key].append(vehicle)

        lane_queues = []
        by_class: Dict[str, Dict[str, int]] = {}
        for lane_key, vehicles in lane_groups.items():
            direction, lane_idx = lane_key.split("_", 1)
            lane_idx = int(lane_idx)

            # Count vehicles in queue zone
            queue_count = sum(
                1
                for v in vehicles
                if v.get("distance_to_stop_line", 100) <= self.queue_params["queue_zone_distance"]
            )

            # Estimate length from BSM data
            total_length = 0.0
            for v in vehicles:
                if v.get("distance_to_stop_line", 100) <= self.queue_params["queue_zone_distance"]:
                    vtype = v.get("vehicle_type", "car")
                    vehicle_len = self.vehicle_lengths.get(vtype, 4.5)
                    total_length += vehicle_len + self.queue_params["vehicle_length_buffer"]
                    key = normalize_class(vtype)
                    direction_counts = by_class.setdefault(direction, {})
                    direction_counts[key] = direction_counts.get(key, 0) + 1

            lane_queues.append(
                LaneQueue(
                    lane_id=lane_key,
                    direction=direction,
                    vehicle_count=queue_count,
                    total_length_m=total_length,
                    avg_spacing_m=total_length / queue_count if queue_count > 0 else 0,
                    confidence=0.9,  # High confidence from V2X
                )
            )

        # Aggregate by direction
        by_direction = {}
        for queue in lane_queues:
            if queue.direction in by_direction:
                existing = by_direction[queue.direction]
                by_direction[queue.direction] = LaneQueue(
                    lane_id=f"{queue.direction}_combined",
                    direction=queue.direction,
                    vehicle_count=existing.vehicle_count + queue.vehicle_count,
                    total_length_m=existing.total_length_m + queue.total_length_m,
                    avg_spacing_m=(existing.avg_spacing_m + queue.avg_spacing_m) / 2,
                    confidence=min(existing.confidence, queue.confidence),
                )
            else:
                by_direction[queue.direction] = queue

        total_vehicles = sum(q.vehicle_count for q in lane_queues)
        total_length = sum(q.total_length_m for q in lane_queues)

        return QueueEstimate(
            intersection_id=intersection_id,
            timestamp=timestamp,
            lanes=lane_queues,
            by_direction=by_direction,
            total_vehicles=total_vehicles,
            total_length_m=total_length,
            by_class=by_class,
        )


def create_queue_estimator(city_profile: CityProfile) -> QueueEstimator:
    """Factory function to create queue estimator"""
    return QueueEstimator(city_profile)
