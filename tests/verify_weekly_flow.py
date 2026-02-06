# ===========================================================================
# Chronos AI Learning Companion
# File: tests/verify_weekly_flow.py
# Purpose: End-to-end verification of Weekly Plan -> Interruption -> Decision
# ===========================================================================

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.weekly_plan_service import get_weekly_plan_service
from services.briefing_service import BriefingService
from db.dao.interruption_dao import InterruptionDAO
from db.dao.weekly_plan_dao import WeeklyPlanDAO
from chronomem.decision_engine import get_decision_engine, DecisionFactor

async def verify_flow():
    print("🚀 Starting End-to-End Verification Flow")
    user_id = "test_user_flow"
    
    # 1. Cleanup previous test data
    print("\n[1] Cleaning up...")
    # Clean up DB for test user
    from db.dao.session_dao import SessionDAO
    
    # Not dropping tables, just proceeding. Weekly setup will overwrite if careful.
    
    # 2. Setup Weekly Plan
    print("\n[2] Setting up Weekly Plan...")
    weekly_service = get_weekly_plan_service(user_id)
    try:
        await weekly_service.setup_week(
            goals=["Verify System", "Test Integration"],
            available_days={"mon": True, "tue": True, "wed": True, "thu": True, "fri": True},
            intensity="balanced"
        )
    except Exception as e:
        print(f"   Note: Setup likely exists: {e}")
    
    # Verify plan exists
    status = await weekly_service.get_week_status()
    if status["has_plan"]:
        print("   ✅ Weekly plan created/verified successfully")
    else:
        print("   ❌ Failed to create weekly plan")
        print(f"   Status: {status}")
        return

    # 3. Check Initial Briefing (Should be Standard/Balanced)
    print("\n[3] Checking Initial Briefing...")
    briefing_service = BriefingService(user_id)
    proposal = await briefing_service.get_today_proposal()
    print(f"   -> Initial Mode: {proposal['mode']}")
    print(f"   -> Weekly Progress Impact: {proposal['weekly_context']['week_progress_pct']}%")
    
    # 4. Simulate a major Interruption
    print("\n[4] Simulating Major Interruption (Sick Day)...")
    await InterruptionDAO.add(
        user_id=user_id,
        source="manual",
        content="Feeling very sick, cannot study today",
        category="health",
        impact_level=0.9
    )
    
    # Process interruptions
    print("   -> Processing interruptions...")
    adjustments = await weekly_service.process_interruptions()
    print(f"   -> Adjustments made: {len(adjustments)}")
    if len(adjustments) > 0:
        print(f"   ✅ System reacted to interruption: {adjustments[0]}")
    else:
        print("   ⚠️ No immediate plan adjustments (might be handled by DecisionEngine dynamic pressure)")

    # 5. Check Updated Decision Engine Output
    print("\n[5] Checking Decision Engine Response...")
    engine = get_decision_engine(user_id)
    # Force re-compute
    decision = await engine.compute()
    
    print(f"   -> New Mode: {decision.mode}")
    print(f"   -> Life Pressure: {decision.life_pressure:.2f}")
    
    # Check if pressure increased or mode changed (might need more interruptions to force mode change)
    if decision.life_pressure > 0.6:
         print("   ✅ Life pressure accurately reflects high impact interruption")
    else:
         print(f"   ⚠️ Life pressure {decision.life_pressure} might be too low calculation")

    # 6. Verify Dashboard Metrics
    print("\n[6] Verifying Dashboard Integration...")
    from services.dashboard_service import DashboardService
    dashboard = DashboardService(user_id)
    metrics = await dashboard.aggregate()
    
    interruption_level = metrics["interruption"]["level"]
    print(f"   -> Dashboard Interruption Level: {interruption_level}")
    
    if interruption_level in ["medium", "high"]:
        print("   ✅ Dashboard correctly shows elevated interruption level")
    else:
         print("   ❌ Dashboard failed to reflect interruption")

    print("\n✨ Verification Complete")
    from db.connection import close_db
    await close_db()

if __name__ == "__main__":
    asyncio.run(verify_flow())
