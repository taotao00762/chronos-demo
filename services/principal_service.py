# ===========================================================================
# Chronos AI Learning Companion
# File: services/principal_service.py
# Purpose: Shared Principal (Decision Engine) context utilities
# ===========================================================================

"""
Principal Context Service

Provides a thin wrapper around the DecisionEngine so UI modules can
request the current Principal decision/context without duplicating logic.

Responsibilities:
    - Lazily compute today's DecisionResult (mode, confidence, etc.)
    - Cache the result per-day to avoid repeated heavy computations
    - Provide prompt-friendly context dictionaries for tutor/briefing
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from chronomem.decision_engine import DecisionEngine, DecisionResult


class PrincipalContextService:
    """Facade for computing and formatting Principal decisions."""

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self._engine = DecisionEngine(user_id=user_id)
        self._cached_date: Optional[str] = None
        self._cached_result: Optional[DecisionResult] = None

    # ---------------------------------------------------------------------
    # Core decision accessors
    # ---------------------------------------------------------------------

    async def get_decision_result(
        self,
        *,
        force_refresh: bool = False,
    ) -> DecisionResult:
        """
        Get today's DecisionResult, recomputing if needed.

        Args:
            force_refresh: Force recomputation even if cached.
        """
        today = date.today().isoformat()

        if (
            not force_refresh
            and self._cached_date == today
            and self._cached_result is not None
        ):
            return self._cached_result

        result = await self._engine.compute()
        self._cached_date = today
        self._cached_result = result
        return result

    # ---------------------------------------------------------------------
    # Context builders
    # ---------------------------------------------------------------------

    async def get_plan_context(
        self,
        *,
        max_reasons: int = 2,
        max_topics: int = 3,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Build a context dict suitable for system prompts / UI.

        Keys:
            mode, confidence, life_pressure, composite_score,
            reasons, recommended_windows, topics, timestamp
        """
        result = await self.get_decision_result(force_refresh=force_refresh)
        return self._format_result(result, max_reasons=max_reasons, max_topics=max_topics)

    def _format_result(
        self,
        result: DecisionResult,
        *,
        max_reasons: int,
        max_topics: int,
    ) -> Dict[str, Any]:
        """Convert DecisionResult into a serializable dict."""
        reasons = [
            step.reasoning
            for step in result.decision_chain
            if step.weighted != 0
        ][:max_reasons]

        windows = result.recommended_windows[:max_topics] if result.recommended_windows else []
        topics = [
            w.get("reason") or w.get("time") or "Focus window"
            for w in windows
            if isinstance(w, dict)
        ]

        return {
            "mode": result.mode,
            "confidence": round(result.confidence, 3),
            "life_pressure": round(result.life_pressure, 3),
            "composite_score": round(result.composite_score, 4),
            "reasons": reasons,
            "recommended_windows": windows,
            "topics": topics,
            "timestamp": result.timestamp.isoformat(),
            "tier_scores": {k: round(v, 4) for k, v in result.tier_scores.items()},
            "factor_contributions": {
                k: round(v, 4) for k, v in result.factor_contributions.items()
            },
        }

    # ---------------------------------------------------------------------
    # Utility helpers
    # ---------------------------------------------------------------------

    async def as_dict(
        self,
        *,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Return the full DecisionResult as a dict for logging/serialization.
        """
        result = await self.get_decision_result(force_refresh=force_refresh)
        data = result.to_dict()
        data["timestamp"] = result.timestamp.isoformat()
        return data


_service_cache: Dict[str, PrincipalContextService] = {}


def get_principal_context_service(user_id: str = "default") -> PrincipalContextService:
    """Get (or create) a PrincipalContextService for the user."""
    if user_id not in _service_cache:
        _service_cache[user_id] = PrincipalContextService(user_id=user_id)
    return _service_cache[user_id]
