# Professional color schemes for Hotel Event Manager
OceanSunset_Pallet = ["#001219","#005f73","#0a9396","#94d2bd","#e9d8a6","#ee9b00","#ca6702","#bb3e03","#ae2012","#9b2226"]
Deep_Ocean_Dive = ["#00115e","#002254","#00334a","#004440","#005435","#00652b","#007621"]
Gold_Shades = ["#f9dc5c","#fae588","#fcefb4","#fdf8e1","#f9dc5c"]
Golden_Twilight = ["#000814","#001d3d","#003566","#ffc300","#ffd60a"]

# === ICON GUIDE ===
# Use these emoji icons consistently throughout the app for better UX
ICONS = {
    # Navigation & Sections
    "inventory": "📊",           # Inventory view
    "add_resource": "➕",        # Add new resource
    "events": "📅",             # Planned events
    "create_event": "📝",       # Create new event
    
    # Actions - Positive
    "save": "✓",               # Save/Confirm
    "add": "+",                # Add/New
    "reload": "🔄",            # Reload/Refresh
    "export": "💾",            # Export/Save to file
    "import": "📥",            # Import/Load from file
    "search": "🔍",            # Search/Find
    "ok": "✅",                # Success/OK
    
    # Actions - Negative
    "delete": "🗑️",            # Delete/Remove
    "cancel": "✕",             # Cancel/Close
    "close": "✕",              # Close
    "error": "❌",             # Error
    
    # Status & Feedback
    "loading": "⏳",            # Loading
    "pending": "⌛",            # Pending
    "available": "✓",          # Available
    "unavailable": "✗",        # Unavailable
    "warning": "⚠",            # Warning
    "info": "ℹ",               # Information
    "success": "✓",            # Success
    "failure": "✗",            # Failure
    
    # Resources
    "room": "🏠",              # Room/Space
    "employee": "👤",          # Employee/Person
    "item": "📦",              # Item/Object
    "equipment": "🔧",         # Equipment/Tools
    "time": "⏱️",              # Time/Duration
    "schedule": "📅",          # Schedule
    
    # Settings & System
    "settings": "⚙️",          # Settings
    "appearance": "🎨",        # Appearance/Theme
    "help": "❓",              # Help
    "info_section": "💡",      # Information/Hint
    "accessibility": "♿",      # Accessibility
    
    # Validation
    "valid": "✓",              # Valid
    "invalid": "✗",            # Invalid
    "required": "*",           # Required field
}

# === MODERN PROFESSIONAL THEME ===
class ProfessionalTheme:
    """Modern, professional color scheme optimized for clarity and usability."""
    
    # Semantic colors (context-aware)
    PRIMARY = "#2563EB"        # Blue - main actions
    PRIMARY_HOVER = "#1D4ED8"  # Darker blue - hover state
    PRIMARY_LIGHT = "#DBEAFE"  # Light blue - backgrounds
    
    SUCCESS = "#10B981"        # Green - success/available
    SUCCESS_LIGHT = "#D1FAE5"
    
    WARNING = "#F59E0B"        # Amber - warnings
    WARNING_LIGHT = "#FEF3C7"
    
    DANGER = "#EF4444"         # Red - errors/unavailable
    DANGER_LIGHT = "#FEE2E2"
    
    # Neutral colors
    DARK_BG = "#0F172A"        # Near-black
    DARK_SURFACE = "#1E293B"   # Card/surface
    DARK_BORDER = "#334155"    # Borders
    
    LIGHT_BG = "#F8FAFC"       # Off-white
    LIGHT_SURFACE = "#FFFFFF"  # Card/surface
    LIGHT_BORDER = "#E2E8F0"   # Borders
    
    TEXT_DARK = "#0F172A"      # Dark mode text
    TEXT_LIGHT = "#F1F5F9"     # Light mode text
    TEXT_MUTED = "#94A3B8"     # Muted text
    
    # Spacing (in pixels)
    class Spacing:
        XS = 2
        SM = 4
        MD = 8
        LG = 12
        XL = 16
        XXL = 24
        XXXL = 32
    
    # Typography
    class Typography:
        H1_SIZE = 24
        H2_SIZE = 20
        H3_SIZE = 18
        BODY_SIZE = 14
        SMALL_SIZE = 12
        
        WEIGHT_BOLD = "bold"
        WEIGHT_NORMAL = "normal"

# Default modern spacing for common UI elements
SPACING = {
    "window_padding": 12,      # Main content padding
    "section_padding": 12,     # Between sections
    "component_padding": 8,    # Inside components
    "element_gap": 6,          # Between elements
}

# Common padding/margin combos
PADDINGS = {
    "section": {"padx": 12, "pady": 12},
    "component": {"padx": 8, "pady": 8},
    "tight": {"padx": 6, "pady": 4},
    "spacious": {"padx": 16, "pady": 16},
}