# ===========================================================================
# Chronos AI Learning Companion
# File: services/gemini_service.py
# Purpose: Async Gemini API service using google-genai SDK
# ===========================================================================

"""
Gemini Service

Provides async chat functionality using Google's Gemini API.
Supports streaming responses for real-time typing effect.

Usage:
    service = GeminiService(api_key="...")
    
    # Streaming
    async for chunk in service.send_message_stream("Hello"):
        print(chunk, end="")
    
    # Non-streaming
    response = await service.send_message("Hello")
"""

import os
from typing import AsyncGenerator, Optional, List, Dict, Any

from google import genai
from google.genai import types


# =============================================================================
# Default Configuration
# =============================================================================

DEFAULT_MODEL = "gemini-3-flash-preview"

DEFAULT_SYSTEM_INSTRUCTION = """You are Chronos, an AI learning companion.
Your role is to help users learn effectively by:
- Explaining concepts clearly and concisely
- Using the Socratic method when appropriate
- Providing examples and analogies
- Breaking down complex topics into manageable parts
- Encouraging active recall and practice

Be friendly, patient, and supportive. Adapt your teaching style to the user's needs."""


# =============================================================================
# Gemini Service Class
# =============================================================================

def _get_model_from_settings() -> Optional[str]:
    try:
        from stores.settings_store import SettingsStore
        settings = SettingsStore.get_instance().get()
        model = getattr(settings, "gemini_model", "")
        return model.strip() if isinstance(model, str) else None
    except Exception:
        return None


class GeminiService:
    """
    Async Gemini API service with chat and streaming support.
    
    This service maintains a chat session for multi-turn conversations.
    """
    
    def __init__(
        self,
        api_key: str,
        model_name: Optional[str] = None,
        system_instruction: Optional[str] = DEFAULT_SYSTEM_INSTRUCTION,
    ) -> None:
        """
        Initialize the Gemini service.
        
        Args:
            api_key: Google AI API key.
            model_name: Model to use (e.g., "gemini-2.5-flash").
            system_instruction: System prompt for the AI.
        """
        self.client = genai.Client(api_key=api_key)
        resolved_model = model_name or _get_model_from_settings() or DEFAULT_MODEL
        self.model_name = resolved_model
        self.system_instruction = system_instruction
        self._history: List[Dict[str, Any]] = []
    
    def set_history(self, history: List[Dict[str, Any]]) -> None:
        """
        Set conversation history for context.
        
        Args:
            history: List of messages in Gemini format.
        """
        self._history = history.copy()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get current conversation history."""
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self._history = []
    
    def set_system_instruction(self, instruction: str) -> None:
        """
        Update the system instruction and clear history.
        
        Args:
            instruction: New system instruction.
        """
        self.system_instruction = instruction
        self._history = []  # Clear history when context changes
    
    async def send_message_stream(
        self,
        message: str,
    ) -> AsyncGenerator[str, None]:
        """
        Send message and yield response chunks asynchronously.
        
        Args:
            message: User message text.
        
        Yields:
            Response text chunks as they arrive.
        """
        # Build contents with history
        contents = self._history.copy()
        contents.append({
            "role": "user",
            "parts": [{"text": message}],
        })
        
        # Build config
        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
        )
        
        # Stream response - need to await the coroutine first
        full_response = ""
        response_stream = await self.client.aio.models.generate_content_stream(
            model=self.model_name,
            contents=contents,
            config=config,
        )
        async for chunk in response_stream:
            if chunk.text:
                full_response += chunk.text
                yield chunk.text
        
        # Update history with this exchange
        self._history.append({
            "role": "user",
            "parts": [{"text": message}],
        })
        self._history.append({
            "role": "model",
            "parts": [{"text": full_response}],
        })
    
    async def send_message(self, message: str) -> str:
        """
        Send message and get full response (non-streaming).
        
        Args:
            message: User message text.
        
        Returns:
            Complete response text.
        """
        # Build contents with history
        contents = self._history.copy()
        contents.append({
            "role": "user",
            "parts": [{"text": message}],
        })
        
        # Build config
        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
        )
        
        # Generate response
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )
        
        response_text = response.text or ""
        
        # Update history
        self._history.append({
            "role": "user",
            "parts": [{"text": message}],
        })
        self._history.append({
            "role": "model",
            "parts": [{"text": response_text}],
        })
        
        return response_text

    async def close(self) -> None:
        """Close the underlying async client session if available."""
        aio = getattr(self.client, "aio", None)
        if aio:
            close = getattr(aio, "close", None)
            if callable(close):
                await close()


# =============================================================================
# Factory Functions
# =============================================================================

def get_api_key() -> Optional[str]:
    """
    Get Gemini API key.
    
    Priority:
        1. GEMINI_API_KEY environment variable
        2. settings.gemini_api_key
    
    Returns:
        API key string.
    """
    # Try environment variable first
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    
    # Try settings
    try:
        from stores.settings_store import SettingsStore
        store = SettingsStore.get_instance()
        key = getattr(store.get(), "gemini_api_key", "")
        if key:
            return key
    except Exception:
        pass
    
    # No key available
    return None


def create_gemini_service(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Optional[GeminiService]:
    """
    Factory function to create GeminiService.
    
    Args:
        api_key: Optional API key (uses get_api_key() if not provided).
        model_name: Model to use.
    
    Returns:
        GeminiService instance or None if API key not available.
    """
    key = api_key or get_api_key()
    if not key:
        return None
    
    return GeminiService(api_key=key, model_name=model_name)
