# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/evidence_dao.py
# Purpose: Evidence data access
# ===========================================================================

"""Evidence DAO - Traceable evidence CRUD operations."""

import uuid
from typing import Optional, Dict, Any, List
from db.connection import get_db


class EvidenceDAO:
    """Data access for evidence table."""
    
    @staticmethod
    async def create(
        type: str,
        summary: str,
        ref_type: Optional[str] = None,
        ref_id: Optional[str] = None,
        ttl_days: int = 30,
        user_id: str = "default"
    ) -> str:
        """
        Create evidence record, return evidence_id.
        
        Args:
            type: Evidence type (receipt, mastery, settings, reme_memory, etc.)
            summary: Human-readable summary of the evidence.
            ref_type: Reference table name (e.g., "execution_receipt").
            ref_id: Reference ID in the referenced table.
            ttl_days: Time-to-live in days (for cleanup).
        """
        evidence_id = str(uuid.uuid4())
        db = await get_db()
        await db.execute(
            """INSERT INTO evidence 
               (evidence_id, user_id, type, ref_type, ref_id, summary, ttl_days)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (evidence_id, user_id, type, ref_type, ref_id, summary, ttl_days)
        )
        await db.commit()
        return evidence_id
    
    @staticmethod
    async def get(evidence_id: str) -> Optional[Dict[str, Any]]:
        """Get evidence by ID."""
        db = await get_db()
        async with db.execute(
            "SELECT * FROM evidence WHERE evidence_id = ?",
            (evidence_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return EvidenceDAO._row_to_dict(row)
        return None
    
    @staticmethod
    async def list_by_type(type: str, user_id: str = "default", limit: int = 20) -> List[Dict[str, Any]]:
        """Get evidence by type."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM evidence 
               WHERE type = ? AND user_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?""",
            (type, user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [EvidenceDAO._row_to_dict(r) for r in rows]
    
    @staticmethod
    async def list_recent(user_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent evidence for user."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM evidence 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?""",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [EvidenceDAO._row_to_dict(r) for r in rows]
    
    @staticmethod
    async def delete_expired() -> int:
        """Delete expired evidence (beyond TTL). Returns count deleted."""
        db = await get_db()
        cursor = await db.execute(
            """DELETE FROM evidence 
               WHERE julianday('now') - julianday(created_at) > ttl_days"""
        )
        await db.commit()
        return cursor.rowcount
    
    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        """Convert row to dict. Handles both tuple and dict formats."""
        # If row is already a dict, return it
        if isinstance(row, dict):
            return row
        # Otherwise, convert from tuple
        return {
            "evidence_id": row[0],
            "user_id": row[1],
            "type": row[2],
            "ref_type": row[3],
            "ref_id": row[4],
            "summary": row[5],
            "created_at": row[6],
            "ttl_days": row[7],
        }
