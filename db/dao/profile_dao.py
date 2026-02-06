# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/profile_dao.py
# Purpose: User profile data access
# ===========================================================================

"""Profile DAO - User profile CRUD operations."""

import json
from typing import Optional, Dict, Any, List
from db.connection import get_db


class ProfileDAO:
    """Data access for user_profile table."""
    
    @staticmethod
    async def get(user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get user profile by ID."""
        db = await get_db()
        async with db.execute(
            "SELECT * FROM user_profile WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "goals": json.loads(row[1]),
                    "constraints": json.loads(row[2]),
                    "preferences": json.loads(row[3]),
                    "created_at": row[4],
                    "updated_at": row[5],
                }
        return None
    
    @staticmethod
    async def update_goals(user_id: str, goals: List[str]) -> None:
        """Update user goals."""
        db = await get_db()
        await db.execute(
            """UPDATE user_profile 
               SET goals_json = ?, updated_at = datetime('now') 
               WHERE user_id = ?""",
            (json.dumps(goals), user_id)
        )
        await db.commit()
    
    @staticmethod
    async def update_preferences(user_id: str, prefs: Dict[str, Any]) -> None:
        """Update user preferences."""
        db = await get_db()
        await db.execute(
            """UPDATE user_profile 
               SET preferences_json = ?, updated_at = datetime('now') 
               WHERE user_id = ?""",
            (json.dumps(prefs), user_id)
        )
        await db.commit()
    
    @staticmethod
    async def update_constraints(user_id: str, constraints: Dict[str, Any]) -> None:
        """Update user constraints."""
        db = await get_db()
        await db.execute(
            """UPDATE user_profile 
               SET constraints_json = ?, updated_at = datetime('now') 
               WHERE user_id = ?""",
            (json.dumps(constraints), user_id)
        )
        await db.commit()
