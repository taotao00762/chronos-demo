# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/complaint_detector.py
# Purpose: LLM-based complaint and life interruption detection
# ===========================================================================

"""
Complaint Detector (LLM Version)

Uses Gemini API to intelligently detect complaints and life interruptions
from user messages with semantic understanding.

Categories:
- fatigue: tired, exhausted, low energy
- time: busy, no time, schedule conflicts
- difficulty: confused, struggling with content
- mood: stressed, frustrated, anxious
- schedule: meetings, deadlines, events

Falls back to keyword matching if LLM unavailable.
"""

import json
import re
from dataclasses import dataclass
from typing import Optional, Dict, List


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class DetectionResult:
    """Result of complaint detection."""
    detected: bool
    category: str
    impact_level: float
    reason: str
    original_message: str
    
    def to_dict(self) -> Dict:
        return {
            "detected": self.detected,
            "category": self.category,
            "impact_level": self.impact_level,
            "reason": self.reason,
        }


# =============================================================================
# Settings Helpers
# =============================================================================

def _get_sensitivity_threshold() -> float:
    """
    Map sensitivity setting to a minimum impact threshold.

    LOW: 0.7 (fewer detections)
    MEDIUM: 0.5 (default)
    HIGH: 0.3 (more detections)
    """
    level = "medium"
    try:
        from stores.settings_store import SettingsStore
        settings = SettingsStore.get_instance().get()
        level = getattr(settings, "sensitivity", "medium") or "medium"
    except Exception:
        level = "medium"

    level = str(level).lower()
    if level == "low":
        return 0.7
    if level == "high":
        return 0.3
    return 0.5


# =============================================================================
# LLM Detection Prompt
# =============================================================================

DETECTION_PROMPT = """Analyze if this message contains a complaint or life interruption that might affect learning.

Categories:
- fatigue: tiredness, exhaustion, sleepiness, low energy
- time: busy schedule, no time, rushing, many tasks
- difficulty: confused, struggling, don't understand content
- mood: stressed, frustrated, anxious, upset
- schedule: meetings, deadlines, appointments, events challenges

User message: "{message}"

Respond in JSON only:
{{"detected": true/false, "category": "category_name", "impact": 0.0-1.0, "reason": "brief explanation"}}

If no complaint detected, use: {{"detected": false, "category": "", "impact": 0, "reason": ""}}
"""


# =============================================================================
# Detector Class
# =============================================================================

class ComplaintDetector:
    """
    LLM-based complaint detector with keyword fallback.
    
    Usage:
        detector = ComplaintDetector()
        result = await detector.detect_async("I am exhausted and cannot focus")
        if result.detected:
            print(f"Detected {result.category}: {result.reason}")
    """
    
    def __init__(self):
        self._service = None
        self._initialized = False
    
    def _get_service(self):
        """Lazy init Gemini service."""
        if not self._initialized:
            try:
                from services.gemini_service import create_gemini_service
                self._service = create_gemini_service()
            except Exception:
                self._service = None
            self._initialized = True
        return self._service

    def _apply_sensitivity(self, result: "DetectionResult") -> "DetectionResult":
        """Adjust detection based on sensitivity setting."""
        if not result.detected:
            return result

        threshold = _get_sensitivity_threshold()
        if result.impact_level < threshold:
            return DetectionResult(
                detected=False,
                category="",
                impact_level=0.0,
                reason="",
                original_message=result.original_message,
            )
        return result
    
    async def detect_async(self, message: str) -> DetectionResult:
        """
        Detect complaint using LLM.
        
        Args:
            message: User message text
            
        Returns:
            DetectionResult with category, impact, and reason
        """
        if not message or len(message) < 3:
            return DetectionResult(
                detected=False,
                category="",
                impact_level=0.0,
                reason="",
                original_message=message or "",
            )
        
        service = self._get_service()
        
        if service:
            try:
                result = await self._detect_with_llm(message, service)
                if result:
                    return self._apply_sensitivity(result)
            except Exception as e:
                print(f"LLM detection failed, using fallback: {e}")
        
        # Fallback to keyword detection
        return self._apply_sensitivity(self._detect_with_keywords(message))
    
    async def _detect_with_llm(self, message: str, service) -> Optional[DetectionResult]:
        """Use LLM for semantic detection."""
        prompt = DETECTION_PROMPT.format(message=message)
        
        # Create a fresh service instance without history to avoid context pollution
        from services.gemini_service import GeminiService, get_api_key
        detector_service = GeminiService(
            api_key=get_api_key(),
            system_instruction="You are a concise JSON-only response bot. Return only valid JSON.",
        )
        try:
            response = await detector_service.send_message(prompt)
        finally:
            close = getattr(detector_service, "close", None)
            if callable(close):
                await close()
        
        # Parse JSON from response
        try:
            # Find JSON in response
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                return DetectionResult(
                    detected=data.get("detected", False),
                    category=data.get("category", ""),
                    impact_level=float(data.get("impact", 0.0)),
                    reason=data.get("reason", ""),
                    original_message=message,
                )
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse LLM response: {e}")
        
        return None
    
    def _detect_with_keywords(self, message: str) -> DetectionResult:
        """Fallback keyword-based detection."""
        message_lower = message.lower()
        
        keywords = {
            "fatigue": {
                "words": ["tired", "exhausted", "sleepy", "drained"],
                "weight": 0.7,
            },
            "time": {
                "words": ["busy", "no time", "rushed", "overloaded"],
                "weight": 0.6,
            },
            "difficulty": {
                "words": ["confused", "struggling", "hard", "difficult"],
                "weight": 0.5,
            },
            "mood": {
                "words": ["stressed", "frustrated", "anxious", "overwhelmed"],
                "weight": 0.6,
            },
            "schedule": {
                "words": ["meeting", "deadline", "appointment", "event"],
                "weight": 0.5,
            },
        }

        for category, data in keywords.items():
            for word in data["words"]:
                if word in message or word in message_lower:
                    return DetectionResult(
                        detected=True,
                        category=category,
                        impact_level=data["weight"],
                        reason=f"Keyword detected: {word}",
                        original_message=message,
                    )
        
        return DetectionResult(
            detected=False,
            category="",
            impact_level=0.0,
            reason="",
            original_message=message,
        )
    
    def detect(self, message: str) -> DetectionResult:
        """
        Synchronous detection using keywords only.
        
        For async LLM detection, use detect_async().
        """
        return self._detect_with_keywords(message)


# =============================================================================
# Factory Functions
# =============================================================================

_detector: Optional[ComplaintDetector] = None

def get_complaint_detector() -> ComplaintDetector:
    """Get singleton ComplaintDetector instance."""
    global _detector
    if _detector is None:
        _detector = ComplaintDetector()
    return _detector


async def detect_complaint_async(message: str) -> Optional[DetectionResult]:
    """
    Quick async function to detect complaint using LLM.
    
    Returns DetectionResult if complaint detected, None otherwise.
    """
    result = await get_complaint_detector().detect_async(message)
    return result if result.detected else None


def detect_complaint(message: str) -> Optional[DetectionResult]:
    """
    Quick sync function for keyword-based detection.
    
    For LLM detection, use detect_complaint_async().
    """
    result = get_complaint_detector().detect(message)
    return result if result.detected else None
