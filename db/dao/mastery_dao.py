# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/mastery_dao.py
# Purpose: Concept mastery data access
# ===========================================================================

"""Mastery DAO - User concept mastery CRUD operations."""

from typing import Optional, Dict, Any, List
from db.connection import get_db


class MasteryDAO:
    """Data access for mastery table."""
    
    @staticmethod
    async def upsert(
        concept_id: str,
        score: float,
        confidence: float = 0.5,
        user_id: str = "default"
    ) -> None:
        """Insert or update mastery record."""
        db = await get_db()
        await db.execute(
            """INSERT INTO mastery 
               (user_id, concept_id, score, confidence, last_practiced_at, updated_at)
               VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
               ON CONFLICT(user_id, concept_id) DO UPDATE SET
               score = excluded.score,
               confidence = excluded.confidence,
               last_practiced_at = datetime('now'),
               updated_at = datetime('now')""",
            (user_id, concept_id, score, confidence)
        )
        await db.commit()
    
    @staticmethod
    async def get(concept_id: str, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get mastery for a concept."""
        db = await get_db()
        async with db.execute(
            "SELECT * FROM mastery WHERE user_id = ? AND concept_id = ?",
            (user_id, concept_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return MasteryDAO._row_to_dict(row)
        return None
    
    @staticmethod
    async def list_all(user_id: str = "default") -> List[Dict[str, Any]]:
        """Get all mastery records for user."""
        db = await get_db()
        async with db.execute(
            "SELECT * FROM mastery WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [MasteryDAO._row_to_dict(r) for r in rows]
    
    @staticmethod
    async def list_weak(user_id: str = "default", threshold: float = 0.6) -> List[Dict[str, Any]]:
        """Get concepts below mastery threshold."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM mastery 
               WHERE user_id = ? AND score < ? 
               ORDER BY score ASC""",
            (user_id, threshold)
        ) as cursor:
            rows = await cursor.fetchall()
            return [MasteryDAO._row_to_dict(r) for r in rows]
    
    @staticmethod
    async def increment_score(
        concept_id: str,
        delta: float,
        user_id: str = "default"
    ) -> None:
        """Increment mastery score (clamped to 0-1)."""
        db = await get_db()
        await db.execute(
            """UPDATE mastery 
               SET score = MIN(1.0, MAX(0.0, score + ?)),
                   last_practiced_at = datetime('now'),
                   updated_at = datetime('now')
               WHERE user_id = ? AND concept_id = ?""",
            (delta, user_id, concept_id)
        )
        await db.commit()
    
    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        """Convert row to dict."""
        return {
            "user_id": row[0],
            "concept_id": row[1],
            "score": row[2],
            "confidence": row[3],
            "last_practiced_at": row[4],
            "updated_at": row[5],
        }
