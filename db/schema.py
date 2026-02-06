# ===========================================================================
# Chronos AI Learning Companion
# File: db/schema.py
# Purpose: SQLite table definitions
# ===========================================================================

"""
Database Schema

Defines all SQLite tables for the Chronos authority database.
Tables are organized by domain:
- User & Profile
- Learning Sessions & Receipts
- Plans & Decisions
- Evidence Chain
- Knowledge & Mastery
"""

import aiosqlite


# =============================================================================
# Table Creation SQL
# =============================================================================

TABLES = {
    # -------------------------------------------------------------------------
    # 1. User Profile
    # -------------------------------------------------------------------------
    "user_profile": """
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id TEXT PRIMARY KEY DEFAULT 'default',
            goals_json TEXT DEFAULT '[]',
            constraints_json TEXT DEFAULT '{}',
            preferences_json TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """,
    
    # -------------------------------------------------------------------------
    # 2. Learning Session
    # -------------------------------------------------------------------------
    "session": """
        CREATE TABLE IF NOT EXISTS session (
            session_id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'default',
            started_at TEXT DEFAULT (datetime('now')),
            ended_at TEXT,
            mode TEXT DEFAULT 'standard',
            meta_json TEXT DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 3. Execution Receipt (Tutor output)
    # -------------------------------------------------------------------------
    "execution_receipt": """
        CREATE TABLE IF NOT EXISTS execution_receipt (
            receipt_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id TEXT DEFAULT 'default',
            topics_json TEXT DEFAULT '[]',
            duration_min INTEGER DEFAULT 0,
            metrics_json TEXT DEFAULT '{}',
            stuck_points_json TEXT DEFAULT '[]',
            learner_state_json TEXT DEFAULT '{}',
            summary TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES session(session_id),
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 4. Plan (Daily learning plan)
    # -------------------------------------------------------------------------
    "plan": """
        CREATE TABLE IF NOT EXISTS plan (
            plan_id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'default',
            date TEXT NOT NULL,
            plan_json TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 5. Decision Record (Principal decisions with rationale)
    # -------------------------------------------------------------------------
    "decision_record": """
        CREATE TABLE IF NOT EXISTS decision_record (
            decision_id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'default',
            date TEXT NOT NULL,
            proposal_json TEXT DEFAULT '{}',
            final_plan_json TEXT DEFAULT '[]',
            diff_json TEXT DEFAULT '{}',
            user_action_type TEXT DEFAULT 'accept',
            user_patch_json TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 6. Evidence (Traceable facts for decisions)
    # -------------------------------------------------------------------------
    "evidence": """
        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'default',
            type TEXT NOT NULL,
            ref_type TEXT,
            ref_id TEXT,
            summary TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            ttl_days INTEGER DEFAULT 30,
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 7. Decision-Evidence Link (M:N)
    # -------------------------------------------------------------------------
    "decision_evidence": """
        CREATE TABLE IF NOT EXISTS decision_evidence (
            decision_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            PRIMARY KEY (decision_id, evidence_id),
            FOREIGN KEY (decision_id) REFERENCES decision_record(decision_id),
            FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 8. Concept (Knowledge graph nodes)
    # -------------------------------------------------------------------------
    "concept": """
        CREATE TABLE IF NOT EXISTS concept (
            concept_id TEXT PRIMARY KEY,
            subject TEXT DEFAULT 'general',
            name TEXT NOT NULL,
            tags_json TEXT DEFAULT '[]',
            difficulty INTEGER DEFAULT 1,
            meta_json TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """,
    
    # -------------------------------------------------------------------------
    # 9. Concept Edge (Knowledge graph edges)
    # -------------------------------------------------------------------------
    "concept_edge": """
        CREATE TABLE IF NOT EXISTS concept_edge (
            src_concept_id TEXT NOT NULL,
            dst_concept_id TEXT NOT NULL,
            edge_type TEXT DEFAULT 'prerequisite',
            PRIMARY KEY (src_concept_id, dst_concept_id, edge_type),
            FOREIGN KEY (src_concept_id) REFERENCES concept(concept_id),
            FOREIGN KEY (dst_concept_id) REFERENCES concept(concept_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 10. Mastery (User proficiency per concept)
    # -------------------------------------------------------------------------
    "mastery": """
        CREATE TABLE IF NOT EXISTS mastery (
            user_id TEXT DEFAULT 'default',
            concept_id TEXT NOT NULL,
            score REAL DEFAULT 0.0,
            confidence REAL DEFAULT 0.5,
            last_practiced_at TEXT,
            updated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, concept_id),
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id),
            FOREIGN KEY (concept_id) REFERENCES concept(concept_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 11. Tutor Chat (Multi-session chat management)
    # -------------------------------------------------------------------------
    "tutor_chat": """
        CREATE TABLE IF NOT EXISTS tutor_chat (
            chat_id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'default',
            title TEXT DEFAULT 'New Chat',
            subject TEXT DEFAULT 'custom',
            grade TEXT DEFAULT 'high',
            style TEXT DEFAULT 'patient',
            message_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 12. Tutor Message (Chat messages)
    # -------------------------------------------------------------------------
    "tutor_message": """
        CREATE TABLE IF NOT EXISTS tutor_message (
            message_id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (chat_id) REFERENCES tutor_chat(chat_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 13. Global Memory (Unified memory for Principal/Tutor)
    # -------------------------------------------------------------------------
    "global_memory": """
        CREATE TABLE IF NOT EXISTS global_memory (
            memory_id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'default',
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            confidence REAL DEFAULT 0.8,
            ttl_days INTEGER DEFAULT 30,
            editable INTEGER DEFAULT 1,
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 14. Weekly Plan (Week-level learning plan)
    # -------------------------------------------------------------------------
    "weekly_plan": """
        CREATE TABLE IF NOT EXISTS weekly_plan (
            week_plan_id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'default',
            week_start TEXT NOT NULL,
            goals_json TEXT DEFAULT '[]',
            available_days_json TEXT DEFAULT '{}',
            intensity TEXT DEFAULT 'balanced',
            status TEXT DEFAULT 'active',
            adjustments_json TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
        )
    """,
    
    # -------------------------------------------------------------------------
    # 15. Interruption (Life interruptions and complaints)
    # -------------------------------------------------------------------------
    "interruption": """
        CREATE TABLE IF NOT EXISTS interruption (
            interruption_id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'default',
            source TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            impact_level REAL DEFAULT 0.5,
            metadata_json TEXT DEFAULT '{}',
            detected_at TEXT DEFAULT (datetime('now')),
            processed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
        )
    """,
}


# =============================================================================
# Index Creation
# =============================================================================

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_session_user ON session(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_receipt_session ON execution_receipt(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_receipt_user ON execution_receipt(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_plan_date ON plan(date)",
    "CREATE INDEX IF NOT EXISTS idx_decision_date ON decision_record(date)",
    "CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(type)",
    "CREATE INDEX IF NOT EXISTS idx_mastery_user ON mastery(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_memory_type ON global_memory(type)",
    "CREATE INDEX IF NOT EXISTS idx_memory_user ON global_memory(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_memory_created ON global_memory(created_at)",
]


# =============================================================================
# Public API
# =============================================================================

async def create_tables(conn: aiosqlite.Connection) -> None:
    """
    Create all database tables and indexes.
    
    Args:
        conn: Database connection.
    """
    for table_name, sql in TABLES.items():
        await conn.execute(sql)
    
    for index_sql in INDEXES:
        await conn.execute(index_sql)
    
    # Insert default user profile if not exists
    await conn.execute("""
        INSERT OR IGNORE INTO user_profile (user_id) VALUES ('default')
    """)
    
    await conn.commit()


async def drop_all_tables(conn: aiosqlite.Connection) -> None:
    """
    Drop all tables (for testing/reset).
    
    Args:
        conn: Database connection.
    """
    for table_name in reversed(list(TABLES.keys())):
        await conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    await conn.commit()
