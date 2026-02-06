# ===========================================================================
# Chronos AI Learning Companion
# File: schemas/receipt_schema.py
# Purpose: Execution receipt Pydantic model for Gemini extraction
# ===========================================================================

"""
Execution Receipt Schema

Structured output from Tutor session, extracted by Gemini 3.
Used to record learning outcomes and identify improvement areas.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Metrics(BaseModel):
    """Quantitative session metrics."""
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0, description="Correct answer ratio")
    questions_attempted: int = Field(default=0, ge=0, description="Total questions tried")
    time_per_question_sec: float = Field(default=0.0, ge=0.0, description="Average seconds per question")


class LearnerState(BaseModel):
    """Learner's subjective state during session."""
    energy_level: str = Field(default="medium", description="high/medium/low")
    interruptions: int = Field(default=0, ge=0, description="Number of interruptions")
    difficulty_rating: int = Field(default=3, ge=1, le=5, description="Self-rated difficulty 1-5")
    notes: Optional[str] = Field(default=None, description="Additional observations")


class ExecutionReceipt(BaseModel):
    """
    Complete record of a Tutor session outcome.
    
    This is extracted by Gemini 3 from the conversation history
    and stored in SQLite as the authoritative execution record.
    """
    topics_covered: List[str] = Field(
        default_factory=list,
        description="Topics discussed during session"
    )
    duration_minutes: int = Field(
        default=0, ge=0,
        description="Session duration in minutes"
    )
    metrics: Metrics = Field(
        default_factory=Metrics,
        description="Quantitative performance metrics"
    )
    stuck_points: List[str] = Field(
        default_factory=list,
        description="Concepts or problems where learner struggled"
    )
    learner_state: LearnerState = Field(
        default_factory=LearnerState,
        description="Learner's state during session"
    )
    summary: str = Field(
        default="",
        description="Brief narrative summary of the session"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "topics_covered": ["recursion", "base case", "call stack"],
                "duration_minutes": 25,
                "metrics": {
                    "accuracy": 0.75,
                    "questions_attempted": 8,
                    "time_per_question_sec": 45.0
                },
                "stuck_points": ["understanding call stack visualization"],
                "learner_state": {
                    "energy_level": "medium",
                    "interruptions": 1,
                    "difficulty_rating": 4
                },
                "summary": "Covered recursion basics. Made good progress on base case but struggled with visualizing the call stack."
            }
        }


# =============================================================================
# Gemini Extraction Prompt
# =============================================================================

RECEIPT_EXTRACTION_PROMPT = """Analyze this tutoring conversation and extract a structured execution receipt.

Return a JSON object with these fields:
- topics_covered: list of topics discussed
- duration_minutes: estimated session length
- metrics: { accuracy (0-1), questions_attempted, time_per_question_sec }
- stuck_points: list of concepts where learner struggled
- learner_state: { energy_level (high/medium/low), interruptions, difficulty_rating (1-5) }
- summary: brief 1-2 sentence summary

Conversation:
{conversation}

Return ONLY valid JSON, no markdown or explanations."""
