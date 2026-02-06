# ===========================================================================
# Chronos AI Learning Companion
# File: views/dashboard_view.py
# Purpose: Main dashboard view with Bento Grid layout
# ===========================================================================

"""
Dashboard View

The main landing page displaying:
- Personalized greeting
- Key statistics cards (learning hours, tasks, knowledge nodes)
- Quick action buttons
- Recent activity summary

Uses Bento Grid layout with GlassContainer for floating glass effect.
"""

import flet as ft
import asyncio
import threading
from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer
# Note: stat_card functions not used - using inline refs for dynamic updates
from services.dashboard_service import DashboardService
from i18n.texts import TXT


def create_dashboard_view(on_checkin: callable = None) -> ft.Container:
    """
    Create the dashboard view with Bento Grid layout.
    
    Layout Structure:
        - Header: Greeting section
        - Row 1: Progress card + Stats cards
        - Row 2: Recent activity + Quick actions
    
    Returns:
        ft.Container: Dashboard wrapped in GlassContainer with margin.
    
    Example:
        ```python
        dashboard = create_dashboard_view()
        page.add(dashboard)
        ```
    """
    
    # =========================================================================
    # Header Section - Greeting
    # =========================================================================
    header_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    TXT.greeting,
                    size=Sizes.FONT_SIZE_XXL,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
                ft.Text(
                    TXT.greeting_sub,
                    size=Sizes.FONT_SIZE_MD,
                    color=Colors.TEXT_SECONDARY,
                ),
            ],
            spacing=Sizes.SPACING_XS,
        ),
        padding=ft.padding.only(bottom=Sizes.SPACING_LG),
    )
    
    # =========================================================================
    # Row 1: Progress + Stats Cards (Dynamic Data)
    # =========================================================================
    
    # State for dynamic data
    state = {"loading": True, "data": None}
    
    # === Dynamic Text References (will be updated) ===
    progress_label_ref = ft.Ref[ft.Text]()
    progress_ring_ref = ft.Ref[ft.ProgressRing]()
    progress_subtitle_ref = ft.Ref[ft.Text]()
    
    mode_value_ref = ft.Ref[ft.Text]()
    mode_subtitle_ref = ft.Ref[ft.Text]()
    
    completion_value_ref = ft.Ref[ft.Text]()
    completion_subtitle_ref = ft.Ref[ft.Text]()
    
    mastery_value_ref = ft.Ref[ft.Text]()
    mastery_subtitle_ref = ft.Ref[ft.Text]()
    
    # === Build Progress Card with refs ===
    progress_stack = ft.Stack(
        controls=[
            ft.ProgressRing(
                ref=progress_ring_ref,
                value=0.0,
                stroke_width=6,
                width=80,
                height=80,
                color=Colors.TEXT_PRIMARY,
                bgcolor=f"rgba(255, 255, 255, 0.1)",
            ),
            ft.Container(
                content=ft.Text(
                    "--",
                    ref=progress_label_ref,
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
    
    progress_card = GlassContainer(
        content=ft.Column(
            controls=[
                ft.Text(
                    TXT.card_progress_title,
                    size=Sizes.FONT_SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(height=Sizes.SPACING_MD),
                ft.Row(controls=[progress_stack], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=Sizes.SPACING_SM),
                ft.Text(
                    "Loading...",
                    ref=progress_subtitle_ref,
                    size=Sizes.FONT_SIZE_SM,
                    color=Colors.TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Sizes.SPACING_XS,
        ),
        height=180,
    )
    
    # === Build Stat Cards with refs ===
    def build_stat_card_with_refs(
        title: str,
        value_ref: ft.Ref,
        subtitle_ref: ft.Ref,
        icon: str,
        icon_color: str = Colors.TEXT_SECONDARY,
    ) -> ft.Container:
        return GlassContainer(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(title, size=Sizes.FONT_SIZE_SM, color=Colors.TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                            ft.Container(content=ft.Icon(icon, size=16, color=icon_color), margin=ft.margin.only(left=Sizes.SPACING_SM)),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=Sizes.SPACING_SM),
                    ft.Text("--", ref=value_ref, size=Sizes.FONT_SIZE_XXL, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                    ft.Text("Loading...", ref=subtitle_ref, size=Sizes.FONT_SIZE_SM, color=Colors.TEXT_MUTED),
                ],
                spacing=Sizes.SPACING_XS,
                alignment=ft.MainAxisAlignment.START,
            ),
        )
    
    mode_card = build_stat_card_with_refs("Plan Mode", mode_value_ref, mode_subtitle_ref, ft.Icons.ADJUST_ROUNDED)
    completion_card = build_stat_card_with_refs("Completion", completion_value_ref, completion_subtitle_ref, ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, Colors.SUCCESS)
    mastery_card = build_stat_card_with_refs("Weak Concepts", mastery_value_ref, mastery_subtitle_ref, ft.Icons.TRENDING_DOWN_ROUNDED, Colors.ACCENT_PURPLE)
    
    stats_row = ft.Row(
        controls=[
            ft.Container(content=progress_card, expand=1),
            ft.Container(width=Sizes.CARD_GAP),
            ft.Container(content=mode_card, expand=1),
            ft.Container(width=Sizes.CARD_GAP),
            ft.Container(content=completion_card, expand=1),
            ft.Container(width=Sizes.CARD_GAP),
            ft.Container(content=mastery_card, expand=1),
        ],
    )
    
    def update_ui_with_data(data: dict):
        """Update all card UI elements with loaded data."""
        try:
            # Progress card
            completion = data.get("completion", {})
            week_pct = completion.get("week", 0)
            if progress_ring_ref.current:
                progress_ring_ref.current.value = week_pct / 100.0
            if progress_label_ref.current:
                progress_label_ref.current.value = f"{week_pct}%"
            if progress_subtitle_ref.current:
                progress_subtitle_ref.current.value = f"{completion.get('week_count', 0)} sessions this week"
            
            # Mode card
            plan_mode = data.get("plan_mode", {})
            if mode_value_ref.current:
                mode_value_ref.current.value = plan_mode.get("label", "Standard")
            if mode_subtitle_ref.current:
                mode_subtitle_ref.current.value = "Today's mode"
            
            # Completion card
            if completion_value_ref.current:
                completion_value_ref.current.value = f"{completion.get('yesterday', 0)}%"
            if completion_subtitle_ref.current:
                completion_subtitle_ref.current.value = f"{completion.get('yesterday_count', 0)} sessions yesterday"
            
            # Mastery card
            mastery = data.get("mastery_trend", [])
            if mastery_value_ref.current:
                mastery_value_ref.current.value = str(len(mastery))
            if mastery_subtitle_ref.current:
                if mastery:
                    mastery_subtitle_ref.current.value = mastery[0].get("concept_id", "None")[:20]
                else:
                    mastery_subtitle_ref.current.value = "No weak spots"
            
            print("Dashboard UI updated successfully")
        except Exception as e:
            print(f"UI update error: {e}")
    
    async def load_dashboard_data():
        """Load real data from DashboardService."""
        try:
            service = DashboardService()
            data = await service.aggregate()
            state["data"] = data
            state["loading"] = False
            
            # Log loaded data for debugging
            print(f"Dashboard data loaded: mode={data.get('plan_mode', {}).get('mode')}")
            print(f"  Completion: {data.get('completion', {})}")
            print(f"  Mastery trend: {len(data.get('mastery_trend', []))} weak concepts")
            
            # Update UI with loaded data
            update_ui_with_data(data)
            
        except Exception as e:
            print(f"Dashboard load error: {e}")
            import traceback
            traceback.print_exc()
            state["loading"] = False
    
    # =========================================================================
    # Row 2: Recent Chats + Quick Actions
    # =========================================================================
    
    # Recent chats card
    def create_chat_item(title: str, preview: str, time: str) -> ft.Container:
        """Create a single chat list item."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.CHAT_BUBBLE_ROUNDED,
                            size=14,
                            color=Colors.TEXT_MUTED,
                        ),
                        width=28,
                        height=28,
                        bgcolor=f"rgba(255, 255, 255, 0.08)",
                        border_radius=8,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=Sizes.SPACING_SM),
                    ft.Column(
                        controls=[
                            ft.Text(
                                title,
                                size=Sizes.FONT_SIZE_SM,
                                weight=ft.FontWeight.W_500,
                                color=Colors.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                preview,
                                size=Sizes.FONT_SIZE_XS,
                                color=Colors.TEXT_MUTED,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Text(
                        time,
                        size=Sizes.FONT_SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                ],
            ),
            padding=ft.padding.symmetric(vertical=Sizes.SPACING_SM),
        )
    
    # Chat list (will be populated)
    chat_list = ft.Column(spacing=0)
    
    chats_content = ft.Column(
        controls=[
            ft.Text(
                TXT.card_chats_title,
                size=Sizes.FONT_SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                weight=ft.FontWeight.W_500,
            ),
            ft.Container(height=Sizes.SPACING_SM),
            chat_list,
        ],
        spacing=0,
    )
    
    async def load_chats():
        """Load recent chats."""
        try:
            if state.get("data"):
                chats = state["data"].get("recent_chats", [])
                chat_list.controls.clear()
                
                if chats:
                    for chat in chats:
                        # Calculate time ago
                        time_ago = "recent"
                        chat_list.controls.append(
                            create_chat_item(
                                chat.get("title", "New Chat"),
                                chat.get("preview", "No messages yet"),
                                time_ago
                            )
                        )
                else:
                    chat_list.controls.append(
                        ft.Text("No chats yet", size=12, color=Colors.TEXT_MUTED)
                    )
        except Exception as e:
            print(f"Chat load error: {e}")
    
    chats_card = GlassContainer(
        content=chats_content,
        expand=True,
    )
    
    # Quick actions card
    state_actions = {"page": None}
    
    def on_new_chat(e):
        """Navigate to Tutor page for new chat."""
        if e.page:
            e.page.go("/tutor")
    
    def on_upload(e):
        """Show file picker for upload."""
        if e.page:
            def on_result(result: ft.FilePickerResultEvent):
                if result.files:
                    print(f"Uploaded: {[f.name for f in result.files]}")
            
            picker = ft.FilePicker(on_result=on_result)
            e.page.overlay.append(picker)
            e.page.update()
            picker.pick_files(allow_multiple=True)
    
    def on_bookmarks(e):
        """Navigate to Memory page for bookmarks."""
        if e.page:
            e.page.go("/memory")

    def on_checkin_click(e):
        """Open check-in page in browser."""
        if on_checkin:
            on_checkin(e)
    
    def create_action_btn(icon: str, label: str, on_click=None) -> ft.Container:
        """Create a quick action button."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, size=22, color=Colors.TEXT_PRIMARY),
                    ft.Container(height=Sizes.SPACING_XS),
                    ft.Text(
                        label,
                        size=Sizes.FONT_SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=70,
            height=70,
            bgcolor=f"rgba(255, 255, 255, 0.05)",
            border_radius=Sizes.GLASS_RADIUS_SM,
            ink=True,
            on_click=on_click,
        )
    
    actions_content = ft.Column(
        controls=[
            ft.Text(
                TXT.card_actions_title,
                size=Sizes.FONT_SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                weight=ft.FontWeight.W_500,
            ),
            ft.Container(height=Sizes.SPACING_MD),
        ft.Row(
            controls=[
                create_action_btn(ft.Icons.ADD_ROUNDED, TXT.action_new_chat, on_new_chat),
                create_action_btn(ft.Icons.UPLOAD_FILE_ROUNDED, TXT.action_upload, on_upload),
                create_action_btn(ft.Icons.BOOKMARK_OUTLINE_ROUNDED, TXT.action_bookmarks, on_bookmarks),
                create_action_btn(ft.Icons.OPEN_IN_BROWSER_ROUNDED, TXT.action_checkin, on_checkin_click),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        ],
        spacing=0,
    )
    
    actions_card = GlassContainer(
        content=actions_content,
        height=160,
    )
    
    row2 = ft.Row(
        controls=[
            ft.Container(content=chats_card, expand=2),
            ft.Container(width=Sizes.CARD_GAP),
            ft.Container(content=actions_card, expand=1),
        ],
        expand=True,
    )
    
    # =========================================================================
    # Compose Dashboard Layout
    # =========================================================================
    dashboard_content = ft.Column(
        controls=[
            header_section,
            stats_row,
            ft.Container(height=Sizes.CARD_GAP),
            row2,
        ],
        expand=True,
    )
    
    # =========================================================================
    # Async Data Loading (using thread)
    # =========================================================================
    def run_async_load():
        """Run async loading in a separate thread."""
        async def do_load():
            await load_dashboard_data()
            await load_chats()
        try:
            asyncio.run(do_load())
        except Exception as e:
            print(f"Dashboard init error: {e}")
    
    # Start loading in background thread
    threading.Thread(target=run_async_load, daemon=True).start()
    
    # =========================================================================
    # Wrap in Glass Container with Margin
    # =========================================================================
    dashboard_glass = GlassContainer(
        content=dashboard_content,
        padding=Sizes.CONTENT_PADDING,
        expand=True,
    )
    
    return ft.Container(
        content=dashboard_glass,
        expand=True,
        margin=ft.margin.only(
            top=Sizes.PAGE_MARGIN,
            right=Sizes.PAGE_MARGIN,
            bottom=Sizes.PAGE_MARGIN,
        ),
    )
