"""
City Profile Loader and Registry
Loads city profiles from JSON files in config/city_profiles/
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from adaptive_traffic.config.city_profile import (
    CityProfile,
)
from adaptive_traffic.config.city_profile import get_city_profile as get_builtin_profile
from adaptive_traffic.config.city_profile import list_city_profiles as list_builtin_profiles

logger = logging.getLogger(__name__)


class CityProfileRegistry:
    """Registry for city profiles with JSON file loading"""

    def __init__(self, profiles_dir: Optional[str] = None):
        if profiles_dir is None:
            # Default to config/city_profiles relative to project root
            project_root = Path(__file__).resolve().parents[3]
            profiles_dir = project_root / "config" / "city_profiles"

        self.profiles_dir = Path(profiles_dir)
        self._cache: Dict[str, CityProfile] = {}
        self._load_builtin_profiles()
        self._load_json_profiles()

    def _load_builtin_profiles(self):
        """Load built-in profiles as fallback"""
        for name in list_builtin_profiles():
            self._cache[name] = get_builtin_profile(name)
        logger.info(f"Loaded {len(self._cache)} built-in city profiles")

    def _load_json_profiles(self):
        """Load profiles from JSON files"""
        if not self.profiles_dir.exists():
            logger.warning(f"City profiles directory not found: {self.profiles_dir}")
            return

        for json_file in self.profiles_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Validate required fields
                if "name" not in data:
                    logger.warning(f"Skipping {json_file.name}: missing 'name' field")
                    continue

                profile = CityProfile(**data)
                self._cache[profile.name] = profile
                logger.info(f"Loaded city profile from JSON: {profile.name}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse {json_file.name}: {e}")
            except Exception as e:
                logger.error(f"Failed to load profile from {json_file.name}: {e}")

    def get(self, name: str) -> CityProfile:
        """Get city profile by name"""
        key = name.lower()
        if key not in self._cache:
            available = list(self._cache.keys())
            raise ValueError(f"Unknown city profile: {name}. Available: {available}")
        return self._cache[key]

    def get_or_default(self, name: str, default: str = "tier2_default") -> CityProfile:
        """Get city profile or return default"""
        try:
            return self.get(name)
        except ValueError:
            logger.warning(f"City profile '{name}' not found, using default: {default}")
            return self.get(default)

    def list(self) -> list[str]:
        """List available city profiles"""
        return sorted(self._cache.keys())

    def reload(self):
        """Reload profiles from disk"""
        self._cache.clear()
        self._load_builtin_profiles()
        self._load_json_profiles()


# Global registry instance
_registry: Optional[CityProfileRegistry] = None


def get_registry(profiles_dir: Optional[str] = None) -> CityProfileRegistry:
    """Get global city profile registry"""
    global _registry
    if _registry is None:
        _registry = CityProfileRegistry(profiles_dir)
    return _registry


def get_city_profile(name: str) -> CityProfile:
    """Get city profile by name (uses global registry)"""
    return get_registry().get(name)


def get_city_profile_or_default(name: str, default: str = "tier2_default") -> CityProfile:
    """Get city profile or return default"""
    return get_registry().get_or_default(name, default)


def list_city_profiles() -> list[str]:
    """List available city profiles"""
    return get_registry().list()


# For backward compatibility with config.city_profile
def get_builtin_city_profile(name: str) -> CityProfile:
    """Get built-in city profile (bypasses JSON files)"""
    return get_builtin_profile(name)


def list_builtin_city_profiles() -> list[str]:
    """List built-in city profiles"""
    return list_builtin_profiles()
