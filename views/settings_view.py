# ===========================================================================
# Chronos AI Learning Companion
# File: views/settings_view.py
# Purpose: Settings page with left-right layout
# ===========================================================================

"""
Settings View

Left-right layout:
- Left: Group navigation (General, Learning, Adaptation, Tutor, Memory)
- Right: Form panel for selected group
"""

import flet as ft
from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer, GlassCard
from stores.settings_store import SettingsStore
from i18n.texts import t, set_language, get_current_language


# =============================================================================
# Group Navigation (Left Panel)
# =============================================================================

def _create_group_item(label: str, icon: str, is_selected: bool, on_click) -> ft.Container:
    """Create a single group navigation item."""
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=18, color=Colors.TEXT_PRIMARY if is_selected else Colors.TEXT_SECONDARY),
            ft.Container(width=10),
            ft.Text(
                label, size=13,
                weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL,
                color=Colors.TEXT_PRIMARY if is_selected else Colors.TEXT_SECONDARY,
            ),
        ]),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        bgcolor=f"rgba(255,255,255,0.08)" if is_selected else "transparent",
        border_radius=10,
        on_click=on_click,
        ink=True,
    )


# =============================================================================
# Form Components
# =============================================================================

def _create_section_header(title: str, desc: str = "") -> ft.Container:
    """Create a form section header."""
    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            ft.Text(desc, size=12, color=Colors.TEXT_MUTED) if desc else ft.Container(),
        ], spacing=4),
        padding=ft.padding.only(bottom=16),
    )


def _create_field_row(label: str, desc: str, control: ft.Control) -> ft.Container:
    """Create a form field row with label and control."""
    return ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text(label, size=13, color=Colors.TEXT_PRIMARY),
                ft.Text(desc, size=11, color=Colors.TEXT_MUTED) if desc else ft.Container(),
            ], spacing=2, expand=True),
            control,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.symmetric(vertical=12),
        border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_GLASS)),
    )


def _create_switch(value: bool, on_change) -> ft.Switch:
    """Create a styled switch."""
    return ft.Switch(value=value, active_color=Colors.TEXT_PRIMARY, on_change=on_change)


def _create_dropdown(value: str, options: list, on_change) -> ft.Dropdown:
    """Create a styled dropdown."""
    return ft.Dropdown(
        value=value,
        options=[ft.dropdown.Option(key=k, text=v) for k, v in options],
        width=150,
        border_color=Colors.BORDER_GLASS,
        bgcolor=f"rgba(255,255,255,0.05)",
        color=Colors.TEXT_PRIMARY,
        on_change=on_change,
    )


# =============================================================================
# Form Panels
# =============================================================================

def _create_general_form(store: SettingsStore, rebuild_view, mark_dirty=None) -> ft.Container:
    """General settings form."""
    settings = store.get()
    
    def on_language_change(e):
        store.update(language=e.control.value)
        set_language(e.control.value)
        rebuild_view()  # Rebuild to refresh all text
    
    def on_checkin_url_change(e):
        store.update(checkin_url=e.control.value)
        if mark_dirty:
            mark_dirty()
    
    def on_checkin_auto_change(e):
        store.update(checkin_auto_open=e.control.value)
        if mark_dirty:
            mark_dirty()
    
    return ft.Column([
        _create_section_header(t("settings.general.title")),
        _create_field_row(
            t("settings.general.language"), "",
            _create_dropdown(
                settings.language,
                [("en", t("settings.general.language_en")), ("zh-CN", t("settings.general.language_zh"))],
                on_language_change,
            ),
        ),
        _create_section_header(t("settings.checkin.title"), t("settings.checkin.description")),
        _create_field_row(
            t("settings.checkin.url"), t("settings.checkin.url_desc"),
            ft.TextField(
                value=getattr(settings, "checkin_url", ""),
                hint_text=t("settings.checkin.url_placeholder"),
                width=260,
                border_color=Colors.BORDER_GLASS,
                bgcolor="rgba(255,255,255,0.05)",
                color=Colors.TEXT_PRIMARY,
                on_change=on_checkin_url_change,
            ),
        ),
        _create_field_row(
            t("settings.checkin.auto_open"), t("settings.checkin.auto_open_desc"),
            _create_switch(getattr(settings, "checkin_auto_open", False), on_checkin_auto_change),
        ),
    ])


