# ============================================================================
# Chronos AI 学习伴侣 - 侧边栏组件
# 文件: sidebar.py
# 风格: Modern Clean Dashboard - 极简黑白高级感
# ============================================================================

import flet as ft
from typing import Callable, Optional


# ============================================================================
# 设计常量
# ============================================================================
class DesignTokens:
    """设计系统 - 颜色和尺寸常量"""
    
    # 颜色系统
    BG_PRIMARY = "#000000"       # 页面主背景 - 纯黑
    BG_CARD = "#1A1A1A"          # 卡片背景 - 深灰
    TEXT_PRIMARY = "#FFFFFF"     # 主文本 - 纯白
    TEXT_SECONDARY = "#888888"   # 副文本 - 灰色
    TEXT_MUTED = "#555555"       # 弱化文本
    ACCENT = "#FFFFFF"           # 强调色 - 白色
    INDICATOR = "#FFFFFF"        # 选中指示器
    
    # 尺寸
    SIDEBAR_WIDTH = 220          # 侧边栏宽度
    BORDER_RADIUS = 16           # 圆角大小
    CARD_PADDING = 20            # 卡片内边距


# ============================================================================
# 路由映射
# ============================================================================
ROUTE_MAP = {
    0: "/",          # 仪表盘
    1: "/chat",      # AI 对话
    2: "/graph",     # 知识图谱
    3: "/settings",  # 设置
}

INDEX_MAP = {v: k for k, v in ROUTE_MAP.items()}


def get_route_from_index(index: int) -> str:
    """根据导航索引获取路由路径"""
    return ROUTE_MAP.get(index, "/")


def get_index_from_route(route: str) -> int:
    """根据路由路径获取导航索引"""
    return INDEX_MAP.get(route, 0)


# ============================================================================
# 侧边栏导航项组件
# ============================================================================
def create_nav_item(
    icon: str,
    label: str,
    is_selected: bool,
    on_click: Callable,
) -> ft.Container:
    """
    创建单个导航项
    
    选中状态：左侧白色指示条 + 背景变浅灰
    未选中：透明背景，灰色图标
    """
    return ft.Container(
        content=ft.Row(
            controls=[
                # 左侧选中指示器（极细白线）
                ft.Container(
                    width=3,
                    height=24,
                    bgcolor=DesignTokens.INDICATOR if is_selected else "transparent",
                    border_radius=2,
                ),
                ft.Container(width=12),  # 间距
                # 图标
                ft.Icon(
                    name=icon,
                    size=20,
                    color=DesignTokens.TEXT_PRIMARY if is_selected else DesignTokens.TEXT_SECONDARY,
                ),
                ft.Container(width=12),  # 间距
                # 文字标签
                ft.Text(
                    label,
                    size=14,
                    weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL,
                    color=DesignTokens.TEXT_PRIMARY if is_selected else DesignTokens.TEXT_SECONDARY,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=8, vertical=12),
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE) if is_selected else "transparent",
        on_click=on_click,
        ink=True,  # 点击波纹效果
    )


# ============================================================================
# 侧边栏主组件
# ============================================================================
def create_sidebar(
    page: ft.Page,
    selected_index: int = 0,
    on_destination_change: Optional[Callable[[int], None]] = None
) -> ft.Container:
    """
    创建现代极简风格的侧边栏
    
    特点：
    - 纯黑背景，与主背景融为一体
    - 极简的"图标+文字"导航项
    - 选中状态用左侧白线指示
    """
    
    # 导航项配置
    nav_items = [
        {"icon": ft.Icons.DASHBOARD_ROUNDED, "label": "仪表盘", "route": "/"},
        {"icon": ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED, "label": "AI 对话", "route": "/chat"},
        {"icon": ft.Icons.HUB_OUTLINED, "label": "知识图谱", "route": "/graph"},
        {"icon": ft.Icons.SETTINGS_OUTLINED, "label": "设置", "route": "/settings"},
    ]
    
    def handle_nav_click(index: int):
        """处理导航点击"""
        def handler(e):
            if on_destination_change:
                on_destination_change(index)
        return handler
    
    # 创建导航项列表
    nav_controls = []
    for i, item in enumerate(nav_items):
        nav_controls.append(
            create_nav_item(
                icon=item["icon"],
                label=item["label"],
                is_selected=(i == selected_index),
                on_click=handle_nav_click(i),
            )
        )
    
    # 侧边栏容器
    sidebar = ft.Container(
        content=ft.Column(
            controls=[
                # ============================================================
                # Logo 区域
                # ============================================================
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    "C",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=DesignTokens.BG_PRIMARY,
                                ),
                                width=36,
                                height=36,
                                bgcolor=DesignTokens.TEXT_PRIMARY,
                                border_radius=10,
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(width=12),
                            ft.Text(
                                "Chronos",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=DesignTokens.TEXT_PRIMARY,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    padding=ft.padding.only(left=16, top=24, bottom=32),
                ),
                
                # ============================================================
                # 导航项列表
                # ============================================================
                ft.Container(
                    content=ft.Column(
                        controls=nav_controls,
                        spacing=4,
                    ),
                    padding=ft.padding.symmetric(horizontal=12),
                    expand=True,
                ),
                
                # ============================================================
                # 底部用户区域
                # ============================================================
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.CircleAvatar(
                                content=ft.Text("U", weight=ft.FontWeight.BOLD),
                                bgcolor=DesignTokens.BG_CARD,
                                radius=18,
                            ),
                            ft.Container(width=10),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "用户",
                                        size=13,
                                        weight=ft.FontWeight.W_500,
                                        color=DesignTokens.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        "Free Plan",
                                        size=11,
                                        color=DesignTokens.TEXT_MUTED,
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                    ),
                    padding=ft.padding.all(16),
                    border=ft.border.only(
                        top=ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))
                    ),
                ),
            ],
            spacing=0,
        ),
        width=DesignTokens.SIDEBAR_WIDTH,
        bgcolor=DesignTokens.BG_PRIMARY,
        # 右侧分隔线
        border=ft.border.only(
            right=ft.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))
        ),
    )
    
    return sidebar
