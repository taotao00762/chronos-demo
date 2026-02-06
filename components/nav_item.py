# ===========================================================================
# Chronos AI Learning Companion
# File: components/nav_item.py
# Purpose: Reusable navigation item component for sidebar
# ===========================================================================

"""
Navigation Item Component

A single navigation item with icon and label.
Supports selected/unselected states with visual feedback.

Visual States:
- Default: Muted icon and text, transparent background
- Selected: Bright icon/text, subtle glass background, left indicator
- Hover: Slightly elevated background (handled by ink effect)
"""

import flet as ft
from typing import Callable, Optional
from styles.tokens import Colors, Sizes


def create_nav_item(
    icon: str,
    label: str,
    is_selected: bool = False,
    on_click: Optional[Callable] = None,
) -> ft.Container:
    """
    Create a navigation item for the sidebar.
    
    Args:
        icon: Flet icon name (e.g., ft.Icons.DASHBOARD_ROUNDED).
        label: Text label for the nav item (from i18n).
        is_selected: Whether this item is currently active.
        on_click: Click event handler.
    
    Returns:
        ft.Container: Styled navigation item.
    
    Example:
        ```python
        nav = create_nav_item(
            icon=ft.Icons.DASHBOARD_ROUNDED,
            label=TXT.nav_dashboard,
            is_selected=True,
            on_click=lambda e: navigate_to("/"),
        )
        ```
    """
    
    # =========================================================================
    # Color Selection Based on State
    # =========================================================================
    icon_color = Colors.TEXT_PRIMARY if is_selected else Colors.TEXT_SECONDARY
    text_color = Colors.TEXT_PRIMARY if is_selected else Colors.TEXT_SECONDARY
    bg_color = Colors.NAV_SELECTED_BG if is_selected else "transparent"
    font_weight = ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL
    
    # =========================================================================
    # Left Indicator (visible only when selected)
    # =========================================================================
    indicator = ft.Container(
        width=Sizes.NAV_INDICATOR_WIDTH,
        height=20,
        bgcolor=Colors.NAV_INDICATOR if is_selected else "transparent",
        border_radius=2,
    )
    
    # =========================================================================
    # Icon
    # =========================================================================
    nav_icon = ft.Icon(
        name=icon,
        size=Sizes.NAV_ICON_SIZE,
        color=icon_color,
    )
    
    # =========================================================================
    # Label
    # =========================================================================
    nav_label = ft.Text(
        label,
        size=Sizes.FONT_SIZE_MD,
        weight=font_weight,
        color=text_color,
    )
    
    # =========================================================================
    # Compose Row Layout
    # =========================================================================
    content_row = ft.Row(
        controls=[
            indicator,
            ft.Container(width=Sizes.SPACING_SM),  # Gap after indicator
            nav_icon,
            ft.Container(width=Sizes.SPACING_SM),  # Gap after icon
            nav_label,
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
    )
    
    # =========================================================================
    # Container with Click Handler
    # =========================================================================
    return ft.Container(
        content=content_row,
        padding=ft.padding.symmetric(
            horizontal=Sizes.SPACING_SM,
            vertical=Sizes.SPACING_SM + 4,
        ),
        border_radius=Sizes.GLASS_RADIUS_XS,
        bgcolor=bg_color,
        on_click=on_click,
        ink=True,  # Ripple effect on click
        animate=ft.Animation(
            duration=Sizes.SPACING_SM * 20,  # 160ms
            curve=ft.AnimationCurve.EASE_OUT,
        ),
    )
