# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/core/vector_store.py
# Purpose: SQLite-based vector storage with numpy
# ===========================================================================

"""
SQLite Vector Store

Simple vector storage using SQLite + numpy for similarity search.
No external dependencies like ChromaDB required.
"""

import json
import numpy as np
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from chronomem.schema.memory import BaseMemory, PersonalMemory, TaskMemory
from chronomem.core.datetime_handler import DatetimeHandler


# Default database path
DB_PATH = Path("data/chronomem.db")


class SQLiteVectorStore:
    """
    SQLite-based vector store with numpy similarity search.
    """
    
    # SQL for table creation
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS chronomem_vectors (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        content TEXT NOT NULL,
        when_to_use TEXT,
        embedding BLOB,
        metadata_json TEXT,
        user_id TEXT DEFAULT 'default',
        created_at TEXT,
        expires_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_chronomem_type_user 
        ON chronomem_vectors(type, user_id);
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize vector store."""
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure database table exists."""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(self.CREATE_TABLE_SQL)
            await db.commit()
        
        self._initialized = True
    
    async def add(self, memory: BaseMemory) -> str:
        """
        Add a memory to the store.
        
        Args:
            memory: Memory to add.
        
        Returns:
            Memory ID.
        """
        await self._ensure_initialized()
        
        # Serialize embedding
        embedding_blob = None
        if memory.embedding:
            embedding_blob = np.array(memory.embedding, dtype=np.float32).tobytes()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO chronomem_vectors
                (id, type, content, when_to_use, embedding, metadata_json, 
                 user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.id,
                    memory.type,
                    memory.content,
                    memory.when_to_use,
                    embedding_blob,
                    json.dumps(memory.metadata),
                    memory.user_id,
                    memory.created_at.isoformat(),
                    memory.expires_at.isoformat() if memory.expires_at else None,
                ),
            )
            await db.commit()
        
        return memory.id
    
    async def add_batch(self, memories: List[BaseMemory]) -> List[str]:
        """Add multiple memories."""
        ids = []
        for memory in memories:
            mem_id = await self.add(memory)
            ids.append(mem_id)
        return ids
    
    async def search(
        self,
        query_embedding: List[float],
        memory_type: str = "personal",
        user_id: str = "default",
        top_k: int = 5,
        use_time_weight: bool = True,
    ) -> List[Tuple[BaseMemory, float]]:
        """
        Search for similar memories.
        
        Args:
            query_embedding: Query vector.
            memory_type: Type of memory (personal/task).
            user_id: User ID.
            top_k: Number of results.
            use_time_weight: Apply time decay weighting.
        
        Returns:
            List of (memory, score) tuples.
        """
        await self._ensure_initialized()
        
        query_vec = np.array(query_embedding, dtype=np.float32)
        
        results = []
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Fetch all memories of this type for this user
            cursor = await db.execute(
                """
                SELECT * FROM chronomem_vectors 
                WHERE type = ? AND user_id = ?
                """,
                (memory_type, user_id),
            )
            
            rows = await cursor.fetchall()
            
            for row in rows:
                # Skip expired
                if row["expires_at"]:
                    expires = datetime.fromisoformat(row["expires_at"])
                    if DatetimeHandler.is_expired(expires):
                        continue
                
                # Calculate similarity
                if row["embedding"]:
                    stored_vec = np.frombuffer(row["embedding"], dtype=np.float32)
                    
                    # Cosine similarity
                    norm_q = np.linalg.norm(query_vec)
                    norm_s = np.linalg.norm(stored_vec)
                    
                    if norm_q > 0 and norm_s > 0:
                        similarity = np.dot(query_vec, stored_vec) / (norm_q * norm_s)
                    else:
                        similarity = 0.0
                else:
                    similarity = 0.0
                
                # Apply time decay weight
                if use_time_weight and row["created_at"]:
                    created = datetime.fromisoformat(row["created_at"])
                    time_weight = DatetimeHandler.get_age_weight(created)
                    similarity = similarity * time_weight
                
                # Create memory object
                memory = self._row_to_memory(row)
                results.append((memory, float(similarity)))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM chronomem_vectors WHERE id = ?",
                (memory_id,),
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def list_by_type(
        self,
        memory_type: str,
        user_id: str = "default",
        limit: int = 50,
    ) -> List[BaseMemory]:
        """List memories by type."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                """
                SELECT * FROM chronomem_vectors 
                WHERE type = ? AND user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (memory_type, user_id, limit),
            )
            
            rows = await cursor.fetchall()
            return [self._row_to_memory(row) for row in rows]
    
    def _row_to_memory(self, row) -> BaseMemory:
        """Convert database row to memory object."""
        metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
        
        created_at = datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        expires_at = datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
        
        if row["type"] == "personal":
            return PersonalMemory(
                id=row["id"],
                type=row["type"],
                content=row["content"],
                when_to_use=row["when_to_use"] or "",
                metadata=metadata,
                user_id=row["user_id"],
                created_at=created_at,
                expires_at=expires_at,
            )
        elif row["type"] == "task":
            return TaskMemory(
                id=row["id"],
                type=row["type"],
                content=row["content"],
                when_to_use=row["when_to_use"] or "",
                metadata=metadata,
                user_id=row["user_id"],
                created_at=created_at,
                expires_at=expires_at,
            )
        else:
            return BaseMemory(
                id=row["id"],
                type=row["type"],
                content=row["content"],
                when_to_use=row["when_to_use"] or "",
                metadata=metadata,
                user_id=row["user_id"],
                created_at=created_at,
                expires_at=expires_at,
            )


# Singleton instance
_store: Optional[SQLiteVectorStore] = None


def get_vector_store() -> SQLiteVectorStore:
    """Get or create singleton vector store."""
    global _store
    if _store is None:
        _store = SQLiteVectorStore()
    return _store
