# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/interruption_dao.py
# Purpose: Life interruption/complaint data access
# ===========================================================================

"""Interruption DAO - Track life interruptions and complaints for plan adjustment."""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from db.connection import get_db
from db.dao.evidence_dao import EvidenceDAO


class InterruptionDAO:
    """Data access for interruption table."""
    
    @staticmethod
    async def add(
        source: str,
        content: str,
        category: str,
        impact_level: float,
        user_id: str = "default",
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Record an interruption event.
        
        Args:
            source: "tutor_chat" | "life_event" | "manual" | "calendar"
            content: Original content that triggered detection
            category: "fatigue" | "time" | "difficulty" | "mood" | "schedule"
            impact_level: 0.0 to 1.0 (severity)
            user_id: User identifier
            metadata: Additional context
            
        Returns:
            interruption_id
        """
        interruption_id = str(uuid.uuid4())
        meta = metadata.copy() if metadata else {}
        try:
            summary = f"Interruption: {category} ({impact_level:.2f}) - {content[:80]}"
            evidence_id = await EvidenceDAO.create(
                type="interruption",
                summary=summary,
                ref_type="interruption",
                ref_id=interruption_id,
                ttl_days=14,
                user_id=user_id,
            )
            meta["evidence_id"] = evidence_id
        except Exception as e:
            print(f"Warning: interruption evidence create failed: {e}")
        
        db = await get_db()
        await db.execute(
            """INSERT INTO interruption 
               (interruption_id, user_id, source, content, category, 
                impact_level, metadata_json, detected_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (
                interruption_id, 
                user_id, 
                source,
                content[:500],  # Limit content length
                category,
                impact_level,
                json.dumps(meta),
            )
        )
        await db.commit()
        return interruption_id
    
    @staticmethod
    async def list_this_week(user_id: str = "default") -> List[Dict[str, Any]]:
        """Get all interruptions for current week."""
        # Calculate week start (Monday)
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        week_start = monday.strftime("%Y-%m-%d")
        
        db = await get_db()
        async with db.execute(
            """SELECT * FROM interruption 
               WHERE user_id = ? AND date(detected_at) >= ?
               ORDER BY detected_at DESC""",
            (user_id, week_start)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "interruption_id": r[0],
                    "user_id": r[1],
                    "source": r[2],
                    "content": r[3],
                    "category": r[4],
                    "impact_level": r[5],
                    "metadata": json.loads(r[6]) if r[6] else {},
                    "detected_at": r[7],
                    "processed": bool(r[8]) if len(r) > 8 else False,
                }
                for r in rows
            ]
    
    @staticmethod
    async def list_today(user_id: str = "default") -> List[Dict[str, Any]]:
        """Get all life event interruptions for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        db = await get_db()
        async with db.execute(
            """SELECT * FROM interruption 
               WHERE user_id = ? AND date(detected_at) = ?
               ORDER BY detected_at DESC""",
            (user_id, today)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "interruption_id": r[0],
                    "user_id": r[1],
                    "source": r[2],
                    "content": r[3],
                    "category": r[4],
                    "impact_level": r[5],
                    "metadata": json.loads(r[6]) if r[6] else {},
                    "detected_at": r[7],
                    "processed": bool(r[8]) if len(r) > 8 else False,
                }
                for r in rows
            ]
    
    @staticmethod
    async def list_unprocessed(user_id: str = "default") -> List[Dict[str, Any]]:
        """Get interruptions that haven't been processed for plan adjustment."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM interruption 
               WHERE user_id = ? AND processed = 0
               ORDER BY detected_at DESC""",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "interruption_id": r[0],
                    "user_id": r[1],
                    "source": r[2],
                    "content": r[3],
                    "category": r[4],
                    "impact_level": r[5],
                    "metadata": json.loads(r[6]) if r[6] else {},
                    "detected_at": r[7],
                }
                for r in rows
            ]
    
    @staticmethod
    async def mark_processed(interruption_ids: List[str]) -> int:
        """Mark interruptions as processed."""
        if not interruption_ids:
            return 0
        
        db = await get_db()
        placeholders = ",".join("?" * len(interruption_ids))
        await db.execute(
            f"""UPDATE interruption 
                SET processed = 1 
                WHERE interruption_id IN ({placeholders})""",
            interruption_ids
        )
        await db.commit()
        return len(interruption_ids)
    
    @staticmethod
    async def get_impact_summary(user_id: str = "default") -> Dict[str, Any]:
        """
        Get summary of interruption impacts for this week.
        
        Returns:
            {
                "total_count": 5,
                "by_category": {"fatigue": 2, "time": 3},
                "avg_impact": 0.6,
                "most_recent": {...},
            }
        """
        interruptions = await InterruptionDAO.list_this_week(user_id)
        
        if not interruptions:
            return {
                "total_count": 0,
                "by_category": {},
                "avg_impact": 0.0,
                "most_recent": None,
            }
        
        by_category = {}
        total_impact = 0.0
        
        for i in interruptions:
            cat = i.get("category", "other")
            by_category[cat] = by_category.get(cat, 0) + 1
            total_impact += i.get("impact_level", 0.5)
        
        return {
            "total_count": len(interruptions),
            "by_category": by_category,
            "avg_impact": total_impact / len(interruptions),
            "most_recent": interruptions[0] if interruptions else None,
        }
