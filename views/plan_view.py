# ===========================================================================
# Chronos AI Learning Companion
# File: views/plan_view.py
# Purpose: Plan Module - Director's Stage with intelligent features
# ===========================================================================

"""
Plan View - The Director's Main Stage

Features:
- Plan Header (Mode + Reason Chips + Actions)
- Today Tab: 3-column layout (Input/Decision/Execution)
- Changes Tab: Diff history
- Strategy Tab: Tuning console
"""

import flet as ft
from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer, GlassCard
from components.plan_header import create_plan_header
# NOTE: create_why_this_plan removed - now using create_decision_panel for right column
from components.life_events_panel import create_life_events_panel
from i18n.texts import TXT


# =============================================================================
# Today Tab - 3 Column Layout
# =============================================================================

# NOTE: create_interruption_panel is now replaced by create_life_events_panel
# from components/life_events_panel.py which loads dynamic data from DecisionEngine


def create_timeline_panel(shared_context: dict = None) -> ft.Container:
    """Middle column: Adaptive Timeline with AI generation."""
    
    # State for plan items and decision tracking
    state = {"plan": [], "loading": False, "page": None, "decision_id": None, "accepted": False}
    
    # Plan items container
    plan_list = ft.Column(controls=[], spacing=8, scroll=ft.ScrollMode.AUTO)
    
    # Loading indicator
    loading_indicator = ft.Column(
        controls=[
            ft.ProgressRing(width=24, height=24, stroke_width=3),
            ft.Container(height=8),
            ft.Text("Generating plan...", size=12, color=Colors.TEXT_MUTED),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False,
    )
    
    # Empty state
    empty_state = ft.Column(
        controls=[
            ft.Icon(ft.Icons.TIMELINE_ROUNDED, size=48, color=Colors.TEXT_MUTED),
            ft.Container(height=12),
            ft.Text("No tasks yet", size=14, color=Colors.TEXT_SECONDARY),
            ft.Text(
                "Generate a plan based on your learning history",
                size=12,
                color=Colors.TEXT_MUTED,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def _get_plan_context() -> dict:
        if isinstance(shared_context, dict):
            return shared_context.get("plan_context") or {}
        return {}

    def _normalize_pressure(plan_context: dict) -> float:
        try:
            return float(plan_context.get("life_pressure", 0.5))
        except Exception:
            return 0.5

    def _pressure_label(pressure: float) -> str:
        if pressure >= 0.7:
            return "High"
        if pressure >= 0.4:
            return "Medium"
        return "Low"

    def _get_plan_constraints(pressure: float, mode: str) -> dict:
        if pressure >= 0.7:
            task_min, task_max = 2, 3
            dur_min, dur_max = 15, 25
            tone = "low friction review"
        elif pressure >= 0.4:
            task_min, task_max = 3, 4
            dur_min, dur_max = 20, 35
            tone = "balanced pacing"
        else:
            task_min, task_max = 4, 5
            dur_min, dur_max = 25, 45
            tone = "challenge-friendly"

        if mode == "recovery":
            focus = "review and light practice"
        elif mode == "sprint":
            focus = "learn and practice"
        else:
            focus = "balanced learn/review/practice"

        return {
            "task_min": task_min,
            "task_max": task_max,
            "dur_min": dur_min,
            "dur_max": dur_max,
            "tone": tone,
            "focus": focus,
        }

    def _build_fallback_plan(pressure: float, mode: str) -> list:
        constraints = _get_plan_constraints(pressure, mode)
        duration = constraints["dur_min"]

        if pressure >= 0.7:
            tasks = [
                {"topic": "Light review of key concepts", "duration_min": duration, "type": "review"},
                {"topic": "Quick practice set", "duration_min": duration, "type": "practice"},
            ]
        elif pressure >= 0.4:
            tasks = [
                {"topic": "Review recent topics", "duration_min": duration, "type": "review"},
                {"topic": "Practice core problems", "duration_min": duration, "type": "practice"},
                {"topic": "Summarize takeaways", "duration_min": duration, "type": "review"},
            ]
        else:
            tasks = [
                {"topic": "Learn a new concept", "duration_min": duration, "type": "learn"},
                {"topic": "Practice core problems", "duration_min": duration, "type": "practice"},
                {"topic": "Review and reflect", "duration_min": duration, "type": "review"},
                {"topic": "Challenge problem set", "duration_min": duration, "type": "practice"},
            ]

        if mode == "sprint" and tasks:
            tasks[0]["topic"] = "Deep dive learning block"
        elif mode == "recovery" and tasks:
            tasks[0]["topic"] = "Gentle review block"

        return tasks[:constraints["task_max"]]
    
    def create_task_item(task: dict) -> ft.Container:
        """Create a task item card."""
        return ft.Container(
            content=ft.Row([
                ft.Checkbox(value=False, fill_color=Colors.TEXT_PRIMARY),
                ft.Column([
                    ft.Text(task.get("topic", "Task"), size=13, color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.W_500),
                    ft.Text(f"{task.get('duration_min', 30)} min", size=11, color=Colors.TEXT_MUTED),
                ], spacing=2, expand=True),
            ]),
            padding=12,
            bgcolor=f"rgba(255,255,255,0.03)",
            border=ft.border.all(1, Colors.BORDER_GLASS),
            border_radius=10,
        )
    
    def update_display():
        """Update the display based on state."""
        if state["loading"]:
            loading_indicator.visible = True
            empty_state.visible = False
            plan_list.visible = False
        elif state["plan"]:
            loading_indicator.visible = False
            empty_state.visible = False
            plan_list.visible = True
            plan_list.controls = [create_task_item(t) for t in state["plan"]]
        else:
            loading_indicator.visible = False
            empty_state.visible = True
            plan_list.visible = False
        
        if state["page"]:
            state["page"].update()
    
    async def generate_plan():
        """Generate plan using Gemini with ChronoMem context."""
        state["loading"] = True
        update_display()
        plan_context = _get_plan_context()
        if not plan_context:
            try:
                from services.principal_service import get_principal_context_service
                principal = get_principal_context_service()
                plan_context = await principal.get_plan_context()
                if isinstance(shared_context, dict):
                    shared_context["plan_context"] = plan_context
            except Exception:
                plan_context = {}
        mode = str(plan_context.get("mode", "standard") or "standard").lower()
        pressure = _normalize_pressure(plan_context)
        pressure_label = _pressure_label(pressure)
        windows = plan_context.get("recommended_windows") or []
        windows_text = ", ".join([w.get("time", "") for w in windows if w.get("time")]) or "Not specified"
        reasons = plan_context.get("reasons") or []
        topics = plan_context.get("topics") or []
        constraints = _get_plan_constraints(pressure, mode)

        try:
            from db.dao import ReceiptDAO
            from services.gemini_service import create_gemini_service
            import json
            import re
            
            # Get recent sessions for context
            receipts = await ReceiptDAO.list_recent(limit=5)
            
            # Get ChronoMem context
            memory_context = ""
            try:
                from chronomem.service import get_chronomem_service
                mem = get_chronomem_service()
                
                # Get relevant memories
                topics = []
                for r in receipts:
                    t = r.get("topics_json", [])
                    if isinstance(t, list):
                        topics.extend(t)
                
                query = " ".join(topics[:5]) if topics else "learning study"
                ctx = await mem.get_context_for_plan(topics[:5])
                
                if ctx.get("personal_memories"):
                    memory_context += "\nUser preferences:\n"
                    for m in ctx["personal_memories"][:3]:
                        memory_context += f"- {m['content']}\n"
                
                if ctx.get("task_strategies"):
                    memory_context += "\nEffective strategies:\n"
                    for s in ctx["task_strategies"][:2]:
                        memory_context += f"- {s['strategy']} (for {s['topic']})\n"
            except Exception as ex:
                print(f"ChronoMem context failed: {ex}")
            
            service = create_gemini_service()
            if service:
                # Build context
                session_context = "\n".join([
                    f"- Topics: {r.get('topics_json', [])}, Summary: {r.get('summary', '')}"
                    for r in receipts
                ]) if receipts else "No previous sessions"

                prompt = f"""Based on the user's learning history, create a personalized study plan for today.

Decision context:
- Recommended mode: {mode}
- Life pressure: {pressure_label} ({pressure:.2f})
- Focus windows: {windows_text}
- Primary reason: {reasons[0] if reasons else "Not specified"}
- Focus topics: {', '.join(topics[:3]) if topics else "Not specified"}

Plan constraints:
- Task count: {constraints['task_min']}-{constraints['task_max']}
- Duration per task: {constraints['dur_min']}-{constraints['dur_max']} min
- Style: {constraints['tone']}
- Emphasis: {constraints['focus']}

Recent sessions:
{session_context}
{memory_context}

Return JSON array:
[{{"topic": "...", "duration_min": 30, "type": "review|learn|practice"}}]

Return ONLY valid JSON array."""
                
                response = await service.send_message(prompt)
                
                # Parse JSON array
                match = re.search(r'\[[\s\S]*\]', response)
                if match:
                    state["plan"] = json.loads(match.group())[:5]
                    print(f"Generated {len(state['plan'])} tasks")
                    
                    # Save decision to database for historical learning
                    try:
                        from db.dao.decision_dao import DecisionDAO
                        from datetime import date
                        
                        decision_id = await DecisionDAO.create(
                            date=date.today().isoformat(),
                            proposal={
                                "mode": mode,
                                "plan": state["plan"],
                                "life_pressure": pressure,
                                "pressure_label": pressure_label,
                                "recommended_windows": windows,
                                "reasons": reasons,
                                "topics": topics,
                            },
                            final_plan=state["plan"],
                            diff={},
                            user_action_type="pending",  # Will be updated on accept
                            user_id="default",
                        )
                        state["decision_id"] = decision_id
                        state["accepted"] = False
                        print(f"Decision saved: {decision_id}")
                    except Exception as dec_err:
                        print(f"Decision save failed: {dec_err}")
                else:
                    state["plan"] = _build_fallback_plan(pressure, mode)
            else:
                state["plan"] = _build_fallback_plan(pressure, mode)
        except Exception as e:
            print(f"Plan generation failed: {e}")
            state["plan"] = _build_fallback_plan(pressure, mode)
        finally:
            state["loading"] = False
            update_display()
    
    async def accept_plan():
        """Record user acceptance of the plan."""
        if state["decision_id"] and not state["accepted"]:
            try:
                from db.connection import get_db
                db = await get_db()
                await db.execute(
                    "UPDATE decision_record SET user_action_type = ? WHERE decision_id = ?",
                    ("accept", state["decision_id"])
                )
                await db.commit()
                state["accepted"] = True
                print(f"Plan accepted: {state['decision_id']}")
            except Exception as e:
                print(f"Accept plan failed: {e}")

    
    def on_generate(e):
        """Handle generate button click."""
        if state["page"] is None:
            if hasattr(e, "page"):
                state["page"] = e.page
            elif hasattr(e, "control") and hasattr(e.control, "page"):
                state["page"] = e.control.page
        
        if state["page"] and not state["loading"]:
            state["page"].run_task(generate_plan)
    
    generate_btn = ft.FilledButton(
        text="Generate Today Plan",
        icon=ft.Icons.AUTO_AWESOME_ROUNDED,
        style=ft.ButtonStyle(bgcolor=Colors.TEXT_PRIMARY, color=Colors.BG_PRIMARY),
        on_click=on_generate,
    )
    
    def on_accept(e):
        """Handle accept button click."""
        if state["page"]:
            async def do_accept():
                await accept_plan()
                # Update button visibility
                accept_btn.visible = False
                accepted_label.visible = True
                state["page"].update()
            state["page"].run_task(do_accept)
    
    accept_btn = ft.FilledButton(
        text="✓ Accept Plan",
        style=ft.ButtonStyle(bgcolor=Colors.SUCCESS, color="#FFFFFF"),
        on_click=on_accept,
        visible=False,  # Initially hidden
    )
    
    accepted_label = ft.Container(
        content=ft.Text("✓ Plan Accepted", size=12, color=Colors.SUCCESS),
        visible=False,
    )
    
    # Update update_display to show/hide accept button
    original_update = update_display
    def update_display():
        original_update()
        if state["plan"] and not state["loading"]:
            accept_btn.visible = not state["accepted"]
            accepted_label.visible = state["accepted"]
        else:
            accept_btn.visible = False
            accepted_label.visible = False
    
    return GlassCard(
        content=ft.Column(
            controls=[
                ft.Text("Adaptive Timeline", size=13, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                ft.Container(height=12),
                loading_indicator,
                empty_state,
                plan_list,
                ft.Container(expand=True),
                ft.Row([generate_btn, accept_btn, accepted_label], spacing=8),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
    )


def create_decision_panel() -> tuple:
    """Right column: Plan Diff + Decision Cards."""
    
    # Diff items
    def create_diff(icon: str, text: str, color: str = Colors.TEXT_SECONDARY) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Text(icon, size=12, color=color),
                ft.Container(width=8),
                ft.Text(text, size=11, color=Colors.TEXT_SECONDARY),
            ]),
            padding=ft.padding.symmetric(vertical=4),
        )
    
    changes_list = ft.Column(spacing=0)
    diff_section = ft.Column(
        controls=[
            ft.Text("Plan Changes", size=12, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
            ft.Container(height=8),
            changes_list,
        ],
        spacing=0,
    )
    
    # Decision cards
    def create_mode_card(title: str, desc: str, mode: str) -> dict:
        colors = {"recovery": "#10B981", "standard": "#3B82F6", "sprint": "#F59E0B"}
        c = colors.get(mode, Colors.TEXT_PRIMARY)
        badge = ft.Container(
            content=ft.Text("✓", size=10, color=Colors.BG_PRIMARY),
            width=16, height=16, bgcolor=c, border_radius=8,
            alignment=ft.alignment.center, visible=False,
        )
        
        card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=c),
                    ft.Container(expand=True),
                    badge,
                ]),
                ft.Text(desc, size=10, color=Colors.TEXT_MUTED),
            ], spacing=4),
            padding=12,
            bgcolor="rgba(255,255,255,0.03)",
            border=ft.border.all(1, Colors.BORDER_GLASS),
            border_radius=10,
            ink=True,
        )
        return {"mode": mode, "card": card, "badge": badge, "color": c}
    
    mode_cards = [
        create_mode_card("Recovery", "Low friction", "recovery"),
        create_mode_card("Standard", "Balanced", "standard"),
        create_mode_card("Sprint", "High push", "sprint"),
    ]
    
    decision_section = ft.Column(
        controls=[
            ft.Text("Today's Mode", size=12, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
            ft.Container(height=8),
            mode_cards[0]["card"],
            ft.Container(height=8),
            mode_cards[1]["card"],
            ft.Container(height=8),
            mode_cards[2]["card"],
        ],
        spacing=0,
    )
    
    panel = GlassCard(
        content=ft.Column([
            diff_section,
            ft.Container(height=20),
            decision_section,
        ]),
        expand=True,
    )
    
    def update_panel(context: dict) -> None:
        ctx = context or {}
        mode = str(ctx.get("mode", "standard") or "standard").lower()
        reasons = ctx.get("reasons") or []
        windows = ctx.get("recommended_windows") or []
        focus_window = windows[0].get("time") if windows else None
        
        items = []
        items.append(create_diff("≈", f"Mode: {mode.capitalize()}"))
        if focus_window:
            items.append(create_diff("↔", f"Focus window: {focus_window}"))
        if reasons:
            items.append(create_diff("+", reasons[0], Colors.SUCCESS))
        
        if not items:
            items.append(create_diff("·", "No decision data yet", Colors.TEXT_MUTED))
        
        changes_list.controls = items
        
        for card in mode_cards:
            is_recommended = card["mode"] == mode
            card["badge"].visible = is_recommended
            card["card"].bgcolor = (
                f"rgba({int(card['color'][1:3],16)},{int(card['color'][3:5],16)},{int(card['color'][5:7],16)},0.1)"
                if is_recommended else "rgba(255,255,255,0.03)"
            )
            card["card"].border = ft.border.all(
                1, card["color"] if is_recommended else Colors.BORDER_GLASS
            )
    
    return panel, update_panel


def create_today_content() -> ft.Container:
    """Today tab: top status bar + 3-column layout."""
    shared_context = {"plan_context": None}
    today_state = {"page": None, "loading": False}
    
    def _pressure_label(pressure: float) -> str:
        if pressure >= 0.7:
            return "High"
        if pressure >= 0.4:
            return "Medium"
        return "Low"
    
    def _energy_label(level: str) -> str:
        level = (level or "medium").lower()
        if level in ("high", "good", "positive"):
            return "High"
        if level in ("low", "poor", "stressed"):
            return "Low"
        return "Medium"
    
    def on_start_session(e):
        if e.page:
            e.page.go("/tutor")
    
    status_bar = ft.Container(
        content=create_plan_header(
            mode="standard",
            interruptions="Medium",
            focus_window="--",
            energy="Medium",
            on_start=on_start_session,
        ),
        margin=ft.margin.only(bottom=16),
    )
    
    decision_panel, update_decision_panel = create_decision_panel()
    update_decision_panel({})
    
    async def load_today_context(force_refresh: bool = False):
        if today_state["loading"]:
            return
        today_state["loading"] = True
        try:
            from services.principal_service import get_principal_context_service
            from chronomem.life_events import get_life_event_collector, LifeEventType
            from db.dao.interruption_dao import InterruptionDAO
            
            principal = get_principal_context_service()
            plan_context = await principal.get_plan_context(force_refresh=force_refresh)
            
            collector = get_life_event_collector("default")
            events = await collector.get_today_events()
            energy_level = "medium"
            for ev in events:
                if ev.event_type == LifeEventType.ENERGY:
                    energy_level = ev.level or "medium"
                    break
            
            interruptions = await InterruptionDAO.list_today("default")
            plan_context["interruptions_count"] = len(interruptions)
            plan_context["energy_level"] = energy_level
            
            shared_context["plan_context"] = plan_context
            
            mode = str(plan_context.get("mode", "standard") or "standard").lower()
            pressure = float(plan_context.get("life_pressure", 0.5) or 0.5)
            focus_window = ""
            windows = plan_context.get("recommended_windows") or []
            if windows:
                focus_window = windows[0].get("time", "") or ""
            if not focus_window:
                focus_window = "--"
            
            status_bar.content = create_plan_header(
                mode=mode,
                interruptions=_pressure_label(pressure),
                focus_window=focus_window,
                energy=_energy_label(energy_level),
                on_start=on_start_session,
            )
            update_decision_panel(plan_context)
        except Exception as e:
            print(f"Today context load error: {e}")
            status_bar.content = create_plan_header(
                mode="standard",
                interruptions="Medium",
                focus_window="--",
                energy="Medium",
                on_start=on_start_session,
            )
            update_decision_panel({"mode": "standard"})
        finally:
            today_state["loading"] = False
            if today_state["page"]:
                today_state["page"].update()
    
    def refresh_today_context():
        if today_state["page"]:
            today_state["page"].run_task(load_today_context)
    
    # === 3-Column Layout ===
    right_col = ft.Column(
        controls=[decision_panel],
        spacing=0,
        expand=True,
    )
    
    three_cols = ft.Row(
        controls=[
            ft.Container(content=create_life_events_panel(on_change=refresh_today_context), expand=1),
            ft.Container(width=Sizes.CARD_GAP),
            ft.Container(content=create_timeline_panel(shared_context), expand=1.5),
            ft.Container(width=Sizes.CARD_GAP),
            ft.Container(content=right_col, expand=1),
        ],
        expand=True,
    )
    
    content = ft.Column(
        controls=[
            status_bar,
            three_cols,
        ],
        expand=True,
        spacing=0,
    )
    
    class TodayLoader(ft.Container):
        def __init__(self, content_control):
            super().__init__(content=content_control, expand=True)
        
        def did_mount(self):
            today_state["page"] = self.page
            if self.page:
                self.page.run_task(load_today_context)
    
    return TodayLoader(content)


# =============================================================================
# Changes Tab
# =============================================================================

def create_changes_content() -> ft.Container:
    """Changes tab: Diff history list."""
    
    def create_change_item(date: str, summary: str, diff_count: int) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(date, size=12, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
                    ft.Text(summary, size=11, color=Colors.TEXT_MUTED),
                ], spacing=2, expand=True),
                ft.Container(
                    content=ft.Text(f"{diff_count} changes", size=10, color=Colors.TEXT_SECONDARY),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=f"rgba(255,255,255,0.05)",
                    border_radius=8,
                ),
            ]),
            padding=12,
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_GLASS)),
        )
    
    return GlassCard(
        content=ft.Column([
            ft.Text("Change History", size=13, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            ft.Container(height=12),
            create_change_item("Today, 09:15", "Mode adjusted to Recovery", 3),
            create_change_item("Yesterday", "Focus block optimized", 2),
            create_change_item("Jan 8", "Added warm-up routine", 1),
        ]),
        expand=True,
    )


# =============================================================================
# Strategy Tab
# =============================================================================

def create_strategy_content() -> ft.Container:
    """Strategy tab: Tuning console."""
    
    def create_slider_row(label: str, value: float, left: str, right: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=12, weight=ft.FontWeight.W_500, color=Colors.TEXT_PRIMARY),
                ft.Container(height=8),
                ft.Slider(value=value, min=0, max=1, divisions=10, active_color=Colors.TEXT_PRIMARY),
                ft.Row([
                    ft.Text(left, size=10, color=Colors.TEXT_MUTED),
                    ft.Container(expand=True),
                    ft.Text(right, size=10, color=Colors.TEXT_MUTED),
                ]),
            ]),
            padding=ft.padding.symmetric(vertical=8),
        )
    
    return GlassCard(
        content=ft.Column([
            ft.Text("Learning Strategy", size=13, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            ft.Container(height=16),
            create_slider_row("Difficulty Preference", 0.6, "Easy", "Challenging"),
            create_slider_row("Session Length", 0.5, "Short (15m)", "Long (60m)"),
            create_slider_row("Review Frequency", 0.7, "Minimal", "Frequent"),
            ft.Container(height=16),
            ft.FilledButton(
                text="Save Strategy",
                icon=ft.Icons.SAVE_ROUNDED,
                style=ft.ButtonStyle(bgcolor=Colors.TEXT_PRIMARY, color=Colors.BG_PRIMARY),
            ),
        ]),
        expand=True,
    )


# =============================================================================
# Segmented Control
# =============================================================================

def create_segmented_control(tabs: list, selected_index: int, on_change: callable) -> ft.Container:
    def create_segment(label: str, index: int) -> ft.Container:
        is_selected = index == selected_index
        return ft.Container(
            content=ft.Text(
                label, size=Sizes.FONT_SIZE_SM,
                weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL,
                color=Colors.TEXT_PRIMARY if is_selected else Colors.TEXT_SECONDARY,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor=f"rgba(255,255,255,0.1)" if is_selected else "transparent",
            border_radius=10,
            on_click=lambda e, idx=index: on_change(idx),
            ink=True,
        )
    return ft.Container(
        content=ft.Row([create_segment(tab, i) for i, tab in enumerate(tabs)], spacing=4),
        bgcolor=f"rgba(255,255,255,0.05)",
        border_radius=12,
        padding=4,
    )


# =============================================================================
# Plan View Main
# =============================================================================

def create_plan_view() -> ft.Container:
    """Create the Plan Module view with weekly plan integration."""
    
    # State
    state = {
        "page": None,
        "selected_tab": 0,
        "week_progress": {"has_plan": False, "progress_pct": 0, "completed_days": 0, "total_days": 5},
    }
    
    tab_contents = [create_today_content, create_changes_content, create_strategy_content]
    content_area = ft.Container(content=tab_contents[0](), expand=True)
    
    # Week progress banner (initially hidden)
    week_banner = ft.Container(visible=False)
    
    def update_week_banner():
        """Update week progress banner from state."""
        wp = state["week_progress"]
        if wp.get("has_plan"):
            progress_pct = wp.get("progress_pct", 0)
            completed = wp.get("completed_days", 0)
            total = wp.get("total_days", 5)
            adjustments = wp.get("adjustments_count", 0)
            
            progress_color = Colors.SUCCESS if progress_pct >= 60 else Colors.TEXT_SECONDARY
            
            adjustment_text = ft.Container(
                content=ft.Text(f"-{adjustments} adjusted", size=10, color="#F59E0B"),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                bgcolor="rgba(245, 158, 11, 0.15)",
                border_radius=8,
                visible=adjustments > 0,
            )
            
            week_banner.content = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY_ROUNDED, size=16, color=Colors.TEXT_MUTED),
                    ft.Container(width=8),
                    ft.Text(f"Week: {completed}/{total} days", size=12, color=Colors.TEXT_SECONDARY),
                    ft.Container(width=8),
                    ft.ProgressBar(
                        value=progress_pct / 100, width=80, height=6,
                        color=progress_color, bgcolor="rgba(255,255,255,0.1)", border_radius=3,
                    ),
                    ft.Container(width=8),
                    ft.Text(f"{progress_pct}%", size=12, weight=ft.FontWeight.W_500, color=progress_color),
                    adjustment_text,
                    ft.Container(expand=True),
                    ft.TextButton(
                        "Edit",
                        icon=ft.Icons.EDIT_ROUNDED,
                        on_click=on_setup_week,
                        style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY),
                    ),
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor="rgba(255,255,255,0.03)",
                border=ft.border.all(1, Colors.BORDER_GLASS),
                border_radius=10,
            )
            week_banner.visible = True
        else:
            # Show setup button
            week_banner.content = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, size=16, color=Colors.TEXT_MUTED),
                    ft.Container(width=8),
                    ft.Text("No weekly plan", size=12, color=Colors.TEXT_MUTED),
                    ft.Container(expand=True),
                    ft.OutlinedButton(
                        "Setup Week",
                        icon=ft.Icons.ADD_ROUNDED,
                        on_click=on_setup_week,
                        style=ft.ButtonStyle(side=ft.BorderSide(1, Colors.BORDER_GLASS), color=Colors.TEXT_PRIMARY),
                    ),
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor="rgba(255,255,255,0.03)",
                border=ft.border.all(1, Colors.BORDER_GLASS),
                border_radius=10,
            )
            week_banner.visible = True
        
        if state["page"]:
            state["page"].update()
    
    async def load_week_progress():
        """Load week progress from service."""
        try:
            from db.dao.weekly_plan_dao import WeeklyPlanDAO
            progress = await WeeklyPlanDAO.get_week_progress()
            state["week_progress"] = progress
            update_week_banner()
            return progress
        except Exception as e:
            print(f"Week progress load error: {e}")
            return {"has_plan": False}
    
    async def load_and_maybe_show_setup():
        """Load week progress and show setup dialog if no plan exists."""
        progress = await load_week_progress()
        if not progress.get("has_plan", False) and state["page"]:
            state["page"].open(setup_dialog)

    async def save_week_plan(goals, available_days, intensity):
        """Save weekly plan from dialog."""
        try:
            from services.weekly_plan_service import get_weekly_plan_service
            service = get_weekly_plan_service()
            await service.setup_week(goals, available_days, intensity)
            await load_week_progress()
            if state["page"]:
                state["page"].close(setup_dialog)
        except Exception as e:
            print(f"Week plan save error: {e}")
    
    def on_setup_confirm(goals, available_days, intensity):
        """Handle setup dialog confirm."""
        if state["page"]:
            state["page"].run_task(lambda: save_week_plan(goals, available_days, intensity))
    
    def on_setup_cancel():
        """Handle setup dialog cancel."""
        if state["page"]:
            state["page"].close(setup_dialog)
    
    def on_setup_week(e):
        """Open weekly setup dialog."""
        if state["page"]:
            state["page"].open(setup_dialog)
    
    # Create setup dialog
    from components.weekly_setup_dialog import create_weekly_setup_dialog
    setup_dialog = create_weekly_setup_dialog(on_confirm=on_setup_confirm, on_cancel=on_setup_cancel)
    
    def on_tab_change(index: int):
        state["selected_tab"] = index
        content_area.content = tab_contents[index]()
        content_area.update()
        header_col.controls[5] = create_segmented_control(
            [TXT.tab_today, TXT.tab_changes, TXT.tab_strategy], index, on_tab_change
        )
        header_col.update()
    
    header_col = ft.Column([
        ft.Text(TXT.plan_title, size=Sizes.FONT_SIZE_XXL, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
        ft.Text(TXT.plan_subtitle, size=Sizes.FONT_SIZE_MD, color=Colors.TEXT_SECONDARY),
        ft.Container(height=Sizes.SPACING_SM),
        week_banner,  # Week progress banner
        ft.Container(height=Sizes.SPACING_SM),
        create_segmented_control([TXT.tab_today, TXT.tab_changes, TXT.tab_strategy], 0, on_tab_change),
    ], spacing=Sizes.SPACING_XS)
    
    plan_content = ft.Column([header_col, ft.Container(height=16), content_area], expand=True)
    
    glass_view = GlassContainer(content=plan_content, padding=Sizes.CONTENT_PADDING, expand=True)
    
    # Wrapper to handle lifecycle (did_mount)
    class PlanLoader(ft.Container):
        def __init__(self):
            super().__init__(content=glass_view, expand=True)

        def did_mount(self):
            state["page"] = self.page
            if self.page:
                self.page.run_task(load_and_maybe_show_setup)

    container = PlanLoader()
    # container is now the PlanLoader itself, which is a Container
    container.margin = ft.margin.only(top=Sizes.PAGE_MARGIN, right=Sizes.PAGE_MARGIN, bottom=Sizes.PAGE_MARGIN)
    
    return container
