# ===========================================================================
# Chronos AI Learning Companion
# File: services/dashboard_service.py
# Purpose: Dashboard data aggregation service
# ===========================================================================

"""
Dashboard Service

Aggregates data for the 6 core Principal decision metrics:
1. Plan Mode - today's mode (Recovery/Standard/Sprint)
2. Interruption Level - fragmentation from Evidence
3. Focus Windows - recommended time slots
4. Completion - yesterday/week completion rate
5. Mastery Trend - top 3 weak concepts
6. Plan Changes - 7-day adjustment count
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from db.dao.decision_dao import DecisionDAO
from db.dao.evidence_dao import EvidenceDAO
from db.dao.mastery_dao import MasteryDAO
from db.dao.session_dao import SessionDAO
from db.dao.tutor_chat_dao import TutorChatDAO, TutorMessageDAO


class DashboardService:
    """Service for dashboard data aggregation."""

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    async def get_plan_mode(self) -> Dict[str, Any]:
        """
        Get today's plan mode.

        Returns mode based on latest decision or default.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        decision = await DecisionDAO.get_by_date(today, self.user_id)

        if decision and decision.get("proposal"):
            mode = decision["proposal"].get("mode", "standard")
        else:
            mode = "standard"

        return {
            "mode": mode,
            "label": mode.capitalize(),
            "has_decision": decision is not None,
        }

    async def get_interruption_level(self) -> Dict[str, Any]:
        """
        Get interruption/fragmentation level from Evidence.

        Counts 'interruption' type evidence in last 24h and 7d.
        """
        all_evidence = await EvidenceDAO.list_recent(self.user_id, limit=100)

        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        count_24h = 0
        count_7d = 0

        for ev in all_evidence:
            created = ev.get("created_at", "")
            if not created:
                continue
            try:
                ev_time = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue

            ev_type = ev.get("type", "").lower()
            if "interrupt" in ev_type or "fragment" in ev_type:
                if ev_time >= day_ago:
                    count_24h += 1
                if ev_time >= week_ago:
                    count_7d += 1

        # Level: low (0-2), medium (3-5), high (6+)
        if count_24h <= 2:
            level = "low"
        elif count_24h <= 5:
            level = "medium"
        else:
            level = "high"

        return {
            "level": level,
            "count_24h": count_24h,
            "count_7d": count_7d,
        }

    async def get_focus_windows(self) -> List[Dict[str, str]]:
        """
        Get recommended focus time windows.

        Rule-based: returns default windows for now.
        Future: analyze session patterns for personalization.
        """
        # Default recommended windows
        return [
            {"start": "09:00", "end": "11:00", "label": "Morning Focus"},
            {"start": "14:00", "end": "16:00", "label": "Afternoon Deep"},
            {"start": "20:00", "end": "21:30", "label": "Evening Review"},
        ]

    async def get_completion(self) -> Dict[str, Any]:
        """
        Get completion rate for yesterday and this week.
        
        Uses WeeklyPlanDAO for week progress if available.
        """
        # Yesterday stats (session based)
        sessions = await SessionDAO.list_recent(self.user_id, limit=30)
        now = datetime.now()
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        
        yesterday_count = 0
        for s in sessions:
            if s.get("started_at", "")[:10] == yesterday:
                yesterday_count += 1
                
        # Expected: 3 sessions per day (default)
        yesterday_pct = min(100, int(yesterday_count / 3 * 100))
        
        # Week stats (Plan based)
        from db.dao.weekly_plan_dao import WeeklyPlanDAO
        plan_progress = await WeeklyPlanDAO.get_week_progress(self.user_id)
        
        if plan_progress.get("has_plan"):
            week_pct = plan_progress.get("progress_pct", 0)
            week_count = plan_progress.get("completed_days", 0)
        else:
            # Fallback to session counting if no plan
            week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
            week_count = 0
            for s in sessions:
                if s.get("started_at", "")[:10] >= week_start:
                    week_count += 1
            week_pct = min(100, int(week_count / 15 * 100))

        return {
            "yesterday": yesterday_pct,
            "yesterday_count": yesterday_count,
            "week": week_pct,
            "week_count": week_count,
        }

    async def get_mastery_trend(self) -> List[Dict[str, Any]]:
        """
        Get top 3 weak concepts from Mastery.

        Returns concepts with lowest score.
        """
        weak = await MasteryDAO.list_weak(self.user_id, threshold=0.6)
        top_weak = weak[:3]

        return [
            {
                "concept_id": m["concept_id"],
                "score": round(m["score"] * 100),
                "last_practiced": m.get("last_practiced_at", "Never"),
            }
            for m in top_weak
        ]

    async def get_plan_changes(self) -> Dict[str, Any]:
        """
        Get plan change count in last 7 days.

        Counts decisions with user_action_type != 'accept'.
        """
        decisions = await DecisionDAO.list_recent(self.user_id, limit=14)

        now = datetime.now()
        week_ago = now - timedelta(days=7)

        change_count = 0
        for d in decisions:
            created = d.get("created_at", "")
            if not created:
                continue
            try:
                d_time = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue

            if d_time >= week_ago:
                if d.get("user_action_type") != "accept":
                    change_count += 1

        return {
            "count_7d": change_count,
            "has_changes": change_count > 0,
        }

    async def get_recent_chats(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get recent tutor chats with preview.

        Returns chat title and last message preview.
        """
        chats = await TutorChatDAO.list_recent(limit=limit, user_id=self.user_id)

        result = []
        for chat in chats:
            messages = await TutorMessageDAO.list_by_chat(chat["chat_id"], limit=1)
            preview = ""
            if messages:
                preview = messages[-1].get("content", "")[:50]
                if len(messages[-1].get("content", "")) > 50:
                    preview += "..."

            result.append({
                "chat_id": chat["chat_id"],
                "title": chat.get("title", "New Chat"),
                "preview": preview,
                "updated_at": chat.get("updated_at", ""),
            })

        return result

    async def aggregate(self) -> Dict[str, Any]:
        """
        Aggregate all dashboard metrics.

        Returns dict with all 6 core metrics + recent chats.
        """
        return {
            "plan_mode": await self.get_plan_mode(),
            "interruption": await self.get_interruption_level(),
            "focus_windows": await self.get_focus_windows(),
            "completion": await self.get_completion(),
            "mastery_trend": await self.get_mastery_trend(),
            "plan_changes": await self.get_plan_changes(),
            "recent_chats": await self.get_recent_chats(),
        }
