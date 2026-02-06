# ===========================================================================
# Chronos AI Learning Companion
# File: services/__init__.py
# Purpose: Export service classes
# ===========================================================================

from services.settings_service import (
    load_settings,
    save_settings,
    get_settings_path,
)

from services.gemini_service import (
    GeminiService,
    create_gemini_service,
    get_api_key,
)

from services.receipt_extractor import (
    extract_receipt,
    extract_and_save_receipt,
)

from services.plan_generator import (
    generate_plan_proposal,
    generate_and_save_plan,
)

from services.dashboard_service import DashboardService
from services.briefing_service import BriefingService
from services.principal_service import (
    PrincipalContextService,
    get_principal_context_service,
)

__all__ = [
    "load_settings",
    "save_settings",
    "get_settings_path",
    "GeminiService",
    "create_gemini_service",
    "get_api_key",
    "extract_receipt",
    "extract_and_save_receipt",
    "generate_plan_proposal",
    "generate_and_save_plan",
    "DashboardService",
    "BriefingService",
    "PrincipalContextService",
    "get_principal_context_service",
]

