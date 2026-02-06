# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/receipt_dao.py
# Purpose: Execution receipt data access
# ===========================================================================

"""Receipt DAO - Tutor execution receipt CRUD operations."""

import json
import uuid
from typing import Optional, Dict, Any, List
from db.connection import get_db


class ReceiptDAO:
    """Data access for execution_receipt table."""
    
    @staticmethod
    async def create(
        session_id: str,
        user_id: str = "default",
        topics: Optional[List[str]] = None,
        duration_min: int = 0,
        metrics: Optional[Dict[str, Any]] = None,
        stuck_points: Optional[List[str]] = None,
        learner_state: Optional[Dict[str, Any]] = None,
        summary: str = ""
    ) -> str:
        """Create execution receipt, return receipt_id."""
        receipt_id = str(uuid.uuid4())
        db = await get_db()
        await db.execute(
            """INSERT INTO execution_receipt 
               (receipt_id, session_id, user_id, topics_json, duration_min,
                metrics_json, stuck_points_json, learner_state_json, summary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                receipt_id, session_id, user_id,
                json.dumps(topics or []),
                duration_min,
                json.dumps(metrics or {}),
                json.dumps(stuck_points or []),
                json.dumps(learner_state or {}),
                summary
            )
        )
        await db.commit()
        return receipt_id
    
    @staticmethod
    async def get(receipt_id: str) -> Optional[Dict[str, Any]]:
        """Get receipt by ID."""
        db = await get_db()
        async with db.execute(
            "SELECT * FROM execution_receipt WHERE receipt_id = ?",
            (receipt_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return ReceiptDAO._row_to_dict(row)
        return None
    
    @staticmethod
    async def list_recent(user_id: str = "default", limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent receipts for user."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM execution_receipt 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?""",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [ReceiptDAO._row_to_dict(r) for r in rows]
    
    @staticmethod
    async def get_by_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get receipt for a session."""
        db = await get_db()
        async with db.execute(
            "SELECT * FROM execution_receipt WHERE session_id = ?",
            (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return ReceiptDAO._row_to_dict(row)
        return None
    
    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        """Convert row to dict."""
        return {
            "receipt_id": row[0],
            "session_id": row[1],
            "user_id": row[2],
            "topics": json.loads(row[3]),
            "duration_min": row[4],
            "metrics": json.loads(row[5]),
            "stuck_points": json.loads(row[6]),
            "learner_state": json.loads(row[7]),
            "summary": row[8],
            "created_at": row[9],
        }
