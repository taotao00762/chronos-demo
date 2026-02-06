# ===========================================================================
# Chronos AI Learning Companion
# File: stores/settings_store.py
# Purpose: Singleton state management for settings
# ===========================================================================

"""
Settings Store

Singleton store that manages settings state:
- Caches settings in memory for fast access
- Tracks dirty state (unsaved changes)
- Provides update methods for UI binding
"""

from dataclasses import replace
from typing import Optional, List, Callable, Any
from copy import deepcopy

from models.settings_model import Settings
from services.settings_service import load_settings, save_settings


class SettingsStore:
    """
    Singleton store for application settings.
    
    Usage:
        store = SettingsStore.get_instance()
        current = store.get()
        store.update(language="zh-CN")
        if store.is_dirty():
            store.save()
    """
    
    _instance: Optional["SettingsStore"] = None
    
    @classmethod
    def get_instance(cls) -> "SettingsStore":
        """
        Get or create the singleton instance.
        
        Returns:
            The global SettingsStore instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize store with settings from disk."""
        self._settings: Settings = load_settings()
        self._original: Settings = deepcopy(self._settings)
        self._listeners: List[Callable[[], None]] = []
    
    def get(self) -> Settings:
        """
        Get current settings.
        
        Returns:
            Current Settings object (do not mutate directly).
        """
        return self._settings
    
    def update(self, **kwargs: Any) -> None:
        """
        Update one or more settings fields.
        
        Notifies all subscribed listeners after update.
        
        Args:
            **kwargs: Field names and new values.
        
        Example:
            store.update(language="zh-CN", daily_target_minutes=120)
        """
        # Create new settings with updated fields
        self._settings = replace(self._settings, **kwargs)
        
        # Notify listeners
        self._notify()
    
    def is_dirty(self) -> bool:
        """
        Check if there are unsaved changes.
        
        Returns:
            True if current settings differ from saved version.
        """
        return self._settings != self._original
    
    def save(self) -> None:
        """
        Persist current settings to disk.
        
        Updates the "original" snapshot after saving.
        """
        save_settings(self._settings)
        self._original = deepcopy(self._settings)
        self._notify()
    
    def reload(self) -> None:
        """
        Reload settings from disk, discarding unsaved changes.
        """
        self._settings = load_settings()
        self._original = deepcopy(self._settings)
        self._notify()
    
    def discard_changes(self) -> None:
        """
        Discard unsaved changes, reverting to last saved state.
        """
        self._settings = deepcopy(self._original)
        self._notify()
    
    def subscribe(self, listener: Callable[[], None]) -> None:
        """
        Subscribe to settings changes.
        
        Listener will be called whenever settings are updated or saved.
        
        Args:
            listener: Callback function with no arguments.
        """
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def unsubscribe(self, listener: Callable[[], None]) -> None:
        """
        Unsubscribe from settings changes.
        
        Args:
            listener: Previously subscribed callback.
        """
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def _notify(self) -> None:
        """Notify all listeners of a change."""
        for listener in self._listeners:
            try:
                listener()
            except Exception as e:
                print(f"Warning: Settings listener error: {e}")
