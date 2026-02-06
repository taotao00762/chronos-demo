# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/schema/memory.py
# Purpose: Memory data models (adapted from ReMe)
# ===========================================================================

"""
Memory Schema

Defines structured memory types for:
- Personal Memory: User preferences, habits
- Task Memory: Learning strategies
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid


class BaseMemory(BaseModel):
    """Base memory model with common fields."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(default="base")
    content: str = Field(..., description="Memory content")
    when_to_use: str = Field(default="", description="Keywords for retrieval")
    embedding: Optional[List[float]] = Field(default=None, exclude=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    user_id: str = Field(default="default")
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PersonalMemory(BaseMemory):
    """
    Personal memory for user-specific information.
    
    Examples:
    - "User prefers studying in the morning"
    - "User learns best with visual examples"
    - "User struggles with abstract concepts"
    """
    
    type: str = Field(default="personal")
    target: str = Field(default="user", description="Who this memory is about")
    author: str = Field(default="system", description="Who extracted this memory")
    observation_type: str = Field(
        default="personal_info",
        description="Type: personal_info, personal_info_with_time"
    )
    time_info: Optional[str] = Field(
        default=None,
        description="Time-related info (e.g., 'every morning', 'on weekends')"
    )
    
    @classmethod
    def from_observation(
        cls,
        content: str,
        keywords: str,
        user_id: str = "default",
        time_info: Optional[str] = None,
        source_message: Optional[str] = None,
    ) -> "PersonalMemory":
        """Create from extracted observation."""
        metadata = {"source_message": source_message} if source_message else {}
        return cls(
            content=content,
            when_to_use=keywords,
            user_id=user_id,
            time_info=time_info,
            observation_type="personal_info_with_time" if time_info else "personal_info",
            metadata=metadata,
        )


class TaskMemory(BaseMemory):
    """
    Task memory for reusable learning strategies.
    
    Examples:
    - "For recursion topics, start with simple examples"
    - "Practice problems are more effective than reading for math"
    """
    
    type: str = Field(default="task")
    strategy: str = Field(default="", description="The learning strategy")
    topic: str = Field(default="", description="Related topic/subject")
    effectiveness_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How effective this strategy was"
    )
    source_session_id: Optional[str] = Field(
        default=None,
        description="Session this was extracted from"
    )
    
    @classmethod
    def from_session(
        cls,
        strategy: str,
        topic: str,
        score: float,
        session_id: Optional[str] = None,
    ) -> "TaskMemory":
        """Create from session analysis."""
        return cls(
            content=strategy,
            strategy=strategy,
            topic=topic,
            when_to_use=topic,
            effectiveness_score=score,
            source_session_id=session_id,
        )
