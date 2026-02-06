# ===========================================================================
# Chronos AI Learning Companion
# File: services/plan_generator.py
# Purpose: Generate learning plans using Gemini with evidence
# ===========================================================================

"""
Plan Generator

Uses Gemini 3 to generate PlanProposal with traceable evidence.
Combines SQLite data with ReMe memories for comprehensive context.
"""

import json
from datetime import date
from typing import List, Dict, Any, Optional

from services.gemini_service import GeminiService, create_gemini_service
from schemas.plan_schema import PlanProposal, PLAN_GENERATION_PROMPT


async def generate_plan_proposal(
    target_date: Optional[str] = None,
    user_id: str = "default",
    gemini_service: Optional[GeminiService] = None,
) -> PlanProposal:
    """
    Generate a learning plan proposal with evidence.
    
    Args:
        target_date: Date for the plan (default: today).
        user_id: User ID.
        gemini_service: Optional pre-initialized Gemini service.
    
    Returns:
        PlanProposal with evidence-backed rationale.
    """
    from db.dao import ProfileDAO, ReceiptDAO, MasteryDAO
    
    # Default to today
    if target_date is None:
        target_date = date.today().isoformat()
    
    # Gather context from SQLite
    user_profile = await ProfileDAO.get(user_id) or {}
    recent_receipts = await ReceiptDAO.list_recent(user_id, limit=5)
    mastery_data = await MasteryDAO.list_all(user_id)
    
    # Try to get ReMe memories (optional)
    personal_memory = []
    task_memory = []
    try:
        from memory.reme_client import ReMeClient
        async with ReMeClient() as reme:
            personal_memory = await reme.retrieve_personal_memory(
                query="learning preferences habits schedule",
                user_id=user_id,
                top_k=5,
            )
            task_memory = await reme.retrieve_task_memory(
                query="effective learning strategies recovery plans",
                top_k=3,
            )
    except Exception as e:
        print(f"Warning: ReMe retrieval failed: {e}")
    
    # Format context for prompt
    receipts_text = json.dumps(recent_receipts, indent=2, default=str)
    mastery_text = json.dumps(mastery_data, indent=2, default=str)
    profile_text = json.dumps(user_profile, indent=2, default=str)
    personal_text = json.dumps(personal_memory, indent=2, default=str)
    task_text = json.dumps(task_memory, indent=2, default=str)
    
    # Build prompt
    prompt = PLAN_GENERATION_PROMPT.format(
        date=target_date,
        user_profile=profile_text,
        receipts=receipts_text,
        mastery=mastery_text,
        personal_memory=personal_text,
        task_memory=task_text,
    )
    
    # Get or create Gemini service
    service = gemini_service or create_gemini_service()
    if service is None:
        return PlanProposal(date=target_date)
    
    # Call Gemini
    try:
        response = await service.send_message(prompt)
        
        # Parse JSON
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            text = "\n".join(json_lines)
        
        data = json.loads(text)
        proposal = PlanProposal(**data)
        
        # Validate evidence
        if not proposal.all_why_have_evidence():
            print("Warning: Some 'why' items lack evidence references")
        
        return proposal
    
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse plan JSON: {e}")
        return PlanProposal(date=target_date)
    
    except Exception as e:
        print(f"Warning: Plan generation error: {e}")
        return PlanProposal(date=target_date)


async def generate_and_save_plan(
    target_date: Optional[str] = None,
    user_id: str = "default",
    user_action: str = "accept",
    user_patch: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate plan, save to database, and link evidence.
    
    Args:
        target_date: Date for the plan.
        user_id: User ID.
        user_action: User action type (accept/customize/reject).
        user_patch: User modifications if customized.
    
    Returns:
        Decision ID.
    """
    from db.dao import PlanDAO, DecisionDAO, EvidenceDAO
    
    if target_date is None:
        target_date = date.today().isoformat()
    
    # Generate proposal
    proposal = await generate_plan_proposal(target_date, user_id)
    
    # Apply patches if customized
    final_plan = [item.model_dump() for item in proposal.plan]
    if user_action == "customize" and user_patch:
        # Apply patches (simplified - full impl would merge)
        pass
    
    # Save plan
    plan_id = await PlanDAO.create(
        date=target_date,
        plan=final_plan,
        user_id=user_id,
    )
    
    # Save decision record
    decision_id = await DecisionDAO.create(
        date=target_date,
        proposal=proposal.model_dump(),
        final_plan=final_plan,
        diff=proposal.diff.model_dump(),
        user_action_type=user_action,
        user_patch=user_patch,
        user_id=user_id,
    )
    
    # Link evidence
    for why_item in proposal.why:
        if why_item.evidence_id:
            await DecisionDAO.link_evidence(decision_id, why_item.evidence_id)
        elif why_item.reme_memory_id:
            # Register ReMe memory as evidence in SQLite
            ev_id = await EvidenceDAO.create(
                type="reme_memory",
                summary=why_item.text,
                ref_type="reme",
                ref_id=why_item.reme_memory_id,
                user_id=user_id,
            )
            await DecisionDAO.link_evidence(decision_id, ev_id)
    
    return decision_id
