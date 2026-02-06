# ===========================================================================
# Chronos AI Learning Companion
# File: views/chat_view.py
# Purpose: AI Chat interface with message bubbles and input area
# ===========================================================================

"""
Chat View

A beautiful chat interface featuring:
- Scrollable message history with auto-scroll
- User messages (right-aligned, purple accent)
- AI messages (left-aligned, Markdown support)
- Floating glass capsule input area
"""

import flet as ft
import asyncio
from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer
from i18n.texts import TXT


# =============================================================================
# Message Bubble Components
# =============================================================================

def create_user_message(text: str) -> ft.Container:
    """Create a user message bubble (right-aligned, purple accent)."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(expand=True),  # Push to right
                ft.Container(
                    content=ft.Text(
                        text,
                        size=Sizes.FONT_SIZE_MD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    bgcolor=f"rgba(139, 92, 246, 0.25)",  # Purple accent
                    border_radius=18,
                    border=ft.border.all(1, f"rgba(139, 92, 246, 0.3)"),
                    width=500,
                ),
            ],
        ),
        padding=ft.padding.only(left=60, right=0, top=4, bottom=4),
    )


def create_ai_message(text: str) -> ft.Container:
    """Create an AI message bubble (left-aligned, Markdown support)."""
    return ft.Container(
        content=ft.Row(
            controls=[
                # AI Avatar
                ft.Container(
                    content=ft.Text(
                        "C",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.BG_PRIMARY,
                    ),
                    width=32,
                    height=32,
                    bgcolor=Colors.TEXT_PRIMARY,
                    border_radius=16,
                    alignment=ft.alignment.center,
                ),
                ft.Container(width=Sizes.SPACING_SM),
                # Message content with Markdown
                ft.Container(
                    content=ft.Markdown(
                        text,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        code_theme=ft.MarkdownCodeTheme.MONOKAI,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    bgcolor=f"rgba(255, 255, 255, 0.05)",
                    border_radius=18,
                    border=ft.border.all(1, Colors.BORDER_GLASS),
                    width=500,
                ),
                ft.Container(expand=True),  # Keep left-aligned
            ],
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=ft.padding.only(left=0, right=60, top=4, bottom=4),
    )


# =============================================================================
# Chat View Main Component
# =============================================================================

def create_chat_view() -> ft.Container:
    """Create the AI Chat view with message bubbles and input area."""
    
    # Message list (will be populated dynamically)
    messages: list = []
    
    # ListView for chat history
    chat_list = ft.ListView(
        controls=messages,
        expand=True,
        auto_scroll=True,
        spacing=Sizes.SPACING_XS,
        padding=ft.padding.symmetric(vertical=Sizes.SPACING_MD),
    )
    
    # Input TextField (ref for accessing value)
    input_field = ft.TextField(
        hint_text="Type your message...",
        hint_style=ft.TextStyle(color=Colors.TEXT_MUTED),
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        color=Colors.TEXT_PRIMARY,
        text_size=Sizes.FONT_SIZE_MD,
        expand=True,
        content_padding=ft.padding.symmetric(horizontal=20, vertical=14),
    )
    
    # === Message Handlers ===
    async def send_message(e):
        """Handle sending a message."""
        text = input_field.value.strip()
        if not text:
            return
        
        # Add user message
        chat_list.controls.append(create_user_message(text))
        input_field.value = ""
        input_field.update()
        chat_list.update()
        
        # Simulate AI response after delay
        await asyncio.sleep(1)
        
        # Generate dummy response based on input
        if "hello" in text.lower():
            response = "Hello! 👋 I'm **Chronos**, your AI learning companion.\n\nHow can I help you today?"
        elif "code" in text.lower() or "python" in text.lower():
            response = "Here's a simple Python example:\n\n```python\ndef greet(name):\n    return f\"Hello, {name}!\"\n\nprint(greet(\"Learner\"))\n```"
        else:
            response = f"I received your message: *\"{text}\"*\n\nThis is a demo response. Connect to Gemini API for real AI capabilities!"
        
        chat_list.controls.append(create_ai_message(response))
        chat_list.update()
    
    def on_submit(e):
        """Handle Enter key press."""
        asyncio.create_task(send_message(e))
    
    def on_send_click(e):
        """Handle send button click."""
        asyncio.create_task(send_message(e))
    
    # Bind Enter key to send
    input_field.on_submit = on_submit
    
    # Send button
    send_button = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=Colors.TEXT_PRIMARY,
        icon_size=20,
        on_click=on_send_click,
        style=ft.ButtonStyle(
            bgcolor=f"rgba(255, 255, 255, 0.1)",
            shape=ft.CircleBorder(),
            padding=12,
        ),
    )
    
    # === Capsule Input Area ===
    input_capsule = ft.Container(
        content=ft.Row(
            controls=[
                input_field,
                send_button,
            ],
            spacing=Sizes.SPACING_SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=f"rgba(255, 255, 255, 0.05)",
        border=ft.border.all(1, Colors.BORDER_GLASS),
        border_radius=50,  # Capsule shape
        padding=ft.padding.only(left=4, right=8, top=4, bottom=4),
        blur=ft.Blur(sigma_x=10, sigma_y=10, tile_mode=ft.BlurTileMode.CLAMP),
    )
    
    # === Header ===
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    TXT.nav_chat,
                    size=Sizes.FONT_SIZE_XL,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.MORE_VERT_ROUNDED,
                    icon_color=Colors.TEXT_SECONDARY,
                    icon_size=20,
                ),
            ],
        ),
        padding=ft.padding.only(bottom=Sizes.SPACING_MD),
        border=ft.border.only(
            bottom=ft.BorderSide(1, Colors.BORDER_GLASS),
        ),
    )
    
    # === Compose Layout ===
    chat_content = ft.Column(
        controls=[
            header,
            chat_list,
            ft.Container(height=Sizes.SPACING_SM),
            input_capsule,
        ],
        expand=True,
        spacing=0,
    )
    
    # Wrap in Glass Container
    glass_view = GlassContainer(
        content=chat_content,
        padding=Sizes.CONTENT_PADDING,
        expand=True,
    )
    
    return ft.Container(
        content=glass_view,
        expand=True,
        margin=ft.margin.only(
            top=Sizes.PAGE_MARGIN,
            right=Sizes.PAGE_MARGIN,
            bottom=Sizes.PAGE_MARGIN,
        ),
    )
