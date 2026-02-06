# ===========================================================================
# Chronos AI Learning Companion
# File: views/placeholder_views.py
# Purpose: Placeholder views for unimplemented pages
# ===========================================================================

"""
Placeholder Views

Temporary views for pages that are not yet fully implemented.
These provide visual feedback when navigating between sections.
"""

import flet as ft
from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer
from i18n.texts import TXT


def create_placeholder_view(
    title: str,
    subtitle: str,
    icon: str,
) -> ft.Container:
    """
    Create a placeholder view for unimplemented pages.
    
    Args:
        title: Page title.
        subtitle: Description text.
        icon: Flet icon name for visual.
    
    Returns:
        GlassContainer with centered placeholder content.
    """
    content = ft.Column(
        controls=[
            ft.Icon(
                icon,
                size=64,
                color=Colors.TEXT_MUTED,
            ),
            ft.Container(height=Sizes.SPACING_MD),
            ft.Text(
                title,
                size=Sizes.FONT_SIZE_XXL,
                weight=ft.FontWeight.BOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            ft.Text(
                subtitle,
                size=Sizes.FONT_SIZE_MD,
                color=Colors.TEXT_SECONDARY,
            ),
            ft.Container(height=Sizes.SPACING_XL),
            ft.Text(
                TXT.coming_soon,
                size=Sizes.FONT_SIZE_SM,
                color=Colors.TEXT_MUTED,
                italic=True,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True,
    )
    
    glass_view = GlassContainer(
        content=content,
        padding=Sizes.CONTENT_PADDING,
        expand=True,
    )
    
    return ft.Container(
        content=glass_view,
        expand=True,
        margin=ft.margin.only(
            top=Sizes.PAGE_MARGIN,
            right=Sizes.PAGE_MARGIN,
            bottom=Sizes.PAGE_MARGIN,
        ),
    )


def create_graph_view() -> ft.Container:
    """Create Knowledge Graph placeholder view."""
    return create_placeholder_view(
        title=TXT.graph_title,
        subtitle=TXT.graph_subtitle,
        icon=ft.Icons.HUB_OUTLINED,
    )


def create_settings_view() -> ft.Container:
    """Create Settings placeholder view."""
    return create_placeholder_view(
        title=TXT.settings_title,
        subtitle=TXT.settings_subtitle,
        icon=ft.Icons.SETTINGS_OUTLINED,
    )
