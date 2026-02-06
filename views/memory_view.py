# ===========================================================================
# Chronos AI Learning Companion
# File: views/memory_view.py
# Purpose: Memory Bank interface - view and manage global memories
# ===========================================================================

"""
Memory View

Displays user's global memory bank with:
- Left: Filter tabs by memory type (Profile/Episodic/Skill)
- Right: Card grid showing memory items
- Edit/Delete functionality
"""

import flet as ft
import asyncio
import threading
from typing import List, Optional

from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer
from i18n.texts import t
from chronomem.models import GlobalMemory, MemoryType, MemorySource


# =============================================================================
# Constants
# =============================================================================

MEMORY_TABS = [
    ("all", "All", ft.Icons.LAYERS_OUTLINED),
    ("profile", "Profile", ft.Icons.PERSON_OUTLINED),
    ("episodic", "Events", ft.Icons.EVENT_OUTLINED),
    ("skill", "Skills", ft.Icons.PSYCHOLOGY_OUTLINED),
]

TYPE_COLORS = {
    "profile": ("rgba(59, 130, 246, 0.2)", "#3B82F6"),   # Blue
    "episodic": ("rgba(251, 146, 60, 0.2)", "#FB923C"),  # Orange
    "skill": ("rgba(34, 197, 94, 0.2)", "#22C55E"),      # Green
}


# =============================================================================
# Memory Card Component
# =============================================================================

def _create_memory_card(
    memory: GlobalMemory,
    on_edit: callable = None,
    on_delete: callable = None,
) -> ft.Container:
    """Create a memory card from GlobalMemory object."""
    mem_type = memory.type.value
    bg_color, border_color = TYPE_COLORS.get(mem_type, ("rgba(255,255,255,0.1)", Colors.TEXT_MUTED))
    
    type_icons = {
        "profile": ft.Icons.PERSON_OUTLINED,
        "episodic": ft.Icons.EVENT_OUTLINED,
        "skill": ft.Icons.PSYCHOLOGY_OUTLINED,
    }
    icon = type_icons.get(mem_type, ft.Icons.MEMORY_OUTLINED)
    
    # Confidence indicator
    conf_color = Colors.SUCCESS if memory.confidence >= 0.7 else (
        Colors.TEXT_SECONDARY if memory.confidence >= 0.4 else "#EF4444"
    )
    
    return ft.Container(
        content=ft.Column(
            controls=[
                # Header row
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(icon, size=16, color=border_color),
                            width=32, height=32,
                            bgcolor=bg_color,
                            border_radius=8,
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text(
                                f"{int(memory.confidence * 100)}%",
                                size=10,
                                color=conf_color,
                            ),
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            bgcolor=f"rgba(255,255,255,0.05)",
                            border_radius=4,
                        ),
                    ],
                ),
                ft.Container(height=8),
                # Content
                ft.Text(
                    memory.content[:120] + ("..." if len(memory.content) > 120 else ""),
                    size=Sizes.FONT_SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Container(expand=True),
                # Footer
                ft.Row(
                    controls=[
                        ft.Text(
                            memory.source.value.capitalize(),
                            size=10,
                            color=Colors.TEXT_MUTED,
                        ),
                        ft.Container(expand=True),
                        ft.Text(
                            memory.created_at.strftime("%m/%d") if memory.created_at else "",
                            size=10,
                            color=Colors.TEXT_MUTED,
                        ),
                    ],
                ),
                # Action buttons
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_size=14,
                            icon_color=Colors.TEXT_MUTED,
                            tooltip="Edit",
                            on_click=lambda e, m=memory: on_edit(m) if on_edit else None,
                        ) if memory.editable and on_edit else ft.Container(),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_size=14,
                            icon_color=Colors.TEXT_MUTED,
                            tooltip="Delete",
                            on_click=lambda e, m=memory: on_delete(m) if on_delete else None,
                        ) if memory.editable and on_delete else ft.Container(),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=0,
                ),
            ],
            spacing=0,
        ),
        width=280,
        height=180,
        padding=16,
        bgcolor=f"rgba(255, 255, 255, 0.03)",
        border=ft.border.all(1, Colors.BORDER_GLASS),
        border_radius=12,
    )


