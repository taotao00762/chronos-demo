# ===========================================================================
# Chronos AI Learning Companion
# File: components/sidebar.py
# Purpose: Floating glass sidebar with role-based navigation
# ===========================================================================

"""
Sidebar Component - Role-Based Architecture

Navigation items:
1. Command Center (Overview)
2. Plan (Director's Stage)
3. Tutor (Teacher's Stage)
4. Memory (Memory Bank)
5. Knowledge Graph
6. Settings
"""

import flet as ft
from typing import Callable, Optional
from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer
from components.nav_item import create_nav_item
from i18n.texts import TXT


# =============================================================================
# Navigation Configuration (Role-Based)
# =============================================================================

NAV_ITEMS = [
    {"icon": ft.Icons.SPACE_DASHBOARD_ROUNDED, "label_key": "nav_command", "route": "/"},
    {"icon": ft.Icons.CALENDAR_MONTH_ROUNDED, "label_key": "nav_plan", "route": "/plan"},
    {"icon": ft.Icons.SCHOOL_ROUNDED, "label_key": "nav_tutor", "route": "/tutor"},
    {"icon": ft.Icons.MEMORY_ROUNDED, "label_key": "nav_memory", "route": "/memory"},
    {"icon": ft.Icons.HUB_OUTLINED, "label_key": "nav_graph", "route": "/graph"},
    {"icon": ft.Icons.SETTINGS_OUTLINED, "label_key": "nav_settings", "route": "/settings"},
]


def create_sidebar(
    selected_index: int = 0,
    on_navigate: Optional[Callable[[int], None]] = None,
) -> ft.Container:
    """
    Create floating glass sidebar with role-based navigation.
    
    Args:
        selected_index: Currently active nav item index (0-5).
        on_navigate: Callback when nav item is clicked, receives index.
    
    Returns:
        ft.Container: Floating glass sidebar with margin.
    """
    
    # =========================================================================
    # Click Handler Factory
    # =========================================================================
    def make_click_handler(index: int):
        def handler(e):
            if on_navigate:
                on_navigate(index)
        return handler
    
    # =========================================================================
    # Build Navigation Items
    # =========================================================================
    nav_controls = []
    for i, item in enumerate(NAV_ITEMS):
        nav_controls.append(
            create_nav_item(
                icon=item["icon"],
                label=getattr(TXT, item["label_key"]),
                is_selected=(i == selected_index),
                on_click=make_click_handler(i),
            )
        )
    
    # =========================================================================
    # Logo Section
    # =========================================================================
    logo_section = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        "C",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.BG_PRIMARY,
                    ),
                    width=36,
                    height=36,
                    bgcolor=Colors.TEXT_PRIMARY,
                    border_radius=10,
                    alignment=ft.alignment.center,
                ),
                ft.Container(width=Sizes.SPACING_SM),
                ft.Text(
                    TXT.app_name,
                    size=Sizes.FONT_SIZE_LG,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(
            left=Sizes.SPACING_MD,
            top=Sizes.SPACING_LG,
            bottom=Sizes.SPACING_XL,
        ),
    )
    
    # =========================================================================
    # Navigation Section
    # =========================================================================
    nav_section = ft.Container(
        content=ft.Column(
            controls=nav_controls,
            spacing=Sizes.SPACING_XS,
        ),
        padding=ft.padding.symmetric(horizontal=Sizes.SPACING_SM),
        expand=True,
    )
    
    # =========================================================================
    # User Profile Section
    # =========================================================================
    user_section = ft.Container(
        content=ft.Row(
            controls=[
                ft.CircleAvatar(
                    content=ft.Text(
                        "U",
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    bgcolor=Colors.BG_CARD,
                    radius=18,
                ),
                ft.Container(width=Sizes.SPACING_SM),
                ft.Column(
                    controls=[
                        ft.Text(
                            TXT.user_label,
                            size=Sizes.FONT_SIZE_SM,
                            weight=ft.FontWeight.W_500,
                            color=Colors.TEXT_PRIMARY,
                        ),
                        ft.Text(
                            TXT.user_plan,
                            size=Sizes.FONT_SIZE_XS,
                            color=Colors.TEXT_MUTED,
                        ),
                    ],
                    spacing=2,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.all(Sizes.SPACING_MD),
        border=ft.border.only(
            top=ft.BorderSide(1, Colors.BORDER_GLASS),
        ),
    )
    
    # =========================================================================
    # Sidebar Glass Container
    # =========================================================================
    sidebar_content = ft.Column(
        controls=[
            logo_section,
            nav_section,
            user_section,
        ],
        spacing=0,
        expand=True,
    )
    
    glass_sidebar = GlassContainer(
        content=sidebar_content,
        padding=0,
        radius=Sizes.GLASS_RADIUS,
        blur=Sizes.GLASS_BLUR,
        expand=True,
    )
    
    # =========================================================================
    # Outer Container with Floating Margin
    # =========================================================================
    return ft.Container(
        content=glass_sidebar,
        width=Sizes.SIDEBAR_WIDTH,
        margin=ft.margin.only(
            left=Sizes.PAGE_MARGIN,
            top=Sizes.PAGE_MARGIN,
            bottom=Sizes.PAGE_MARGIN,
        ),
    )
