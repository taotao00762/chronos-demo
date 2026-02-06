# ===========================================================================
# Chronos AI Learning Companion
# File: db/connection.py
# Purpose: Async SQLite connection management
# ===========================================================================

"""
Database Connection Management

Provides async connection to SQLite database.
Uses aiosqlite for non-blocking database operations.
"""

import aiosqlite
from pathlib import Path
from typing import Optional

# Database file path
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "chronos.db"

# Global connection (singleton pattern for desktop app)
_connection: Optional[aiosqlite.Connection] = None


async def init_db() -> aiosqlite.Connection:
    """
    Initialize database connection and create tables.
    
    Returns:
        Active database connection.
    """
    global _connection
    
    # Ensure data directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create connection
    _connection = await aiosqlite.connect(DB_PATH)
    _connection.row_factory = aiosqlite.Row
    
    # Enable foreign keys
    await _connection.execute("PRAGMA foreign_keys = ON")
    
    # Create tables
    from db.schema import create_tables
    await create_tables(_connection)
    
    return _connection


async def get_db() -> aiosqlite.Connection:
    """
    Get database connection.
    
    Initializes connection if not already connected.
    
    Returns:
        Active database connection.
    """
    global _connection
    
    if _connection is None:
        await init_db()
    
    return _connection


async def close_db() -> None:
    """Close database connection."""
    global _connection
    
    if _connection is not None:
        await _connection.close()
        _connection = None
