# ===========================================================================
# Chronos AI Learning Companion
# File: config/__init__.py
# Purpose: Config module exports
# ===========================================================================

from config.tutor_config import (
    SUBJECTS,
    GRADES,
    TEACHING_STYLES,
    SUBJECT_MAP,
    GRADE_MAP,
    STYLE_MAP,
    generate_tutor_system_prompt,
    get_subject_options,
    get_grade_options,
    get_style_options,
)

__all__ = [
    "SUBJECTS",
    "GRADES",
    "TEACHING_STYLES",
    "SUBJECT_MAP",
    "GRADE_MAP",
    "STYLE_MAP",
    "generate_tutor_system_prompt",
    "get_subject_options",
    "get_grade_options",
    "get_style_options",
]
