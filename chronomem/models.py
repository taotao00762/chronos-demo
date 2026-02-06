# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/models.py
# Purpose: Unified global memory data models
# ===========================================================================

"""
Global Memory Models

Three types of memory for Principal decision-making:
1. Profile: User preferences and constraints (long-term stable)
2. Episodic: Recent events and interruptions (with TTL)
3. Skill: Learning abilities and weak points (continuously updated)
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


# =============================================================================
# Constants
# =============================================================================

class MemoryType(Enum):
    """Memory classification types."""
    PROFILE = "profile"      # Preferences/constraints (stable, long TTL)
    EPISODIC = "episodic"    # Events/interruptions (short TTL)
    SKILL = "skill"          # Abilities/weak points (updated frequently)


class MemorySource(Enum):
    """Where the memory came from."""
    SETTINGS = "settings"         # From Settings page
    CONVERSATION = "conversation" # Extracted from chat
    SESSION = "session"           # From learning session
    MANUAL = "manual"             # User added manually
    SYSTEM = "system"             # System generated


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class GlobalMemory:
    """
    Unified memory model for all memory types.
    
    Fields:
        memory_id: Unique identifier
        user_id: User who owns this memory
        type: Memory type (profile/episodic/skill)
        content: Structured summary text
        source: Where the memory came from
        confidence: Confidence score (0.0 - 1.0)
        ttl_days: Time-to-live in days (for expiration)
        editable: Whether user can edit/delete
        metadata: Extended fields (JSON serialized)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    memory_id: str
    user_id: str
    type: MemoryType
    content: str
    source: MemorySource
    confidence: float = 0.8
    ttl_days: int = 30
    editable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "type": self.type.value,
            "content": self.content,
            "source": self.source.value,
            "confidence": self.confidence,
            "ttl_days": self.ttl_days,
            "editable": self.editable,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GlobalMemory":
        """Create from dictionary."""
        return cls(
            memory_id=data["memory_id"],
            user_id=data.get("user_id", "default"),
            type=MemoryType(data["type"]),
            content=data["content"],
            source=MemorySource(data.get("source", "system")),
            confidence=data.get("confidence", 0.8),
            ttl_days=data.get("ttl_days", 30),
            editable=data.get("editable", True),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
    
    def is_expired(self) -> bool:
        """Check if memory has expired."""
        if not self.created_at:
            return False
        age_days = (datetime.now() - self.created_at).days
        return age_days > self.ttl_days
    
    def summary_for_lens(self) -> str:
        """Get concise summary for Lens context."""
        type_prefix = {
            MemoryType.PROFILE: "[Pref]",
            MemoryType.EPISODIC: "[Event]",
            MemoryType.SKILL: "[Skill]",
        }
        prefix = type_prefix.get(self.type, "[Mem]")
        return f"{prefix} {self.content[:100]}"


# =============================================================================
# Helper Functions
# =============================================================================

def create_profile_memory(
    content: str,
    user_id: str = "default",
    source: MemorySource = MemorySource.SETTINGS,
    metadata: Dict[str, Any] = None,
) -> GlobalMemory:
    """Create a profile memory (long-term preference)."""
    import uuid
    return GlobalMemory(
        memory_id=str(uuid.uuid4()),
        user_id=user_id,
        type=MemoryType.PROFILE,
        content=content,
        source=source,
        confidence=0.9,
        ttl_days=365,  # Long TTL for profile
        editable=True,
        metadata=metadata or {},
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def create_episodic_memory(
    content: str,
    user_id: str = "default",
    source: MemorySource = MemorySource.CONVERSATION,
    ttl_days: int = 7,
    metadata: Dict[str, Any] = None,
) -> GlobalMemory:
    """Create an episodic memory (short-term event)."""
    import uuid
    return GlobalMemory(
        memory_id=str(uuid.uuid4()),
        user_id=user_id,
        type=MemoryType.EPISODIC,
        content=content,
        source=source,
        confidence=0.7,
        ttl_days=ttl_days,
        editable=True,
        metadata=metadata or {},
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def create_skill_memory(
    content: str,
    user_id: str = "default",
    source: MemorySource = MemorySource.SESSION,
    confidence: float = 0.5,
    metadata: Dict[str, Any] = None,
) -> GlobalMemory:
    """Create a skill memory (learning ability/weakness)."""
    import uuid
    return GlobalMemory(
        memory_id=str(uuid.uuid4()),
        user_id=user_id,
        type=MemoryType.SKILL,
        content=content,
        source=source,
        confidence=confidence,
        ttl_days=90,  # Medium TTL for skills
        editable=True,
        metadata=metadata or {},
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
