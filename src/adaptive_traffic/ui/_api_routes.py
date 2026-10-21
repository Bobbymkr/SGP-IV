"""The API routes the FastAPI app serves, listed for the dashboard.

Kept free of streamlit so the guard test (tests/unit/test_ui_api_routes.py) can
run in the core CI environment, which does not install the [ui] extra.
"""

API_ROUTES = [
    ("GET", "/", "Service root"),
    ("GET", "/api/v1/health", "Health summary"),
    ("GET", "/api/v1/health/live", "Liveness probe"),
    ("GET", "/api/v1/health/ready", "Readiness probe"),
    ("GET", "/api/v1/metrics", "Service metrics"),
    ("GET", "/api/v1/version", "Build version"),
    ("GET", "/api/v1/signals/", "List signal controllers"),
    ("GET", "/api/v1/signals/{signal_id}", "Signal status and timing"),
    ("GET", "/api/v1/signals/{signal_id}/status", "Current phase state"),
    ("GET", "/api/v1/signals/{signal_id}/health", "NTCIP health of one signal"),
    ("GET", "/api/v1/signals/{signal_id}/ntcip/timing", "Live NTCIP timing plan"),
    ("POST", "/api/v1/signals/{signal_id}/timing", "Update the timing plan"),
    ("GET", "/api/v1/signals/{signal_id}/v2x/queue-refinement", "V2X queue refinement"),
    ("POST", "/api/v1/signals/{signal_id}/v2x/spat", "Publish SPAT to vehicles"),
    ("GET", "/api/v1/signals/plans/", "List timing plans"),
    ("POST", "/api/v1/signals/plans/", "Create a timing plan"),
    ("GET", "/api/v1/signals/plans/{plan_id}", "One timing plan"),
    ("PUT", "/api/v1/signals/plans/{plan_id}", "Replace a timing plan"),
    ("DELETE", "/api/v1/signals/plans/{plan_id}", "Delete a timing plan"),
    ("GET", "/api/v1/detection/cameras/", "List cameras"),
    ("POST", "/api/v1/detection/cameras/", "Add a camera"),
    ("GET", "/api/v1/detection/cameras/{camera_id}", "One camera"),
    ("PUT", "/api/v1/detection/cameras/{camera_id}", "Update a camera"),
    ("DELETE", "/api/v1/detection/cameras/{camera_id}", "Remove a camera"),
    ("GET", "/api/v1/detection/counts/{camera_id}", "Live vehicle counts"),
    ("GET", "/api/v1/detection/history", "Detection history"),
    ("POST", "/api/v1/detection/detect", "Detect vehicles in one frame"),
    ("POST", "/api/v1/detection/detect/batch", "Detect vehicles in a batch"),
    ("GET", "/api/v1/analytics/metrics/{intersection_id}", "Performance metrics"),
    ("GET", "/api/v1/analytics/performance/{intersection_id}", "Timing performance"),
    ("GET", "/api/v1/analytics/environmental/{intersection_id}", "Environmental impact"),
    ("GET", "/api/v1/analytics/recommendations/{intersection_id}", "Timing suggestions"),
    ("POST", "/api/v1/analytics/forecast", "Traffic flow forecast"),
    ("POST", "/api/v1/analytics/ingest", "Push events in"),
    ("POST", "/api/v1/analytics/scenario", "Run a scenario"),
]
