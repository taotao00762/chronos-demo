# ===========================================================================
# Chronos AI Learning Companion
# File: scripts/backfill_interruption_evidence.py
# Purpose: Backfill evidence for existing interruptions
# ===========================================================================

"""
Backfill Interruption Evidence

Creates Evidence records for interruptions that do not yet have an
associated evidence_id stored in metadata_json.
"""

import asyncio
import json
import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.connection import get_db, close_db
from db.dao.evidence_dao import EvidenceDAO


async def backfill(user_id: str = "default") -> int:
    db = await get_db()
    updated = 0

    async with db.execute(
        """
        SELECT interruption_id, content, category, impact_level, metadata_json
        FROM interruption
        WHERE user_id = ?
        ORDER BY detected_at DESC
        """,
        (user_id,),
    ) as cursor:
        rows = await cursor.fetchall()

    for row in rows:
        interruption_id = row[0]
        content = row[1] or ""
        category = row[2] or "other"
        impact_level = float(row[3] or 0.0)
        metadata_json = row[4] or "{}"

        try:
            metadata = json.loads(metadata_json) if metadata_json else {}
        except json.JSONDecodeError:
            metadata = {}

        if isinstance(metadata, dict) and metadata.get("evidence_id"):
            continue

        summary = f"Interruption: {category} ({impact_level:.2f}) - {content[:80]}"
        evidence_id = await EvidenceDAO.create(
            type="interruption",
            summary=summary,
            ref_type="interruption",
            ref_id=interruption_id,
            ttl_days=14,
            user_id=user_id,
        )

        metadata = metadata if isinstance(metadata, dict) else {}
        metadata["evidence_id"] = evidence_id

        await db.execute(
            """
            UPDATE interruption
            SET metadata_json = ?
            WHERE interruption_id = ?
            """,
            (json.dumps(metadata), interruption_id),
        )
        updated += 1

    await db.commit()
    return updated


async def main() -> None:
    updated = await backfill("default")
    print(f"Backfilled evidence for {updated} interruptions")
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
