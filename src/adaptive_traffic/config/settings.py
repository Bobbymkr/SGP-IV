"""
Configuration management using Pydantic Settings
"""

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
    environment: str = Field(
        default="development", description="Environment: development, staging, production"
    )

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
        default="sqlite+aiosqlite:///./adaptive_traffic.db", description="Database connection URL"
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
    controller_type: str = Field(
        default="dqn", description="Controller type: dqn, fixed, webster, fuzzy"
    )
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
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")

    # External Services
    sentry_dsn: str | None = Field(default=None, description="Sentry DSN for error tracking")
    grafana_url: str | None = Field(default=None, description="Grafana URL")
    grafana_api_key: str | None = Field(default=None, description="Grafana API key")

    # File Storage
    data_dir: str = Field(default="./data", description="Data directory")
    models_dir: str = Field(default="./data/models", description="Models directory")
    logs_dir: str = Field(default="./logs", description="Logs directory")

    # NTCIP / J2735 V2X
    ntcip_controller_ip: str = Field(default="127.0.0.1", description="NTCIP controller IP")
    ntcip_stmp_port: int = Field(default=5000, description="NTCIP STMP port")
    ntcip_snmp_port: int = Field(default=161, description="NTCIP SNMP port")
    ntcip_community: str = Field(default="public", description="SNMP community string")
    ntcip_snmp_community: str = Field(default="public", description="SNMP community string")
    ntcip_timeout: float = Field(default=5.0, description="NTCIP request timeout (seconds)")
    ntcip_max_retries: int = Field(default=3, description="NTCIP max retries")
    ntcip_phase_mapping: dict = Field(
        default={"north": 1, "south": 2, "east": 3, "west": 4},
        description="Direction to NTCIP phase number mapping",
    )
    ntcip_detector_mapping: dict = Field(
        default={"1": "north", "2": "south", "3": "east", "4": "west"},
        description="Detector ID to direction mapping",
    )
    ntcip_transport: str = Field(default="both", description="NTCIP transport: stmp, snmp, both")

    # J2735 V2X
    j2735_bsm_port: int = Field(default=1735, description="J2735 BSM receive port")
    j2735_spat_port: int = Field(default=1736, description="J2735 SPAT transmit port")
    j2735_broadcast_ip: str = Field(default="255.255.255.255", description="J2735 broadcast IP")
    j2735_tx_power_dbm: int = Field(default=20, description="J2735 transmit power dBm")
    j2735_transmit_interval: float = Field(
        default=0.1, description="J2735 SPAT transmit interval (seconds)"
    )
    j2735_max_bsm_age: float = Field(
        default=1.0, description="Max BSM age for queue refinement (seconds)"
    )

    # City Profile
    city_profile: str = Field(
        default="tier2_default", description="City profile: mumbai, delhi, bangalore, tier2_default"
    )


def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