def _create_learning_form(store: SettingsStore, mark_dirty) -> ft.Container:
    """Learning preferences form."""
    settings = store.get()
    
    def on_target_change(e):
        store.update(daily_target_minutes=int(e.control.value))
        mark_dirty()
    
    def on_session_change(e):
        store.update(preferred_session_length=int(e.control.value))
        mark_dirty()
    
    def on_mode_change(e):
        store.update(mode_preference=e.control.value)
        mark_dirty()
    
    return ft.Column([
        _create_section_header(t("settings.learning.title"), t("settings.learning.description")),
        _create_field_row(
            t("settings.learning.daily_target"), t("settings.learning.daily_target_desc"),
            ft.TextField(
                value=str(settings.daily_target_minutes), width=80, text_align=ft.TextAlign.CENTER,
                border_color=Colors.BORDER_GLASS, bgcolor=f"rgba(255,255,255,0.05)",
                color=Colors.TEXT_PRIMARY, on_change=on_target_change,
            ),
        ),
        _create_field_row(
            t("settings.learning.session_length"), t("settings.learning.session_length_desc"),
            _create_dropdown(
                str(settings.preferred_session_length),
                [("25", "25 min"), ("45", "45 min"), ("60", "60 min")],
                on_session_change,
            ),
        ),
        _create_field_row(
            t("settings.learning.mode_preference"), t("settings.learning.mode_preference_desc"),
            _create_dropdown(
                settings.mode_preference,
                [
                    ("recovery", t("settings.learning.mode_recovery")),
                    ("standard", t("settings.learning.mode_standard")),
                    ("sprint", t("settings.learning.mode_sprint")),
                ],
                on_mode_change,
            ),
        ),
    ])


def _create_adaptation_form(store: SettingsStore, mark_dirty) -> ft.Container:
    """Adaptation settings form."""
    settings = store.get()
    
    def on_adapt_change(e):
        store.update(adapt_plan_automatically=e.control.value)
        mark_dirty()
    
    def on_approval_change(e):
        store.update(approval_required=e.control.value)
        mark_dirty()
    
    def on_sensitivity_change(e):
        store.update(sensitivity=e.control.value)
        mark_dirty()
    
    return ft.Column([
        _create_section_header(t("settings.adaptation.title"), t("settings.adaptation.description")),
        _create_field_row(
            t("settings.adaptation.adapt_auto"), t("settings.adaptation.adapt_auto_desc"),
            _create_switch(settings.adapt_plan_automatically, on_adapt_change),
        ),
        _create_field_row(
            t("settings.adaptation.approval_required"), t("settings.adaptation.approval_required_desc"),
            _create_switch(settings.approval_required, on_approval_change),
        ),
        _create_field_row(
            t("settings.adaptation.sensitivity"), t("settings.adaptation.sensitivity_desc"),
            _create_dropdown(
                settings.sensitivity,
                [
                    ("low", t("settings.adaptation.sensitivity_low")),
                    ("medium", t("settings.adaptation.sensitivity_medium")),
                    ("high", t("settings.adaptation.sensitivity_high")),
                ],
                on_sensitivity_change,
            ),
        ),
    ])


