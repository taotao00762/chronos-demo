# ===========================================================================
# Chronos AI Learning Companion
# File: components/daily_briefing.py
# Purpose: Daily Briefing Modal - Morning decision ceremony
# ===========================================================================

"""
Daily Briefing Modal

The "morning briefing" experience that makes users feel like they're
interacting with an intelligent system. Contains:
1. Yesterday Snapshot (completion, interruptions, best window, stuck point)
2. Principal Proposal (mode + diff + benefit)
3. Your Call (3-way decision: Recovery / Standard / Sprint)
"""

import flet as ft
import asyncio
import threading
from datetime import datetime
from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer
from services.briefing_service import BriefingService


# =============================================================================
# Section Components
# =============================================================================

def create_stat_item(label: str, value: str, icon: str = None) -> ft.Container:
    """Create a single stat item for Yesterday Snapshot."""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(icon, size=14, color=Colors.TEXT_MUTED) if icon else ft.Container(),
                        ft.Container(width=4) if icon else ft.Container(),
                        ft.Text(label, size=11, color=Colors.TEXT_MUTED),
                    ],
                    spacing=0,
                ),
                ft.Text(value, size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
        expand=True,
    )


def create_diff_item(icon: str, text: str, color: str = Colors.TEXT_SECONDARY) -> ft.Container:
    """Create a single diff item."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(icon, size=14, color=color),
                ft.Container(width=8),
                ft.Text(text, size=12, color=Colors.TEXT_SECONDARY),
            ],
            spacing=0,
        ),
        padding=ft.padding.symmetric(vertical=4),
    )


def create_decision_card(
    title: str,
    description: str,
    mode: str,
    is_recommended: bool = False,
    on_click: callable = None,
) -> ft.Container:
    """Create a decision card for mode selection."""
    mode_colors = {
        "recovery": "#10B981",
        "standard": "#3B82F6",
        "sprint": "#F59E0B",
    }
    color = mode_colors.get(mode, Colors.TEXT_PRIMARY)
    
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=color),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text("Recommended", size=10, color=Colors.BG_PRIMARY),
                            bgcolor=color,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=10,
                            visible=is_recommended,
                        ),
                    ],
                ),
                ft.Container(height=4),
                ft.Text(description, size=11, color=Colors.TEXT_MUTED),
            ],
            spacing=0,
        ),
        padding=16,
        bgcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.08)" if is_recommended else f"rgba(255,255,255,0.03)",
        border=ft.border.all(1, color if is_recommended else Colors.BORDER_GLASS),
        border_radius=12,
        on_click=on_click,
        ink=True,
        expand=True,
    )


# =============================================================================
# Daily Briefing Content
# =============================================================================

def create_briefing_content(on_accept: callable = None, on_customize: callable = None) -> ft.Container:
    """Create the Daily Briefing modal content."""
    
    # State for dynamic data
    state = {"loading": True, "data": None}
    
    # === Section 1: Yesterday Snapshot (Dynamic) ===
    snapshot_stats = ft.Row(spacing=16)
    
    yesterday_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Yesterday Snapshot", size=12, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                ft.Container(height=12),
                snapshot_stats,
            ],
        ),
        padding=16,
        bgcolor=f"rgba(255,255,255,0.03)",
        border_radius=12,
    )
    
    # === Section 2: Principal Proposal (Dynamic) ===
    proposal_text = ft.Text(
        "Loading proposal...",
        size=13,
        color=Colors.TEXT_SECONDARY,
        italic=True,
    )
    
    changes_list = ft.Column(spacing=0)
    reasons_list = ft.Column(spacing=4)
    
    benefit_row = ft.Row(
        controls=[
            ft.Icon(ft.Icons.TRENDING_UP_ROUNDED, size=14, color=Colors.SUCCESS),
            ft.Container(width=4),
            ft.Text(
                "Loading...",
                size=11,
                color=Colors.SUCCESS,
            ),
        ],
    )
    
    proposal_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Principal Proposal", size=12, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                ft.Container(height=8),
                proposal_text,
                ft.Container(height=8),
                ft.Text("Reasons", size=11, color=Colors.TEXT_MUTED),
                ft.Container(height=4),
                reasons_list,
                ft.Container(height=12),
                ft.Text("Changes", size=11, color=Colors.TEXT_MUTED),
                ft.Container(height=4),
                changes_list,
                ft.Container(height=8),
                benefit_row,
            ],
        ),
        padding=16,
        bgcolor=f"rgba(255,255,255,0.03)",
        border_radius=12,
    )
    
    # === Section 3: Your Call (Dynamic) ===
    decision_cards = ft.Row(spacing=12)
    
    decision_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Your Call", size=12, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                ft.Container(height=12),
                decision_cards,
            ],
        ),
    )
    
    # === Async Data Loading ===
    async def load_briefing_data():
        """Load real briefing data."""
        try:
            service = BriefingService()
            data = await service.generate()
            state["data"] = data
            state["loading"] = False
            
            snapshot = data.get("snapshot", {})
            proposal = data.get("proposal", {})
            
            # Update snapshot stats
            snapshot_stats.controls.clear()
            snapshot_stats.controls.extend([
                create_stat_item("Completion", snapshot.get("completion", "--"), ft.Icons.CHECK_CIRCLE_OUTLINE),
                create_stat_item("Interruptions", str(snapshot.get("interruptions", 0)), ft.Icons.NOTIFICATION_IMPORTANT_OUTLINED),
                create_stat_item("Best Window", snapshot.get("best_window", "--"), ft.Icons.SCHEDULE),
                create_stat_item("Stuck Point", str(snapshot.get("stuck_point", "None"))[:15], ft.Icons.ERROR_OUTLINE),
            ])
            
            # Update proposal text
            mode = proposal.get("mode", "standard")
            proposal_text.value = f"Today is {mode.capitalize()} mode based on yesterday's data."

            # Update reasons
            reasons_list.controls.clear()
            reasons = proposal.get("decision_reasons", [])[:3]
            if reasons:
                for reason in reasons:
                    reasons_list.controls.append(
                        ft.Text(
                            f"- {reason.get('summary', '')}",
                            size=11,
                            color=Colors.TEXT_SECONDARY,
                        )
                    )
            else:
                reasons_list.controls.append(
                    ft.Text("No specific reasons available.", size=11, color=Colors.TEXT_MUTED, italic=True)
                )
            
            # Update changes
            changes_list.controls.clear()
            for change in proposal.get("changes", []):
                color = Colors.SUCCESS if change.get("type") == "add" else Colors.TEXT_SECONDARY
                changes_list.controls.append(
                    create_diff_item(change.get("icon", "-"), change.get("text", ""), color)
                )
            
            # Update benefit
            if len(benefit_row.controls) > 2:
                benefit_row.controls[2].value = proposal.get("benefit", "")
            
            # Update decision cards
            decision_cards.controls.clear()
            for mode_name, desc in [("Recovery", "Low friction, gentle pace"), 
                                     ("Standard", "Balanced approach"), 
                                     ("Sprint", "High intensity push")]:
                is_rec = mode_name.lower() == mode
                decision_cards.controls.append(
                    create_decision_card(
                        mode_name,
                        desc,
                        mode_name.lower(),
                        is_recommended=is_rec,
                        on_click=on_accept,
                    )
                )
                if mode_name != "Sprint":
                    decision_cards.controls.append(ft.Container(width=12))
            
            print(f"Briefing UI updated: mode={mode}")
            
        except Exception as e:
            print(f"Briefing load error: {e}")
            import traceback
            traceback.print_exc()
            state["loading"] = False
    
    # === Action Buttons ===
    actions_row = ft.Row(
        controls=[
            ft.TextButton(
                text="Customize",
                icon=ft.Icons.TUNE_ROUNDED,
                on_click=on_customize,
                style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY),
            ),
            ft.Container(expand=True),
            ft.OutlinedButton(
                text="Keep Original",
                style=ft.ButtonStyle(
                    color=Colors.TEXT_SECONDARY,
                    side=ft.BorderSide(1, Colors.BORDER_GLASS),
                ),
            ),
            ft.Container(width=8),
            ft.FilledButton(
                text="Accept & Generate",
                icon=ft.Icons.CHECK_ROUNDED,
                on_click=on_accept,
                style=ft.ButtonStyle(
                    bgcolor=Colors.TEXT_PRIMARY,
                    color=Colors.BG_PRIMARY,
                ),
            ),
        ],
    )
    
    # === Main Content ===
    date_text = ft.Text(datetime.now().strftime("%A, %b %d"), size=12, color=Colors.TEXT_MUTED)
    
    main_content = ft.Container(
        content=ft.Column(
            controls=[
                # Header
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.WB_SUNNY_ROUNDED, size=24, color="#F59E0B"),
                        ft.Container(width=8),
                        ft.Text("Daily Briefing", size=20, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                        ft.Container(expand=True),
                        date_text,
                    ],
                ),
                ft.Container(height=20),
                yesterday_section,
                ft.Container(height=12),
                proposal_section,
                ft.Container(height=16),
                decision_section,
                ft.Container(height=20),
                actions_row,
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        width=600,
        padding=24,
        bgcolor=Colors.BG_CARD,
        border_radius=20,
        border=ft.border.all(1, Colors.BORDER_GLASS),
    )
    
    # Start loading in background thread
    def run_async_load():
        try:
            asyncio.run(load_briefing_data())
            # Update UI after loading
            try:
                main_content.update()
            except Exception:
                pass
        except Exception as e:
            print(f"Briefing init error: {e}")
    
    threading.Thread(target=run_async_load, daemon=True).start()
    
    return main_content
