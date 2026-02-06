# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/summary/task/extractor.py
# Purpose: Extract task memories (learning strategies) from sessions
# ===========================================================================

"""
Task Memory Extractor

Extracts reusable learning strategies from completed sessions.
Adapted from ReMe's task memory with learning-focused prompts.
"""

import json
from typing import List, Dict, Any, Optional

from chronomem.schema.memory import TaskMemory
from chronomem.core.embedder import get_embedder


STRATEGY_EXTRACTION_PROMPT = """Analyze this learning session and extract reusable strategies.

Session data:
- Topics: {topics}
- Duration: {duration} minutes
- Summary: {summary}
- Stuck points: {stuck_points}

Questions to answer:
1. What learning approaches worked well in this session?
2. What should be avoided for similar topics?
3. What's a recommended strategy for this topic area?

Output JSON array with strategies:
[
  {{
    "strategy": "Description of the effective strategy",
    "topic": "Topic/subject area this applies to",
    "effectiveness": 0.0-1.0 score
  }}
]

Return ONLY valid JSON array. If no clear strategies, return []."""


class TaskExtractor:
    """
    Extract task memories (learning strategies) from sessions.
    """
    
    def __init__(self):
        """Initialize extractor."""
        self.embedder = get_embedder()
    
    async def extract_from_session(
        self,
        session_data: Dict[str, Any],
        score: float = 0.5,
        session_id: Optional[str] = None,
    ) -> List[TaskMemory]:
        """
        Extract learning strategies from a completed session.
        
        Args:
            session_data: Session receipt data (topics, summary, etc.).
            score: Overall session success score (0-1).
            session_id: Session identifier.
        
        Returns:
            List of TaskMemory objects.
        """
        from services.gemini_service import create_gemini_service
        import re
        
        service = create_gemini_service()
        if not service:
            return []
        
        # Format session data
        topics = session_data.get("topics", [])
        if isinstance(topics, str):
            topics = [topics]
        
        prompt = STRATEGY_EXTRACTION_PROMPT.format(
            topics=", ".join(topics) if topics else "General",
            duration=session_data.get("duration_min", 0),
            summary=session_data.get("summary", "No summary"),
            stuck_points=", ".join(session_data.get("stuck_points", [])) or "None",
        )
        
        try:
            response = await service.send_message(prompt)
            
            # Parse JSON
            match = re.search(r'\[[\s\S]*\]', response)
            if not match:
                return []
            
            strategies = json.loads(match.group())
            
            memories = []
            for s in strategies:
                if not s.get("strategy"):
                    continue
                
                memory = TaskMemory.from_session(
                    strategy=s.get("strategy", ""),
                    topic=s.get("topic", ""),
                    score=min(1.0, max(0.0, s.get("effectiveness", score))),
                    session_id=session_id,
                )
                
                # Generate embedding
                embed_text = f"{memory.topic} {memory.strategy}"
                memory.embedding = await self.embedder.embed(embed_text)
                
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            print(f"Strategy extraction failed: {e}")
            return []
    
    async def extract_from_receipt(
        self,
        receipt: Dict[str, Any],
    ) -> List[TaskMemory]:
        """
        Extract strategies from an execution receipt.
        
        Args:
            receipt: Receipt data from ReceiptDAO.
        
        Returns:
            List of TaskMemory objects.
        """
        # Convert receipt to session data format
        session_data = {
            "topics": receipt.get("topics_json", []),
            "duration_min": receipt.get("duration_min", 0),
            "summary": receipt.get("summary", ""),
            "stuck_points": receipt.get("stuck_points_json", []),
        }
        
        # Estimate score from metrics
        metrics = receipt.get("metrics_json", {})
        score = metrics.get("accuracy", 0.5) if isinstance(metrics, dict) else 0.5
        
        return await self.extract_from_session(
            session_data,
            score=score,
            session_id=receipt.get("session_id"),
        )