def _create_type_tab(
    type_id: str,
    label: str,
    icon: str,
    is_selected: bool,
    on_click: callable,
) -> ft.Container:
    """Create a single type filter tab."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(
                    icon,
                    size=18,
                    color=Colors.TEXT_PRIMARY if is_selected else Colors.TEXT_SECONDARY,
                ),
                ft.Text(
                    label,
                    size=Sizes.FONT_SIZE_SM,
                    color=Colors.TEXT_PRIMARY if is_selected else Colors.TEXT_SECONDARY,
                    weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.W_400,
                ),
            ],
            spacing=Sizes.SPACING_SM,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        bgcolor=f"rgba(139, 92, 246, 0.15)" if is_selected else "transparent",
        border_radius=8,
        on_click=lambda e: on_click(type_id),
        ink=True,
    )


def _create_empty_state() -> ft.Container:
    """Create empty state when no memories."""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.MEMORY_OUTLINED, size=48, color=Colors.TEXT_MUTED),
                ft.Container(height=12),
                ft.Text("No memories yet", size=16, color=Colors.TEXT_SECONDARY),
                ft.Container(height=8),
                ft.Text(
                    "Memories will appear here as you use Chronos.",
                    size=13,
                    color=Colors.TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        expand=True,
        alignment=ft.alignment.center,
    )


# =============================================================================
# Memory View Main
# =============================================================================

def create_memory_view() -> ft.Container:
    """Create the Memory Bank view."""
    
    # State
    state = {
        "selected_type": "all",
        "memories": [],
    }
    
    # UI References
    cards_container = ft.GridView(
        runs_count=3,
        max_extent=300,
        child_aspect_ratio=1.55,
        spacing=16,
        run_spacing=16,
        padding=16,
    )
    content_area = ft.Container(content=_create_empty_state(), expand=True)
    type_tabs = ft.Column(spacing=4)
    
    # -------------------------------------------------------------------------
    # Data Loading
    # -------------------------------------------------------------------------
    
    async def load_memories():
        """Load memories from GlobalMemory store."""
        print(f"Loading GlobalMemory: type={state['selected_type']}")
        try:
            from chronomem.memory_store import get_memory_store
            store = get_memory_store()
            
            selected = state["selected_type"]
            
            if selected == "all":
                memories = await store.list_all(limit=50)
            elif selected == "profile":
                memories = await store.list_profile(limit=30)
            elif selected == "episodic":
                memories = await store.list_episodic(limit=30)
            elif selected == "skill":
                memories = await store.list_skill(limit=30)
            else:
                memories = await store.list_all(limit=50)
            
            state["memories"] = memories
            print(f"Loaded {len(memories)} memories")
            update_cards()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error loading memories: {e}")
            state["memories"] = []
            update_cards()
    
    def update_cards():
        """Update card display."""
        if not state["memories"]:
            content_area.content = _create_empty_state()
        else:
            cards_container.controls = [
                _create_memory_card(m, on_edit=handle_edit, on_delete=handle_delete)
                for m in state["memories"]
            ]
            content_area.content = cards_container
        
        try:
            content_area.update()
        except Exception:
            pass
    
    def update_tabs():
        """Update tab selection."""
        type_tabs.controls = [
            _create_type_tab(
                tid, label, icon,
                is_selected=(tid == state["selected_type"]),
                on_click=handle_type_change,
            )
            for tid, label, icon in MEMORY_TABS
        ]
        try:
            type_tabs.update()
        except Exception:
            pass
    
    # -------------------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------------------
    
    def handle_type_change(type_id: str):
        """Handle type filter change."""
        state["selected_type"] = type_id
        update_tabs()
        
        def run_load():
            asyncio.run(load_memories())
        threading.Thread(target=run_load, daemon=True).start()
    
    def handle_edit(memory: GlobalMemory):
        """Handle memory edit."""
        print(f"Edit memory: {memory.memory_id}")
        # TODO: Show edit dialog
    
    def handle_delete(memory: GlobalMemory):
        """Handle memory deletion."""
        print(f"Delete memory: {memory.memory_id}")
        
        async def do_delete():
            from chronomem.memory_store import get_memory_store
            store = get_memory_store()
            await store.delete(memory.memory_id)
            await load_memories()
        
        def run_delete():
            asyncio.run(do_delete())
        threading.Thread(target=run_delete, daemon=True).start()
    
    # -------------------------------------------------------------------------
    # Build UI
    # -------------------------------------------------------------------------
    
    # Initial tabs
    type_tabs.controls = [
        _create_type_tab(tid, label, icon, is_selected=(tid == "all"), on_click=handle_type_change)
        for tid, label, icon in MEMORY_TABS
    ]
    
    # Header
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    t("memory.title"),
                    size=Sizes.FONT_SIZE_XL,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH_OUTLINED,
                    icon_color=Colors.TEXT_SECONDARY,
                    icon_size=20,
                    tooltip="Refresh",
                    on_click=lambda e: handle_type_change(state["selected_type"]),
                ),
            ],
        ),
        padding=ft.padding.only(bottom=Sizes.SPACING_MD),
        border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_GLASS)),
    )
    
    # Layout
    layout = ft.Row(
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Filter by Type", size=11, color=Colors.TEXT_MUTED, weight=ft.FontWeight.W_500),
                        ft.Container(height=8),
                        type_tabs,
                    ],
                ),
                width=160,
                padding=ft.padding.only(right=Sizes.SPACING_MD),
                border=ft.border.only(right=ft.BorderSide(1, Colors.BORDER_GLASS)),
            ),
            ft.Container(
                content=ft.Column(controls=[content_area], expand=True),
                expand=True,
                padding=ft.padding.only(left=Sizes.SPACING_MD),
            ),
        ],
        expand=True,
        spacing=0,
    )
    
    main_content = ft.Column(controls=[header, layout], expand=True, spacing=0)
    
    glass_view = GlassContainer(
        content=main_content,
        padding=Sizes.CONTENT_PADDING,
        expand=True,
    )
    
    view_container = ft.Container(
        content=glass_view,
        expand=True,
        margin=ft.margin.only(
            top=Sizes.PAGE_MARGIN,
            right=Sizes.PAGE_MARGIN,
            bottom=Sizes.PAGE_MARGIN,
        ),
    )
    
    # Start loading
    def run_async_load():
        asyncio.run(load_memories())
    threading.Thread(target=run_async_load, daemon=True).start()
    
    return view_container
