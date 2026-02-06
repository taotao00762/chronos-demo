# ===========================================================================
# Chronos AI Learning Companion
# File: services/weekly_plan_service.py
# Purpose: Weekly plan management and adjustment service
# ===========================================================================

"""
Weekly Plan Service

Manages week-level learning plans:
- Setup week with goals and available days
- Track progress through the week
- Adjust plan based on interruptions
- Redistribute tasks when needed
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from db.dao.weekly_plan_dao import WeeklyPlanDAO, get_week_start
from db.dao.interruption_dao import InterruptionDAO
from stores.settings_store import SettingsStore


class WeeklyPlanService:
    """Service for managing weekly learning plans."""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
    
    async def setup_week(
        self,
        goals: List[str],
        available_days: Dict[str, bool],
        intensity: str = "balanced",
    ) -> Dict[str, Any]:
        """
        Create a new weekly plan.
        
        Args:
            goals: List of learning goals (e.g., ["Python basics", "Math review"])
            available_days: {"mon": True, "tue": False, ...}
            intensity: "light" | "balanced" | "push"
            
        Returns:
            Created plan details
        """
        week_plan_id = await WeeklyPlanDAO.create(
            goals=goals,
            available_days=available_days,
            intensity=intensity,
            user_id=self.user_id,
        )
        
        return {
            "week_plan_id": week_plan_id,
            "week_start": get_week_start(),
            "goals": goals,
            "available_days": available_days,
            "intensity": intensity,
            "message": "Weekly plan created successfully",
        }
    
    async def get_week_status(self) -> Dict[str, Any]:
        """
        Get current week status including progress and adjustments.
        
        Returns:
            Week status with progress, interruptions, and adjustments
        """
        # Get progress from DAO
        progress = await WeeklyPlanDAO.get_week_progress(self.user_id)
        
        # Get interruption summary
        interruptions = await InterruptionDAO.get_impact_summary(self.user_id)
        
        # Get current plan
        plan = await WeeklyPlanDAO.get_current_week(self.user_id)
        
        return {
            "has_plan": progress.get("has_plan", False),
            "week_start": get_week_start(),
            "progress": {
                "total_days": progress.get("total_days", 0),
                "completed_days": progress.get("completed_days", 0),
                "progress_pct": progress.get("progress_pct", 0),
            },
            "goals": progress.get("goals", []),
            "intensity": progress.get("intensity", "balanced"),
            "interruptions": {
                "count": interruptions.get("total_count", 0),
                "avg_impact": interruptions.get("avg_impact", 0),
                "by_category": interruptions.get("by_category", {}),
            },
            "adjustments_count": progress.get("adjustments_count", 0),
            "adjustments": plan.get("adjustments", []) if plan else [],
        }
    
    async def process_interruptions(self) -> Dict[str, Any]:
        """
        Process unprocessed interruptions and generate adjustments.
        
        Returns:
            Adjustment actions taken
        """
        settings = None
        try:
            settings = SettingsStore.get_instance().get()
        except Exception:
            settings = None

        # Get unprocessed interruptions
        interruptions = await InterruptionDAO.list_unprocessed(self.user_id)
        
        if not interruptions:
            return {"adjustments": [], "message": "No new interruptions"}

        if settings and not settings.adapt_plan_automatically:
            return {
                "adjustments": [],
                "pending_approval": False,
                "processed_count": 0,
                "pending_interruptions": len(interruptions),
                "message": "Adaptation disabled in settings",
            }
        
        # Get current plan
        plan = await WeeklyPlanDAO.get_current_week(self.user_id)
        if not plan:
            return {"adjustments": [], "message": "No active weekly plan"}
        
        adjustments = []
        processed_ids = []
        approval_required = bool(settings.approval_required) if settings else False
        apply_changes = not approval_required
        
        # Calculate total impact
        total_impact = sum(i.get("impact_level", 0.5) for i in interruptions)
        avg_impact = total_impact / len(interruptions)
        
        # Determine adjustment type based on impact
        if avg_impact >= 0.7:
            # High impact: reduce intensity
            adjustment = {
                "type": "intensity_change",
                "from": plan.get("intensity", "balanced"),
                "to": "light",
                "reason": f"High life pressure detected ({len(interruptions)} interruptions)",
            }
            adjustments.append(adjustment)
            if apply_changes:
                await WeeklyPlanDAO.add_adjustment(plan["week_plan_id"], adjustment)
        
        elif avg_impact >= 0.5:
            # Medium impact: redistribute tasks
            today = datetime.now()
            today_name = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][today.weekday()]
            
            # Find available days later this week
            available = plan.get("available_days", {})
            later_days = []
            for i in range(today.weekday() + 1, 7):
                day_name = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][i]
                if available.get(day_name, False):
                    later_days.append(day_name)
            
            if later_days:
                adjustment = {
                    "type": "redistribute",
                    "from_day": today_name,
                    "to_days": later_days[:2],  # Max 2 days
                    "reason": f"Medium pressure - redistributing to {', '.join(later_days[:2])}",
                }
                adjustments.append(adjustment)
                if apply_changes:
                    await WeeklyPlanDAO.add_adjustment(plan["week_plan_id"], adjustment)

        if not apply_changes:
            return {
                "adjustments": adjustments,
                "pending_approval": True,
                "processed_count": 0,
                "pending_interruptions": len(interruptions),
                "message": "Approval required to apply adjustments",
            }

        # Mark interruptions as processed
        processed_ids = [i["interruption_id"] for i in interruptions]
        await InterruptionDAO.mark_processed(processed_ids)
        
        return {
            "adjustments": adjustments,
            "pending_approval": False,
            "processed_count": len(processed_ids),
            "message": f"Processed {len(processed_ids)} interruptions",
        }
    
    async def get_today_context(self) -> Dict[str, Any]:
        """
        Get weekly context for today's decision making.
        
        Used by DecisionEngine/BriefingService to incorporate week-level data.
        """
        status = await self.get_week_status()
        
        # Calculate remaining workload
        remaining_days = status["progress"]["total_days"] - status["progress"]["completed_days"]
        
        # Check if behind schedule
        today = datetime.now()
        week_start = datetime.strptime(status["week_start"], "%Y-%m-%d")
        days_elapsed = (today - week_start).days + 1
        expected_progress = min(100, int(days_elapsed / 7 * 100))
        actual_progress = status["progress"]["progress_pct"]
        
        behind_schedule = actual_progress < expected_progress - 15  # 15% tolerance
        
        return {
            "has_weekly_plan": status["has_plan"],
            "week_progress_pct": actual_progress,
            "remaining_days": remaining_days,
            "behind_schedule": behind_schedule,
            "interruption_count": status["interruptions"]["count"],
            "avg_impact": status["interruptions"]["avg_impact"],
            "intensity": status["intensity"],
            "goals": status["goals"],
        }


# =============================================================================
# Factory Function
# =============================================================================

def get_weekly_plan_service(user_id: str = "default") -> WeeklyPlanService:
    """Get a WeeklyPlanService instance."""
    return WeeklyPlanService(user_id)
