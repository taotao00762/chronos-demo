# ===========================================================================
# Chronos AI Learning Companion
# File: styles/glass.py
# Purpose: GlassContainer - reusable glass-morphism container component
# ===========================================================================

"""
GlassContainer implements the glass-morphism effect for Dark Luxury theme.

Key visual properties:
- Semi-transparent white background (5% opacity)
- Subtle white border (8% opacity)
- Backdrop blur filter for frosted glass effect
- Large border radius for modern look
"""

import flet as ft
from styles.tokens import Colors, Sizes


class GlassContainer(ft.Container):
    """
    Reusable glass-morphism container with backdrop blur effect.
    
    This is the core visual building block for the Dark Luxury Bento Glass theme.
    All UI panels, cards, and floating elements should use this container.
    
    Args:
        content: Child control to wrap inside the glass container.
        blur: Backdrop blur intensity in pixels (default: 15).
        radius: Border radius in pixels (default: 24).
        padding: Inner padding in pixels (default: 20).
        border_opacity: Border opacity 0.0-1.0 (default: 0.08).
        bg_opacity: Background opacity 0.0-1.0 (default: 0.05).
        **kwargs: Additional ft.Container arguments.
    
    Example:
        ```python
        card = GlassContainer(
            content=ft.Text("Hello"),
            padding=24,
            radius=20,
        )
        ```
    """
    
    def __init__(
        self,
        content: ft.Control = None,
        blur: int = Sizes.GLASS_BLUR,
        radius: int = Sizes.GLASS_RADIUS,
        padding: int = Sizes.CARD_PADDING,
        border_opacity: float = 0.08,
        bg_opacity: float = 0.05,
        **kwargs
    ) -> None:
        # Build RGBA color strings with custom opacity
        bg_color = f"rgba(255, 255, 255, {bg_opacity})"
        border_color = f"rgba(255, 255, 255, {border_opacity})"
        
        super().__init__(
            content=content,
            padding=padding,
            border_radius=radius,
            bgcolor=bg_color,
            border=ft.border.all(1, border_color),
            # Backdrop blur for frosted glass effect
            blur=ft.Blur(
                sigma_x=blur,
                sigma_y=blur,
                tile_mode=ft.BlurTileMode.CLAMP,
            ),
            # Subtle shadow for depth
            shadow=ft.BoxShadow(
                blur_radius=30,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 8),
            ),
            **kwargs
        )


class GlassCard(GlassContainer):
    """
    Specialized glass container for Bento Grid cards.
    
    Inherits from GlassContainer with card-specific defaults:
    - Smaller border radius (16px)
    - Optimized padding for card content
    """
    
    def __init__(
        self,
        content: ft.Control = None,
        **kwargs
    ) -> None:
        # Card-specific defaults
        kwargs.setdefault("radius", Sizes.GLASS_RADIUS_SM)
        kwargs.setdefault("padding", Sizes.CARD_PADDING)
        
        super().__init__(content=content, **kwargs)


class GlassButton(ft.Container):
    """
    Glass-styled button with hover effect.
    
    Args:
        content: Button content (icon, text, or row).
        on_click: Click event handler.
        **kwargs: Additional container arguments.
    """
    
    def __init__(
        self,
        content: ft.Control = None,
        on_click: callable = None,
        **kwargs
    ) -> None:
        super().__init__(
            content=content,
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=Sizes.GLASS_RADIUS_XS,
            bgcolor=f"rgba(255, 255, 255, 0.05)",
            border=ft.border.all(1, f"rgba(255, 255, 255, 0.08)"),
            on_click=on_click,
            ink=True,
            **kwargs
        )
