"""Per-camera estimator geometry: calibration overrides legacy 640x480 buckets."""

from adaptive_traffic.config.city_profile import DetectorCalibration, get_city_profile
from adaptive_traffic.core.analytics.queue_estimator import QueueEstimator
from adaptive_traffic.core.domain import VehicleDetection


def _det(y1=400, y2=460):
    return VehicleDetection(
        class_id=0,
        class_name="car",
        confidence=0.9,
        bbox=(10, y1, 60, y2),
        center=(35, (y1 + y2) // 2),
    )


def test_default_geometry_stays_640x480():
    est = QueueEstimator(get_city_profile("tier2_default"))
    assert (est.image_width_px, est.image_height_px) == (640, 480)
    out = est.estimate_from_detections([_det()])
    assert out.total_vehicles == 1
    assert set(out.by_direction) == {"south"}  # center 430 > 320


def test_calibration_geometry_overrides_buckets():
    prof = get_city_profile("tier2_default").model_copy(
        update={
            "detector_calibration": DetectorCalibration(frame_width_px=1920, frame_height_px=1080)
        }
    )
    est = QueueEstimator(prof)
    assert (est.image_width_px, est.image_height_px) == (1920, 1080)
    # Same pixels, different frame: center 600 is bottom-third at 480p (south)
    # but middle-band at 1080p (west); in queue zone under both (y2=700).
    out = est.estimate_from_detections([_det(y1=500, y2=700)])
    assert out.total_vehicles == 1
    assert set(out.by_direction) == {"west"}
