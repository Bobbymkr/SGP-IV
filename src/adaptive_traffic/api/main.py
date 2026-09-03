"""
FastAPI Main Application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adaptive_traffic.api.routes import analytics, detection, health, signals
from adaptive_traffic.config.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Adaptive Traffic Signal API")
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")

    yield

    # Shutdown
    logger.info("Shutting down Adaptive Traffic Signal API")


def create_app() -> FastAPI:
    """Create FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered adaptive traffic signal control system API",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
    app.include_router(detection.router, prefix="/api/v1/detection", tags=["detection"])
    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])

    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "operational",
            "docs": "/docs",
        }

    return app


app = create_app()
