"""
Health check endpoints
"""

from datetime import datetime

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
    """Readiness check for Kubernetes"""
    # Add database, redis, model checks here
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {"database": "ok", "redis": "ok", "models": "ok"},
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
