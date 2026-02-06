# ===========================================================================
# Chronos AI Learning Companion
# File: components/interruption_dialog.py
# Purpose: Dialog for reporting life interruptions
# ===========================================================================

import flet as ft
from styles.tokens import Colors

def create_interruption_dialog(
    on_confirm: callable,
    on_cancel: callable = None,
) -> ft.AlertDialog:
    """
    Create a dialog to report an interruption.
    
    Args:
        on_confirm: Callback with (category, impact_level, description)
        on_cancel: Optional cancel callback
    """
    
    state = {
        "category": "fatigue",
        "impact": 0.5,
        "description": "",
    }
    
    # Category selection
    categories = {
        "fatigue": "😴 Health / Fatigue",
        "time": "⏰ Time Constraint",
        "mood": "🌩️ Mood / Stress",
        "social": "🎉 Social Event",
        "other": "📝 Other",
    }
    
    category_dropdown = ft.Dropdown(
        label="Type",
        value="fatigue",
        options=[ft.dropdown.Option(k, v) for k, v in categories.items()],
        text_size=14,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY, size=12),
        border_color=Colors.BORDER_GLASS,
        bgcolor="rgba(255,255,255,0.03)",
        color=Colors.TEXT_PRIMARY,
        on_change=lambda e: state.update({"category": e.control.value}),
    )
    
    # Impact slider
    impact_slider = ft.Slider(
        value=0.5,
        min=0.1,
        max=1.0,
        divisions=9,
        label="{value}",
        active_color=Colors.TEXT_PRIMARY,
        on_change=lambda e: state.update({"impact": e.control.value}),
    )
    
    # Description input
    desc_field = ft.TextField(
        label="Description (Optional)",
        hint_text="What happened?",
        hint_style=ft.TextStyle(color=Colors.TEXT_MUTED),
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY, size=12),
        border_color=Colors.BORDER_GLASS,
        bgcolor="rgba(255,255,255,0.03)",
        color=Colors.TEXT_PRIMARY,
        text_size=14,
        multiline=True,
        min_lines=2,
        max_lines=3,
        on_change=lambda e: state.update({"description": e.control.value}),
    )
    
    def handle_confirm(e):
        on_confirm(
            state["category"],
            state["impact"],
            state["description"] or categories.get(state["category"], "Interruption")
        )
    
    def handle_cancel(e):
        if on_cancel:
            on_cancel()
            
    content = ft.Column([
        ft.Text("Report an interruption to adjust your plan.", size=12, color=Colors.TEXT_SECONDARY),
        ft.Container(height=8),
        category_dropdown,
        ft.Container(height=8),
        ft.Text("Impact Level", size=12, color=Colors.TEXT_SECONDARY),
        ft.Row([
            ft.Text("Low", size=10, color=Colors.TEXT_MUTED),
            ft.Container(content=impact_slider, expand=True),
            ft.Text("High", size=10, color=Colors.TEXT_MUTED),
        ]),
        ft.Container(height=8),
        desc_field,
    ], tight=True, width=400)
    
    return ft.AlertDialog(
        title=ft.Row([
            ft.Icon(ft.Icons.FLASH_ON_ROUNDED, color="#F59E0B"),
            ft.Container(width=8),
            ft.Text("Report Interruption", size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
        ]),
        content=content,
        actions=[
            ft.TextButton("Cancel", on_click=handle_cancel),
            ft.FilledButton("Report", on_click=handle_confirm),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
