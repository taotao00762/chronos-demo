# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/session_dao.py
# Purpose: Learning session data access
# ===========================================================================

"""Session DAO - Learning session CRUD operations."""

import json
import uuid
from typing import Optional, Dict, Any, List
from db.connection import get_db


class SessionDAO:
    """Data access for session table."""
    
    @staticmethod
    async def create(
        user_id: str = "default",
        mode: str = "standard",
        meta: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new session, return session_id."""
        session_id = str(uuid.uuid4())
        db = await get_db()
        await db.execute(
            """INSERT INTO session (session_id, user_id, mode, meta_json) 
               VALUES (?, ?, ?, ?)""",
            (session_id, user_id, mode, json.dumps(meta or {}))
        )
        await db.commit()
        return session_id
    
    @staticmethod
    async def end(session_id: str) -> None:
        """Mark session as ended."""
        db = await get_db()
        await db.execute(
            "UPDATE session SET ended_at = datetime('now') WHERE session_id = ?",
            (session_id,)
        )
        await db.commit()
    
    @staticmethod
    async def get(session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        db = await get_db()
        async with db.execute(
            "SELECT * FROM session WHERE session_id = ?",
            (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "session_id": row[0],
                    "user_id": row[1],
                    "started_at": row[2],
                    "ended_at": row[3],
                    "mode": row[4],
                    "meta": json.loads(row[5]),
                }
        return None
    
    @staticmethod
    async def list_recent(user_id: str = "default", limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions for user."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM session 
               WHERE user_id = ? 
               ORDER BY started_at DESC 
               LIMIT ?""",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            result = []
            for r in rows:
                try:
                    # Handle both tuple and dict row formats
                    if isinstance(r, dict):
                        result.append({
                            "session_id": r.get("session_id"),
                            "user_id": r.get("user_id"),
                            "started_at": r.get("started_at"),
                            "ended_at": r.get("ended_at"),
                            "mode": r.get("mode"),
                            "meta": json.loads(r.get("meta_json", "{}")),
                        })
                    else:
                        result.append({
                            "session_id": r[0],
                            "user_id": r[1],
                            "started_at": r[2],
                            "ended_at": r[3],
                            "mode": r[4],
                            "meta": json.loads(r[5] if r[5] else "{}"),
                        })
                except (IndexError, KeyError, TypeError) as e:
                    print(f"SessionDAO row parse error: {e}, row={r}")
                    continue
            return result
