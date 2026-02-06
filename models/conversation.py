# ===========================================================================
# Chronos AI Learning Companion
# File: models/conversation.py
# Purpose: Chat conversation and message models
# ===========================================================================

"""
Conversation Models

Data structures for chat history management.
Supports serialization to/from JSON and Gemini API format.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any
import uuid


class MessageRole(Enum):
    """Message sender role."""
    USER = "user"
    MODEL = "model"


@dataclass
class Message:
    """
    Single chat message.
    
    Attributes:
        role: Who sent the message (user or model).
        content: Message text content.
        timestamp: When the message was sent.
    """
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dict."""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
    
    def to_gemini_format(self) -> Dict[str, Any]:
        """
        Convert to Gemini API Content format.
        
        Returns:
            {"role": "user", "parts": [{"text": "..."}]}
        """
        return {
            "role": self.role.value,
            "parts": [{"text": self.content}],
        }


@dataclass
class Conversation:
    """
    Chat conversation with message history.
    
    Attributes:
        id: Unique conversation identifier.
        title: Conversation title (auto-generated from first message).
        messages: List of messages in chronological order.
        created_at: When conversation was started.
        updated_at: When conversation was last modified.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: MessageRole, content: str) -> Message:
        """
        Add a new message to the conversation.
        
        Args:
            role: Message sender role.
            content: Message text.
        
        Returns:
            The created Message object.
        """
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        self.updated_at = datetime.now()
        
        # Auto-generate title from first user message
        if len(self.messages) == 1 and role == MessageRole.USER:
            self.title = content[:50] + ("..." if len(content) > 50 else "")
        
        return msg
    
    def get_gemini_history(self) -> List[Dict[str, Any]]:
        """
        Get conversation history in Gemini API format.
        
        Returns:
            List of Content dicts for Gemini chat.
        """
        return [msg.to_gemini_format() for msg in self.messages]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create from dict."""
        return cls(
            id=data["id"],
            title=data["title"],
            messages=[Message.from_dict(m) for m in data["messages"]],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
