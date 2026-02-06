# ===========================================================================
# Chronos AI Learning Companion
# File: models/settings_model.py
# Purpose: Settings data model with dataclass and enums
# ===========================================================================

"""
Settings Model

Defines the Settings dataclass and all related enums.
All fields have sensible defaults for first-time users.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any


# =============================================================================
# Enums
# =============================================================================

class ModePreference(Enum):
    """Learning mode preference for Principal planning."""
    RECOVERY = "recovery"
    STANDARD = "standard"
    SPRINT = "sprint"


class Sensitivity(Enum):
    """Sensitivity level for interruption detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TutorStyle(Enum):
    """AI Tutor teaching style."""
    SOCRATIC = "socratic"
    DIRECT = "direct"
    PRACTICE_FIRST = "practice_first"


class AvoidMode(Enum):
    """Modes to avoid in learning sessions."""
    PRACTICE = "avoid_practice"
    NEW_LEARNING = "avoid_new_learning"
    MEMORIZATION = "avoid_memorization"


class RememberScope(Enum):
    """What the Memory module should remember."""
    PREFERENCES = "preferences"
    GOALS = "goals"
    WEAK_TOPICS = "weak_topics"
    SCHEDULE_CONSTRAINTS = "schedule_constraints"


# =============================================================================
# Settings Dataclass
# =============================================================================

@dataclass
class Settings:
    """
    Application settings with sensible defaults.
    
    Grouped by module:
    - A. General: Language
    - B. Learning: Principal planning preferences
    - C. Adaptation: Interruption handling
    - D. Tutor: AI teaching style
    - E. Memory: What to remember
    """
    
    # A. General
    language: str = "en"
    
    # B. Learning Preferences (for Principal)
    daily_target_minutes: int = 90
    preferred_session_length: int = 25  # Options: 25, 45, 60
    mode_preference: str = "standard"  # ModePreference value
    avoid_modes: List[str] = field(default_factory=list)  # AvoidMode values
    
    # C. Interruption & Adaptation
    adapt_plan_automatically: bool = True
    approval_required: bool = True
    sensitivity: str = "medium"  # Sensitivity value
    
    # D. Tutor
    default_tutor_style: str = "direct"  # TutorStyle value
    tutor_use_memory: bool = True
    
    # E. Memory
    enable_memory: bool = True
    remember_scope: List[str] = field(default_factory=lambda: [
        "preferences",
        "goals"
    ])  # RememberScope values
    
    # F. API Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"

    # G. 浏览器打卡
    checkin_url: str = ""
    checkin_auto_open: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to JSON-serializable dictionary.
        
        Returns:
            Dict with all settings fields.
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """
        Create Settings from dictionary.
        
        Missing keys will use default values.
        
        Args:
            data: Dictionary with settings values.
        
        Returns:
            Settings instance.
        """
        # Get default values
        defaults = cls()
        
        # Build kwargs with fallbacks to defaults
        kwargs = {
            "language": data.get("language", defaults.language),
            "daily_target_minutes": data.get("daily_target_minutes", defaults.daily_target_minutes),
            "preferred_session_length": data.get("preferred_session_length", defaults.preferred_session_length),
            "mode_preference": data.get("mode_preference", defaults.mode_preference),
            "avoid_modes": data.get("avoid_modes", defaults.avoid_modes),
            "adapt_plan_automatically": data.get("adapt_plan_automatically", defaults.adapt_plan_automatically),
            "approval_required": data.get("approval_required", defaults.approval_required),
            "sensitivity": data.get("sensitivity", defaults.sensitivity),
            "default_tutor_style": data.get("default_tutor_style", defaults.default_tutor_style),
            "tutor_use_memory": data.get("tutor_use_memory", defaults.tutor_use_memory),
            "enable_memory": data.get("enable_memory", defaults.enable_memory),
            "remember_scope": data.get("remember_scope", defaults.remember_scope),
            "gemini_api_key": data.get("gemini_api_key", defaults.gemini_api_key),
            "gemini_model": data.get("gemini_model", defaults.gemini_model),
            "checkin_url": data.get("checkin_url", defaults.checkin_url),
            "checkin_auto_open": data.get("checkin_auto_open", defaults.checkin_auto_open),
        }
        
        return cls(**kwargs)
    
    def get_mode_preference(self) -> ModePreference:
        """Get mode_preference as enum."""
        return ModePreference(self.mode_preference)
    
    def get_sensitivity(self) -> Sensitivity:
        """Get sensitivity as enum."""
        return Sensitivity(self.sensitivity)
    
    def get_tutor_style(self) -> TutorStyle:
        """Get default_tutor_style as enum."""
        return TutorStyle(self.default_tutor_style)