def _create_tutor_form(store: SettingsStore, mark_dirty) -> ft.Container:
    """Tutor settings form."""
    settings = store.get()
    
    def on_style_change(e):
        store.update(default_tutor_style=e.control.value)
        mark_dirty()

    def on_use_memory_change(e):
        store.update(tutor_use_memory=e.control.value)
        mark_dirty()
    
    return ft.Column([
        _create_section_header(t("settings.tutor.title"), t("settings.tutor.description")),
        _create_field_row(
            t("settings.tutor.style"), t("settings.tutor.style_desc"),
            _create_dropdown(
                settings.default_tutor_style,
                [
                    ("socratic", t("settings.tutor.style_socratic")),
                    ("direct", t("settings.tutor.style_direct")),
                    ("practice_first", t("settings.tutor.style_practice")),
                ],
                on_style_change,
            ),
        ),
        _create_field_row(
            t("settings.tutor.use_memory"), t("settings.tutor.use_memory_desc"),
            _create_switch(getattr(settings, "tutor_use_memory", True), on_use_memory_change),
        ),
    ])


def _create_memory_form(store: SettingsStore, mark_dirty) -> ft.Container:
    """Memory settings form."""
    settings = store.get()
    
    def on_enable_change(e):
        store.update(enable_memory=e.control.value)
        mark_dirty()
    
    return ft.Column([
        _create_section_header(t("settings.memory.title"), t("settings.memory.description")),
        _create_field_row(
            t("settings.memory.enable"), t("settings.memory.enable_desc"),
            _create_switch(settings.enable_memory, on_enable_change),
        ),
    ])


def _create_api_form(store: SettingsStore, mark_dirty) -> ft.Container:
    """API configuration form."""
    settings = store.get()
    
    def on_key_change(e):
        store.update(gemini_api_key=e.control.value)
        mark_dirty()
    
    def on_model_change(e):
        store.update(gemini_model=e.control.value)
        mark_dirty()
    
    # Password field for API key
    api_key_field = ft.TextField(
        value=settings.gemini_api_key,
        password=True,
        can_reveal_password=True,
        width=300,
        hint_text=t("settings.api.api_key_placeholder"),
        border_color=Colors.BORDER_GLASS,
        bgcolor=f"rgba(255,255,255,0.05)",
        color=Colors.TEXT_PRIMARY,
        on_change=on_key_change,
    )
    
    return ft.Column([
        _create_section_header(t("settings.api.title"), t("settings.api.description")),
        _create_field_row(
            t("settings.api.api_key"), t("settings.api.api_key_desc"),
            api_key_field,
        ),
        _create_field_row(
            t("settings.api.model"), t("settings.api.model_desc"),
            _create_dropdown(
                settings.gemini_model,
                [
                    ("gemini-2.5-flash", "Gemini 2.5 Flash"),
                    ("gemini-2.0-flash", "Gemini 2.0 Flash"),
                    ("gemini-1.5-pro", "Gemini 1.5 Pro"),
                ],
                on_model_change,
            ),
        ),
    ])


# =============================================================================
# Settings View Main
# =============================================================================

