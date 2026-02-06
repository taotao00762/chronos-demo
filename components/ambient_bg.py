# ===========================================================================
# Chronos AI Learning Companion
# File: components/ambient_bg.py
# Purpose: Ambient lighting background with blurred color orbs
# ===========================================================================

"""
Ambient Background Component

Creates the "Dark Luxury" atmosphere with:
- Pure black base background
- Large blurred purple orb (top-right area)
- Large blurred blue orb (bottom-left area)

The orbs use extreme Gaussian blur (120+) to create a soft, 
diffused glow that adds depth without being distracting.
"""

import flet as ft
from styles.tokens import Colors, Sizes


def create_ambient_background() -> ft.Stack:
    """
    Create ambient lighting background with blurred color orbs.
    
    The background consists of three layers:
    1. Pure black base container (fills entire screen)
    2. Purple orb - positioned top-right, heavily blurred
    3. Blue orb - positioned bottom-left, heavily blurred
    
    Returns:
        ft.Stack: Layered background with ambient lighting effect.
    
    Example:
        ```python
        page.add(
            ft.Stack([
                create_ambient_background(),
                # ... your content on top
            ])
        )
        ```
    """
    
    # =========================================================================
    # Layer 1: Pure Black Base
    # =========================================================================
    black_base = ft.Container(
        expand=True,
        bgcolor=Colors.BG_PRIMARY,
    )
    
    # =========================================================================
    # Layer 2: Purple Orb (Top-Right)
    # =========================================================================
    purple_orb = ft.Container(
        width=Sizes.ORB_SIZE_LARGE,
        height=Sizes.ORB_SIZE_LARGE,
        border_radius=Sizes.ORB_SIZE_LARGE // 2,  # Make it circular
        bgcolor=Colors.ACCENT_PURPLE,
        # Extreme blur for soft diffused glow
        blur=ft.Blur(
            sigma_x=Sizes.GLASS_BLUR_AMBIENT,
            sigma_y=Sizes.GLASS_BLUR_AMBIENT,
            tile_mode=ft.BlurTileMode.CLAMP,
        ),
        # Reduce opacity for subtlety
        opacity=0.4,
        # Position: top-right area
        top=-100,
        right=-50,
    )
    
    # =========================================================================
    # Layer 3: Blue Orb (Bottom-Left)
    # =========================================================================
    blue_orb = ft.Container(
        width=Sizes.ORB_SIZE_MEDIUM,
        height=Sizes.ORB_SIZE_MEDIUM,
        border_radius=Sizes.ORB_SIZE_MEDIUM // 2,  # Make it circular
        bgcolor=Colors.ACCENT_BLUE,
        # Extreme blur for soft diffused glow
        blur=ft.Blur(
            sigma_x=Sizes.GLASS_BLUR_AMBIENT,
            sigma_y=Sizes.GLASS_BLUR_AMBIENT,
            tile_mode=ft.BlurTileMode.CLAMP,
        ),
        # Reduce opacity for subtlety
        opacity=0.3,
        # Position: bottom-left area
        bottom=-80,
        left=-30,
    )
    
    # =========================================================================
    # Combine Layers
    # =========================================================================
    return ft.Stack(
        controls=[
            black_base,
            purple_orb,
            blue_orb,
        ],
        expand=True,
    )
