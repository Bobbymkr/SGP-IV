"""
Adaptive Traffic Signal Timer
AI-powered adaptive traffic signal control system
"""

__version__ = "1.0.0"
__author__ = "Adaptive Traffic Signal Team"
__email__ = "team@adaptivesignal.io"

from .config.settings import get_settings

__all__ = ["get_settings", "__version__"]
