# ===========================================================================
# Chronos AI Learning Companion
# File: db/dao/decision_dao.py
# Purpose: Decision record data access
# ===========================================================================

"""Decision DAO - Principal decision record CRUD operations."""

import json
import uuid
from typing import Optional, Dict, Any, List
from db.connection import get_db


class DecisionDAO:
    """Data access for decision_record table."""
    
    @staticmethod
    async def create(
        date: str,
        proposal: Dict[str, Any],
        final_plan: List[Dict[str, Any]],
        diff: Dict[str, Any],
        user_action_type: str = "accept",
        user_patch: Optional[Dict[str, Any]] = None,
        user_id: str = "default"
    ) -> str:
        """Create decision record, return decision_id."""
        decision_id = str(uuid.uuid4())
        db = await get_db()
        await db.execute(
            """INSERT INTO decision_record 
               (decision_id, user_id, date, proposal_json, final_plan_json, 
                diff_json, user_action_type, user_patch_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                decision_id, user_id, date,
                json.dumps(proposal),
                json.dumps(final_plan),
                json.dumps(diff),
                user_action_type,
                json.dumps(user_patch or {})
            )
        )
        await db.commit()
        return decision_id
    
    @staticmethod
    async def get(decision_id: str) -> Optional[Dict[str, Any]]:
        """Get decision by ID."""
        db = await get_db()
        async with db.execute(
            "SELECT * FROM decision_record WHERE decision_id = ?",
            (decision_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return DecisionDAO._row_to_dict(row)
        return None
    
    @staticmethod
    async def get_by_date(date: str, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get decision for a specific date."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM decision_record 
               WHERE date = ? AND user_id = ? 
               ORDER BY created_at DESC 
               LIMIT 1""",
            (date, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return DecisionDAO._row_to_dict(row)
        return None
    
    @staticmethod
    async def list_recent(user_id: str = "default", limit: int = 7) -> List[Dict[str, Any]]:
        """Get recent decisions for user."""
        db = await get_db()
        async with db.execute(
            """SELECT * FROM decision_record 
               WHERE user_id = ? 
               ORDER BY date DESC 
               LIMIT ?""",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [DecisionDAO._row_to_dict(r) for r in rows]
    
    @staticmethod
    async def link_evidence(decision_id: str, evidence_id: str) -> None:
        """Link decision to evidence."""
        db = await get_db()
        await db.execute(
            """INSERT OR IGNORE INTO decision_evidence 
               (decision_id, evidence_id) VALUES (?, ?)""",
            (decision_id, evidence_id)
        )
        await db.commit()
    
    @staticmethod
    async def get_evidence_ids(decision_id: str) -> List[str]:
        """Get all evidence IDs for a decision."""
        db = await get_db()
        async with db.execute(
            "SELECT evidence_id FROM decision_evidence WHERE decision_id = ?",
            (decision_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]
    
    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        """Convert row to dict."""
        return {
            "decision_id": row[0],
            "user_id": row[1],
            "date": row[2],
            "proposal": json.loads(row[3]),
            "final_plan": json.loads(row[4]),
            "diff": json.loads(row[5]),
            "user_action_type": row[6],
            "user_patch": json.loads(row[7]),
            "created_at": row[8],
        }
    
    @staticmethod
    async def get_mode_history(user_id: str = "default", days: int = 30) -> List[Dict[str, Any]]:
        """
        Get decision mode history for pattern analysis.
        
        Returns list of {date, mode, user_action_type, day_of_week, hour}.
        """
        db = await get_db()
        async with db.execute(
            """SELECT date, proposal_json, user_action_type, created_at
               FROM decision_record 
               WHERE user_id = ? 
               ORDER BY date DESC 
               LIMIT ?""",
            (user_id, days)
        ) as cursor:
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                proposal = json.loads(r[1])
                # Parse datetime for day/hour
                created = r[3] if r[3] else r[0]
                try:
                    from datetime import datetime as dt
                    dt_obj = dt.fromisoformat(created.replace("Z", ""))
                    day_of_week = dt_obj.weekday()
                    hour = dt_obj.hour
                except Exception:
                    day_of_week = 0
                    hour = 12
                
                results.append({
                    "date": r[0],
                    "mode": proposal.get("mode", "standard"),
                    "user_action_type": r[2],
                    "day_of_week": day_of_week,
                    "hour": hour,
                })
            return results
    
    @staticmethod
    async def get_pattern_by_day(user_id: str = "default") -> Dict[int, Dict[str, Any]]:
        """
        Analyze patterns by day of week.
        
        Returns {day_of_week: {mode_counts, accept_rate, avg_completion}}.
        """
        history = await DecisionDAO.get_mode_history(user_id, days=60)
        
        # Group by day
        day_stats = {i: {"recovery": 0, "standard": 0, "sprint": 0, "accepts": 0, "total": 0} 
                     for i in range(7)}
        
        for h in history:
            day = h["day_of_week"]
            mode = h["mode"]
            if mode in day_stats[day]:
                day_stats[day][mode] += 1
            day_stats[day]["total"] += 1
            if h["user_action_type"] == "accept":
                day_stats[day]["accepts"] += 1
        
        # Calculate rates
        results = {}
        for day, stats in day_stats.items():
            total = stats["total"]
            if total > 0:
                results[day] = {
                    "predominant_mode": max(["recovery", "standard", "sprint"], 
                                           key=lambda m: stats[m]),
                    "accept_rate": stats["accepts"] / total,
                    "recovery_rate": stats["recovery"] / total,
                    "total_decisions": total,
                }
            else:
                results[day] = {
                    "predominant_mode": "standard",
                    "accept_rate": 0.5,
                    "recovery_rate": 0.0,
                    "total_decisions": 0,
                }
        
        return results
    
    @staticmethod
    async def get_pattern_by_hour(user_id: str = "default") -> Dict[str, Dict[str, Any]]:
        """
        Analyze patterns by time of day.
        
        Returns {period: {mode_counts, accept_rate}}.
        """
        history = await DecisionDAO.get_mode_history(user_id, days=60)
        
        # Group by period
        periods = {
            "morning": (6, 12),    # 6am - 12pm
            "afternoon": (12, 18), # 12pm - 6pm
            "evening": (18, 24),   # 6pm - 12am
        }
        
        period_stats = {p: {"recovery": 0, "standard": 0, "sprint": 0, "accepts": 0, "total": 0}
                       for p in periods}
        
        for h in history:
            hour = h["hour"]
            for period, (start, end) in periods.items():
                if start <= hour < end:
                    mode = h["mode"]
                    if mode in period_stats[period]:
                        period_stats[period][mode] += 1
                    period_stats[period]["total"] += 1
                    if h["user_action_type"] == "accept":
                        period_stats[period]["accepts"] += 1
                    break
        
        # Calculate rates
        results = {}
        for period, stats in period_stats.items():
            total = stats["total"]
            if total > 0:
                results[period] = {
                    "predominant_mode": max(["recovery", "standard", "sprint"],
                                           key=lambda m: stats[m]),
                    "accept_rate": stats["accepts"] / total,
                    "total_decisions": total,
                }
            else:
                results[period] = {
                    "predominant_mode": "standard",
                    "accept_rate": 0.5,
                    "total_decisions": 0,
                }
        
        return results
    
    @staticmethod
    async def get_success_signal(user_id: str = "default") -> float:
        """
        Get overall history success signal for decision engine.
        
        Returns -1 to 1 based on recent accept rate and mode stability.
        """
        history = await DecisionDAO.get_mode_history(user_id, days=14)
        
        if len(history) < 3:
            return 0.0  # Not enough data
        
        # Calculate accept rate
        accepts = sum(1 for h in history if h["user_action_type"] == "accept")
        accept_rate = accepts / len(history)
        
        # Convert to -1 to 1 scale
        # 50% accept = 0, 100% = +0.5, 0% = -0.5
        return (accept_rate - 0.5) * 1.0
