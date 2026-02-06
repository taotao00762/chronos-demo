# ===========================================================================
# Chronos AI Learning Companion
# File: views/tutor_view.py
# Purpose: AI Tutor interface with multi-session chat support
# ===========================================================================

"""
Tutor View - Multi-Session Chat Interface

Features:
- Left sidebar with chat session list
- Create new chat with subject/grade/style selection
- Switch between chat sessions
- Persistent chat history
- Real-time AI responses with streaming
"""

import base64
import flet as ft
from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer
from services.gemini_service import create_gemini_service, GeminiService
from services.principal_service import get_principal_context_service
from config.tutor_config import (
    SUBJECTS, GRADES, TEACHING_STYLES, SUBJECT_MAP,
    generate_tutor_system_prompt,
)
from i18n.texts import t


# =============================================================================
# Message Bubble Components
# =============================================================================

def create_user_message(text: str) -> ft.Container:
    """Create a user message bubble."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text(text, size=14, color=Colors.TEXT_PRIMARY, selectable=True),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    bgcolor="rgba(139, 92, 246, 0.25)",
                    border_radius=18,
                    border=ft.border.all(1, "rgba(139, 92, 246, 0.3)"),
                    width=380,
                ),
            ],
        ),
        padding=ft.padding.only(left=60, right=0, top=4, bottom=4),
    )


def create_ai_message_container(text_control: ft.Text) -> ft.Container:
    """Create an AI message bubble container."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text("C", size=12, weight=ft.FontWeight.BOLD, color=Colors.BG_PRIMARY),
                    width=32, height=32, bgcolor=Colors.TEXT_PRIMARY, border_radius=16,
                    alignment=ft.alignment.center,
                ),
                ft.Container(width=8),
                ft.Container(
                    content=text_control,
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    bgcolor="rgba(255, 255, 255, 0.05)",
                    border_radius=18, border=ft.border.all(1, Colors.BORDER_GLASS),
                    width=380,
                ),
                ft.Container(expand=True),
            ],
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=ft.padding.only(left=0, right=60, top=4, bottom=4),
    )


