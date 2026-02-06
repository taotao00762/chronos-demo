# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/plan_dao.py
# Purpose: Learning plan data access
# ===========================================================================

"""Plan DAO - Daily learning plan CRUD operations."""

import json
import uuid
from typing import Optional, Dict, Any, List
from db.connection import get_db


class PlanDAO:
    """Data access for plan table."""
    
    @staticmethod
    async def create(
        date: str,
        plan: List[Dict[str, Any]],
        user_id: str = "default"
    ) -> str:
        """Create daily plan, return plan_id."""
        plan_id = str(uuid.uuid4())
        db = await get_db()
        await db.execute(
            """INSERT INTO plan (plan_id, user_id, date, plan_json)
               VALUES (?, ?, ?, ?)""",
            (plan_id, user_id, date, json.dumps(plan))
        )
        await db.commit()
        return plan_id
    
    @staticmethod
    async def get_by_date(date: str, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get plan for a specific date."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM plan 
               WHERE date = ? AND user_id = ? 
               ORDER BY created_at DESC 
               LIMIT 1""",
            (date, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "plan_id": row[0],
                    "user_id": row[1],
                    "date": row[2],
                    "plan": json.loads(row[3]),
                    "created_at": row[4],
                }
        return None
    
    @staticmethod
    async def list_recent(user_id: str = "default", limit: int = 7) -> List[Dict[str, Any]]:
        """Get recent plans for user."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM plan 
               WHERE user_id = ? 
               ORDER BY date DESC 
               LIMIT ?""",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "plan_id": r[0],
                    "user_id": r[1],
                    "date": r[2],
                    "plan": json.loads(r[3]),
                    "created_at": r[4],
                }
                for r in rows
            ]
