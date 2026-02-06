# ===========================================================================
# Chronos AI Learning Companion
# File: tests/test_dashboard_service.py
# Purpose: Smoke tests for DashboardService
# ===========================================================================

"""
Dashboard Service Smoke Tests

Minimal tests to ensure DashboardService.aggregate() works.
"""

import pytest
import asyncio
from services.dashboard_service import DashboardService


@pytest.mark.asyncio
async def test_dashboard_aggregate_returns_dict():
    """Test that aggregate() returns a dict."""
    service = DashboardService()
    result = await service.aggregate()
    
    assert isinstance(result, dict), "aggregate() should return a dict"


@pytest.mark.asyncio
async def test_dashboard_aggregate_has_required_fields():
    """Test that aggregate() returns all required fields."""
    service = DashboardService()
    result = await service.aggregate()
    
    required_fields = [
        "plan_mode",
        "interruption",
        "focus_windows",
        "completion",
        "mastery_trend",
        "plan_changes",
        "recent_chats",
    ]
    
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"


@pytest.mark.asyncio
async def test_dashboard_plan_mode_structure():
    """Test plan_mode field structure."""
    service = DashboardService()
    result = await service.aggregate()
    
    plan_mode = result.get("plan_mode", {})
    assert "mode" in plan_mode
    assert "label" in plan_mode
    assert plan_mode["mode"] in ["recovery", "standard", "sprint"]


@pytest.mark.asyncio
async def test_dashboard_completion_structure():
    """Test completion field structure."""
    service = DashboardService()
    result = await service.aggregate()
    
    completion = result.get("completion", {})
    assert "yesterday" in completion
    assert "week" in completion
    assert isinstance(completion["yesterday"], int)
    assert isinstance(completion["week"], int)


@pytest.mark.asyncio
async def test_dashboard_focus_windows_is_list():
    """Test focus_windows returns a list."""
    service = DashboardService()
    result = await service.aggregate()
    
    focus_windows = result.get("focus_windows", [])
    assert isinstance(focus_windows, list)
    assert len(focus_windows) > 0


@pytest.mark.asyncio
async def test_dashboard_recent_chats_is_list():
    """Test recent_chats returns a list."""
    service = DashboardService()
    result = await service.aggregate()
    
    recent_chats = result.get("recent_chats", [])
    assert isinstance(recent_chats, list)


if __name__ == "__main__":
    # Run tests manually
    async def run_tests():
        print("Running Dashboard Service smoke tests...")
        
        try:
            await test_dashboard_aggregate_returns_dict()
            print("✓ aggregate() returns dict")
            
            await test_dashboard_aggregate_has_required_fields()
            print("✓ All required fields present")
            
            await test_dashboard_plan_mode_structure()
            print("✓ plan_mode structure valid")
            
            await test_dashboard_completion_structure()
            print("✓ completion structure valid")
            
            await test_dashboard_focus_windows_is_list()
            print("✓ focus_windows is list")
            
            await test_dashboard_recent_chats_is_list()
            print("✓ recent_chats is list")
            
            print("\n✅ All tests passed!")
            
        except AssertionError as e:
            print(f"\n❌ Test failed: {e}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    asyncio.run(run_tests())
