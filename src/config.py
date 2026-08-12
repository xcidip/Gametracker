import os
import sys
from pathlib import Path

# Base Paths
APP_NAME = "GameTracker"
APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
APP_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = APP_DIR / "library.json"
ICONS_DIR = APP_DIR / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# Application Settings Defaults
POLL_INTERVAL_SECONDS = 1.0  # Time tracking refresh rate
AUTO_SAVE_INTERVAL_SECONDS = 30.0

# UI Theme Palette (Dark Velvet & Neon Glow)
COLOR_BG_PRIMARY = "#0F111A"
COLOR_BG_SECONDARY = "#181B28"
COLOR_CARD_BG = "#1E2235"
COLOR_CARD_HOVER = "#272C45"
COLOR_ACCENT = "#6C5CE7"
COLOR_ACCENT_HOVER = "#5B4BC4"
COLOR_CYAN = "#00CEC9"
COLOR_SUCCESS = "#00B894"
COLOR_DANGER = "#FF7675"
COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_TEXT_MUTED = "#8E9BB0"
COLOR_BORDER = "#2B304A"

def format_playtime(seconds: float, verbose: bool = False) -> str:
    """Formats seconds into human-readable string like '12h', '45m', or '35s'."""
    seconds = int(max(0, seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if verbose:
        parts = []
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        elif minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            if secs > 0:
                parts.append(f"{secs} second{'s' if secs != 1 else ''}")
        else:
            parts.append(f"{secs} second{'s' if secs != 1 else ''}")
        return " ".join(parts)

    if hours > 0:
        return f"{hours}h"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{secs}s"
