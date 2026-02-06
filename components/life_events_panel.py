# ===========================================================================
# Chronos AI Learning Companion
# File: components/life_events_panel.py
# Purpose: Dynamic Life Events Panel with real-time data from DecisionEngine
# ===========================================================================

"""
Life Events Panel

Displays current life events status from DecisionEngine:
- Overall life pressure indicator
- Top 5 factors (Sleep, Schedule, Social, Energy, Mood)
- Recommended learning windows
- Quick log buttons for updating status
"""

import flet as ft
from styles.tokens import Colors, Sizes
from styles.glass import GlassCard


# =============================================================================
# Life Events Panel
# =============================================================================

def create_life_events_panel(page: ft.Page = None, on_change: callable = None) -> ft.Container:
    """
    Create a dynamic life events panel.
    
    Loads data from DecisionEngine on mount and provides quick-log buttons.
    """
    
    # State
    state = {
        "pressure": 0.5,
        "pressure_label": "Medium",
        "factors": [],
        "windows": [],
        "loading": True,
        "page": page,
    }
    
    # UI Components
    pressure_value_text = ft.Text("--", size=12, weight=ft.FontWeight.BOLD, color=Colors.TEXT_MUTED)
    pressure_ring = ft.ProgressRing(
        value=0.5,
        stroke_width=6,
        width=60,
        height=60,
        color=Colors.TEXT_MUTED,
        bgcolor="rgba(255,255,255,0.1)",
    )
    
    factors_column = ft.Column(controls=[
        # Default loading state - will be replaced when data loads
        ft.Container(
            content=ft.Row([
                ft.Container(width=8, height=8, bgcolor=Colors.TEXT_MUTED, border_radius=4),
                ft.Container(width=8),
                ft.Text("Loading factors...", size=11, color=Colors.TEXT_MUTED),
            ]),
            padding=ft.padding.symmetric(vertical=4),
        ),
    ], spacing=0)
    windows_column = ft.Column(controls=[], spacing=0)
    loading_indicator = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=True)
    
    def get_pressure_color(pressure: float) -> str:
        """Get color based on pressure level."""
        if pressure < 0.3:
            return Colors.SUCCESS
        elif pressure < 0.6:
            return "#F59E0B"  # Amber
        else:
            return "#EF4444"  # Red
    
    def get_pressure_label(pressure: float) -> str:
        """Get label for pressure level."""
        if pressure < 0.3:
            return "Low"
        elif pressure < 0.6:
            return "Medium"
        else:
            return "High"
    
    def create_factor_row(label: str, level: str, impact: float) -> ft.Container:
        """Create a factor display row."""
        if impact > 0.2:
            color = Colors.SUCCESS
        elif impact < -0.2:
            color = "#EF4444"
        else:
            color = "#F59E0B"
        
        return ft.Container(
            content=ft.Row([
                ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
                ft.Container(width=8),
                ft.Text(label, size=11, color=Colors.TEXT_SECONDARY, expand=True),
                ft.Text(level.capitalize(), size=11, weight=ft.FontWeight.W_500, color=color),
            ]),
            padding=ft.padding.symmetric(vertical=4),
        )
    
    def create_window_row(window: dict) -> ft.Container:
        """Create a time window display row."""
        quality = window.get("quality", 0.5)
        color = Colors.SUCCESS if quality > 0.6 else Colors.TEXT_SECONDARY
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=color),
                ft.Container(width=6),
                ft.Text(window.get("time", ""), size=12, color=Colors.TEXT_PRIMARY),
            ]),
            padding=ft.padding.symmetric(vertical=4),
        )
    
    def update_ui():
        """Update UI from state."""
        # Update pressure ring
        pressure = state["pressure"]
        color = get_pressure_color(pressure)
        
        pressure_ring.value = pressure
        pressure_ring.color = color
        pressure_value_text.value = state["pressure_label"]
        pressure_value_text.color = color
        
        # Update factors
        factors_column.controls = [
            create_factor_row(f["label"], f["level"], f["impact"])
            for f in state["factors"][:5]
        ]
        
        # Update windows
        windows_column.controls = [
            ft.Text("Available Windows", size=11, color=Colors.TEXT_MUTED),
            ft.Container(height=8),
        ] + [create_window_row(w) for w in state["windows"][:3]]
        
        # Hide loading
        loading_indicator.visible = False
        
        if state["page"]:
            state["page"].update()
        if on_change:
            try:
                on_change()
            except Exception as callback_err:
                print(f"LifeEventsPanel callback error: {callback_err}")
    
    async def load_data():
        """Load data from DecisionEngine."""
        try:
            from chronomem.decision_engine import get_decision_engine
            
            engine = get_decision_engine("default")
            result = await engine.compute()
            
            # Update state
            state["pressure"] = result.life_pressure
            state["pressure_label"] = get_pressure_label(result.life_pressure)
            
            # Extract factors from decision chain (Tier 1 only)
            factor_labels = {
                "sleep": "Sleep Quality",
                "schedule": "Schedule",
                "social": "Social Events",
                "energy": "Energy Level",
                "mood": "Mood",
            }
            
            tier1_steps = [s for s in result.decision_chain if s.tier == 1]
            state["factors"] = [
                {
                    "label": factor_labels.get(s.factor, s.factor),
                    "level": _get_level_from_value(s.value),
                    "impact": s.value,
                }
                for s in tier1_steps
            ]
            
            # Windows
            state["windows"] = result.recommended_windows
            
        except Exception as e:
            print(f"LifeEventsPanel load error: {e}")
            state["factors"] = [
                {"label": "Sleep Quality", "level": "fair", "impact": 0.0},
                {"label": "Schedule", "level": "normal", "impact": 0.0},
                {"label": "Energy Level", "level": "medium", "impact": 0.0},
            ]
            state["windows"] = []
        
        state["loading"] = False
        update_ui()
    
    def _get_level_from_value(value: float) -> str:
        """Convert impact value to level label."""
        if value > 0.3:
            return "good"
        elif value < -0.3:
            return "low"
        else:
            return "medium"
    
    def on_mount(e):
        """Called when panel is added to page."""
        if e.page:
            state["page"] = e.page
            e.page.run_task(load_data)
    
    async def quick_log(event_type: str, level: str):
        """Quick log a life event."""
        try:
            from chronomem.life_events import quick_log_event, LifeEventType
            
            type_map = {
                "sleep": LifeEventType.SLEEP,
                "energy": LifeEventType.ENERGY,
                "mood": LifeEventType.MOOD,
                "schedule": LifeEventType.SCHEDULE,
                "fatigue": LifeEventType.ENERGY,
                "time": LifeEventType.SCHEDULE,
                "social": LifeEventType.SOCIAL,
            }
            
            if event_type in type_map:
                await quick_log_event(type_map[event_type], level)
                # Reload data
                await load_data()
        except Exception as e:
            print(f"Quick log error: {e}")
    
    def on_quick_log(event_type: str, level: str):
        """Handle quick log button click."""
        if state["page"]:
            state["page"].run_task(lambda: quick_log(event_type, level))
    
    # Quick log buttons - more event types in compact layout
    quick_buttons = ft.Column([
        ft.Row([
            ft.TextButton("😴 Tired", on_click=lambda e: on_quick_log("energy", "low")),
            ft.TextButton("⚡ Energized", on_click=lambda e: on_quick_log("energy", "high")),
        ], spacing=0),
        ft.Row([
            ft.TextButton("😟 Stressed", on_click=lambda e: on_quick_log("mood", "stressed")),
            ft.TextButton("😊 Good Mood", on_click=lambda e: on_quick_log("mood", "positive")),
        ], spacing=0),
        ft.Row([
            ft.TextButton("💤 Poor Sleep", on_click=lambda e: on_quick_log("sleep", "poor")),
            ft.TextButton("📅 Busy Day", on_click=lambda e: on_quick_log("schedule", "busy")),
        ], spacing=0),
    ], spacing=2)
    
    # Pressure indicator stack
    pressure_stack = ft.Stack([
        pressure_ring,
        ft.Container(
            content=pressure_value_text,
            width=60,
            height=60,
            alignment=ft.alignment.center,
        ),
    ])
    
    # Main panel content
    panel_content = ft.Column([
        ft.Text("Life Interruptions", size=13, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
        ft.Container(height=16),
        ft.Row([pressure_stack, loading_indicator], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=16),
        ft.Text("Top Factors", size=11, color=Colors.TEXT_MUTED),
        ft.Container(height=8),
        factors_column,
        ft.Container(height=16),
        windows_column,
        ft.Container(height=12),
        ft.Divider(height=1, color=Colors.BORDER_GLASS),
        ft.Container(height=8),
        ft.Row([
            ft.Text("Quick Update", size=11, color=Colors.TEXT_MUTED),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                icon_size=16,
                icon_color=Colors.TEXT_PRIMARY,
                tooltip="Report Interruption",
                on_click=lambda e: on_open_report_dialog(e),
            ),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        quick_buttons,
    ])
    
    # Dialog logic
    def on_report_confirm(category, impact, description):
        """Handle interruption report."""
        if state["page"]:
            async def submit():
                from db.dao.interruption_dao import InterruptionDAO
                await InterruptionDAO.add(
                    source="manual",
                    content=description,
                    category=category,
                    impact_level=impact,
                )
                # Also quick log to life events for immediate pressure update
                await quick_log(category, "high" if impact > 0.6 else "medium")
                state["page"].close(report_dialog)
                
            state["page"].run_task(submit)
    
    def on_report_cancel():
        if state["page"]:
            state["page"].close(report_dialog)
            
    def on_open_report_dialog(e):
        if state["page"]:
            state["page"].open(report_dialog)

    from components.interruption_dialog import create_interruption_dialog
    report_dialog = create_interruption_dialog(on_confirm=on_report_confirm, on_cancel=on_report_cancel)
    
    # Use did_mount() lifecycle for reliable async data loading
    # (same pattern as plan_view.py)
    class LifeEventsLoader(ft.Container):
        def __init__(self, content):
            super().__init__(content=content, expand=True)
            
        def did_mount(self):
            state["page"] = self.page
            if self.page:
                self.page.run_task(load_data)
    
    panel_container = GlassCard(content=panel_content, expand=True)
    return LifeEventsLoader(content=panel_container)
