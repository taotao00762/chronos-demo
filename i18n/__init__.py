# ===========================================================================
# Chronos AI Learning Companion
# File: i18n/__init__.py
# Purpose: Export internationalization modules
# ===========================================================================

from i18n.texts import TXT, get_text, set_language, get_current_language

__all__ = [
    "TXT",
    "get_text",
    "set_language",
    "get_current_language",
]
