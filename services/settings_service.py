# ===========================================================================
# Chronos AI Learning Companion
# File: services/settings_service.py
# Purpose: File I/O for settings.json
# ===========================================================================

"""
Settings Service

Handles reading and writing settings to JSON file.
Creates default file if it doesn't exist.
"""

import json
from pathlib import Path
from typing import Optional

from models.settings_model import Settings


# =============================================================================
# Constants
# =============================================================================

# Settings file location (relative to app root)
DATA_DIR: Path = Path(__file__).parent.parent / "data"
SETTINGS_FILE: Path = DATA_DIR / "settings.json"


# =============================================================================
# Public API
# =============================================================================

def get_settings_path() -> Path:
    """
    Get the absolute path to settings.json.
    
    Returns:
        Path object pointing to settings file.
    """
    return SETTINGS_FILE.resolve()


def load_settings() -> Settings:
    """
    Load settings from JSON file.
    
    If file doesn't exist, creates it with default values.
    If file is corrupted, returns default settings.
    
    Returns:
        Settings object with current or default values.
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists
    if not SETTINGS_FILE.exists():
        # Create with defaults
        defaults = Settings()
        save_settings(defaults)
        return defaults
    
    # Read and parse
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Settings.from_dict(data)
    except (json.JSONDecodeError, IOError) as e:
        # Return defaults on error (don't overwrite potentially recoverable file)
        print(f"Warning: Failed to load settings: {e}")
        return Settings()


def save_settings(settings: Settings) -> None:
    """
    Save settings to JSON file.
    
    Creates data directory if it doesn't exist.
    
    Args:
        settings: Settings object to persist.
    
    Raises:
        IOError: If write fails.
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict and write
    data = settings.to_dict()
    
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def reset_settings() -> Settings:
    """
    Reset settings to defaults.
    
    Overwrites settings file with default values.
    
    Returns:
        New Settings object with defaults.
    """
    defaults = Settings()
    save_settings(defaults)
    return defaults
