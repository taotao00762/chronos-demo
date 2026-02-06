# ===========================================================================
# Chronos AI Learning Companion
# File: scripts/seed_memories.py
# Purpose: Populate database with initial/restored memories
# ===========================================================================

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chronomem.memory_store import get_memory_store, MemorySource
from db.connection import close_db

async def seed_data():
    print("🌱 Seeding Memory Bank...")
    store = get_memory_store()
    
    # 1. Profile Memories (User Preferences)
    print("   -> Adding Profile Memories...")
    await store.add_profile(
        content="User prefers Python for backend and Flet for UI development.",
        source=MemorySource.SETTINGS
    )
    await store.add_profile(
        content="Learning style: visual learner, prefers diagrams and code examples over long text.",
        source=MemorySource.SETTINGS
    )
    
    # 2. Skill Memories (Knowledge State)
    print("   -> Adding Skill Memories...")
    await store.add_skill(
        content="Proficient in Python basics and async implementation.",
        confidence=0.9
    )
    await store.add_skill(
        content="Concept: Dependency Injection - Needs more practice to fully grasp.",
        confidence=0.4
    )
    
    # 3. Episodic Memories (Recent Events)
    print("   -> Adding Episodic Memories...")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    await store.add_episodic(
        content=f"Completed verification of Weekly Plan module on {yesterday}. Logic flow confirmed.",
        source=MemorySource.SESSION,
        ttl_days=14
    )
    
    # 4. Weekly Plan (Ensure clean slate or basic plan)
    from db.dao.weekly_plan_dao import WeeklyPlanDAO
    status = await WeeklyPlanDAO.get_current_week()
    if not status:
        print("   -> Creating default Weekly Plan...")
        await WeeklyPlanDAO.create(
            goals=["Master Chronos Architecture", "Verify Memory System"],
            available_days={"mon": True, "tue": True, "wed": True, "thu": True, "fri": True},
            intensity="balanced"
        )
    else:
        print("   -> Weekly Plan already exists.")

    print("✨ Seeding Complete. Data restored/initialized.")
    await close_db()

if __name__ == "__main__":
    asyncio.run(seed_data())
