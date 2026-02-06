# ===========================================================================
# Chronos AI Learning Companion
# File: components/stat_card.py
# Purpose: Bento-style statistics card component
# ===========================================================================

"""
Statistics Card Component

A clean, minimal card for displaying key metrics in the dashboard.
Follows Bento Grid design principles with:
- Small muted label on top
- Large bold value as the focus
- Optional subtitle or secondary info
- Optional icon for visual interest
"""

import flet as ft
from typing import Optional
from styles.tokens import Colors, Sizes
from styles.glass import GlassCard


def create_stat_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: Optional[str] = None,
    icon_color: str = Colors.TEXT_SECONDARY,
    expand: bool = False,
    height: Optional[int] = None,
) -> ft.Container:
    """
    Create a Bento-style statistics card.
    
    Args:
        title: Card title/label (small, muted text).
        value: Main value to display (large, bold).
        subtitle: Optional secondary text below value.
        icon: Optional Flet icon name.
        icon_color: Color for the icon.
        expand: Whether card should expand to fill space.
        height: Optional fixed height in pixels.
    
    Returns:
        GlassCard: Styled statistics card.
    
    Example:
        ```python
        card = create_stat_card(
            title=TXT.card_progress_title,
            value="72%",
            subtitle="18 / 25 hours",
            icon=ft.Icons.TRENDING_UP_ROUNDED,
        )
        ```
    """
    
    # =========================================================================
    # Build Content Elements
    # =========================================================================
    content_controls = []
    
    # Row with title and optional icon
    title_row_controls = [
        ft.Text(
            title,
            size=Sizes.FONT_SIZE_SM,
            color=Colors.TEXT_SECONDARY,
            weight=ft.FontWeight.W_500,
        ),
    ]
    
    if icon:
        title_row_controls.append(
            ft.Container(
                content=ft.Icon(
                    icon,
                    size=16,
                    color=icon_color,
                ),
                margin=ft.margin.only(left=Sizes.SPACING_SM),
            )
        )
    
    title_row = ft.Row(
        controls=title_row_controls,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    content_controls.append(title_row)
    
    # Spacer
    content_controls.append(ft.Container(height=Sizes.SPACING_SM))
    
    # Main value (large bold text)
    content_controls.append(
        ft.Text(
            value,
            size=Sizes.FONT_SIZE_XXL,
            weight=ft.FontWeight.BOLD,
            color=Colors.TEXT_PRIMARY,
        )
    )
    
    # Optional subtitle
    if subtitle:
        content_controls.append(
            ft.Text(
                subtitle,
                size=Sizes.FONT_SIZE_SM,
                color=Colors.TEXT_MUTED,
            )
        )
    
    # =========================================================================
    # Compose Card
    # =========================================================================
    card_content = ft.Column(
        controls=content_controls,
        spacing=Sizes.SPACING_XS,
        alignment=ft.MainAxisAlignment.START,
    )
    
    return GlassCard(
        content=card_content,
        expand=expand,
        height=height,
    )


def create_progress_card(
    title: str,
    value: float,
    label: str,
    subtitle: str = "",
) -> ft.Container:
    """
    Create a card with circular progress indicator.
    
    Args:
        title: Card title.
        value: Progress value (0.0 to 1.0).
        label: Text inside the progress ring.
        subtitle: Optional text below progress.
    
    Returns:
        GlassCard with circular progress.
    """
    
    # Progress ring with label overlay
    progress_stack = ft.Stack(
        controls=[
            ft.ProgressRing(
                value=value,
                stroke_width=6,
                width=80,
                height=80,
                color=Colors.TEXT_PRIMARY,
                bgcolor=f"rgba(255, 255, 255, 0.1)",
            ),
            ft.Container(
                content=ft.Text(
                    label,
                    size=Sizes.FONT_SIZE_LG,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
                width=80,
                height=80,
                alignment=ft.alignment.center,
            ),
        ],
    )
    
    card_content = ft.Column(
        controls=[
            ft.Text(
                title,
                size=Sizes.FONT_SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                weight=ft.FontWeight.W_500,
            ),
            ft.Container(height=Sizes.SPACING_MD),
            ft.Row(
                controls=[progress_stack],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(height=Sizes.SPACING_SM),
            ft.Text(
                subtitle,
                size=Sizes.FONT_SIZE_SM,
                color=Colors.TEXT_MUTED,
                text_align=ft.TextAlign.CENTER,
            ) if subtitle else ft.Container(),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=Sizes.SPACING_XS,
    )
    
    return GlassCard(
        content=card_content,
        height=180,
    )
