# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/pattern_analyzer.py
# Purpose: Analyze decision history for pattern insights
# ===========================================================================

"""
Pattern Analyzer

Extracts actionable insights from decision history:
- Day of week patterns (e.g., "Wednesdays tend to be recovery days")
- Time of day preferences (e.g., "You learn best in the morning")
- Accept rate trends (e.g., "Trust in recommendations is increasing")
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from db.dao.decision_dao import DecisionDAO


# =============================================================================
# Day Names
# =============================================================================

DAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}

DAY_NAMES_ZH = {
    0: "周一",
    1: "周二",
    2: "周三",
    3: "周四",
    4: "周五",
    5: "周六",
    6: "周日",
}


# =============================================================================
# Pattern Analyzer
# =============================================================================

class PatternAnalyzer:
    """Analyze decision history for user insights."""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
    
    async def get_insights(self, max_insights: int = 3) -> List[Dict[str, Any]]:
        """
        Generate top insights from history.
        
        Returns list of {type, title, description, impact}.
        """
        insights = []
        
        # Collect all potential insights
        day_insights = await self._analyze_day_patterns()
        insights.extend(day_insights)
        
        hour_insights = await self._analyze_hour_patterns()
        insights.extend(hour_insights)
        
        trend_insights = await self._analyze_trends()
        insights.extend(trend_insights)
        
        # Sort by impact and return top N
        insights.sort(key=lambda x: x.get("impact", 0), reverse=True)
        return insights[:max_insights]
    
    async def _analyze_day_patterns(self) -> List[Dict[str, Any]]:
        """Find day-of-week patterns."""
        insights = []
        
        try:
            day_patterns = await DecisionDAO.get_pattern_by_day(self.user_id)
        except Exception:
            return insights
        
        # Find best and worst days
        valid_days = {d: p for d, p in day_patterns.items() 
                      if p.get("total_decisions", 0) >= 3}
        
        if len(valid_days) < 2:
            return insights
        
        best_day = max(valid_days.items(), key=lambda x: x[1]["accept_rate"])
        worst_day = min(valid_days.items(), key=lambda x: x[1]["accept_rate"])
        
        # High recovery rate day
        high_recovery = [(d, p) for d, p in valid_days.items() 
                         if p.get("recovery_rate", 0) > 0.5]
        
        if high_recovery:
            day, data = high_recovery[0]
            insights.append({
                "type": "day_pattern",
                "title": f"{DAY_NAMES[day]} Recovery Pattern",
                "description": f"You often need recovery mode on {DAY_NAMES[day]}s. "
                              f"Consider lighter scheduling this day.",
                "impact": data["recovery_rate"] * 0.8,
                "day": day,
            })
        
        # Best vs worst spread
        spread = best_day[1]["accept_rate"] - worst_day[1]["accept_rate"]
        if spread > 0.2:
            insights.append({
                "type": "day_contrast",
                "title": "Day Performance Varies",
                "description": f"{DAY_NAMES[best_day[0]]}s work well for you, "
                              f"but {DAY_NAMES[worst_day[0]]}s are challenging.",
                "impact": spread * 0.7,
                "best_day": best_day[0],
                "worst_day": worst_day[0],
            })
        
        return insights
    
    async def _analyze_hour_patterns(self) -> List[Dict[str, Any]]:
        """Find time-of-day patterns."""
        insights = []
        
        try:
            hour_patterns = await DecisionDAO.get_pattern_by_hour(self.user_id)
        except Exception:
            return insights
        
        valid_periods = {p: d for p, d in hour_patterns.items() 
                         if d.get("total_decisions", 0) >= 3}
        
        if not valid_periods:
            return insights
        
        # Find best period
        best = max(valid_periods.items(), key=lambda x: x[1]["accept_rate"])
        
        if best[1]["accept_rate"] > 0.6:
            period_desc = {
                "morning": "mornings (6am-12pm)",
                "afternoon": "afternoons (12pm-6pm)",
                "evening": "evenings (6pm-12am)",
            }
            insights.append({
                "type": "time_pattern",
                "title": f"Best Learning Time: {best[0].title()}",
                "description": f"Your acceptance rate is highest in {period_desc.get(best[0], best[0])}. "
                              f"Consider scheduling focused work then.",
                "impact": (best[1]["accept_rate"] - 0.5) * 0.8,
                "period": best[0],
            })
        
        return insights
    
    async def _analyze_trends(self) -> List[Dict[str, Any]]:
        """Analyze recent trends vs older history."""
        insights = []
        
        try:
            recent = await DecisionDAO.get_mode_history(self.user_id, days=7)
            older = await DecisionDAO.get_mode_history(self.user_id, days=30)
        except Exception:
            return insights
        
        if len(recent) < 3 or len(older) < 10:
            return insights
        
        # Compare accept rates
        recent_accepts = sum(1 for h in recent if h["user_action_type"] == "accept")
        recent_rate = recent_accepts / len(recent)
        
        older_accepts = sum(1 for h in older if h["user_action_type"] == "accept")
        older_rate = older_accepts / len(older)
        
        if recent_rate > older_rate + 0.15:
            insights.append({
                "type": "trend",
                "title": "Improving Alignment",
                "description": "Recent recommendations match your needs better. "
                              "The system is learning your patterns.",
                "impact": (recent_rate - older_rate) * 0.9,
            })
        elif recent_rate < older_rate - 0.15:
            insights.append({
                "type": "trend",
                "title": "Recent Adjustments Needed",
                "description": "You've been modifying plans more recently. "
                              "Life circumstances may have changed.",
                "impact": (older_rate - recent_rate) * 0.6,
            })
        
        return insights
    
    async def get_today_insight(self) -> Optional[str]:
        """Get a single insight relevant to today."""
        today = datetime.now().weekday()
        
        try:
            day_patterns = await DecisionDAO.get_pattern_by_day(self.user_id)
        except Exception:
            return None
        
        today_data = day_patterns.get(today, {})
        
        if today_data.get("total_decisions", 0) < 3:
            return None
        
        mode = today_data.get("predominant_mode", "standard")
        recovery_rate = today_data.get("recovery_rate", 0)
        
        if recovery_rate > 0.5:
            return f"Historically, {DAY_NAMES[today]}s often need lighter workload."
        elif mode == "sprint":
            return f"You tend to do well on {DAY_NAMES[today]}s - good day for challenges."
        
        return None


# =============================================================================
# Factory
# =============================================================================

def get_pattern_analyzer(user_id: str = "default") -> PatternAnalyzer:
    """Get a PatternAnalyzer instance."""
    return PatternAnalyzer(user_id)
