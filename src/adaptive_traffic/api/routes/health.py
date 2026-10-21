"""
Health check endpoints
"""

from datetime import datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException, Response

from adaptive_traffic.config.settings import get_settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "adaptive-traffic-signal-api",
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness: registry shipped + tier resolved, no phantom infra claims"""
    # ponytail: read device.yaml; Settings wrapper when it owns registry
    repo = Path(__file__).resolve().parents[4]
    tier, registry_ok = "low", False
    try:
        text = (repo / "configs" / "device.yaml").read_text()
        device = yaml.safe_load(text) or {}
        tier = str(device.get("active_tier", "low"))
        if tier == "auto":
            tier = "low"  # CPU-only box default until auto-detect lands
        reg = str(((device.get("detection") or {}).get("low") or {}).get(
            "registry_dir", "models/registry/india-yolov8n-final"))
        registry_ok = (repo / reg).is_dir()
    except OSError:
        registry_ok = False
    return {
        "status": "ready" if registry_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {"models": "ok" if registry_ok else "missing", "tier": tier},
    }


@router.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/version")
async def version():
    """Get application version"""
    settings = get_settings()
    return {
        "version": settings.app_version,
        "name": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus scrape endpoint for phase-boundary histograms"""
    if not get_settings().prometheus_enabled:
        raise HTTPException(status_code=404, detail="metrics disabled")
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
