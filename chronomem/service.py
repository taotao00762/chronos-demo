# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/service.py
# Purpose: Unified ChronoMem service interface
# ===========================================================================

"""
ChronoMem Service

Unified interface for all memory operations:
- Personal memory: Add/retrieve user preferences
- Task memory: Add/retrieve learning strategies
- Working memory: Compact long conversations
"""

from typing import List, Dict, Any, Optional, Tuple

from chronomem.schema.memory import PersonalMemory, TaskMemory, BaseMemory
from chronomem.core.vector_store import get_vector_store
from chronomem.core.embedder import get_embedder
from chronomem.summary.personal import PersonalExtractor
from chronomem.summary.task import TaskExtractor


class ChronoMemService:
    """
    Unified service for ChronoMem operations.
    
    Usage:
        mem = ChronoMemService()
        
        # Add personal memories from conversation
        await mem.add_personal_from_conversation(messages, user_id)
        
        # Retrieve relevant memories
        memories = await mem.retrieve_personal("learning preferences", user_id)
    """
    
    def __init__(self, language: str = "en"):
        """Initialize service."""
        self.language = language
        self.store = get_vector_store()
        self.embedder = get_embedder()
        self.personal_extractor = PersonalExtractor(language)
        self.task_extractor = TaskExtractor()
    
    # =========================================================================
    # Personal Memory
    # =========================================================================
    
    async def add_personal_from_conversation(
        self,
        messages: List[Dict[str, Any]],
        user_id: str = "default",
        user_name: str = "user",
    ) -> List[str]:
        """
        Extract and store personal memories from conversation.
        
        Args:
            messages: List of {role, content} message dicts.
            user_id: User identifier.
            user_name: User's display name.
        
        Returns:
            List of created memory IDs.
        """
        # Get existing memories for dedup
        existing = await self.store.list_by_type("personal", user_id, limit=20)
        
        # Extract new memories
        memories = await self.personal_extractor.extract(
            messages,
            user_id=user_id,
            user_name=user_name,
            existing_memories=existing,
        )
        
        # Store memories
        ids = await self.store.add_batch(memories)
        
        print(f"ChronoMem: Added {len(ids)} personal memories")
        return ids
    
    async def retrieve_personal(
        self,
        query: str,
        user_id: str = "default",
        top_k: int = 5,
    ) -> List[Tuple[PersonalMemory, float]]:
        """
        Retrieve relevant personal memories.
        
        Args:
            query: Search query.
            user_id: User identifier.
            top_k: Number of results.
        
        Returns:
            List of (memory, score) tuples.
        """
        query_embedding = await self.embedder.embed(query)
        
        results = await self.store.search(
            query_embedding,
            memory_type="personal",
            user_id=user_id,
            top_k=top_k,
            use_time_weight=True,
        )
        
        return results
    
    async def list_personal(
        self,
        user_id: str = "default",
        limit: int = 20,
    ) -> List[PersonalMemory]:
        """List all personal memories for a user."""
        return await self.store.list_by_type("personal", user_id, limit)
    
    # =========================================================================
    # Task Memory
    # =========================================================================
    
    async def add_task_from_session(
        self,
        session_data: Dict[str, Any],
        score: float = 0.5,
        session_id: Optional[str] = None,
    ) -> List[str]:
        """
        Extract and store task memories from session.
        
        Args:
            session_data: Session data (topics, summary, etc.).
            score: Session success score (0-1).
            session_id: Session identifier.
        
        Returns:
            List of created memory IDs.
        """
        memories = await self.task_extractor.extract_from_session(
            session_data,
            score=score,
            session_id=session_id,
        )
        
        ids = await self.store.add_batch(memories)
        
        print(f"ChronoMem: Added {len(ids)} task memories")
        return ids
    
    async def retrieve_task(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[Tuple[TaskMemory, float]]:
        """
        Retrieve relevant task memories (strategies).
        
        Args:
            query: Search query (topic/subject).
            top_k: Number of results.
        
        Returns:
            List of (memory, score) tuples.
        """
        query_embedding = await self.embedder.embed(query)
        
        results = await self.store.search(
            query_embedding,
            memory_type="task",
            user_id="default",  # Task memories are shared
            top_k=top_k,
            use_time_weight=True,
        )
        
        return results
    
    async def list_task(self, limit: int = 20) -> List[TaskMemory]:
        """List all task memories."""
        return await self.store.list_by_type("task", "default", limit)
    
    # =========================================================================
    # Working Memory (Context Compression)
    # =========================================================================
    
    async def compact_context(
        self,
        messages: List[Dict[str, Any]],
        max_messages: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Compact long conversation context.
        
        Keeps recent messages and summarizes older ones.
        
        Args:
            messages: Full message history.
            max_messages: Max messages to return.
        
        Returns:
            Compacted message list.
        """
        if len(messages) <= max_messages:
            return messages
        
        from services.gemini_service import create_gemini_service
        
        service = create_gemini_service()
        if not service:
            # Fallback: just truncate
            return messages[-max_messages:]
        
        # Split into old and recent
        keep_count = max_messages - 1  # Reserve 1 for summary
        old_messages = messages[:-keep_count]
        recent_messages = messages[-keep_count:]
        
        # Summarize old messages
        old_text = "\n".join([
            f"{m.get('role')}: {m.get('content', '')[:200]}"
            for m in old_messages
        ])
        
        try:
            summary = await service.send_message(
                f"Summarize this conversation context in 2-3 sentences:\n\n{old_text}"
            )
            
            # Create summary message
            summary_msg = {
                "role": "system",
                "content": f"[Previous context summary: {summary}]",
            }
            
            return [summary_msg] + recent_messages
            
        except Exception:
            return messages[-max_messages:]
    
    # =========================================================================
    # Utility
    # =========================================================================
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        return await self.store.delete(memory_id)
    
    async def get_context_for_plan(
        self,
        topics: List[str],
        user_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Get memory context for plan generation.
        
        Args:
            topics: Topics for the plan.
            user_id: User identifier.
        
        Returns:
            Context dict with personal and task memories.
        """
        query = " ".join(topics) if topics else "learning study habits"
        
        personal = await self.retrieve_personal(query, user_id, top_k=5)
        task = await self.retrieve_task(query, top_k=3)
        
        return {
            "personal_memories": [
                {"content": m.content, "score": s} for m, s in personal
            ],
            "task_strategies": [
                {"strategy": m.strategy, "topic": m.topic, "score": s}
                for m, s in task
            ],
        }


# Singleton instance
_service: Optional[ChronoMemService] = None


def get_chronomem_service(language: str = "en") -> ChronoMemService:
    """Get or create singleton ChronoMem service."""
    global _service
    if _service is None:
        _service = ChronoMemService(language)
    return _service
