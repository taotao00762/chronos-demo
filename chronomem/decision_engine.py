# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/decision_engine.py
# Purpose: Multi-factor weighted decision engine with life event priority
# ===========================================================================

"""
Decision Engine

3-Tier weighted decision-making:
- Tier 1 (50%): Life Events (sleep, schedule, social, energy, mood)
- Tier 2 (30%): Learning State (completion, streak, weak skills)
- Tier 3 (20%): Historical Patterns (time, day, past success)

Life events have highest priority - they can override other factors.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

from chronomem.life_events import (
    LifeEventCollector,
    LifeEventType,
    get_life_event_collector,
)
from db.dao.decision_dao import DecisionDAO


# =============================================================================
# Constants
# =============================================================================

class DecisionFactor(Enum):
    """
    All decision factors with (name, weight, tier).
    
    Tier 1: Life Events (total 0.50)
    Tier 2: Learning State (total 0.30)
    Tier 3: Historical Patterns (total 0.20)
    """
    # Tier 1: Life Events
    SLEEP_QUALITY = ("sleep", 0.12, 1)
    SCHEDULE_PRESSURE = ("schedule", 0.12, 1)
    SOCIAL_LOAD = ("social", 0.10, 1)
    ENERGY_LEVEL = ("energy", 0.10, 1)
    MOOD_STATE = ("mood", 0.06, 1)
    
    # Tier 2: Learning State
    COMPLETION_RATE = ("completion", 0.12, 2)
    STREAK_DAYS = ("streak", 0.08, 2)
    WEAK_SKILL_URGENCY = ("weak_skill", 0.10, 2)
    
    # Tier 3: Historical Patterns
    TIME_OF_DAY = ("time", 0.08, 3)
    DAY_OF_WEEK = ("day", 0.06, 3)
    PAST_MODE_SUCCESS = ("history", 0.06, 3)
    
    @property
    def name_key(self) -> str:
        return self.value[0]
    
    @property
    def weight(self) -> float:
        return self.value[1]
    
    @property
    def tier(self) -> int:
        return self.value[2]


class LearningMode(Enum):
    """Available learning modes."""
    RECOVERY = "recovery"    # Low pressure, easy tasks
    STANDARD = "standard"    # Balanced approach
    SPRINT = "sprint"        # High intensity


# Mode thresholds based on composite score
# Score: -1 (worst) to +1 (best)
MODE_THRESHOLDS = {
    LearningMode.RECOVERY: (-1.0, -0.2),    # Bad conditions
    LearningMode.STANDARD: (-0.2, 0.3),     # Neutral
    LearningMode.SPRINT: (0.3, 1.0),        # Great conditions
}


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class DecisionStep:
    """A step in the decision chain for explainability."""
    factor: str
    tier: int
    value: float           # Raw value (-1 to 1)
    weighted: float        # After weight applied
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor": self.factor,
            "tier": self.tier,
            "value": round(self.value, 2),
            "weighted": round(self.weighted, 4),
            "reasoning": self.reasoning,
        }


@dataclass
class DecisionResult:
    """Complete decision output with explainability."""
    mode: str                                    # recovery/standard/sprint
    confidence: float                            # 0.0-1.0
    composite_score: float                       # -1.0 to 1.0
    life_pressure: float                         # 0.0-1.0 (from Tier 1)
    factor_contributions: Dict[str, float]       # Factor -> weighted value
    tier_scores: Dict[int, float]                # Tier -> total contribution
    decision_chain: List[DecisionStep]           # Ordered reasoning steps
    counterfactuals: List[str]                   # "If X then Y" hints
    recommended_windows: List[Dict[str, Any]]    # Time windows
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "confidence": round(self.confidence, 2),
            "composite_score": round(self.composite_score, 2),
            "life_pressure": round(self.life_pressure, 2),
            "factor_contributions": {
                k: round(v, 4) for k, v in self.factor_contributions.items()
            },
            "tier_scores": {
                str(k): round(v, 3) for k, v in self.tier_scores.items()
            },
            "decision_chain": [s.to_dict() for s in self.decision_chain],
            "counterfactuals": self.counterfactuals,
            "recommended_windows": self.recommended_windows,
        }
    
    @property
    def top_factors(self) -> List[Tuple[str, float]]:
        """Get top 3 contributing factors."""
        sorted_factors = sorted(
            self.factor_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )
        return sorted_factors[:3]


# =============================================================================
# Decision Engine
# =============================================================================

class DecisionEngine:
    """
    Multi-factor weighted decision engine.
    
    Computes optimal learning mode based on 3-tier factor hierarchy.
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.life_collector = get_life_event_collector(user_id)
    
    async def compute(self) -> DecisionResult:
        """
        Compute learning mode decision.
        
        Returns full DecisionResult with mode, confidence, and explanation.
        """
        # Step 1: Collect all signals
        signals = await self._collect_signals()
        
        # Step 2: Apply weights and build decision chain
        chain, contributions = self._apply_weights(signals)
        
        # Step 3: Calculate tier scores
        tier_scores = self._calculate_tier_scores(chain)
        
        # Step 4: Compute composite score
        composite = sum(contributions.values())
        
        # Step 5: Select mode
        mode_preference = self._get_mode_preference()
        mode, confidence = self._select_mode(composite, tier_scores, mode_preference)
        
        # Step 6: Get life pressure
        life_pressure = await self.life_collector.compute_life_pressure()
        
        # Step 7: Get recommended windows
        windows = await self.life_collector.get_available_windows()
        
        # Step 8: Generate counterfactuals
        counterfactuals = self._generate_counterfactuals(
            mode, composite, signals, contributions
        )
        
        return DecisionResult(
            mode=mode,
            confidence=confidence,
            composite_score=composite,
            life_pressure=life_pressure,
            factor_contributions=contributions,
            tier_scores=tier_scores,
            decision_chain=chain,
            counterfactuals=counterfactuals,
            recommended_windows=[
                {"time": w.display_time, "quality": w.quality, "reason": w.reason}
                for w in windows
            ],
        )
    
    async def _collect_signals(self) -> Dict[DecisionFactor, float]:
        """Collect raw signal values for all factors."""
        signals = {}
        
        # Tier 1: Life Events
        life_events = await self.life_collector.get_today_events()
        event_map = {e.event_type: e for e in life_events}
        
        signals[DecisionFactor.SLEEP_QUALITY] = event_map.get(
            LifeEventType.SLEEP
        ).impact_score if LifeEventType.SLEEP in event_map else 0.0
        
        signals[DecisionFactor.SCHEDULE_PRESSURE] = event_map.get(
            LifeEventType.SCHEDULE
        ).impact_score if LifeEventType.SCHEDULE in event_map else 0.0
        
        signals[DecisionFactor.SOCIAL_LOAD] = event_map.get(
            LifeEventType.SOCIAL
        ).impact_score if LifeEventType.SOCIAL in event_map else 0.0
        
        signals[DecisionFactor.ENERGY_LEVEL] = event_map.get(
            LifeEventType.ENERGY
        ).impact_score if LifeEventType.ENERGY in event_map else 0.0
        
        signals[DecisionFactor.MOOD_STATE] = event_map.get(
            LifeEventType.MOOD
        ).impact_score if LifeEventType.MOOD in event_map else 0.0
        
        # Tier 2: Learning State
        signals[DecisionFactor.COMPLETION_RATE] = await self._get_completion_signal()
        signals[DecisionFactor.STREAK_DAYS] = await self._get_streak_signal()
        signals[DecisionFactor.WEAK_SKILL_URGENCY] = await self._get_weak_skill_signal()
        
        # Tier 3: Historical
        signals[DecisionFactor.TIME_OF_DAY] = self._get_time_of_day_signal()
        signals[DecisionFactor.DAY_OF_WEEK] = self._get_day_of_week_signal()
        signals[DecisionFactor.PAST_MODE_SUCCESS] = await self._get_history_signal()
        
        return signals
    
    async def _get_completion_signal(self) -> float:
        """Get yesterday's completion rate signal (-1 to 1)."""
        try:
            from db.dao.session_dao import SessionDAO
            sessions = await SessionDAO.list_recent(self.user_id, limit=10)
            
            # New user: no sessions at all -> slightly positive (encourage starting)
            if not sessions:
                return 0.2
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            yesterday_sessions = [
                s for s in sessions
                if s.get("started_at", "")[:10] == yesterday
            ]
            
            expected = 3  # Expected sessions
            completed = len(yesterday_sessions)
            rate = min(1.0, completed / expected)
            
            # Convert to -1 to 1 scale
            return (rate * 2) - 1
            
        except Exception:
            return 0.2  # Slightly positive for new users
    
    async def _get_streak_signal(self) -> float:
        """Get learning streak signal (-1 to 1)."""
        try:
            from db.dao.session_dao import SessionDAO
            sessions = await SessionDAO.list_recent(self.user_id, limit=30)
            
            # Count consecutive days with sessions
            dates = set()
            for s in sessions:
                started = s.get("started_at", "")[:10]
                if started:
                    dates.add(started)
            
            streak = 0
            check_date = datetime.now().date()
            
            for _ in range(30):
                if check_date.isoformat() in dates:
                    streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break
            
            # Normalize: 7+ days = max positive
            return min(1.0, (streak / 7) * 2 - 1)
            
        except Exception:
            return 0.1  # Slightly positive for new users
    
    async def _get_weak_skill_signal(self) -> float:
        """Get weak skill urgency signal (-1 to 1)."""
        try:
            from db.dao.mastery_dao import MasteryDAO
            weak = await MasteryDAO.list_weak(self.user_id, threshold=0.4)
            
            # More weak skills = more urgency = negative score
            count = len(weak)
            if count == 0:
                return 0.5  # No weak skills = positive
            elif count <= 2:
                return 0.0  # Neutral
            else:
                return -0.5  # Many weak skills = negative
                
        except Exception:
            return 0.0
    
    def _get_time_of_day_signal(self) -> float:
        """Get time of day signal (-1 to 1)."""
        hour = datetime.now().hour
        
        # Best hours: 9-11, 14-16
        if 9 <= hour <= 11 or 14 <= hour <= 16:
            return 0.5
        # Good hours: 8-9, 11-12, 16-18
        elif 8 <= hour <= 18:
            return 0.2
        # Evening: 18-21
        elif 18 <= hour <= 21:
            return 0.0
        # Late night or early morning
        else:
            return -0.3
    
    def _get_day_of_week_signal(self) -> float:
        """Get day of week signal (-1 to 1)."""
        day = datetime.now().weekday()
        
        # Weekdays slightly better for learning habits
        if day < 5:
            return 0.2
        # Weekend: mixed
        return 0.0
    
    async def _get_history_signal(self) -> float:
        """Get past mode success signal (-1 to 1) from real history data."""
        try:
            # Get combined signal from accept rate and day patterns
            success_signal = await DecisionDAO.get_success_signal(self.user_id)
            
            # Add day-of-week specific adjustment
            day_patterns = await DecisionDAO.get_pattern_by_day(self.user_id)
            today = datetime.now().weekday()
            
            day_data = day_patterns.get(today, {})
            if day_data.get("total_decisions", 0) >= 3:
                # Adjust based on historical performance on this day
                day_accept = day_data.get("accept_rate", 0.5)
                day_adjustment = (day_accept - 0.5) * 0.3
                success_signal += day_adjustment
            
            return max(-1.0, min(1.0, success_signal))
        except Exception:
            return 0.0
    
    def _apply_weights(
        self, 
        signals: Dict[DecisionFactor, float]
    ) -> Tuple[List[DecisionStep], Dict[str, float]]:
        """Apply factor weights and build decision chain."""
        chain = []
        contributions = {}
        
        for factor, raw_value in signals.items():
            weighted = raw_value * factor.weight
            
            step = DecisionStep(
                factor=factor.name_key,
                tier=factor.tier,
                value=raw_value,
                weighted=weighted,
                reasoning=self._get_reasoning(factor, raw_value),
            )
            chain.append(step)
            contributions[factor.name_key] = weighted
        
        # Sort by tier, then by absolute contribution
        chain.sort(key=lambda s: (s.tier, -abs(s.weighted)))
        
        return chain, contributions
    
    def _get_reasoning(self, factor: DecisionFactor, value: float) -> str:
        """Get human-readable reasoning for a factor."""
        direction = "positive" if value > 0 else "negative" if value < 0 else "neutral"
        
        reasonings = {
            DecisionFactor.SLEEP_QUALITY: {
                "positive": "Good sleep supports focus",
                "negative": "Poor sleep reduces capacity",
                "neutral": "Sleep was adequate",
            },
            DecisionFactor.SCHEDULE_PRESSURE: {
                "positive": "Schedule is free for learning",
                "negative": "Busy schedule limits windows",
                "neutral": "Normal schedule pressure",
            },
            DecisionFactor.ENERGY_LEVEL: {
                "positive": "High energy enables intensive work",
                "negative": "Low energy suggests lighter tasks",
                "neutral": "Energy level is moderate",
            },
            DecisionFactor.COMPLETION_RATE: {
                "positive": "Yesterday's progress was strong",
                "negative": "Recovery needed from low completion",
                "neutral": "Completion was average",
            },
        }
        
        factor_reasons = reasonings.get(factor, {})
        return factor_reasons.get(direction, f"{factor.name_key}: {direction}")
    
    def _calculate_tier_scores(self, chain: List[DecisionStep]) -> Dict[int, float]:
        """Calculate total contribution per tier."""
        scores = {1: 0.0, 2: 0.0, 3: 0.0}
        
        for step in chain:
            scores[step.tier] += step.weighted
        
        return scores
    
    def _select_mode(
        self, 
        composite: float, 
        tier_scores: Dict[int, float],
        mode_preference: Optional[str] = None,
    ) -> Tuple[str, float]:
        """Select mode and confidence from composite score."""
        thresholds = MODE_THRESHOLDS
        if mode_preference == "sprint":
            thresholds = {
                LearningMode.RECOVERY: (-1.0, -0.2),
                LearningMode.STANDARD: (-0.2, 0.1),
                LearningMode.SPRINT: (0.1, 1.0),
            }
        elif mode_preference == "recovery":
            thresholds = {
                LearningMode.RECOVERY: (-1.0, 0.1),
                LearningMode.STANDARD: (0.1, 0.3),
                LearningMode.SPRINT: (0.3, 1.0),
            }

        # Check thresholds
        for mode, (low, high) in thresholds.items():
            if low <= composite < high:
                # Confidence based on distance from threshold
                mid = (low + high) / 2
                distance = abs(composite - mid) / ((high - low) / 2)
                confidence = 0.5 + (1 - distance) * 0.4
                
                return mode.value, min(0.95, confidence)
        
        # Default to standard
        return LearningMode.STANDARD.value, 0.5

    def _get_mode_preference(self) -> Optional[str]:
        """Read mode preference from settings store if available."""
        try:
            from stores.settings_store import SettingsStore
            settings = SettingsStore.get_instance().get()
            value = getattr(settings, "mode_preference", "")
            return value if value in ("recovery", "standard", "sprint") else None
        except Exception:
            return None
    
    def _generate_counterfactuals(
        self,
        mode: str,
        composite: float,
        signals: Dict[DecisionFactor, float],
        contributions: Dict[str, float],
    ) -> List[str]:
        """Generate 'if X then Y' counterfactual hints."""
        counterfactuals = []
        
        # Find factors that could change the mode
        if mode == "recovery":
            # What would get us to standard?
            gap = 0.3 - composite  # Need to reach -0.2
            
            sleep_signal = signals.get(DecisionFactor.SLEEP_QUALITY, 0)
            if sleep_signal < 0:
                counterfactuals.append(
                    "If you had better sleep, Standard mode might be possible"
                )
            
            energy_signal = signals.get(DecisionFactor.ENERGY_LEVEL, 0)
            if energy_signal < 0:
                counterfactuals.append(
                    "Higher energy would shift recommendation toward Standard"
                )
        
        elif mode == "standard":
            # What would get us to sprint?
            if composite > 0.1:
                counterfactuals.append(
                    "A lighter schedule could enable Sprint mode"
                )
        
        return counterfactuals[:2]


# =============================================================================
# Factory Functions
# =============================================================================

def get_decision_engine(user_id: str = "default") -> DecisionEngine:
    """Get a DecisionEngine instance."""
    return DecisionEngine(user_id)
