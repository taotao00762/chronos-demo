# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/life_events.py
# Purpose: Life Event Collection and Analysis for Decision Engine
# ===========================================================================

"""
Life Events Module

Collects and analyzes life events that impact learning:
- Sleep quality
- Schedule conflicts
- Social events
- Energy level
- Mood/stress

These factors have the highest priority (50% weight) in decision-making.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple


# =============================================================================
# Constants
# =============================================================================

class LifeEventType(Enum):
    """Types of life events that impact learning."""
    SLEEP = "sleep"           # Sleep quality (poor/fair/good)
    SCHEDULE = "schedule"     # Schedule pressure (busy/normal/free)
    SOCIAL = "social"         # Social events load (high/medium/low)
    ENERGY = "energy"         # Energy level (low/medium/high)
    MOOD = "mood"             # Mood/stress (stressed/neutral/positive)


class EventLevel(Enum):
    """Standardized event levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Impact scores: negative = blocks learning, positive = supports learning
IMPACT_SCORES = {
    LifeEventType.SLEEP: {
        "poor": -0.8,
        "fair": 0.0,
        "good": 0.5,
    },
    LifeEventType.SCHEDULE: {
        "busy": -0.7,
        "normal": 0.0,
        "free": 0.6,
    },
    LifeEventType.SOCIAL: {
        "high": -0.5,
        "medium": 0.0,
        "low": 0.3,
    },
    LifeEventType.ENERGY: {
        "low": -0.6,
        "medium": 0.1,
        "high": 0.5,
    },
    LifeEventType.MOOD: {
        "stressed": -0.6,
        "neutral": 0.0,
        "positive": 0.4,
    },
}

# Default levels when no data
DEFAULT_LEVELS = {
    LifeEventType.SLEEP: "fair",
    LifeEventType.SCHEDULE: "normal",
    LifeEventType.SOCIAL: "medium",
    LifeEventType.ENERGY: "medium",
    LifeEventType.MOOD: "neutral",
}


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class LifeEventScore:
    """A single life event with impact score."""
    event_type: LifeEventType
    level: str                    # poor/fair/good, low/medium/high, etc.
    impact_score: float           # -1.0 to +1.0
    source: str = "inferred"      # user_input | inferred | calendar
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "level": self.level,
            "impact_score": self.impact_score,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @property
    def is_blocking(self) -> bool:
        """Whether this event blocks effective learning."""
        return self.impact_score < -0.3
    
    @property
    def display_label(self) -> str:
        """Human-readable label for UI."""
        labels = {
            LifeEventType.SLEEP: "Sleep Quality",
            LifeEventType.SCHEDULE: "Schedule",
            LifeEventType.SOCIAL: "Social Events",
            LifeEventType.ENERGY: "Energy Level",
            LifeEventType.MOOD: "Mood",
        }
        return labels.get(self.event_type, self.event_type.value)


@dataclass
class TimeWindow:
    """A recommended learning time window."""
    start: datetime
    end: datetime
    quality: float    # 0.0 to 1.0 (how good this window is)
    reason: str       # Why this window is recommended
    
    @property
    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        return int((self.end - self.start).total_seconds() / 60)
    
    @property
    def display_time(self) -> str:
        """Get display string like '10:30 - 11:15'."""
        return f"{self.start.strftime('%H:%M')} - {self.end.strftime('%H:%M')}"


# =============================================================================
# Life Event Collector
# =============================================================================

