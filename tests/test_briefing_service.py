# ===========================================================================
# Chronos AI Learning Companion
# File: tests/test_briefing_service.py
# Purpose: Smoke tests for BriefingService
# ===========================================================================

"""
Briefing Service Smoke Tests

Minimal tests to ensure BriefingService.generate() works with empty/sparse data.
"""

import pytest
import asyncio
from services.briefing_service import BriefingService


@pytest.mark.asyncio
async def test_briefing_generate_returns_dict():
    """Test that generate() returns a dict."""
    service = BriefingService()
    result = await service.generate()
    
    assert isinstance(result, dict), "generate() should return a dict"


@pytest.mark.asyncio
async def test_briefing_generate_has_required_fields():
    """Test that generate() returns all required fields."""
    service = BriefingService()
    result = await service.generate()
    
    required_fields = ["snapshot", "proposal", "date"]
    
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"


@pytest.mark.asyncio
async def test_briefing_snapshot_structure():
    """Test snapshot field structure."""
    service = BriefingService()
    result = await service.generate()
    
    snapshot = result.get("snapshot", {})
    assert "completion" in snapshot
    assert "sessions" in snapshot
    assert "interruptions" in snapshot
    assert "best_window" in snapshot
    assert "stuck_point" in snapshot


@pytest.mark.asyncio
async def test_briefing_proposal_structure():
    """Test proposal field structure."""
    service = BriefingService()
    result = await service.generate()
    
    proposal = result.get("proposal", {})
    assert "mode" in proposal
    assert "type_ratio" in proposal
    assert "block_sizes" in proposal
    assert "benefit" in proposal
    assert "changes" in proposal
    
    # Validate mode
    assert proposal["mode"] in ["recovery", "standard", "sprint"]


@pytest.mark.asyncio
async def test_briefing_mode_determination():
    """Test mode determination logic."""
    service = BriefingService()
    
    # Test with empty snapshot (should default to standard)
    snapshot = {"completion_value": 70, "interruptions": 2}
    mode = service._determine_mode(snapshot)
    assert mode in ["recovery", "standard", "sprint"]


@pytest.mark.asyncio
async def test_briefing_type_ratio_valid():
    """Test type ratio returns valid percentages."""
    service = BriefingService()
    
    for mode in ["recovery", "standard", "sprint"]:
        ratio = service._get_type_ratio(mode)
        assert isinstance(ratio, dict)
        assert "learn" in ratio
        assert "review" in ratio
        assert "practice" in ratio
        # Total should be 100
        assert sum(ratio.values()) == 100


@pytest.mark.asyncio
async def test_briefing_works_with_empty_data():
    """Test that service works even with no database data."""
    service = BriefingService()
    
    try:
        result = await service.generate()
        assert result is not None
        print("✓ Service handles empty data gracefully")
    except Exception as e:
        pytest.fail(f"Service should handle empty data: {e}")


if __name__ == "__main__":
    # Run tests manually
    async def run_tests():
        print("Running Briefing Service smoke tests...")
        
        try:
            await test_briefing_generate_returns_dict()
            print("✓ generate() returns dict")
            
            await test_briefing_generate_has_required_fields()
            print("✓ All required fields present")
            
            await test_briefing_snapshot_structure()
            print("✓ snapshot structure valid")
            
            await test_briefing_proposal_structure()
            print("✓ proposal structure valid")
            
            await test_briefing_mode_determination()
            print("✓ mode determination works")
            
            await test_briefing_type_ratio_valid()
            print("✓ type ratios valid")
            
            await test_briefing_works_with_empty_data()
            print("✓ handles empty data")
            
            print("\n✅ All tests passed!")
            
        except AssertionError as e:
            print(f"\n❌ Test failed: {e}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    asyncio.run(run_tests())
