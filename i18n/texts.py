# ===========================================================================
# Chronos AI Learning Companion
# File: i18n/texts.py
# Purpose: Internationalization with JSON file support and dynamic switching
# ===========================================================================

"""
Internationalization Module

Supports:
- Loading translations from JSON files
- Dynamic language switching
- Dot-notation key access (e.g., "settings.general.language")
- Fallback to English for missing keys
- Template variable interpolation
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


# =============================================================================
# Constants
# =============================================================================

I18N_DIR: Path = Path(__file__).parent
SUPPORTED_LANGUAGES: list = ["en", "zh-CN"]
DEFAULT_LANGUAGE: str = "en"


# =============================================================================
# State
# =============================================================================

_current_language: str = DEFAULT_LANGUAGE
_translations: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# Internal Functions
# =============================================================================

def _load_json(lang: str) -> Dict[str, Any]:
    """Load translation JSON file for a language."""
    # Map language codes to file names
    file_map = {
        "en": "en.json",
        "zh-CN": "zh_cn.json",
    }
    
    filename = file_map.get(lang, "en.json")
    filepath = I18N_DIR / filename
    
    if not filepath.exists():
        print(f"Warning: Translation file not found: {filepath}")
        return {}
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load translations: {e}")
        return {}


def _get_nested(data: Dict[str, Any], key: str) -> Optional[str]:
    """
    Get value from nested dict using dot notation.
    
    Args:
        data: Nested dictionary
        key: Dot-separated key (e.g., "settings.general.language")
    
    Returns:
        Value at key path, or None if not found.
    """
    parts = key.split(".")
    current = data
    
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    
    return current if isinstance(current, str) else None


# =============================================================================
# Public API
# =============================================================================

def load_translations(lang: str) -> None:
    """
    Load translations for a language into cache.
    
    Args:
        lang: Language code ("en" or "zh-CN")
    """
    if lang not in _translations:
        _translations[lang] = _load_json(lang)


def set_language(lang: str) -> None:
    """
    Set current language and load translations.
    
    Args:
        lang: Language code ("en" or "zh-CN")
    """
    global _current_language
    
    if lang not in SUPPORTED_LANGUAGES:
        print(f"Warning: Unsupported language '{lang}', falling back to English")
        lang = DEFAULT_LANGUAGE
    
    # Load if not cached
    load_translations(lang)
    
    # Also ensure English is loaded for fallback
    load_translations(DEFAULT_LANGUAGE)
    
    _current_language = lang


def get_current_language() -> str:
    """Get current language code."""
    return _current_language


def t(key: str, **kwargs: Any) -> str:
    """
    Get translated string by dot-notation key.
    
    Args:
        key: Translation key (e.g., "settings.general.language")
        **kwargs: Template variables for interpolation
    
    Returns:
        Translated string. Falls back to English, then to key itself.
    
    Example:
        t("settings.title")  # Returns "Settings" or "设置"
        t("common.minutes")  # Returns "minutes" or "分钟"
    """
    # Ensure translations are loaded
    if not _translations:
        load_translations(_current_language)
        load_translations(DEFAULT_LANGUAGE)
    
    # Try current language
    result = _get_nested(_translations.get(_current_language, {}), key)
    
    # Fallback to English
    if result is None:
        result = _get_nested(_translations.get(DEFAULT_LANGUAGE, {}), key)
    
    # Fallback to key itself
    if result is None:
        return key
    
    # Template interpolation
    if kwargs:
        try:
            result = result.format(**kwargs)
        except KeyError:
            pass  # If formatting fails, return as-is
    
    return result


def get_text(key: str, **kwargs: Any) -> str:
    """Alias for t() function."""
    return t(key, **kwargs)


# =============================================================================
# TXT Class - Attribute-style Access (Legacy Compatibility)
# =============================================================================

class _TextAccessor:
    """
    Provides attribute-style access for backward compatibility.
    
    Maps old TXT.nav_dashboard style to new t("nav.command") style.
    """
    
    # Mapping from old attribute names to new keys
    _KEY_MAP: Dict[str, str] = {
        # Navigation
        "nav_command": "nav.command",
        "nav_plan": "nav.plan",
        "nav_tutor": "nav.tutor",
        "nav_memory": "nav.memory",
        "nav_graph": "nav.graph",
        "nav_settings": "nav.settings",
        
        # Sidebar
        "app_name": "app.name",
        "user_label": "sidebar.user_label",
        "user_plan": "sidebar.user_plan",
        
        # Dashboard
        "greeting": "dashboard.greeting",
        "greeting_sub": "dashboard.greeting_sub",
        
        # Plan
        "plan_title": "plan.title",
        "plan_subtitle": "plan.subtitle",
        "tab_today": "plan.tab_today",
        "tab_changes": "plan.tab_changes",
        "tab_strategy": "plan.tab_strategy",
        "today_title": "plan.today_title",
        "today_empty": "plan.today_empty",
        "today_add_task": "plan.today_add",
        "changes_title": "plan.changes_title",
        "changes_empty": "plan.changes_empty",
        "strategy_title": "plan.strategy_title",
        "strategy_subtitle": "plan.strategy_subtitle",
        
        # Tutor
        "tutor_title": "tutor.title",
        "tutor_subtitle": "tutor.subtitle",
        "tutor_placeholder": "tutor.placeholder",
        
        # Memory
        "memory_title": "memory.title",
        "memory_subtitle": "memory.subtitle",
        
        # Graph
        "graph_title": "graph.title",
        "graph_subtitle": "graph.subtitle",
        
        # Settings
        "settings_title": "settings.title",
        "settings_subtitle": "settings.subtitle",
        
        # Common
        "coming_soon": "common.coming_soon",
        "loading": "common.loading",
        
        # Dashboard Cards
        "card_progress_title": "dashboard.card_progress",
        "card_chats_title": "dashboard.card_chats",
        "card_actions_title": "dashboard.card_actions",
        "action_new_chat": "dashboard.action_new_chat",
        "action_upload": "dashboard.action_upload",
        "action_bookmarks": "dashboard.action_bookmarks",
        "action_checkin": "dashboard.action_checkin",
    }
    
    def __getattr__(self, name: str) -> str:
        """Get text by attribute name."""
        # Check mapping first
        if name in self._KEY_MAP:
            return t(self._KEY_MAP[name])
        # Try direct dot notation conversion (snake_case to dot.notation)
        key = name.replace("_", ".")
        return t(key)
    
    def __call__(self, key: str, **kwargs: Any) -> str:
        """Get text by key with interpolation."""
        return t(key, **kwargs)


# Singleton instance
TXT = _TextAccessor()


# =============================================================================
# Initialize on Import
# =============================================================================

# Load English as default on module import
load_translations(DEFAULT_LANGUAGE)