def create_settings_view() -> ft.Container:
    """Create the Settings page."""
    store = SettingsStore.get_instance()
    
    # State
    state = {"group": "general", "dirty": False}
    
    # References for dynamic updates
    form_container = ft.Container(expand=True)
    dirty_indicator = ft.Container(visible=False)
    snackbar = ft.SnackBar(content=ft.Text(""))
    
    # Groups config
    groups = [
        ("general", t("settings.groups.general"), ft.Icons.SETTINGS_OUTLINED),
        ("learning", t("settings.groups.learning"), ft.Icons.SCHOOL_OUTLINED),
        ("adaptation", t("settings.groups.adaptation"), ft.Icons.AUTO_FIX_HIGH_OUTLINED),
        ("tutor", t("settings.groups.tutor"), ft.Icons.PSYCHOLOGY_OUTLINED),
        ("memory", t("settings.groups.memory"), ft.Icons.MEMORY_OUTLINED),
        ("api", t("settings.groups.api"), ft.Icons.KEY_OUTLINED),
    ]
    
    def mark_dirty():
        state["dirty"] = True
        dirty_indicator.visible = True
        dirty_indicator.update()
    
    def rebuild_view():
        # Trigger full page rebuild by updating the form
        update_form()
        update_nav()
    
    def update_form():
        forms = {
            "general": lambda: _create_general_form(store, rebuild_view, mark_dirty),
            "learning": lambda: _create_learning_form(store, mark_dirty),
            "adaptation": lambda: _create_adaptation_form(store, mark_dirty),
            "tutor": lambda: _create_tutor_form(store, mark_dirty),
            "memory": lambda: _create_memory_form(store, mark_dirty),
            "api": lambda: _create_api_form(store, mark_dirty),
        }
        form_container.content = forms.get(state["group"], forms["general"])()
        form_container.update()
    
    def update_nav():
        nav_list.controls = [
            _create_group_item(
                label, icon, state["group"] == key,
                lambda e, k=key: on_group_select(k),
            )
            for key, label, icon in groups
        ]
        nav_list.update()
    
    def on_group_select(group: str):
        state["group"] = group
        update_form()
        update_nav()
    
    def on_save(e):
        store.save()
        state["dirty"] = False
        dirty_indicator.visible = False
        dirty_indicator.update()
        # Show snackbar
        snackbar.content = ft.Text(t("settings.saved"))
        snackbar.open = True
        snackbar.update()
    
    # Navigation list
    nav_list = ft.Column(
        controls=[
            _create_group_item(label, icon, state["group"] == key, lambda e, k=key: on_group_select(k))
            for key, label, icon in groups
        ],
        spacing=4,
    )
    
    # Header with save button
    header = ft.Row([
        ft.Column([
            ft.Text(t("settings.title"), size=22, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            ft.Text(t("settings.subtitle"), size=13, color=Colors.TEXT_SECONDARY),
        ], spacing=4),
        ft.Container(expand=True),
        ft.Container(
            content=ft.Row([
                ft.Container(width=8, height=8, bgcolor=Colors.WARNING, border_radius=4),
                ft.Container(width=6),
                ft.Text(t("settings.unsaved"), size=11, color=Colors.WARNING),
            ]),
            visible=False,
            ref=ft.Ref(),  # Will assign dirty_indicator
        ),
        ft.Container(width=12),
        ft.FilledButton(
            text=t("settings.save"), icon=ft.Icons.SAVE_ROUNDED,
            style=ft.ButtonStyle(bgcolor=Colors.TEXT_PRIMARY, color=Colors.BG_PRIMARY),
            on_click=on_save,
        ),
    ])
    
    # Assign dirty indicator
    dirty_indicator = header.controls[3]
    dirty_indicator.visible = False
    
    # Initial form
    form_container.content = _create_general_form(store, rebuild_view, mark_dirty)
    
    # Left panel
    left_panel = ft.Container(
        content=ft.Column([
            ft.Text(t("settings.groups.general").upper(), size=10, color=Colors.TEXT_MUTED, weight=ft.FontWeight.BOLD),
            ft.Container(height=8),
            nav_list,
        ]),
        width=200,
        padding=ft.padding.only(right=24),
        border=ft.border.only(right=ft.BorderSide(1, Colors.BORDER_GLASS)),
    )
    
    # Right panel
    right_panel = ft.Container(
        content=ft.Column([
            form_container,
        ], scroll=ft.ScrollMode.AUTO, expand=True),
        expand=True,
        padding=ft.padding.only(left=24),
    )
    
    # Main content
    content = ft.Column([
        header,
        ft.Container(height=24),
        ft.Row([left_panel, right_panel], expand=True),
        snackbar,
    ], expand=True)
    
    glass_view = GlassContainer(content=content, padding=Sizes.CONTENT_PADDING, expand=True)
    
    return ft.Container(
        content=glass_view, expand=True,
        margin=ft.margin.only(top=Sizes.PAGE_MARGIN, right=Sizes.PAGE_MARGIN, bottom=Sizes.PAGE_MARGIN),
    )
