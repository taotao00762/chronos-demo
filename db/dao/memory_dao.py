# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/memory_dao.py
# Purpose: Global memory data access operations
# ===========================================================================

"""
MemoryDAO - CRUD operations for global_memory table.

Supports:
- Add/get/update/delete memories
- List by type with filtering
- Expiration cleanup
"""

import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from db.connection import get_db
from chronomem.models import GlobalMemory, MemoryType, MemorySource


class MemoryDAO:
    """Data access for global_memory table."""
    
    @staticmethod
    async def create(memory: GlobalMemory) -> str:
        """
        Create a memory record.
        
        Args:
            memory: GlobalMemory object to store.
        
        Returns:
            memory_id of created record.
        """
        db = await get_db()
        await db.execute(
            """INSERT INTO global_memory 
               (memory_id, user_id, type, content, source, confidence, 
                ttl_days, editable, metadata_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory.memory_id,
                memory.user_id,
                memory.type.value,
                memory.content,
                memory.source.value,
                memory.confidence,
                memory.ttl_days,
                1 if memory.editable else 0,
                json.dumps(memory.metadata),
                memory.created_at.isoformat() if memory.created_at else datetime.now().isoformat(),
                memory.updated_at.isoformat() if memory.updated_at else datetime.now().isoformat(),
            )
        )
        await db.commit()
        return memory.memory_id
    
    @staticmethod
    async def get(memory_id: str) -> Optional[GlobalMemory]:
        """Get memory by ID."""
        db = await get_db()
        async with db.execute(
            "SELECT * FROM global_memory WHERE memory_id = ?",
            (memory_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return MemoryDAO._row_to_memory(row)
        return None
    
    @staticmethod
    async def list_by_type(
        mem_type: MemoryType,
        user_id: str = "default",
        limit: int = 50,
    ) -> List[GlobalMemory]:
        """List memories by type."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM global_memory 
               WHERE type = ? AND user_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?""",
            (mem_type.value, user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [MemoryDAO._row_to_memory(r) for r in rows]
    
    @staticmethod
    async def list_recent(
        user_id: str = "default",
        limit: int = 50,
    ) -> List[GlobalMemory]:
        """List all recent memories for a user."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM global_memory 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?""",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [MemoryDAO._row_to_memory(r) for r in rows]
    
    @staticmethod
    async def update(
        memory_id: str,
        content: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update memory fields.
        
        Returns:
            True if updated, False if not found.
        """
        db = await get_db()
        
        updates = ["updated_at = datetime('now')"]
        params = []
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if confidence is not None:
            updates.append("confidence = ?")
            params.append(confidence)
        if metadata is not None:
            updates.append("metadata_json = ?")
            params.append(json.dumps(metadata))
        
        params.append(memory_id)
        
        cursor = await db.execute(
            f"UPDATE global_memory SET {', '.join(updates)} WHERE memory_id = ?",
            params
        )
        await db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    async def delete(memory_id: str) -> bool:
        """Delete a memory by ID."""
        db = await get_db()
        cursor = await db.execute(
            "DELETE FROM global_memory WHERE memory_id = ?",
            (memory_id,)
        )
        await db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    async def cleanup_expired() -> int:
        """
        Delete expired memories (beyond TTL).
        
        Returns:
            Number of records deleted.
        """
        db = await get_db()
        cursor = await db.execute(
            """DELETE FROM global_memory 
               WHERE julianday('now') - julianday(created_at) > ttl_days"""
        )
        await db.commit()
        return cursor.rowcount
    
    @staticmethod
    def _row_to_memory(row) -> GlobalMemory:
        """Convert database row to GlobalMemory object."""
        # Handle both tuple and dict rows
        if isinstance(row, dict):
            data = row
        else:
            data = {
                "memory_id": row[0],
                "user_id": row[1],
                "type": row[2],
                "content": row[3],
                "source": row[4],
                "confidence": row[5],
                "ttl_days": row[6],
                "editable": row[7],
                "metadata_json": row[8],
                "created_at": row[9],
                "updated_at": row[10],
            }
        
        metadata = {}
        if data.get("metadata_json"):
            try:
                metadata = json.loads(data["metadata_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        
        return GlobalMemory(
            memory_id=data["memory_id"],
            user_id=data.get("user_id", "default"),
            type=MemoryType(data["type"]),
            content=data["content"],
            source=MemorySource(data.get("source", "system")),
            confidence=data.get("confidence", 0.8),
            ttl_days=data.get("ttl_days", 30),
            editable=bool(data.get("editable", 1)),
            metadata=metadata,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
