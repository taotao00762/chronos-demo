# ===========================================================================
# Chronos AI Learning Companion
# File: styles/tokens.py
# Purpose: Design system tokens - colors, sizes, and typography constants
# ===========================================================================

"""
Design Tokens for Dark Luxury Bento Glass theme.

Color Philosophy:
- Pure black background creates depth
- Glass elements float with subtle transparency
- Purple/Blue accent orbs provide ambient lighting
- White text with varying opacity for hierarchy
"""


class Colors:
    """
    Color palette for Dark Luxury theme.
    
    All colors follow a dark-to-light hierarchy:
    BG_PRIMARY (darkest) -> BG_GLASS -> BORDER -> TEXT (lightest)
    """
    
    # =======================================================================
    # Background Colors
    # =======================================================================
    BG_PRIMARY: str = "#000000"          # Pure black - page background
    BG_SECONDARY: str = "#0A0A0A"        # Near black - subtle variation
    BG_CARD: str = "#1A1A1A"             # Dark gray - solid card background
    
    # =======================================================================
    # Glass Effect Colors (RGBA for transparency)
    # =======================================================================
    BG_GLASS: str = "rgba(255, 255, 255, 0.05)"        # Glass fill
    BG_GLASS_HOVER: str = "rgba(255, 255, 255, 0.08)"  # Glass hover state
    BORDER_GLASS: str = "rgba(255, 255, 255, 0.08)"    # Glass border
    BORDER_GLASS_STRONG: str = "rgba(255, 255, 255, 0.12)"  # Emphasized border
    
    # =======================================================================
    # Text Colors
    # =======================================================================
    TEXT_PRIMARY: str = "#FFFFFF"        # Pure white - headings
    TEXT_SECONDARY: str = "#A0A0A0"      # Light gray - body text
    TEXT_MUTED: str = "#666666"          # Dark gray - captions
    TEXT_DISABLED: str = "#444444"       # Very dark - disabled state
    
    # =======================================================================
    # Accent Colors (for ambient light orbs)
    # =======================================================================
    ACCENT_PURPLE: str = "#8B5CF6"       # Vibrant purple
    ACCENT_PURPLE_DARK: str = "#6D28D9"  # Deep purple
    ACCENT_BLUE: str = "#3B82F6"         # Vibrant blue
    ACCENT_BLUE_DARK: str = "#1D4ED8"    # Deep blue
    ACCENT_CYAN: str = "#06B6D4"         # Cyan for highlights
    
    # =======================================================================
    # Semantic Colors
    # =======================================================================
    SUCCESS: str = "#10B981"             # Green
    WARNING: str = "#F59E0B"             # Amber
    ERROR: str = "#EF4444"               # Red
    INFO: str = "#3B82F6"                # Blue
    
    # =======================================================================
    # Navigation States
    # =======================================================================
    NAV_INDICATOR: str = "#FFFFFF"       # Selected indicator line
    NAV_SELECTED_BG: str = "rgba(255, 255, 255, 0.08)"  # Selected item bg


class Sizes:
    """
    Layout dimensions and spacing constants.
    
    All sizes are in pixels unless otherwise noted.
    """
    
    # =======================================================================
    # Layout Structure
    # =======================================================================
    SIDEBAR_WIDTH: int = 240             # Sidebar width
    SIDEBAR_COLLAPSED: int = 72          # Collapsed sidebar width
    PAGE_MARGIN: int = 16                # Margin around floating panels
    CONTENT_PADDING: int = 24            # Padding inside main content
    
    # =======================================================================
    # Glass Effect
    # =======================================================================
    GLASS_BLUR: int = 15                 # Backdrop blur intensity
    GLASS_BLUR_AMBIENT: int = 120        # Blur for ambient orbs
    GLASS_RADIUS: int = 24               # Border radius for glass panels
    GLASS_RADIUS_SM: int = 16            # Small radius for cards
    GLASS_RADIUS_XS: int = 12            # Extra small for buttons
    
    # =======================================================================
    # Spacing Scale
    # =======================================================================
    SPACING_XS: int = 4
    SPACING_SM: int = 8
    SPACING_MD: int = 16
    SPACING_LG: int = 24
    SPACING_XL: int = 32
    SPACING_XXL: int = 48
    
    # =======================================================================
    # Card Dimensions
    # =======================================================================
    CARD_PADDING: int = 20               # Padding inside cards
    CARD_GAP: int = 16                   # Gap between cards
    CARD_MIN_HEIGHT: int = 160           # Minimum card height
    
    # =======================================================================
    # Navigation
    # =======================================================================
    NAV_ITEM_HEIGHT: int = 44            # Height of nav items
    NAV_INDICATOR_WIDTH: int = 3         # Width of selection indicator
    NAV_ICON_SIZE: int = 20              # Icon size in nav
    
    # =======================================================================
    # Typography Scale
    # =======================================================================
    FONT_SIZE_XS: int = 11
    FONT_SIZE_SM: int = 12
    FONT_SIZE_MD: int = 14
    FONT_SIZE_LG: int = 16
    FONT_SIZE_XL: int = 20
    FONT_SIZE_XXL: int = 28
    FONT_SIZE_DISPLAY: int = 36
    
    # =======================================================================
    # Ambient Orbs
    # =======================================================================
    ORB_SIZE_LARGE: int = 400            # Large ambient orb diameter
    ORB_SIZE_MEDIUM: int = 300           # Medium ambient orb diameter


class Animation:
    """
    Animation timing constants.
    
    All durations are in milliseconds.
    """
    
    DURATION_FAST: int = 150
    DURATION_NORMAL: int = 250
    DURATION_SLOW: int = 400
    
    # Easing curves (for reference in ft.Animation)
    EASE_OUT: str = "easeOut"
    EASE_IN_OUT: str = "easeInOut"
