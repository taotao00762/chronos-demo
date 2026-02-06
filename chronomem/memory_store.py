# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/memory_store.py
# Purpose: Unified memory store wrapping DAO with convenience methods
# ===========================================================================

"""
MemoryStore - High-level interface for global memory operations.

Provides:
- Convenient add/get/list methods
- Automatic ID generation
- Type-safe operations
"""

from typing import Optional, List, Dict, Any

from chronomem.models import (
    GlobalMemory, 
    MemoryType, 
    MemorySource,
    create_profile_memory,
    create_episodic_memory,
    create_skill_memory,
)


def _get_dao():
    """Lazy import to avoid circular dependency."""
    from db.dao.memory_dao import MemoryDAO
    return MemoryDAO


class MemoryStore:
    """Unified memory store interface."""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
    
    # =========================================================================
    # Add Methods
    # =========================================================================
    
    async def add(self, memory: GlobalMemory) -> str:
        """Add a memory to the store."""
        return await _get_dao().create(memory)
    
    async def add_profile(
        self,
        content: str,
        source: MemorySource = MemorySource.SETTINGS,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Add a profile memory (preference/constraint)."""
        memory = create_profile_memory(
            content=content,
            user_id=self.user_id,
            source=source,
            metadata=metadata,
        )
        return await self.add(memory)
    
    async def add_episodic(
        self,
        content: str,
        source: MemorySource = MemorySource.CONVERSATION,
        ttl_days: int = 7,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Add an episodic memory (event/interruption)."""
        memory = create_episodic_memory(
            content=content,
            user_id=self.user_id,
            source=source,
            ttl_days=ttl_days,
            metadata=metadata,
        )
        return await self.add(memory)
    
    async def add_skill(
        self,
        content: str,
        source: MemorySource = MemorySource.SESSION,
        confidence: float = 0.5,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Add a skill memory (ability/weakness)."""
        memory = create_skill_memory(
            content=content,
            user_id=self.user_id,
            source=source,
            confidence=confidence,
            metadata=metadata,
        )
        return await self.add(memory)
    
    # =========================================================================
    # Query Methods
    # =========================================================================
    
    async def get(self, memory_id: str) -> Optional[GlobalMemory]:
        """Get a memory by ID."""
        return await _get_dao().get(memory_id)
    
    async def list_all(self, limit: int = 50) -> List[GlobalMemory]:
        """List all memories for user."""
        return await _get_dao().list_recent(self.user_id, limit)
    
    async def list_profile(self, limit: int = 20) -> List[GlobalMemory]:
        """List profile memories."""
        return await _get_dao().list_by_type(MemoryType.PROFILE, self.user_id, limit)
    
    async def list_episodic(self, limit: int = 20) -> List[GlobalMemory]:
        """List episodic memories."""
        return await _get_dao().list_by_type(MemoryType.EPISODIC, self.user_id, limit)
    
    async def list_skill(self, limit: int = 20) -> List[GlobalMemory]:
        """List skill memories."""
        return await _get_dao().list_by_type(MemoryType.SKILL, self.user_id, limit)
    
    # =========================================================================
    # Update/Delete Methods
    # =========================================================================
    
    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update a memory."""
        return await _get_dao().update(memory_id, content, confidence, metadata)
    
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory."""
        return await _get_dao().delete(memory_id)
    
    async def cleanup_expired(self) -> int:
        """Clean up expired memories."""
        return await _get_dao().cleanup_expired()


# =============================================================================
# Singleton Instance
# =============================================================================

_store: Optional[MemoryStore] = None


def get_memory_store(user_id: str = "default") -> MemoryStore:
    """Get or create memory store instance."""
    global _store
    if _store is None or _store.user_id != user_id:
        _store = MemoryStore(user_id)
    return _store
