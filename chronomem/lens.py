# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/lens.py
# Purpose: Memory lenses for Principal and Tutor perspectives
# ===========================================================================

"""
Memory Lenses

Two different views of memory for different roles:
- PrincipalLens: Decision-making context (profile + recent episodes + decisions)
- TutorLens: Teaching context (skills + session history + resources)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from chronomem.models import GlobalMemory, MemoryType
from chronomem.memory_store import get_memory_store


class PrincipalLens:
    """
    Principal (decision-maker) perspective on memory.
    
    Returns compressed, decision-relevant context:
    - User preferences and constraints
    - Recent events and interruptions
    - Previous decision patterns
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
    
    async def get_context(self) -> Dict[str, Any]:
        """
        Get memory context for Principal decision-making.
        
        Returns:
            {
                "profile_summary": str,      # User preferences summary
                "recent_episodes": list,     # Recent events (last 7 days)
                "decision_hints": list,      # Relevant memories for decisions
                "constraints": list,         # Hard constraints
            }
        """
        store = get_memory_store(self.user_id)
        
        # Get profile memories (preferences)
        profiles = await store.list_profile(limit=10)
        profile_summary = self._summarize_profiles(profiles)
        
        # Get recent episodic memories
        episodes = await store.list_episodic(limit=10)
        recent_episodes = self._filter_recent(episodes, days=7)
        
        # Get skill weaknesses for planning
        skills = await store.list_skill(limit=5)
        weak_skills = [s for s in skills if s.confidence < 0.5]
        
        return {
            "profile_summary": profile_summary,
            "recent_episodes": [self._memory_to_hint(m) for m in recent_episodes],
            "weak_skills": [self._memory_to_hint(m) for m in weak_skills],
            "constraints": self._extract_constraints(profiles),
        }
    
    def _summarize_profiles(self, memories: List[GlobalMemory]) -> str:
        """Create concise summary of profile memories."""
        if not memories:
            return "No preference data available."
        summaries = [m.content[:100] for m in memories[:5]]
        return " | ".join(summaries)
    
    def _filter_recent(
        self, 
        memories: List[GlobalMemory], 
        days: int
    ) -> List[GlobalMemory]:
        """Filter to memories from last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            m for m in memories 
            if m.created_at and m.created_at > cutoff
        ]
    
    def _extract_constraints(self, profiles: List[GlobalMemory]) -> List[str]:
        """Extract hard constraints from profiles."""
        constraints = []
        for m in profiles:
            meta = m.metadata or {}
            if meta.get("is_constraint"):
                constraints.append(m.content)
        return constraints
    
    def _memory_to_hint(self, m: GlobalMemory) -> Dict[str, Any]:
        """Convert memory to decision hint."""
        return {
            "memory_id": m.memory_id,
            "type": m.type.value,
            "summary": m.summary_for_lens(),
            "confidence": m.confidence,
        }


class TutorLens:
    """
    Tutor (teacher) perspective on memory.
    
    Returns teaching-relevant context:
    - Skill levels and weak points
    - Recent session summaries
    - Recommended approaches
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
    
    async def get_context(
        self, 
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get memory context for Tutor teaching.
        
        Args:
            topic: Optional topic filter for relevance.
        
        Returns:
            {
                "skill_summary": str,        # Skill levels summary
                "weak_points": list,         # Areas needing work
                "style_hints": list,         # Teaching style preferences
                "session_history": list,     # Recent session notes
            }
        """
        store = get_memory_store(self.user_id)
        
        # Get skill memories
        skills = await store.list_skill(limit=15)
        
        # Filter by topic if provided
        if topic:
            skills = self._filter_by_topic(skills, topic)
        
        # Get teaching style preferences from profile
        profiles = await store.list_profile(limit=10)
        style_hints = self._extract_style_hints(profiles)
        
        # Get recent episodic for session history
        episodes = await store.list_episodic(limit=5)
        session_notes = [
            m for m in episodes 
            if m.metadata.get("source_type") == "session"
        ]
        
        return {
            "skill_summary": self._summarize_skills(skills),
            "weak_points": [s.content for s in skills if s.confidence < 0.5],
            "strong_points": [s.content for s in skills if s.confidence >= 0.7],
            "style_hints": style_hints,
            "session_history": [self._memory_to_note(m) for m in session_notes[:3]],
        }
    
    def _filter_by_topic(
        self, 
        memories: List[GlobalMemory], 
        topic: str
    ) -> List[GlobalMemory]:
        """Filter memories relevant to a topic."""
        topic_lower = topic.lower()
        return [
            m for m in memories
            if topic_lower in m.content.lower()
            or topic_lower in str(m.metadata.get("topic", "")).lower()
        ]
    
    def _summarize_skills(self, skills: List[GlobalMemory]) -> str:
        """Create skill summary for teaching context."""
        if not skills:
            return "No skill data available."
        
        weak = [s for s in skills if s.confidence < 0.5]
        strong = [s for s in skills if s.confidence >= 0.7]
        
        parts = []
        if weak:
            parts.append(f"Weak: {', '.join(s.content[:30] for s in weak[:3])}")
        if strong:
            parts.append(f"Strong: {', '.join(s.content[:30] for s in strong[:3])}")
        
        return " | ".join(parts) if parts else "Mixed skill levels."
    
    def _extract_style_hints(self, profiles: List[GlobalMemory]) -> List[str]:
        """Extract teaching style preferences."""
        hints = []
        for m in profiles:
            if "style" in m.content.lower() or "prefer" in m.content.lower():
                hints.append(m.content[:80])
        return hints[:3]
    
    def _memory_to_note(self, m: GlobalMemory) -> Dict[str, str]:
        """Convert memory to session note."""
        return {
            "content": m.content,
            "date": m.created_at.strftime("%Y-%m-%d") if m.created_at else "unknown",
        }


# =============================================================================
# Factory Functions
# =============================================================================

def get_principal_lens(user_id: str = "default") -> PrincipalLens:
    """Get a PrincipalLens instance."""
    return PrincipalLens(user_id)


def get_tutor_lens(user_id: str = "default") -> TutorLens:
    """Get a TutorLens instance."""
    return TutorLens(user_id)
