# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/core/datetime_handler.py
# Purpose: Time-aware processing (adapted from ReMe)
# ===========================================================================

"""
Datetime Handler

Provides time-aware capabilities:
- Time word detection in text
- Time-based decay weights for retrieval
- Datetime formatting for prompts
"""

import re
from datetime import datetime, timedelta
from typing import Optional


class DatetimeHandler:
    """
    Handler for time-aware memory processing.
    
    Adapted from ReMe's DatetimeHandler with full functionality.
    """
    
    # Time-related keywords for detection
    TIME_WORDS = {
        "zh": [
            "早上", "上午", "中午", "下午", "晚上", "深夜",
            "每天", "每周", "周末", "工作日",
            "早晨", "傍晚", "凌晨",
            "周一", "周二", "周三", "周四", "周五", "周六", "周日",
            "今天", "明天", "昨天", "最近",
            "小时", "分钟", "点钟",
        ],
        "en": [
            "morning", "afternoon", "evening", "night",
            "daily", "weekly", "weekend", "weekday",
            "dawn", "dusk", "midnight",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "today", "tomorrow", "yesterday", "recently",
            "hour", "minute", "o'clock",
            "am", "pm",
        ],
    }
    
    # Time patterns for extraction
    TIME_PATTERNS = {
        "zh": [
            r"\d{1,2}点",
            r"\d{1,2}:\d{2}",
            r"\d{1,2}时\d{1,2}分",
        ],
        "en": [
            r"\d{1,2}:\d{2}\s*(am|pm)?",
            r"\d{1,2}\s*(am|pm)",
            r"\d{1,2}\s*o'clock",
        ],
    }
    
    def __init__(self, dt: Optional[datetime] = None):
        """Initialize with optional datetime."""
        self.dt = dt or datetime.now()
    
    @classmethod
    def has_time_word(cls, query: str, language: str = "en") -> bool:
        """
        Check if text contains time-related keywords.
        
        Args:
            query: Text to check.
            language: Language code (en/zh).
        
        Returns:
            True if time words found.
        """
        query_lower = query.lower()
        lang = "zh" if language in ("zh", "cn", "zh-cn") else "en"
        
        # Check keywords
        for word in cls.TIME_WORDS.get(lang, cls.TIME_WORDS["en"]):
            if word.lower() in query_lower:
                return True
        
        # Check patterns
        for pattern in cls.TIME_PATTERNS.get(lang, cls.TIME_PATTERNS["en"]):
            if re.search(pattern, query_lower, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def extract_time_info(cls, query: str, language: str = "en") -> Optional[str]:
        """
        Extract time information from text.
        
        Args:
            query: Text to extract from.
            language: Language code.
        
        Returns:
            Extracted time info or None.
        """
        lang = "zh" if language in ("zh", "cn", "zh-cn") else "en"
        
        # Find all time words
        found_words = []
        query_lower = query.lower()
        
        for word in cls.TIME_WORDS.get(lang, cls.TIME_WORDS["en"]):
            if word.lower() in query_lower:
                found_words.append(word)
        
        # Find time patterns
        for pattern in cls.TIME_PATTERNS.get(lang, cls.TIME_PATTERNS["en"]):
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            found_words.extend(matches)
        
        return ", ".join(found_words) if found_words else None
    
    def string_format(
        self,
        string_format: str = "%Y-%m-%d %H:%M",
        language: str = "en",
    ) -> str:
        """
        Format datetime as string.
        
        Args:
            string_format: Format string.
            language: Language code.
        
        Returns:
            Formatted datetime string.
        """
        return self.dt.strftime(string_format)
    
    @classmethod
    def get_age_weight(
        cls,
        created_at: datetime,
        half_life_days: float = 7.0,
    ) -> float:
        """
        Calculate time decay weight for retrieval.
        
        Newer memories get higher weights.
        Weight = 0.5 ^ (age_in_days / half_life_days)
        
        Args:
            created_at: When memory was created.
            half_life_days: Days until weight halves.
        
        Returns:
            Weight between 0.0 and 1.0.
        """
        age = datetime.now() - created_at
        age_days = age.total_seconds() / (24 * 3600)
        
        # Exponential decay
        weight = 0.5 ** (age_days / half_life_days)
        
        return max(0.01, min(1.0, weight))
    
    @classmethod
    def is_expired(cls, expires_at: Optional[datetime]) -> bool:
        """Check if a timestamp has expired."""
        if expires_at is None:
            return False
        return datetime.now() > expires_at
