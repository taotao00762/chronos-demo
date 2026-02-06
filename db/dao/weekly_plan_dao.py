# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/weekly_plan_dao.py
# Purpose: Weekly plan data access
# ===========================================================================

"""Weekly Plan DAO - Week-level learning plan CRUD operations."""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from db.connection import get_db


def get_week_start(date: datetime = None) -> str:
    """Get Monday of the week for a given date as ISO string."""
    if date is None:
        date = datetime.now()
    monday = date - timedelta(days=date.weekday())
    return monday.strftime("%Y-%m-%d")


class WeeklyPlanDAO:
    """Data access for weekly_plan table."""
    
    @staticmethod
    async def create(
        goals: List[str],
        available_days: Dict[str, bool],
        intensity: str = "balanced",
        user_id: str = "default",
        week_start: str = None,
    ) -> str:
        """
        Create a weekly plan.
        
        Args:
            goals: List of learning goals for the week
            available_days: {"mon": True, "tue": False, ...}
            intensity: "light" | "balanced" | "push"
            user_id: User identifier
            week_start: Optional override for week start date
            
        Returns:
            week_plan_id
        """
        week_plan_id = str(uuid.uuid4())
        week_start = week_start or get_week_start()
        
        db = await get_db()
        await db.execute(
            """INSERT INTO weekly_plan 
               (week_plan_id, user_id, week_start, goals_json, 
                available_days_json, intensity, status)
               VALUES (?, ?, ?, ?, ?, ?, 'active')""",
            (
                week_plan_id, 
                user_id, 
                week_start, 
                json.dumps(goals),
                json.dumps(available_days),
                intensity,
            )
        )
        await db.commit()
        return week_plan_id
    
    @staticmethod
    async def get_current_week(user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get the active weekly plan for current week."""
        week_start = get_week_start()
        
        db = await get_db()
        async with db.execute(
            """SELECT * FROM weekly_plan 
               WHERE user_id = ? AND week_start = ? AND status = 'active'
               ORDER BY created_at DESC LIMIT 1""",
            (user_id, week_start)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "week_plan_id": row[0],
                    "user_id": row[1],
                    "week_start": row[2],
                    "goals": json.loads(row[3]),
                    "available_days": json.loads(row[4]),
                    "intensity": row[5],
                    "status": row[6],
                    "adjustments": json.loads(row[7]) if row[7] else [],
                    "created_at": row[8],
                    "updated_at": row[9],
                }
        return None
    
    @staticmethod
    async def add_adjustment(
        week_plan_id: str,
        adjustment: Dict[str, Any],
    ) -> bool:
        """
        Add an adjustment record to the weekly plan.
        
        Args:
            week_plan_id: Plan to adjust
            adjustment: {"type": "reschedule", "from_day": "wed", "to_day": "sat", ...}
        """
        # Get current adjustments
        db = await get_db()
        async with db.execute(
            "SELECT adjustments_json FROM weekly_plan WHERE week_plan_id = ?",
            (week_plan_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            
            current = json.loads(row[0]) if row[0] else []
        
        # Append new adjustment
        adjustment["timestamp"] = datetime.now().isoformat()
        current.append(adjustment)
        
        await db.execute(
            """UPDATE weekly_plan 
               SET adjustments_json = ?, updated_at = datetime('now')
               WHERE week_plan_id = ?""",
            (json.dumps(current), week_plan_id)
        )
        await db.commit()
        return True
    
    @staticmethod
    async def update_available_days(
        week_plan_id: str,
        available_days: Dict[str, bool],
    ) -> bool:
        """Update which days are available for learning."""
        db = await get_db()
        await db.execute(
            """UPDATE weekly_plan 
               SET available_days_json = ?, updated_at = datetime('now')
               WHERE week_plan_id = ?""",
            (json.dumps(available_days), week_plan_id)
        )
        await db.commit()
        return True
    
    @staticmethod
    async def get_week_progress(user_id: str = "default") -> Dict[str, Any]:
        """
        Get progress summary for current week.
        
        Returns:
            {
                "total_days": 5,
                "completed_days": 2,
                "adjustments_count": 1,
                "progress_pct": 40,
            }
        """
        plan = await WeeklyPlanDAO.get_current_week(user_id)
        if not plan:
            return {
                "total_days": 0,
                "completed_days": 0,
                "adjustments_count": 0,
                "progress_pct": 0,
                "has_plan": False,
            }
        
        available = plan.get("available_days", {})
        total_days = sum(1 for v in available.values() if v)
        
        # Count days with sessions this week
        from db.dao.session_dao import SessionDAO
        sessions = await SessionDAO.list_recent(user_id, limit=50)
        
        week_start = datetime.strptime(plan["week_start"], "%Y-%m-%d")
        week_end = week_start + timedelta(days=7)
        
        session_days = set()
        for s in sessions:
            started = s.get("started_at", "")[:10]
            if started:
                try:
                    dt = datetime.strptime(started, "%Y-%m-%d")
                    if week_start <= dt < week_end:
                        session_days.add(started)
                except ValueError:
                    pass
        
        completed = len(session_days)
        
        return {
            "total_days": total_days,
            "completed_days": completed,
            "adjustments_count": len(plan.get("adjustments", [])),
            "progress_pct": int(completed / total_days * 100) if total_days > 0 else 0,
            "has_plan": True,
            "goals": plan.get("goals", []),
            "intensity": plan.get("intensity", "balanced"),
        }
