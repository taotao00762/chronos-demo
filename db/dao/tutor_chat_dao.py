# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/tutor_chat_dao.py
# Purpose: Data Access Object for tutor chat sessions
# ===========================================================================

"""
Tutor Chat DAO

Manages tutor chat sessions and messages for multi-session support.
"""

import uuid
from typing import List, Dict, Any, Optional
from db.connection import get_db


class TutorChatDAO:
    """Data access for tutor chat sessions."""
    
    @staticmethod
    async def create(
        subject: str = "custom",
        grade: str = "high",
        style: str = "patient",
        title: str = "New Chat",
        user_id: str = "default",
    ) -> str:
        """Create a new chat session."""
        chat_id = str(uuid.uuid4())
        conn = await get_db()
        await conn.execute(
            """
            INSERT INTO tutor_chat (chat_id, user_id, title, subject, grade, style)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (chat_id, user_id, title, subject, grade, style),
        )
        await conn.commit()
        return chat_id
    
    @staticmethod
    async def get(chat_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session by ID."""
        conn = await get_db()
        conn = await get_db()
        # conn.row_factory is already aiosqlite.Row (global)
        cursor = await conn.execute(
            "SELECT * FROM tutor_chat WHERE chat_id = ?",
            (chat_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    
    @staticmethod
    async def list_recent(limit: int = 20, user_id: str = "default") -> List[Dict[str, Any]]:
        """List recent chat sessions."""
        conn = await get_db()
        conn = await get_db()
        # conn.row_factory is already aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT * FROM tutor_chat 
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    @staticmethod
    async def update_title(chat_id: str, title: str) -> None:
        """Update chat title."""
        conn = await get_db()
        await conn.execute(
            """
            UPDATE tutor_chat 
            SET title = ?, updated_at = datetime('now')
            WHERE chat_id = ?
            """,
            (title, chat_id),
        )
        await conn.commit()
    
    @staticmethod
    async def increment_message_count(chat_id: str) -> None:
        """Increment message count and update timestamp."""
        conn = await get_db()
        await conn.execute(
            """
            UPDATE tutor_chat 
            SET message_count = message_count + 1, updated_at = datetime('now')
            WHERE chat_id = ?
            """,
            (chat_id,),
        )
        await conn.commit()
    
    @staticmethod
    async def delete(chat_id: str) -> None:
        """Delete a chat session and its messages."""
        conn = await get_db()
        await conn.execute("DELETE FROM tutor_message WHERE chat_id = ?", (chat_id,))
        await conn.execute("DELETE FROM tutor_chat WHERE chat_id = ?", (chat_id,))
        await conn.commit()


class TutorMessageDAO:
    """Data access for tutor chat messages."""
    
    @staticmethod
    async def create(chat_id: str, role: str, content: str) -> str:
        """Create a new message."""
        message_id = str(uuid.uuid4())
        conn = await get_db()
        await conn.execute(
            """
            INSERT INTO tutor_message (message_id, chat_id, role, content)
            VALUES (?, ?, ?, ?)
            """,
            (message_id, chat_id, role, content),
        )
        await conn.commit()
        return message_id
    
    @staticmethod
    async def list_by_chat(chat_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """List messages for a chat session."""
        conn = await get_db()
        conn = await get_db()
        # conn.row_factory is already aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT * FROM tutor_message 
            WHERE chat_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (chat_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    @staticmethod
    async def delete_by_chat(chat_id: str) -> None:
        """Delete all messages for a chat."""
        conn = await get_db()
        await conn.execute("DELETE FROM tutor_message WHERE chat_id = ?", (chat_id,))
        await conn.commit()
