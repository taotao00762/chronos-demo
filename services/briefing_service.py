  # ===========================================================================
# Chronos AI Learning Companion
# File: services/briefing_service.py
# Purpose: Daily Briefing generation service (rule-first, AI polish optional)
# ===========================================================================

"""
Briefing Service

Generates daily briefing data using rule-based logic:
1. Yesterday Snapshot - completion, sessions, stuck points
2. Today Proposal - mode recommendation, type ratio, block sizes
3. AI Polish (optional) - natural language copywriting

Rule layer decides WHAT, AI layer (optional) decides HOW TO SAY.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from db.dao.decision_dao import DecisionDAO
from db.dao.evidence_dao import EvidenceDAO
from db.dao.mastery_dao import MasteryDAO
from db.dao.session_dao import SessionDAO


class BriefingService:
    """Service for generating daily briefing data."""

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    async def get_yesterday_snapshot(self) -> Dict[str, Any]:
        """
        Get yesterday's learning snapshot.

        Returns completion rate, session count, best window, stuck point.
        """
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Get sessions from yesterday
        sessions = await SessionDAO.list_recent(self.user_id, limit=20)
        yesterday_sessions = [
            s for s in sessions
            if s.get("started_at", "")[:10] == yesterday
        ]

        session_count = len(yesterday_sessions)
        expected_sessions = 3  # Default expected

        # Completion percentage
        completion = min(100, int(session_count / expected_sessions * 100))

        # Best window: analyze session times (simplified)
        best_window = self._analyze_best_window(yesterday_sessions)

        # Stuck point: from recent evidence
        stuck_point = await self._get_stuck_point()

        # Interruption count from evidence
        interruptions = await self._count_interruptions(yesterday)

        return {
            "date": yesterday,
            "completion": f"{completion}%",
            "completion_value": completion,
            "sessions": session_count,
            "interruptions": interruptions,
            "best_window": best_window,
            "stuck_point": stuck_point,
        }

    async def get_today_proposal(self) -> Dict[str, Any]:
        """
        Generate today's learning proposal.

        Uses DecisionEngine for intelligent mode selection with life events
        as the primary factor (50% weight).
        """
        snapshot = await self.get_yesterday_snapshot()
        weak_concepts = await MasteryDAO.list_weak(self.user_id, threshold=0.6)

        # Use DecisionEngine for intelligent mode selection
        decision_result = await self._get_decision()
        mode = decision_result.mode if decision_result else "standard"
        
        # Get memory context from PrincipalLens (for additional reasons)
        memory_context = await self._get_memory_context()

        # Type ratio based on mode
        type_ratio = self._get_type_ratio(mode)

        # Block sizes
        block_sizes = self._get_block_sizes(mode)

        # Benefit prediction
        benefit = self._predict_benefit(mode, snapshot)

        # Changes from standard
        changes = self._generate_changes(mode)
        
        # Build decision reasons from engine + memory
        decision_reasons = await self._build_decision_reasons(decision_result, memory_context)
        
        # Get weekly plan context
        weekly_context = await self._get_weekly_context()
        
        # Get history insight for today
        history_insight = await self._get_history_insight()

        return {
            "mode": mode,
            "mode_label": mode.capitalize(),
            "type_ratio": type_ratio,
            "block_sizes": block_sizes,
            "benefit": benefit,
            "changes": changes,
            "weak_concepts": [c["concept_id"] for c in weak_concepts[:3]],
            "is_recommended": True,
            "confidence": decision_result.confidence if decision_result else 0.5,
            "life_pressure": decision_result.life_pressure if decision_result else 0.5,
            "decision_reasons": decision_reasons,
            "counterfactuals": decision_result.counterfactuals if decision_result else [],
            "recommended_windows": decision_result.recommended_windows if decision_result else [],
            "memory_context": memory_context,
            "weekly_context": weekly_context,
            "history_insight": history_insight,
        }
    
    async def _get_weekly_context(self) -> Dict[str, Any]:
        """Get weekly plan context for day-level decisions."""
        try:
            from services.weekly_plan_service import get_weekly_plan_service
            service = get_weekly_plan_service(self.user_id)
            return await service.get_today_context()
        except Exception as e:
            print(f"Weekly context error: {e}")
            return {
                "has_weekly_plan": False,
                "week_progress_pct": 0,
                "remaining_days": 0,
                "behind_schedule": False,
                "interruption_count": 0,
            }
    
    async def _get_decision(self) -> Optional["DecisionResult"]:
        """Get decision from DecisionEngine."""
        try:
            from chronomem.decision_engine import get_decision_engine
            engine = get_decision_engine(self.user_id)
            return await engine.compute()
        except Exception as e:
            print(f"DecisionEngine error: {e}")
            return None
    
    async def _get_history_insight(self) -> Optional[str]:
        """Get history insight for today from PatternAnalyzer."""
        try:
            from chronomem.pattern_analyzer import get_pattern_analyzer
            analyzer = get_pattern_analyzer(self.user_id)
            return await analyzer.get_today_insight()
        except Exception as e:
            print(f"PatternAnalyzer error: {e}")
            return None
    
    async def _build_decision_reasons(
        self, 
        decision_result, 
        memory_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Build decision reasons from engine and memory."""
        reasons = []

        # Add interruption-based reasons (top 2 by impact today)
        try:
            from db.dao.interruption_dao import InterruptionDAO
            interruptions = await InterruptionDAO.list_today(self.user_id)
            interruptions = sorted(
                interruptions,
                key=lambda i: i.get("impact_level", 0.0),
                reverse=True,
            )[:2]
            for i in interruptions:
                meta = i.get("metadata", {}) if isinstance(i.get("metadata"), dict) else {}
                summary = f"Recent interruption: {i.get('category', 'other')} - {i.get('content', '')[:60]}"
                reasons.append({
                    "type": "interruption",
                    "tier_label": "Life",
                    "factor": i.get("category", "interruption"),
                    "summary": summary,
                    "impact": "negative",
                    "confidence": min(1.0, float(i.get("impact_level", 0.5))),
                    "evidence_id": meta.get("evidence_id"),
                })
        except Exception as e:
            print(f"Interruption reason error: {e}")
        
        # Add top factors from decision engine
        if decision_result:
            for factor, weighted in decision_result.top_factors:
                direction = "positive" if weighted > 0 else "negative"
                tier_label = {1: "Life", 2: "Learning", 3: "Pattern"}
                
                # Find the step for this factor
                step = next(
                    (s for s in decision_result.decision_chain if s.factor == factor),
                    None
                )
                
                reasons.append({
                    "type": f"tier_{step.tier}" if step else "factor",
                    "tier_label": tier_label.get(step.tier, "Factor") if step else "Factor",
                    "factor": factor,
                    "summary": step.reasoning if step else f"{factor}: {direction}",
                    "impact": direction,
                    "confidence": abs(weighted) * 10,  # Scale to 0-1
                })
        
        # Add memory-based reasons
        for mem_reason in memory_context.get("decision_reasons", [])[:2]:
            reasons.append({
                "type": "memory",
                "tier_label": "Memory",
                "factor": mem_reason.get("type", "context"),
                "summary": mem_reason.get("summary", ""),
                "impact": "neutral",
                "confidence": mem_reason.get("confidence", 0.5),
            })
        
        return reasons[:5]  # Top 5 reasons
    
    async def _get_memory_context(self) -> Dict[str, Any]:
        """Get memory context from PrincipalLens for decision-making."""
        try:
            from chronomem.lens import get_principal_lens
            lens = get_principal_lens(self.user_id)
            context = await lens.get_context()
            
            # Build decision reasons from memory
            reasons = []
            
            # Add profile-based reasons
            if context.get("profile_summary") and context["profile_summary"] != "No preference data available.":
                reasons.append({
                    "type": "profile",
                    "summary": context["profile_summary"][:60],
                    "confidence": 0.9,
                })
            
            # Add episode-based reasons
            for ep in context.get("recent_episodes", [])[:2]:
                reasons.append({
                    "type": "episodic",
                    "summary": ep.get("summary", "")[:60],
                    "confidence": ep.get("confidence", 0.7),
                })
            
            # Add skill-based reasons
            for sk in context.get("weak_skills", [])[:2]:
                reasons.append({
                    "type": "skill",
                    "summary": sk.get("summary", "")[:60],
                    "confidence": sk.get("confidence", 0.5),
                })
            
            return {
                "profile_summary": context.get("profile_summary", ""),
                "constraints": context.get("constraints", []),
                "has_recent_episodes": len(context.get("recent_episodes", [])) > 0,
                "weak_skill_count": len(context.get("weak_skills", [])),
                "decision_reasons": reasons,
            }
        except Exception as e:
            print(f"PrincipalLens context error: {e}")
            return {
                "profile_summary": "",
                "constraints": [],
                "has_recent_episodes": False,
                "weak_skill_count": 0,
                "decision_reasons": [],
            }

    def _determine_mode(self, snapshot: Dict[str, Any], memory_context: Dict[str, Any] = None) -> str:
        """
        Determine today's mode based on yesterday's data.

        Rules:
        - Recovery: completion < 50% or interruptions >= 5
        - Sprint: completion >= 90% and interruptions < 2
        - Standard: otherwise
        """
        completion = snapshot.get("completion_value", 0)
        interruptions = snapshot.get("interruptions", 0)

        if completion < 50 or interruptions >= 5:
            return "recovery"
        elif completion >= 90 and interruptions < 2:
            return "sprint"
        else:
            return "standard"

    def _get_type_ratio(self, mode: str) -> Dict[str, int]:
        """Get learning type ratio for mode."""
        ratios = {
            "recovery": {"learn": 20, "review": 50, "practice": 30},
            "standard": {"learn": 40, "review": 30, "practice": 30},
            "sprint": {"learn": 60, "review": 20, "practice": 20},
        }
        return ratios.get(mode, ratios["standard"])

    def _get_block_sizes(self, mode: str) -> Dict[str, int]:
        """Get block sizes (in minutes) for mode."""
        sizes = {
            "recovery": {"small": 15, "medium": 25, "large": 40},
            "standard": {"small": 25, "medium": 45, "large": 60},
            "sprint": {"small": 30, "medium": 50, "large": 75},
        }
        return sizes.get(mode, sizes["standard"])

    def _predict_benefit(self, mode: str, snapshot: Dict[str, Any]) -> str:
        """Generate benefit prediction text."""
        benefits = {
            "recovery": "Higher completion + lower start cost",
            "standard": "Balanced progress across all areas",
            "sprint": "Accelerated learning with deeper focus",
        }
        return benefits.get(mode, benefits["standard"])

    def _generate_changes(self, mode: str) -> List[Dict[str, str]]:
        """Generate change items for display."""
        if mode == "recovery":
            return [
                {"type": "change", "icon": "~", "text": "Mode: Learn -> Practice"},
                {"type": "move", "icon": "<->", "text": "Deep block moved to focus window"},
                {"type": "add", "icon": "+", "text": "Add: 10m warm-up review"},
            ]
        elif mode == "sprint":
            return [
                {"type": "change", "icon": "~", "text": "Mode: Standard -> Sprint"},
                {"type": "extend", "icon": "+", "text": "Extended focus blocks"},
                {"type": "remove", "icon": "-", "text": "Reduced review time"},
            ]
        else:
            return [
                {"type": "keep", "icon": "=", "text": "Standard mode maintained"},
            ]

    def _analyze_best_window(self, sessions: List[Dict]) -> str:
        """Analyze best focus window from sessions."""
        if not sessions:
            return "10:00-11:00"

        # Count sessions by hour
        hour_counts = {}
        for s in sessions:
            started = s.get("started_at", "")
            if len(started) >= 13:
                try:
                    hour = int(started[11:13])
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                except ValueError:
                    pass

        if not hour_counts:
            return "10:00-11:00"

        best_hour = max(hour_counts, key=hour_counts.get)
        return f"{best_hour:02d}:00-{best_hour + 1:02d}:00"

    async def _get_stuck_point(self) -> str:
        """Get stuck point from recent evidence or mastery."""
        weak = await MasteryDAO.list_weak(self.user_id, threshold=0.4)
        if weak:
            return weak[0]["concept_id"]

        # Check evidence for stuck type
        evidence = await EvidenceDAO.list_by_type("stuck", self.user_id, limit=1)
        if evidence:
            return evidence[0].get("summary", "Unknown")[:30]

        return "None detected"

    async def _count_interruptions(self, date: str) -> int:
        """Count interruption evidence for a date."""
        from db.dao.interruption_dao import InterruptionDAO
        
        # Get all interruptions for the week (optimization: could add specific date query)
        week_interruptions = await InterruptionDAO.list_this_week(self.user_id)
        
        count = 0
        for i in week_interruptions:
            # i["detected_at"] is ISO string
            detected = i.get("detected_at", "")
            if detected[:10] == date:
                count += 1
        
        return count

    async def generate(self) -> Dict[str, Any]:
        """
        Generate complete briefing data.

        Returns snapshot + proposal.
        """
        return {
            "snapshot": await self.get_yesterday_snapshot(),
            "proposal": await self.get_today_proposal(),
            "date": datetime.now().strftime("%A, %b %d"),
        }
