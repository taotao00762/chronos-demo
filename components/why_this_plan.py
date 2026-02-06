# ===========================================================================
# Chronos AI Learning Companion
# File: components/why_this_plan.py
# Purpose: "Why This Plan?" component showing decision rationale
# ===========================================================================

"""
Why This Plan Component

Shows the reasoning behind Principal's plan decisions:
- Memory references (profile/episodic/skill)
- Recent changes (diff)
- Editable to update memory
"""

import flet as ft
import asyncio
import threading
from typing import List, Dict, Any, Optional

from styles.tokens import Colors, Sizes
from styles.glass import GlassCard


def create_why_this_plan(
    reasons: List[Dict[str, Any]] = None,
    changes: List[Dict[str, Any]] = None,
    on_edit_memory: callable = None,
    on_refresh: callable = None,
) -> ft.Container:
    """
    Create "Why This Plan?" decision rationale card.
    
    Args:
        reasons: List of memory references [{memory_id, type, summary, confidence}]
        changes: List of changes [{action, description}]
        on_edit_memory: Callback for editing a memory
        on_refresh: Callback to refresh reasons
    """
    
    # State
    state = {
        "reasons": reasons or [],
        "changes": changes or [],
        "loading": False,
        "expanded": False,
    }
    
    # Loading indicator
    loading_row = ft.Row(
        controls=[
            ft.ProgressRing(width=16, height=16, stroke_width=2),
            ft.Container(width=8),
            ft.Text("Analyzing decision...", size=11, color=Colors.TEXT_MUTED),
        ],
        visible=False,
    )
    
    # Reason items container
    reasons_col = ft.Column(spacing=6)
    changes_col = ft.Column(spacing=4)
    
    def _create_reason_chip(reason: Dict[str, Any]) -> ft.Container:
        """Create a single reason chip."""
        type_colors = {
            "profile": ("#3B82F6", ft.Icons.PERSON_OUTLINED),
            "episodic": ("#FB923C", ft.Icons.EVENT_OUTLINED),
            "skill": ("#22C55E", ft.Icons.PSYCHOLOGY_OUTLINED),
        }
        color, icon = type_colors.get(reason.get("type", "profile"), ("#888", ft.Icons.MEMORY))
        confidence = reason.get("confidence", 0.8)
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=14, color=color),
                    ft.Container(width=6),
                    ft.Text(
                        reason.get("summary", "")[:60] + ("..." if len(reason.get("summary", "")) > 60 else ""),
                        size=11,
                        color=Colors.TEXT_SECONDARY,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Text(f"{int(confidence * 100)}%", size=9, color=color),
                        padding=ft.padding.symmetric(horizontal=4, vertical=1),
                        bgcolor=f"rgba(255,255,255,0.05)",
                        border_radius=4,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_size=12,
                        icon_color=Colors.TEXT_MUTED,
                        tooltip="Edit this memory",
                        on_click=lambda e, m=reason: on_edit_memory(m) if on_edit_memory else None,
                    ) if on_edit_memory else ft.Container(),
                ],
                spacing=0,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            bgcolor=f"rgba(255,255,255,0.03)",
            border=ft.border.all(1, f"rgba(255,255,255,0.1)"),
            border_radius=8,
        )
    
    def _create_change_item(change: Dict[str, Any]) -> ft.Container:
        """Create a change diff item."""
        action = change.get("action", "~")
        action_colors = {"+": Colors.SUCCESS, "-": "#EF4444", "~": Colors.TEXT_SECONDARY}
        color = action_colors.get(action, Colors.TEXT_MUTED)
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(action, size=12, color=color, weight=ft.FontWeight.BOLD),
                    ft.Container(width=8),
                    ft.Text(change.get("description", ""), size=11, color=Colors.TEXT_SECONDARY),
                ],
            ),
            padding=ft.padding.symmetric(vertical=2),
        )
    
    def update_display():
        """Update the display."""
        loading_row.visible = state["loading"]
        
        # Update reasons
        reasons_col.controls = [
            _create_reason_chip(r) for r in state["reasons"][:4]
        ] if state["reasons"] else [
            ft.Text("No memory references yet.", size=11, color=Colors.TEXT_MUTED, italic=True)
        ]
        
        # Update changes
        changes_col.controls = [
            _create_change_item(c) for c in state["changes"][:3]
        ] if state["changes"] else []
        
        try:
            reasons_col.update()
            changes_col.update()
            loading_row.update()
        except Exception:
            pass
    
    async def load_reasons():
        """Load reasons from PrincipalLens."""
        state["loading"] = True
        update_display()
        
        try:
            from chronomem.lens import get_principal_lens
            lens = get_principal_lens()
            context = await lens.get_context()
            
            # Convert to reasons format
            reasons = []
            
            # Add recent episodes
            for ep in context.get("recent_episodes", [])[:2]:
                reasons.append({
                    "memory_id": ep.get("memory_id"),
                    "type": "episodic",
                    "summary": ep.get("summary", ""),
                    "confidence": ep.get("confidence", 0.7),
                })
            
            # Add weak skills
            for sk in context.get("weak_skills", [])[:2]:
                reasons.append({
                    "memory_id": sk.get("memory_id"),
                    "type": "skill",
                    "summary": sk.get("summary", ""),
                    "confidence": sk.get("confidence", 0.5),
                })
            
            # Add profile summary as a reason
            if context.get("profile_summary") and context["profile_summary"] != "No preference data available.":
                reasons.insert(0, {
                    "memory_id": None,
                    "type": "profile",
                    "summary": context["profile_summary"][:80],
                    "confidence": 0.9,
                })
            
            state["reasons"] = reasons
            
            # Default changes if none provided
            if not state["changes"]:
                state["changes"] = [
                    {"action": "~", "description": "Mode based on recent activity"},
                ]
            
        except Exception as e:
            print(f"Why this plan load error: {e}")
            state["reasons"] = []
        finally:
            state["loading"] = False
            update_display()
    
    def handle_refresh(e):
        """Handle refresh button click."""
        def run():
            asyncio.run(load_reasons())
        threading.Thread(target=run, daemon=True).start()
    
    # Header
    header = ft.Row(
        controls=[
            ft.Icon(ft.Icons.LIGHTBULB_OUTLINED, size=16, color="#F59E0B"),
            ft.Container(width=6),
            ft.Text("Why This Plan?", size=12, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.REFRESH_OUTLINED,
                icon_size=14,
                icon_color=Colors.TEXT_MUTED,
                tooltip="Refresh",
                on_click=handle_refresh,
            ),
        ],
    )
    
    # Changes section (if any)
    changes_section = ft.Column(
        controls=[
            ft.Container(height=8),
            ft.Text("Recent Changes", size=10, color=Colors.TEXT_MUTED),
            ft.Container(height=4),
            changes_col,
        ],
        visible=bool(state["changes"]),
    )
    
    # Container
    content = ft.Column(
        controls=[
            header,
            ft.Container(height=8),
            loading_row,
            reasons_col,
            changes_section,
        ],
        spacing=0,
    )
    
    card = GlassCard(content=content)
    
    # Initial load if no reasons provided
    if not reasons:
        def init_load():
            asyncio.run(load_reasons())
        threading.Thread(target=init_load, daemon=True).start()
    else:
        update_display()
    
    return card
