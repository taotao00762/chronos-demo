# ===========================================================================
# Chronos AI Learning Companion
# File: components/plan_header.py
# Purpose: Plan Header - Mode indicator and quick actions
# ===========================================================================

"""
Plan Header Component

Displays:
- Today's Mode (Recovery / Cruise / Sprint)
- Reason Snapshot chips (Interruptions / Focus Window / Energy)
- Quick action buttons (Review Plan / Start Session)
"""

import flet as ft
from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer


# =============================================================================
# Mode Badge Component
# =============================================================================

def create_mode_badge(mode: str) -> ft.Container:
    """
    Create a prominent mode badge.
    
    Args:
        mode: "recovery" | "cruise" | "sprint"
    """
    mode_config = {
        "recovery": {"label": "Recovery", "color": "#10B981", "icon": ft.Icons.SELF_IMPROVEMENT_ROUNDED},
        "standard": {"label": "Standard", "color": "#3B82F6", "icon": ft.Icons.TRENDING_UP_ROUNDED},
        "cruise": {"label": "Cruise", "color": "#3B82F6", "icon": ft.Icons.DIRECTIONS_BOAT_ROUNDED},
        "sprint": {"label": "Sprint", "color": "#F59E0B", "icon": ft.Icons.FLASH_ON_ROUNDED},
    }
    
    config = mode_config.get(mode, mode_config["cruise"])
    
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(config["icon"], size=18, color=config["color"]),
                ft.Container(width=6),
                ft.Text(
                    config["label"],
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=config["color"],
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        bgcolor=f"rgba({int(config['color'][1:3], 16)}, {int(config['color'][3:5], 16)}, {int(config['color'][5:7], 16)}, 0.15)",
        border=ft.border.all(1, f"rgba({int(config['color'][1:3], 16)}, {int(config['color'][3:5], 16)}, {int(config['color'][5:7], 16)}, 0.3)"),
        border_radius=20,
    )


# =============================================================================
# Reason Chip Component
# =============================================================================

def create_reason_chip(label: str, value: str, level: str = "medium") -> ft.Container:
    """
    Create a small reason chip.
    
    Args:
        label: Chip label (e.g., "Interruptions")
        value: Chip value (e.g., "High")
        level: "low" | "medium" | "high" for color coding
    """
    level_colors = {
        "low": Colors.SUCCESS,
        "medium": "#F59E0B",
        "high": "#EF4444",
    }
    color = level_colors.get(level, Colors.TEXT_SECONDARY)
    
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    f"{label}:",
                    size=11,
                    color=Colors.TEXT_MUTED,
                ),
                ft.Container(width=4),
                ft.Text(
                    value,
                    size=11,
                    weight=ft.FontWeight.W_500,
                    color=color,
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=6),
        bgcolor=f"rgba(255, 255, 255, 0.05)",
        border_radius=12,
    )


# =============================================================================
# Plan Header Main Component
# =============================================================================

def create_plan_header(
    mode: str = "recovery",
    interruptions: str = "High",
    focus_window: str = "10:30–11:15",
    energy: str = "Medium",
    on_review: callable = None,
    on_start: callable = None,
) -> ft.Container:
    """
    Create the Plan Header component.
    
    Args:
        mode: Current day mode ("recovery" | "cruise" | "sprint")
        interruptions: Interruption level
        focus_window: Best focus window today
        energy: Energy level
        on_review: Review Plan button callback
        on_start: Start Session button callback
    """
    
    # Mode badge
    mode_badge = create_mode_badge(mode)
    
    # Reason chips
    interruptions_label = (interruptions or "").lower()
    energy_label = (energy or "").lower()
    interruption_level = "high" if interruptions_label == "high" else "low" if interruptions_label == "low" else "medium"
    energy_level = "high" if energy_label == "high" else "low" if energy_label == "low" else "medium"
    
    chips_row = ft.Row(
        controls=[
            create_reason_chip("Interruptions", interruptions, interruption_level),
            create_reason_chip("Focus", focus_window, "low"),
            create_reason_chip("Energy", energy, energy_level),
        ],
        spacing=8,
    )
    
    # Action buttons
    review_btn = ft.OutlinedButton(
        text="Review Plan",
        icon=ft.Icons.RATE_REVIEW_OUTLINED,
        on_click=on_review,
        style=ft.ButtonStyle(
            color=Colors.TEXT_PRIMARY,
            side=ft.BorderSide(1, Colors.BORDER_GLASS),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        ),
    )
    
    start_btn = ft.FilledButton(
        text="Start Session",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        on_click=on_start,
        style=ft.ButtonStyle(
            bgcolor=Colors.TEXT_PRIMARY,
            color=Colors.BG_PRIMARY,
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        ),
    )
    
    # Left section (Mode + Chips)
    left_section = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text(
                        "Today Mode",
                        size=11,
                        color=Colors.TEXT_MUTED,
                    ),
                    ft.Container(width=8),
                    mode_badge,
                ],
            ),
            ft.Container(height=8),
            chips_row,
        ],
        spacing=0,
    )
    
    # Right section (Buttons)
    right_section = ft.Row(
        controls=[review_btn, ft.Container(width=8), start_btn],
        spacing=0,
    )
    
    # Main container
    return ft.Container(
        content=ft.Row(
            controls=[
                left_section,
                ft.Container(expand=True),
                right_section,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.all(16),
        bgcolor=f"rgba(255, 255, 255, 0.03)",
        border=ft.border.all(1, Colors.BORDER_GLASS),
        border_radius=16,
        margin=ft.margin.only(bottom=16),
    )
