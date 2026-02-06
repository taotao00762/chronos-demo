# ===========================================================================
# Chronos AI Learning Companion
# File: views/__init__.py
# Purpose: Export view modules
# ===========================================================================

from views.dashboard_view import create_dashboard_view
from views.memory_view import create_memory_view

__all__ = [
    "create_dashboard_view",
    "create_memory_view",
]
