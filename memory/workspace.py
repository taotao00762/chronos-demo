# ===========================================================================
# Chronos AI Learning Companion
# File: memory/workspace.py
# Purpose: ReMe workspace ID conventions
# ===========================================================================

"""
Workspace ID Helpers

Defines workspace naming conventions for ReMe integration.
"""


def get_personal_workspace(user_id: str = "default") -> str:
    """
    Get personal memory workspace ID for a user.
    
    Personal memory stores:
    - User preferences and habits
    - Learning style patterns
    - Interruption patterns
    - Context-specific adaptations
    
    Args:
        user_id: User identifier.
    
    Returns:
        Workspace ID string.
    """
    return f"user:{user_id}:personal"


def get_task_workspace() -> str:
    """
    Get shared task memory workspace ID.
    
    Task memory stores:
    - Reusable learning strategies
    - Effective plan templates
    - Error recovery patterns
    - Success patterns across users
    
    Returns:
        Workspace ID string.
    """
    return "app:study:task"


def get_tool_workspace() -> str:
    """
    Get tool memory workspace ID.
    
    Tool memory stores:
    - Tool usage success rates
    - Optimal parameter configurations
    - Cost/performance metrics
    
    Returns:
        Workspace ID string.
    """
    return "app:tool"