def create_ai_message_markdown(text: str) -> ft.Container:
    """Create an AI message with Markdown."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text("C", size=12, weight=ft.FontWeight.BOLD, color=Colors.BG_PRIMARY),
                    width=32, height=32, bgcolor=Colors.TEXT_PRIMARY, border_radius=16,
                    alignment=ft.alignment.center,
                ),
                ft.Container(width=8),
                ft.Container(
                    content=ft.Markdown(text, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    bgcolor="rgba(255, 255, 255, 0.05)",
                    border_radius=18, border=ft.border.all(1, Colors.BORDER_GLASS),
                    width=380,
                ),
                ft.Container(expand=True),
            ],
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=ft.padding.only(left=0, right=60, top=4, bottom=4),
    )


# =============================================================================
# Main Tutor View
# =============================================================================

def create_tutor_view() -> ft.Container:
    """Create the AI Tutor view with multi-session chat."""
    
    gemini_service = create_gemini_service()
    if gemini_service is None:
        return ft.Container(
            content=ft.Text("No API Key. Go to Settings.", color=Colors.TEXT_SECONDARY),
            expand=True, alignment=ft.alignment.center,
        )
    
    # State
    state = {
        "page": None,
        "is_generating": False,
        "current_chat_id": None,
        "chats": [],
        "visual_mode": True,
        "plan_context": None,
        "memory_context": None,
        "current_chat_meta": None,
        "cleanup_registered": False,
    }

    def is_memory_enabled() -> bool:
        try:
            from stores.settings_store import SettingsStore
            settings = SettingsStore.get_instance().get()
            return bool(getattr(settings, "enable_memory", True))
        except Exception:
            return True

    def is_tutor_memory_enabled() -> bool:
        try:
            from stores.settings_store import SettingsStore
            settings = SettingsStore.get_instance().get()
            return bool(getattr(settings, "enable_memory", True)) and bool(getattr(settings, "tutor_use_memory", True))
        except Exception:
            return True
    
    # UI Components
    chat_list_view = ft.ListView(controls=[], expand=True, spacing=4, padding=8)
    message_list = ft.ListView(controls=[], expand=True, auto_scroll=True, spacing=4, padding=16)

    async def _maybe_close(service, label: str) -> None:
        close = getattr(service, "close", None)
        if callable(close):
            try:
                result = close()
                if hasattr(result, "__await__"):
                    await result
            except Exception as close_err:
                print(f"{label} cleanup failed: {close_err}")

    async def close_services() -> None:
        await _maybe_close(gemini_service, "GeminiService")

    def register_cleanup(page: ft.Page) -> None:
        if state.get("cleanup_registered"):
            return
        state["cleanup_registered"] = True

        def on_disconnect(e):
            if page:
                page.run_task(close_services)

        page.on_disconnect = on_disconnect
        try:
            page.on_close = on_disconnect
        except Exception:
            pass


    def append_image_to_chat(image_path: str, caption: str = "") -> None:
        """Render a generated image (and optional caption) inside the chat feed."""
        try:
            with open(image_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
        except Exception as read_err:
            print(f"Image render failed: {read_err}")
            return
        
        img_container = ft.Container(
            content=ft.Row([
                ft.Container(width=40),
                ft.Container(
                    content=ft.Image(
                        src_base64=encoded,
                        width=350,
                        height=350,
                        fit=ft.ImageFit.CONTAIN,
                        border_radius=12,
                    ),
                    padding=8,
                    bgcolor="rgba(255, 255, 255, 0.05)",
                    border_radius=12,
                ),
            ]),
            padding=ft.padding.only(left=0, right=60, top=4, bottom=4),
        )
        message_list.controls.append(img_container)
        if caption:
            message_list.controls.append(
                ft.Container(
                    content=ft.Text(caption, size=12, color=Colors.TEXT_SECONDARY),
                    padding=ft.padding.only(left=40, right=60, bottom=4),
                )
            )
        if state["page"]:
            state["page"].update()
    
    input_field = ft.TextField(
        hint_text="Ask a question...", hint_style=ft.TextStyle(color=Colors.TEXT_MUTED),
        border=ft.InputBorder.NONE, bgcolor="transparent", color=Colors.TEXT_PRIMARY,
        text_size=14, expand=True, content_padding=ft.padding.symmetric(horizontal=20, vertical=14),
    )
    
    # Chat header (shows current chat info)
    chat_title_text = ft.Text("Select or create a chat", size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)
    chat_subtitle_text = ft.Text("", size=12, color=Colors.TEXT_SECONDARY)
    
    # New chat dialog components
    new_subject = ft.Dropdown(
        value="math", width=200,
        options=[ft.dropdown.Option(key=s["id"], text=s["name_en"]) for s in SUBJECTS],
        bgcolor="rgba(255,255,255,0.05)", border_color=Colors.BORDER_GLASS, color=Colors.TEXT_PRIMARY,
    )
    new_grade = ft.Dropdown(
        value="high", width=200,
        options=[ft.dropdown.Option(key=g["id"], text=g["name_en"]) for g in GRADES],
        bgcolor="rgba(255,255,255,0.05)", border_color=Colors.BORDER_GLASS, color=Colors.TEXT_PRIMARY,
    )
    new_style = ft.Dropdown(
        value="patient", width=200,
        options=[ft.dropdown.Option(key=s["id"], text=s["name_en"]) for s in TEACHING_STYLES],
        bgcolor="rgba(255,255,255,0.05)", border_color=Colors.BORDER_GLASS, color=Colors.TEXT_PRIMARY,
    )
    
    async def load_chats():
        """Load chat sessions from database."""
        from db.dao import TutorChatDAO
        state["chats"] = await TutorChatDAO.list_recent(limit=30)
        refresh_chat_list()
    
    def refresh_chat_list():
        """Refresh the chat list UI."""
        chat_list_view.controls.clear()
        for chat in state["chats"]:
            subject = SUBJECT_MAP.get(chat.get("subject", "custom"), {})
            icon = subject.get("icon", "chat")
            chat_list_view.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(getattr(ft.Icons, icon.upper() + "_ROUNDED", ft.Icons.CHAT_ROUNDED), size=18, color=Colors.TEXT_SECONDARY),
                        ft.Container(width=8),
                        ft.Column([
                            ft.Text(chat.get("title", "Chat")[:25], size=13, color=Colors.TEXT_PRIMARY, max_lines=1),
                            ft.Text(chat.get("subject", "").capitalize(), size=11, color=Colors.TEXT_MUTED),
                        ], spacing=2, expand=True),
                    ]),
                    padding=10, border_radius=8,
                    bgcolor="rgba(139,92,246,0.15)" if chat.get("chat_id") == state["current_chat_id"] else "transparent",
                    on_click=lambda e, cid=chat.get("chat_id"): on_select_chat(cid),
                )
            )
        if state["page"]:
            state["page"].update()
    
    def refresh_system_prompt():
        """Apply the current Principal + visual-mode context to Gemini."""
        chat_meta = state.get("current_chat_meta")
        if not chat_meta:
            return
        memory_context = state.get("memory_context") if is_tutor_memory_enabled() else None
        system_prompt = generate_tutor_system_prompt(
            chat_meta.get("subject"),
            chat_meta.get("grade"),
            chat_meta.get("style"),
            plan_context=state.get("plan_context"),
            memory_context=memory_context,
            visual_mode=state.get("visual_mode", False),
        )
        gemini_service.set_system_instruction(system_prompt)

    async def load_memory_context(chat: dict) -> None:
        """加载全局记忆上下文，用于导师个性化提示。"""
        if not is_tutor_memory_enabled():
            state["memory_context"] = None
            refresh_system_prompt()
            return

        try:
            from chronomem.service import get_chronomem_service

            subject_name = SUBJECT_MAP.get(chat.get("subject", "custom"), {}).get("name_en", "Learning")
            mem = get_chronomem_service()
            context = await mem.get_context_for_plan([subject_name], user_id="default")

            if context:
                context["personal_memories"] = (context.get("personal_memories") or [])[:3]
                context["task_strategies"] = (context.get("task_strategies") or [])[:2]

            state["memory_context"] = context
        except Exception as ctx_err:
            print(f"Memory context failed: {ctx_err}")
            state["memory_context"] = None

        refresh_system_prompt()
    
    async def load_messages(chat_id: str):
        """Load messages for a chat."""
        from db.dao import TutorChatDAO, TutorMessageDAO
        chat = await TutorChatDAO.get(chat_id)
        if not chat:
            return
        
        state["current_chat_id"] = chat_id
        chat_title_text.value = chat.get("title", "Chat")
        subject = SUBJECT_MAP.get(chat.get("subject", "custom"), {})
        chat_subtitle_text.value = f"{subject.get('name_en', 'Custom')} - {chat.get('grade', '').replace('_', ' ').title()}"
        
        # Fetch Principal context for Today
        plan_context = None
        try:
            principal_service = get_principal_context_service()
            plan_context = await principal_service.get_plan_context()
            if plan_context:
                mode = plan_context.get("mode", "standard")
                pressure = plan_context.get("life_pressure", 0.0)
                print(f"Injected Principal context: mode={mode}, pressure={pressure:.2f}")
        except Exception as ctx_err:
            print(f"Principal context failed: {ctx_err}")
        
        state["plan_context"] = plan_context
        state["current_chat_meta"] = chat
        await load_memory_context(chat)
        
        # Load messages
        messages = await TutorMessageDAO.list_by_chat(chat_id)
        message_list.controls.clear()
        gemini_service.clear_history()
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                message_list.controls.append(create_user_message(content))
            else:
                message_list.controls.append(create_ai_message_markdown(content))
            # Rebuild history
            gemini_service._history.append({
                "role": "user" if role == "user" else "model",
                "parts": [{"text": content}],
            })
        
        refresh_chat_list()
        if state["page"]:
            state["page"].update()
    
    def on_select_chat(chat_id: str):
        """Handle chat selection."""
        async def do_load():
            await load_messages(chat_id)
        if state["page"]:
            state["page"].run_task(do_load)
    
    async def create_new_chat():
        """Create a new chat session."""
        from db.dao import TutorChatDAO
        subject = new_subject.value or "custom"
        grade = new_grade.value or "high"
        style = new_style.value or "patient"
        subject_name = SUBJECT_MAP.get(subject, {}).get("name_en", "Custom")
        title = f"{subject_name} Chat"
        
        chat_id = await TutorChatDAO.create(subject=subject, grade=grade, style=style, title=title)
        await load_chats()
        await load_messages(chat_id)
        if state["page"]:
            state["page"].close(new_chat_dialog)
    
    def on_new_chat_click(e):
        if state["page"]:
            state["page"].open(new_chat_dialog)
    
    def on_create_confirm(e):
        if state["page"]:
            state["page"].run_task(create_new_chat)
    
    new_chat_dialog = ft.AlertDialog(
        title=ft.Text("New Chat", size=18, weight=ft.FontWeight.BOLD),
        content=ft.Column([
            ft.Text("Subject", size=12, color=Colors.TEXT_SECONDARY),
            new_subject,
            ft.Container(height=8),
            ft.Text("Grade", size=12, color=Colors.TEXT_SECONDARY),
            new_grade,
            ft.Container(height=8),
            ft.Text("Teaching Style", size=12, color=Colors.TEXT_SECONDARY),
            new_style,
        ], tight=True, spacing=4),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: state["page"].close(new_chat_dialog) if state["page"] else None),
            ft.FilledButton("Create", on_click=on_create_confirm),
        ],
    )
    
    async def handle_send():
        """Handle sending a message."""
        if state["is_generating"] or not state["current_chat_id"]:
            return
        text = input_field.value.strip() if input_field.value else ""
        if not text:
            return
        
        state["is_generating"] = True
        from db.dao import TutorChatDAO, TutorMessageDAO
        
        # Save user message
        await TutorMessageDAO.create(state["current_chat_id"], "user", text)
        await TutorChatDAO.increment_message_count(state["current_chat_id"])
        
        message_list.controls.append(create_user_message(text))
        input_field.value = ""
        if state["page"]:
            state["page"].update()
        
        # AI response
        ai_text = ft.Text("", selectable=True, color=Colors.TEXT_PRIMARY)
        message_list.controls.append(create_ai_message_container(ai_text))
        if state["page"]:
            state["page"].update()
        
        full_response = ""
        try:
            async for chunk in gemini_service.send_message_stream(text):
                full_response += chunk
                ai_text.value = full_response
                if state["page"]:
                    state["page"].update()
        except Exception as ex:
            ai_text.value = f"Error: {ex}"
        finally:
            state["is_generating"] = False
            if full_response:
                await TutorMessageDAO.create(state["current_chat_id"], "assistant", full_response)
                await TutorChatDAO.increment_message_count(state["current_chat_id"])
                # Update title if first message
                chat = await TutorChatDAO.get(state["current_chat_id"])
                if chat and chat.get("message_count", 0) <= 2:
                    short_title = text[:30] + ("..." if len(text) > 30 else "")
                    await TutorChatDAO.update_title(state["current_chat_id"], short_title)
                    await load_chats()
                if "```" in full_response or "**" in full_response or "[GENERATE_IMAGE:" in full_response:
                    message_list.controls[-1] = create_ai_message_markdown(full_response)
                
                # Detect and generate images from [GENERATE_IMAGE: description] markers
                generated_visual = False
                if "[GENERATE_IMAGE:" in full_response:
                    try:
                        import re
                        from services.image_service import create_image_service
                        
                        image_service = create_image_service()
                        if image_service:
                            try:
                                pattern = r'\[GENERATE_IMAGE:\s*([^\]]+)\]'
                                matches = re.findall(pattern, full_response)
                                
                                for desc in matches:
                                    print(f"Generating image: {desc}")
                                    image_path = await image_service.generate_image(desc.strip())
                                    
                                    if image_path:
                                        append_image_to_chat(image_path)
                                        generated_visual = True
                            finally:
                                await _maybe_close(image_service, "ImageService")
                    except Exception as img_err:
                        print(f"Image generation failed: {img_err}")
                
                # Fallback: auto-generate diagram when visual mode is on
                if not generated_visual and state.get("visual_mode"):
                    try:
                        from services.image_service import create_image_service
                        
                        image_service = create_image_service()
                        if image_service:
                            try:
                                subject_name = SUBJECT_MAP.get(chat.get("subject", "custom"), {}).get("name_en", "Concept") if chat else "Concept"
                                first_line = next((line for line in full_response.splitlines() if line.strip()), text)
                                base_prompt = first_line[:140] if first_line else text[:140]
                                prompt = f"{subject_name} concept diagram: {base_prompt}"
                                print(f"Auto visual mode prompt: {prompt}")
                                image_path = await image_service.generate_image(prompt.strip())
                                if image_path:
                                    append_image_to_chat(image_path, caption="Auto-generated teaching diagram")
                                    generated_visual = True
                            finally:
                                await _maybe_close(image_service, "ImageService")
                    except Exception as auto_img_err:
                        print(f"Auto image generation failed: {auto_img_err}")

                # Real-time memory integration: record every exchange
                try:
                    await record_learning_exchange(
                        chat_id=state["current_chat_id"],
                        user_msg=text,
                        ai_response=full_response,
                        chat=chat,
                    )
                except Exception as mem_ex:
                    print(f"Memory recording failed: {mem_ex}")
                        
            if state["page"]:
                state["page"].update()
    
    async def record_learning_exchange(chat_id: str, user_msg: str, ai_response: str, chat: dict):
        """Record each learning exchange to Evidence table for real-time memory."""
        from db.dao import EvidenceDAO
        
        subject = chat.get("subject", "learning") if chat else "learning"
        grade = chat.get("grade", "") if chat else ""
        
        # Create summary from the exchange
        user_short = user_msg[:100] + "..." if len(user_msg) > 100 else user_msg
        ai_short = ai_response[:150] + "..." if len(ai_response) > 150 else ai_response
        summary = f"[{subject.upper()}] Q: {user_short}\nA: {ai_short}"
        
        # Store as Evidence (visible in Memory view immediately)
        if is_memory_enabled():
            await EvidenceDAO.create(
                type="receipt",
                ref_type="tutor_chat",
                ref_id=chat_id,
                summary=summary,
                ttl_days=365,
            )
            print(f"Recorded learning exchange to memory: {subject}")
        
        # Detect complaints/interruptions in user message using LLM
        try:
            from chronomem.complaint_detector import detect_complaint_async
            from db.dao.interruption_dao import InterruptionDAO
            
            complaint = await detect_complaint_async(user_msg)
            if complaint:
                await InterruptionDAO.add(
                    source="tutor_chat",
                    content=user_msg,
                    category=complaint.category,
                    impact_level=complaint.impact_level,
                    metadata={
                        "chat_id": chat_id,
                        "subject": subject,
                        "reason": complaint.reason,
                    },
                )
                print(f"LLM detected complaint: {complaint.category} ({complaint.reason})")
                
                # Track stuck points for ExecutionReceipt
                if "stuck_points" not in state:
                    state["stuck_points"] = []
                state["stuck_points"].append(complaint.reason or user_msg[:50])
        except Exception as ex:
            print(f"Complaint detection failed: {ex}")
        
        # Generate ExecutionReceipt every 3 message exchanges
        msg_count = chat.get("message_count", 0) if chat else 0
        if msg_count > 0 and msg_count % 6 == 0:  # Every 3 exchanges (6 messages)
            try:
                from db.dao.receipt_dao import ReceiptDAO
                
                stuck = state.get("stuck_points", [])[-3:]  # Last 3 stuck points
                learner_state = {
                    "engagement": "active" if len(ai_response) > 100 else "minimal",
                    "questions_asked": msg_count // 2,
                    "stuck_count": len(state.get("stuck_points", [])),
                }
                
                await ReceiptDAO.create(
                    session_id=chat_id,
                    user_id="default",
                    topics=[subject] if subject else [],
                    duration_min=msg_count * 2,  # Rough estimate
                    stuck_points=stuck,
                    learner_state=learner_state,
                    summary=f"Chat session: {msg_count} messages on {subject}",
                )
                print(f"ExecutionReceipt generated for chat {chat_id}")
                state["stuck_points"] = []  # Reset
            except Exception as receipt_err:
                print(f"ExecutionReceipt failed: {receipt_err}")

    def on_visual_mode_change(e):
        """Toggle illustrated teaching mode."""
        state["visual_mode"] = bool(getattr(e.control, "value", False))
        refresh_system_prompt()
    
    def on_send(e):
        if state["page"] is None:
            state["page"] = e.page if hasattr(e, "page") else (e.control.page if hasattr(e, "control") else None)
        if state["page"]:
            register_cleanup(state["page"])
            state["page"].run_task(handle_send)
    
    input_field.on_submit = on_send
    
    send_btn = ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=Colors.TEXT_PRIMARY, icon_size=20, on_click=on_send)
    
    input_capsule = ft.Container(
        content=ft.Row([input_field, send_btn], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="rgba(255,255,255,0.05)", border=ft.border.all(1, Colors.BORDER_GLASS),
        border_radius=50, padding=ft.padding.only(left=4, right=8, top=4, bottom=4),
    )
    
    # Left sidebar
    sidebar = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("Chats", size=14, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.Icons.ADD_ROUNDED, icon_size=20, icon_color=Colors.TEXT_PRIMARY, on_click=on_new_chat_click),
                ]),
                padding=ft.padding.only(left=12, right=4, top=8, bottom=4),
            ),
            ft.Container(content=chat_list_view, expand=True),
        ]),
        width=220, bgcolor="rgba(255,255,255,0.02)",
        border=ft.border.only(right=ft.BorderSide(1, Colors.BORDER_GLASS)),
    )
    
    # Chat area
    visual_mode_switch = ft.Switch(
        label="Visual mode",
        value=state["visual_mode"],
        on_change=on_visual_mode_change,
        active_color=Colors.TEXT_PRIMARY,
    )
    
    chat_header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column([chat_title_text, chat_subtitle_text], spacing=2, expand=True),
                ft.Container(content=visual_mode_switch, padding=ft.padding.only(left=8)),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(bottom=12),
        border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_GLASS)),
    )
    
    chat_area = ft.Column([chat_header, message_list, ft.Container(height=8), input_capsule], expand=True, spacing=0)
    
    main_content = ft.Row([sidebar, ft.Container(content=chat_area, expand=True, padding=16)], expand=True, spacing=0)
    
    glass_view = GlassContainer(content=main_content, padding=0, expand=True)
    
    # Initialize
    def on_build(e):
        state["page"] = e.page if hasattr(e, "page") else (e.control.page if hasattr(e, "control") else None)
        if state["page"]:
            register_cleanup(state["page"])
            state["page"].run_task(load_chats)
    
    container = ft.Container(
        content=glass_view, expand=True,
        margin=ft.margin.only(top=Sizes.PAGE_MARGIN, right=Sizes.PAGE_MARGIN, bottom=Sizes.PAGE_MARGIN),
        on_hover=on_build,  # Trigger init on first interaction
    )
    
    return container
