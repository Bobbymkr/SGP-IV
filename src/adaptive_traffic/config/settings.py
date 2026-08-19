"""
Configuration management using Pydantic Settings
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Adaptive Traffic Signal Timer"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="development", description="Environment: development, staging, production")

    # API Server
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    api_workers: int = Field(default=4, description="Number of API workers")
    api_reload: bool = Field(default=False, description="Enable auto-reload in development")

    # Streamlit Dashboard
    dashboard_host: str = Field(default="0.0.0.0", description="Dashboard host")
    dashboard_port: int = Field(default=8501, description="Dashboard port")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./adaptive_traffic.db",
        description="Database connection URL"
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_max_connections: int = Field(default=10, description="Max Redis connections")

    # Computer Vision / ML
    yolo_model_path: str = Field(default="yolov8n.pt", description="YOLO model path")
    yolo_confidence_threshold: float = Field(default=0.5, description="YOLO confidence threshold")
    yolo_iou_threshold: float = Field(default=0.45, description="YOLO IoU threshold")
    device: str = Field(default="auto", description="Device: auto, cpu, cuda, mps")
    batch_size: int = Field(default=1, description="Inference batch size")

    # Traffic Simulation
    simulation_enabled: bool = Field(default=True, description="Enable traffic simulation")
    simulation_time: int = Field(default=300, description="Simulation time in seconds")
    num_signals: int = Field(default=4, description="Number of traffic signals")
    default_green_time: int = Field(default=20, description="Default green light duration")
    default_yellow_time: int = Field(default=5, description="Default yellow light duration")
    default_red_time: int = Field(default=150, description="Default red light duration")

    # Signal Control
    controller_type: str = Field(default="dqn", description="Controller type: dqn, fixed, webster, fuzzy")
    min_green_time: int = Field(default=10, description="Minimum green time (seconds)")
    max_green_time: int = Field(default=60, description="Maximum green time (seconds)")
    detection_time: int = Field(default=5, description="Detection time before green (seconds)")

    # Monitoring
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=9090, description="Prometheus metrics port")
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json, text")

    # Security
    secret_key: str = Field(default="change-me-in-production", description="Secret key for JWT")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiry")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")

    # External Services
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    grafana_url: Optional[str] = Field(default=None, description="Grafana URL")
    grafana_api_key: Optional[str] = Field(default=None, description="Grafana API key")

    # File Storage
    data_dir: str = Field(default="./data", description="Data directory")
    models_dir: str = Field(default="./data/models", description="Models directory")
    logs_dir: str = Field(default="./logs", description="Logs directory")


def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()