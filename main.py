# ===========================================================================
# Chronos AI Learning Companion
# File: main.py
# Purpose: Application entry point with Settings integration
# ===========================================================================

"""
Chronos - AI Learning Companion

Role-Based Architecture with Settings and i18n support.
"""

import flet as ft
import webbrowser
from styles.tokens import Colors, Sizes
from components.ambient_bg import create_ambient_background
from components.sidebar import create_sidebar
from components.daily_briefing import create_briefing_content
from views.dashboard_view import create_dashboard_view
from views.plan_view import create_plan_view
from views.tutor_view import create_tutor_view
from views.memory_view import create_memory_view
from views.settings_view import create_settings_view
from views.placeholder_views import create_placeholder_view
from views.graph_view import create_graph_view
from router import get_route_from_index, get_index_from_route
from stores.settings_store import SettingsStore
from i18n.texts import t, set_language, TXT


def main(page: ft.Page) -> None:
    """Application entry point."""
    
    # === Initialize Settings Store ===
    store = SettingsStore.get_instance()
    settings = store.get()
    
    # Apply saved language
    set_language(settings.language)
    
    # === Page Configuration ===
    page.title = "Chronos - AI Learning Companion"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = Colors.BG_PRIMARY
    page.padding = 0
    page.spacing = 0
    page.window.min_width = 1000
    page.window.min_height = 700
    page.window.width = 1280
    page.window.height = 800
    
    # === Daily Briefing State ===
    briefing_shown = {"value": False}

    # === Browser Check-in State ===
    checkin_auto_opened = {"value": False}

    def show_snackbar(message: str, target_page: ft.Page = None) -> None:
        page_ref = target_page or page
        page_ref.snack_bar = ft.SnackBar(content=ft.Text(message))
        page_ref.snack_bar.open = True
        page_ref.update()

    def open_checkin(e=None) -> None:
        page_ref = getattr(e, "page", None) or page
        current_settings = store.get()
        checkin_url = (getattr(current_settings, "checkin_url", "") or "").strip()
        if not checkin_url:
            show_snackbar(t("dashboard.checkin_missing"), page_ref)
            return
        try:
            launcher = getattr(page_ref, "launch_url", None)
            if callable(launcher):
                launcher(checkin_url)
            else:
                webbrowser.open(checkin_url)
        except Exception:
            webbrowser.open(checkin_url)

    def maybe_auto_open_checkin() -> None:
        if checkin_auto_opened["value"]:
            return
        current_settings = store.get()
        if not getattr(current_settings, "checkin_auto_open", False):
            return
        checkin_auto_opened["value"] = True
        open_checkin()
    
    def close_briefing(e=None):
        if page.overlay:
            page.overlay.clear()
            page.update()
    
    def show_briefing():
        if briefing_shown["value"]:
            return
        briefing_shown["value"] = True
        
        backdrop = ft.Container(
            bgcolor="rgba(0,0,0,0.7)",
            expand=True,
            on_click=close_briefing,
        )
        briefing = ft.Container(
            content=create_briefing_content(on_accept=close_briefing),
            alignment=ft.alignment.center,
            expand=True,
        )
        page.overlay.append(ft.Stack([backdrop, briefing], expand=True))
        page.update()
    
    # === View Cache (preserve state across navigation) ===
    view_cache = {}
    
    def get_view(route: str) -> ft.Container:
        if route not in view_cache:
            views = {
                "/": lambda: create_dashboard_view(open_checkin),
                "/plan": create_plan_view,
                "/tutor": create_tutor_view,
                "/memory": create_memory_view,
                "/graph": create_graph_view,
                "/settings": create_settings_view,
            }
            view_factory = views.get(route, lambda: create_dashboard_view(open_checkin))
            view_cache[route] = view_factory()
        return view_cache[route]
    
    content_container = ft.Container(content=get_view("/"), expand=True)
    
    def handle_navigate(index: int) -> None:
        page.go(get_route_from_index(index))
    
    def on_route_change(e=None) -> None:
        current_index = get_index_from_route(page.route)
        content_container.content = get_view(page.route)
        
        page.views.clear()
        page.views.append(ft.View(
            route=page.route,
            padding=0,
            bgcolor=Colors.BG_PRIMARY,
            controls=[
                ft.Stack([
                    create_ambient_background(),
                    ft.Row([
                        create_sidebar(current_index, handle_navigate),
                        content_container,
                    ], expand=True, spacing=0),
                ], expand=True),
            ],
        ))
        page.update()
        
        # Show briefing on first load
        if not briefing_shown["value"]:
            show_briefing()
        maybe_auto_open_checkin()
    
    page.on_route_change = on_route_change
    on_route_change()


if __name__ == "__main__":
    ft.app(target=main)