class LifeEventCollector:
    """
    Collects and analyzes life events for decision-making.
    
    Data sources:
    1. User input (via Memory module)
    2. Inferred from episodic memories
    3. Future: Calendar integration, health apps
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
    
    async def get_today_events(self) -> List[LifeEventScore]:
        """
        Get all life events for today.
        
        Returns list of LifeEventScore for each event type.
        """
        events = []
        
        # Try to get from memory store
        memory_events = await self._get_from_memory()
        
        # Fill in missing types with defaults
        found_types = {e.event_type for e in memory_events}
        for event_type in LifeEventType:
            if event_type in found_types:
                # Use memory event
                ev = next(e for e in memory_events if e.event_type == event_type)
                events.append(ev)
            else:
                # Use default
                level = DEFAULT_LEVELS[event_type]
                score = IMPACT_SCORES[event_type][level]
                events.append(LifeEventScore(
                    event_type=event_type,
                    level=level,
                    impact_score=score,
                    source="inferred",
                ))
        
        return events
    
    async def _get_from_memory(self) -> List[LifeEventScore]:
        """Get life events from database and episodic memory."""
        events = []
        
        # First, check InterruptionDAO for today's life events (persistent storage)
        try:
            from db.dao.interruption_dao import InterruptionDAO
            
            today_interruptions = await InterruptionDAO.list_today(self.user_id)
            
            # Category to LifeEventType mapping
            category_map = {
                "sleep": LifeEventType.SLEEP,
                "schedule": LifeEventType.SCHEDULE,
                "social": LifeEventType.SOCIAL,
                "energy": LifeEventType.ENERGY,
                "mood": LifeEventType.MOOD,
                "fatigue": LifeEventType.ENERGY,  # fatigue maps to energy
                "time": LifeEventType.SCHEDULE,  # time maps to schedule
            }
            
            for i in today_interruptions:
                event_type = category_map.get(i.get("category"))
                if not event_type:
                    continue
                    
                level = i.get("metadata", {}).get("level", "medium")
                impact = i.get("impact_level", 0.5)
                # Convert impact from 0-1 scale to -1 to +1 scale
                # High impact (bad) = negative, Low impact (good) = positive
                impact_score = -impact if impact > 0.5 else (0.5 - impact)
                
                events.append(LifeEventScore(
                    event_type=event_type,
                    level=level,
                    impact_score=impact_score,
                    source="interruption_db",
                    timestamp=datetime.fromisoformat(i["detected_at"]) if i.get("detected_at") else datetime.now(),
                ))
                
        except Exception as e:
            print(f"LifeEventCollector interruption error: {e}")
        
        # Then, also check episodic memory for backward compatibility
        try:
            from chronomem.memory_store import get_memory_store
            store = get_memory_store(self.user_id)
            
            # Get recent episodic memories
            memories = await store.list_episodic(limit=20)
            today = datetime.now().date()
            
            for m in memories:
                if not m.created_at or m.created_at.date() != today:
                    continue
                
                # Parse event type from metadata or content
                event = self._parse_memory_to_event(m)
                if event:
                    events.append(event)
                    
        except Exception as e:
            print(f"LifeEventCollector memory error: {e}")
        
        return events

    
    def _parse_memory_to_event(self, memory) -> Optional[LifeEventScore]:
        """Parse a memory into a life event."""
        content = memory.content.lower()
        meta = memory.metadata or {}
        
        # Check for explicit event_type in metadata
        if "life_event_type" in meta:
            try:
                event_type = LifeEventType(meta["life_event_type"])
                level = meta.get("level", "medium")
                score = IMPACT_SCORES.get(event_type, {}).get(level, 0.0)
                return LifeEventScore(
                    event_type=event_type,
                    level=level,
                    impact_score=score,
                    source="user_input",
                    timestamp=memory.created_at or datetime.now(),
                    metadata=meta,
                )
            except ValueError:
                pass
        
        # Infer from content keywords
        event_type, level = self._infer_from_content(content)
        if event_type:
            score = IMPACT_SCORES.get(event_type, {}).get(level, 0.0)
            return LifeEventScore(
                event_type=event_type,
                level=level,
                impact_score=score,
                source="inferred",
                timestamp=memory.created_at or datetime.now(),
            )
        
        return None
    
    def _infer_from_content(self, content: str) -> Tuple[Optional[LifeEventType], str]:
        """Infer event type and level from content keywords."""
        # Sleep keywords
        if any(w in content for w in ["sleep", "slept", "tired", "insomnia"]):
            if any(w in content for w in ["poor", "bad", "terrible", "didn't"]):
                return LifeEventType.SLEEP, "poor"
            elif any(w in content for w in ["good", "great", "well"]):
                return LifeEventType.SLEEP, "good"
            return LifeEventType.SLEEP, "fair"
        
        # Schedule keywords
        if any(w in content for w in ["meeting", "busy", "schedule", "appointment"]):
            if any(w in content for w in ["busy", "packed", "full", "many"]):
                return LifeEventType.SCHEDULE, "busy"
            elif any(w in content for w in ["free", "empty", "clear"]):
                return LifeEventType.SCHEDULE, "free"
            return LifeEventType.SCHEDULE, "normal"
        
        # Social keywords
        if any(w in content for w in ["party", "dinner", "friends", "family", "social"]):
            if any(w in content for w in ["big", "many", "lots"]):
                return LifeEventType.SOCIAL, "high"
            return LifeEventType.SOCIAL, "medium"
        
        # Energy keywords
        if any(w in content for w in ["energy", "tired", "exhausted", "energetic"]):
            if any(w in content for w in ["low", "tired", "exhausted", "drained"]):
                return LifeEventType.ENERGY, "low"
            elif any(w in content for w in ["high", "energetic", "great"]):
                return LifeEventType.ENERGY, "high"
            return LifeEventType.ENERGY, "medium"
        
        # Mood keywords
        if any(w in content for w in ["stress", "anxious", "happy", "mood"]):
            if any(w in content for w in ["stressed", "anxious", "worried"]):
                return LifeEventType.MOOD, "stressed"
            elif any(w in content for w in ["happy", "positive", "great"]):
                return LifeEventType.MOOD, "positive"
            return LifeEventType.MOOD, "neutral"
        
        return None, ""
    
    async def compute_life_pressure(self) -> float:
        """
        Compute overall life pressure score (0.0 to 1.0).
        
        Higher = more pressure = harder to learn effectively.
        """
        events = await self.get_today_events()
        
        if not events:
            return 0.5  # Neutral
        
        # Average negative impacts (convert to 0-1 scale)
        total_impact = sum(e.impact_score for e in events)
        avg_impact = total_impact / len(events)
        
        # Convert from [-1, 1] to [0, 1] where higher = more pressure
        pressure = (1.0 - avg_impact) / 2.0
        
        return max(0.0, min(1.0, pressure))
    
    async def get_available_windows(self) -> List[TimeWindow]:
        """
        Get recommended learning windows based on life events.
        
        Considers all life event types:
        - Sleep: affects morning window quality
        - Schedule: may reduce all window qualities or suggest shorter sessions
        - Social: affects afternoon/evening windows
        - Energy: affects window durations and quality
        - Mood: affects focus-heavy vs review-light recommendations
        
        Returns windows sorted by quality (best first).
        """
        events = await self.get_today_events()
        pressure = await self.compute_life_pressure()
        
        now = datetime.now()
        today = now.date()
        windows = []
        
        # Build event lookup for quick access
        event_map = {e.event_type: e for e in events}
        
        # Base windows with dynamic reasons
        base_windows = [
            (9, 0, 11, 0, "Morning focus", "morning"),
            (14, 0, 16, 0, "Afternoon session", "afternoon"),
            (19, 0, 21, 0, "Evening review", "evening"),
        ]
        
        # Extract event states
        sleep_level = event_map.get(LifeEventType.SLEEP)
        energy_level = event_map.get(LifeEventType.ENERGY)
        mood_level = event_map.get(LifeEventType.MOOD)
        schedule_level = event_map.get(LifeEventType.SCHEDULE)
        social_level = event_map.get(LifeEventType.SOCIAL)
        
        for start_h, start_m, end_h, end_m, base_reason, period in base_windows:
            start = datetime.combine(today, datetime.min.time().replace(
                hour=start_h, minute=start_m
            ))
            end = datetime.combine(today, datetime.min.time().replace(
                hour=end_h, minute=end_m
            ))
            
            # Skip if window is in past
            if end < now:
                continue
            
            # Adjust start if partially past
            if start < now:
                start = now + timedelta(minutes=15 - now.minute % 15)
            
            # Start with base quality (inversely related to pressure)
            quality = 1.0 - pressure * 0.4
            reason = base_reason
            
            # === Sleep adjustments ===
            if sleep_level and sleep_level.level == "poor":
                if period == "morning":
                    quality *= 0.5
                    reason = "Morning may be hard after poor sleep"
                elif period == "afternoon":
                    quality *= 1.1  # Slightly boost afternoon
                    reason = "Afternoon may work better today"
            elif sleep_level and sleep_level.level == "good":
                if period == "morning":
                    quality *= 1.2
                    reason = "Morning is great after good sleep"
            
            # === Energy adjustments ===
            if energy_level and energy_level.level == "low":
                if period == "evening":
                    quality *= 0.6
                    reason = "Consider rest over evening study"
                else:
                    quality *= 0.8
            elif energy_level and energy_level.level == "high":
                quality *= 1.15
                if period == "morning":
                    reason = "High energy - great for challenging work"
            
            # === Mood adjustments ===
            if mood_level and mood_level.level == "stressed":
                quality *= 0.7
                if period == "evening":
                    reason = "Consider light review only when stressed"
            elif mood_level and mood_level.level == "positive":
                quality *= 1.1
                if quality > 0.8:
                    reason = "Good mood - optimal learning time"
            
            # === Schedule adjustments ===
            if schedule_level and schedule_level.level == "busy":
                quality *= 0.65
                reason = f"Short session recommended ({end_h - start_h - 1}h max)"
            
            # === Social adjustments ===
            if social_level and social_level.level == "high":
                if period in ("afternoon", "evening"):
                    quality *= 0.7
                    reason = "Social commitments may interrupt"
            
            windows.append(TimeWindow(
                start=start,
                end=end,
                quality=max(0.1, min(1.0, quality)),
                reason=reason,
            ))
        
        # If all windows are low quality, add a short "quick session" option
        if windows and all(w.quality < 0.5 for w in windows):
            # Find next available 30-min slot
            quick_start = now + timedelta(minutes=15 - now.minute % 15)
            quick_end = quick_start + timedelta(minutes=30)
            windows.append(TimeWindow(
                start=quick_start,
                end=quick_end,
                quality=0.6,
                reason="Quick 30-min session for tough days",
            ))
        
        # Sort by quality
        windows.sort(key=lambda w: w.quality, reverse=True)
        
        return windows[:3]


# =============================================================================
# Factory Functions
# =============================================================================

def get_life_event_collector(user_id: str = "default") -> LifeEventCollector:
    """Get a LifeEventCollector instance."""
    return LifeEventCollector(user_id)


async def quick_log_event(
    event_type: LifeEventType,
    level: str,
    user_id: str = "default",
) -> str:
    """
    Quick log a life event to database.
    
    Args:
        event_type: Type of life event (SLEEP, ENERGY, MOOD, etc.)
        level: Level string (low/medium/high, poor/fair/good, etc.)
        user_id: User identifier
    
    Returns:
        interruption_id.
    """
    from db.dao.interruption_dao import InterruptionDAO
    
    content = f"{event_type.value.capitalize()}: {level}"
    
    # Calculate impact level (0-1 scale, higher = worse)
    level_impacts = {
        # Negative states (high impact)
        "low": 0.7, "poor": 0.8, "stressed": 0.75, "busy": 0.7, "high": 0.6,
        # Neutral states
        "medium": 0.4, "fair": 0.4, "neutral": 0.4, "normal": 0.4,
        # Positive states (low impact)
        "good": 0.2, "great": 0.1, "positive": 0.2, "free": 0.2,
    }
    impact = level_impacts.get(level.lower(), 0.5)
    
    return await InterruptionDAO.add(
        source="life_event",
        content=content,
        category=event_type.value,
        impact_level=impact,
        user_id=user_id,
        metadata={"level": level, "event_type": event_type.value},
    )
