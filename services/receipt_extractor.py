# ===========================================================================
# Chronos AI Learning Companion
# File: services/receipt_extractor.py
# Purpose: Extract execution receipts from Tutor conversations using Gemini
# ===========================================================================

"""
Receipt Extractor

Uses Gemini 3 to extract structured ExecutionReceipt from conversation.
Falls back to simple recording if extraction fails.
"""

import json
import re
from typing import List, Dict, Any, Optional

from services.gemini_service import GeminiService, create_gemini_service
from schemas.receipt_schema import ExecutionReceipt, RECEIPT_EXTRACTION_PROMPT


def _extract_json_from_text(text: str) -> Optional[dict]:
    """
    Try to extract JSON from text that may contain markdown or other content.
    """
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in code blocks
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
        r'\{[\s\S]*\}',  # Any JSON object
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                if isinstance(match, str):
                    return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
    
    return None


async def extract_receipt(
    conversation: List[Dict[str, Any]],
    gemini_service: Optional[GeminiService] = None,
) -> ExecutionReceipt:
    """
    Extract ExecutionReceipt from a Tutor conversation.
    
    Args:
        conversation: List of messages (role, content).
        gemini_service: Optional pre-initialized Gemini service.
    
    Returns:
        Structured ExecutionReceipt.
    """
    # Format conversation for prompt
    formatted = "\n".join(
        f"{msg.get('role', 'user')}: {msg.get('content', '')[:500]}"
        for msg in conversation[-10:]  # Limit to last 10 messages
    )
    
    # Build prompt
    prompt = RECEIPT_EXTRACTION_PROMPT.format(conversation=formatted)
    
    # Get or create Gemini service
    service = gemini_service or create_gemini_service()
    if service is None:
        return ExecutionReceipt(summary="No API key available")
    
    # Call Gemini
    try:
        response = await service.send_message(prompt)
        
        # Extract JSON from response
        data = _extract_json_from_text(response)
        
        if data:
            return ExecutionReceipt(**data)
        else:
            # Create summary from conversation if JSON parse fails
            topics = []
            for msg in conversation:
                if msg.get("role") == "assistant":
                    content = msg.get("content", "")[:200]
                    topics.append(content[:50])
            
            return ExecutionReceipt(
                topics_covered=topics[:3],
                duration_minutes=len(conversation) * 2,
                summary=f"Session with {len(conversation)} exchanges"
            )
    
    except Exception as e:
        print(f"Warning: Receipt extraction error: {e}")
        return ExecutionReceipt(
            duration_minutes=len(conversation) * 2,
            summary=f"Session recorded ({len(conversation)} messages)"
        )


async def extract_and_save_receipt(
    session_id: str,
    conversation: List[Dict[str, Any]],
    user_id: str = "default",
) -> str:
    """
    Extract receipt and save to database with evidence.
    
    Args:
        session_id: Session ID.
        conversation: Conversation messages.
        user_id: User ID.
    
    Returns:
        Receipt ID.
    """
    from db.dao import ReceiptDAO, EvidenceDAO
    
    # Extract receipt (with fallback)
    receipt = await extract_receipt(conversation)
    
    # Save to database
    receipt_id = await ReceiptDAO.create(
        session_id=session_id,
        user_id=user_id,
        topics=receipt.topics_covered,
        duration_min=receipt.duration_minutes,
        metrics=receipt.metrics.model_dump(),
        stuck_points=receipt.stuck_points,
        learner_state=receipt.learner_state.model_dump(),
        summary=receipt.summary,
    )
    
    # Create evidence record
    if receipt.topics_covered:
        evidence_summary = f"Session: {', '.join(receipt.topics_covered[:3])}. {receipt.summary[:80]}"
    else:
        evidence_summary = receipt.summary or f"Tutor session {session_id[:8]}"
    
    await EvidenceDAO.create(
        type="receipt",
        summary=evidence_summary,
        ref_type="execution_receipt",
        ref_id=receipt_id,
        user_id=user_id,
    )
    
    print(f"Receipt saved: {receipt_id}")
    return receipt_id
