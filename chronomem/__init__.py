# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/__init__.py
# Purpose: ChronoMem - Memory management system
# ===========================================================================

"""
ChronoMem - Chronos Memory Management System

Three-tier memory architecture:
- Profile: User preferences and constraints (long-term)
- Episodic: Events and interruptions (short-term with TTL)
- Skill: Learning abilities and weak points (updated)

Two Lens perspectives:
- PrincipalLens: Decision-making context
- TutorLens: Teaching context

Usage:
    from chronomem.memory_store import get_memory_store
    from chronomem.lens import get_principal_lens
    
    store = get_memory_store()
    await store.add_profile("Prefers visual learning")
"""

# Core models (no circular deps)
from chronomem.models import GlobalMemory, MemoryType, MemorySource

# Legacy exports (for backward compatibility)
try:
    from chronomem.schema.memory import PersonalMemory, TaskMemory, BaseMemory
    from chronomem.service import ChronoMemService
except ImportError:
    PersonalMemory = None
    TaskMemory = None
    BaseMemory = None
    ChronoMemService = None

__all__ = [
    # Core models
    "GlobalMemory",
    "MemoryType",
    "MemorySource",
    # Decision Engine
    "DecisionEngine",
    "get_decision_engine",
    "DecisionResult",
    # Life Events
    "LifeEventCollector",
    "get_life_event_collector",
    "LifeEventType",
    "quick_log_event",
    # Legacy (may be None)
    "PersonalMemory",
    "TaskMemory",
    "BaseMemory",
    "ChronoMemService",
]

# Decision Engine exports
try:
    from chronomem.decision_engine import (
        DecisionEngine,
        get_decision_engine,
        DecisionResult,
        DecisionFactor,
        LearningMode,
    )
    from chronomem.life_events import (
        LifeEventCollector,
        get_life_event_collector,
        LifeEventType,
        quick_log_event,
    )
    from chronomem.pattern_analyzer import (
        PatternAnalyzer,
        get_pattern_analyzer,
    )
except ImportError as e:
    print(f"Decision engine import warning: {e}")
    DecisionEngine = None
    get_decision_engine = None
    DecisionResult = None
    LifeEventCollector = None
    get_life_event_collector = None
    LifeEventType = None
    quick_log_event = None
    PatternAnalyzer = None
    get_pattern_analyzer = None
