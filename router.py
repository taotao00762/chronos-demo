# ===========================================================================
# Chronos AI Learning Companion
# File: router.py
# Purpose: Route management for role-based navigation architecture
# ===========================================================================

"""
Router Module - Role-Based Architecture

Navigation Structure:
    / (Command Center)  -> Overview / Status Dashboard
    /plan               -> Plan Module (Director's Stage)
    /tutor              -> Tutor Module (Teacher's Stage)
    /memory             -> Memory Bank
    /graph              -> Knowledge Graph
    /settings           -> Settings
"""

from typing import Dict


# =============================================================================
# Route Definitions (Role-Based Architecture)
# =============================================================================

ROUTES: Dict[str, int] = {
    "/": 0,           # Command Center (Overview)
    "/plan": 1,       # Plan Module (Director)
    "/tutor": 2,      # Tutor Module (Teacher)
    "/memory": 3,     # Memory Bank
    "/graph": 4,      # Knowledge Graph
    "/settings": 5,   # Settings
}

# Reverse mapping: index -> route
INDEX_TO_ROUTE: Dict[int, str] = {v: k for k, v in ROUTES.items()}


# =============================================================================
# Helper Functions
# =============================================================================

def get_route_from_index(index: int) -> str:
    """
    Get route path from navigation index.
    
    Args:
        index: Navigation item index (0-5).
    
    Returns:
        Route path string. Defaults to "/" if index not found.
    """
    return INDEX_TO_ROUTE.get(index, "/")


def get_index_from_route(route: str) -> int:
    """
    Get navigation index from route path.
    
    Args:
        route: Route path string (e.g., "/plan").
    
    Returns:
        Navigation index (0-5). Defaults to 0 if route not found.
    """
    return ROUTES.get(route, 0)


def is_valid_route(route: str) -> bool:
    """Check if a route path is valid."""
    return route in ROUTES
