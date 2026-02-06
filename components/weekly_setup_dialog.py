# ===========================================================================
# Chronos AI Learning Companion
# File: components/weekly_setup_dialog.py
# Purpose: Minimal weekly plan setup dialog
# ===========================================================================

"""
Weekly Setup Dialog

Minimal 3-step setup for weekly learning plan:
1. Enter learning goals (free text)
2. Toggle available days (Mon-Sun checkboxes)
3. Select intensity (Light/Balanced/Push)
"""

import flet as ft
from styles.tokens import Colors


# =============================================================================
# Weekly Setup Component
# =============================================================================

def create_weekly_setup_dialog(
    on_confirm: callable,
    on_cancel: callable = None,
) -> ft.AlertDialog:
    """
    Create the weekly setup dialog.
    
    Args:
        on_confirm: Callback with (goals, available_days, intensity)
        on_cancel: Optional cancel callback
    """
    
    # State
    state = {
        "goals": "",
        "days": {
            "mon": True, "tue": True, "wed": True, 
            "thu": True, "fri": True, "sat": False, "sun": False,
        },
        "intensity": "balanced",
    }
    
    # Goals input
    goals_field = ft.TextField(
        hint_text="e.g., Python basics, Math review",
        hint_style=ft.TextStyle(color=Colors.TEXT_MUTED),
        border_color=Colors.BORDER_GLASS,
        bgcolor="rgba(255,255,255,0.03)",
        color=Colors.TEXT_PRIMARY,
        text_size=14,
        multiline=True,
        min_lines=2,
        max_lines=3,
        on_change=lambda e: state.update({"goals": e.control.value}),
    )
    
    # Day toggles
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    
    day_checkboxes = []
    
    def create_day_toggle(label: str, key: str, default: bool) -> ft.Container:
        checkbox = ft.Checkbox(
            value=default,
            fill_color=Colors.TEXT_PRIMARY,
            check_color=Colors.BG_PRIMARY,
            on_change=lambda e, k=key: state["days"].update({k: e.control.value}),
        )
        day_checkboxes.append(checkbox)
        
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=11, color=Colors.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                checkbox,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            padding=4,
        )
    
    days_row = ft.Row(
        controls=[create_day_toggle(l, k, state["days"][k]) for l, k in zip(day_labels, day_keys)],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    
    # Intensity selection
    intensity_group = ft.RadioGroup(
        value="balanced",
        on_change=lambda e: state.update({"intensity": e.control.value}),
        content=ft.Row([
            ft.Radio(value="light", label="Light", fill_color=Colors.TEXT_PRIMARY),
            ft.Radio(value="balanced", label="Balanced", fill_color=Colors.TEXT_PRIMARY),
            ft.Radio(value="push", label="Push", fill_color=Colors.TEXT_PRIMARY),
        ], spacing=16),
    )
    
    # Callbacks
    def handle_confirm(e):
        goals_list = [g.strip() for g in state["goals"].split(",") if g.strip()]
        if not goals_list:
            goals_list = [state["goals"].strip()] if state["goals"].strip() else ["General learning"]
        
        on_confirm(goals_list, state["days"], state["intensity"])
    
    def handle_cancel(e):
        if on_cancel:
            on_cancel()
    
    # Dialog content
    content = ft.Column([
        ft.Text("What do you want to learn this week?", size=13, color=Colors.TEXT_SECONDARY),
        goals_field,
        ft.Container(height=16),
        
        ft.Text("Which days are good for learning?", size=13, color=Colors.TEXT_SECONDARY),
        days_row,
        ft.Container(height=16),
        
        ft.Text("How intense?", size=13, color=Colors.TEXT_SECONDARY),
        intensity_group,
    ], tight=True, spacing=8, width=400)
    
    return ft.AlertDialog(
        title=ft.Row([
            ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, color=Colors.TEXT_PRIMARY, size=24),
            ft.Container(width=8),
            ft.Text("This Week's Setup", size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
        ]),
        content=content,
        actions=[
            ft.TextButton("Cancel", on_click=handle_cancel),
            ft.FilledButton("Start Week", on_click=handle_confirm),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )


def create_week_progress_banner(
    progress_pct: int = 0,
    completed_days: int = 0,
    total_days: int = 5,
    adjustments_count: int = 0,
    on_setup_click: callable = None,
) -> ft.Container:
    """
    Create a compact week progress banner for Plan page.
    
    Shows:
    - Week progress bar
    - Days completed
    - Adjustment count (if any)
    """
    
    # Progress indicator
    progress_text = f"{progress_pct}%" if progress_pct > 0 else "No plan"
    progress_color = Colors.SUCCESS if progress_pct >= 60 else Colors.TEXT_SECONDARY
    
    # Adjustment badge
    adjustment_badge = None
    if adjustments_count > 0:
        adjustment_badge = ft.Container(
            content=ft.Text(f"-{adjustments_count} adjusted", size=10, color="#F59E0B"),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            bgcolor="rgba(245, 158, 11, 0.15)",
            border_radius=8,
        )
    
    # Setup button (if no plan)
    setup_btn = None
    if progress_pct == 0 and on_setup_click:
        setup_btn = ft.OutlinedButton(
            "Setup Week",
            icon=ft.Icons.ADD_ROUNDED,
            on_click=on_setup_click,
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, Colors.BORDER_GLASS),
                color=Colors.TEXT_PRIMARY,
            ),
        )
    
    content = ft.Row([
        ft.Icon(ft.Icons.CALENDAR_TODAY_ROUNDED, size=16, color=Colors.TEXT_MUTED),
        ft.Container(width=8),
        ft.Text(f"Week: {completed_days}/{total_days} days", size=12, color=Colors.TEXT_SECONDARY),
        ft.Container(width=8),
        ft.ProgressBar(
            value=progress_pct / 100 if progress_pct > 0 else 0,
            width=80,
            height=6,
            color=progress_color,
            bgcolor="rgba(255,255,255,0.1)",
            border_radius=3,
        ),
        ft.Container(width=8),
        ft.Text(progress_text, size=12, weight=ft.FontWeight.W_500, color=progress_color),
        adjustment_badge if adjustment_badge else ft.Container(),
        ft.Container(expand=True),
        setup_btn if setup_btn else ft.Container(),
    ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    
    return ft.Container(
        content=content,
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        bgcolor="rgba(255,255,255,0.03)",
        border=ft.border.all(1, Colors.BORDER_GLASS),
        border_radius=10,
    )
