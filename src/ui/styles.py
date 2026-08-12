THEME_PALETTES = {
    "dark": {
        "name": "Dark",
        "bg_main": "#0F111A",
        "bg_sidebar": "#141724",
        "card_bg": "#1E2235",
        "card_hover": "#24293E",
        "border": "#2B304A",
        "text_primary": "#FFFFFF",
        "text_muted": "#8E9BB0",
        "accent": "#6C5CE7",
        "accent_hover": "#5B4BC4",
        "accent_pressed": "#4A3BB3",
        "cyan": "#00CEC9",
        "success": "#00B894",
        "danger_bg": "#272C45",
        "danger_text": "#FF7675",
    },
    "white": {
        "name": "White",
        "bg_main": "#F4F5F9",
        "bg_sidebar": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "card_hover": "#EAEFF6",
        "border": "#D0D7DE",
        "text_primary": "#1F2328",
        "text_muted": "#656D76",
        "accent": "#4A6CF7",
        "accent_hover": "#3859E0",
        "accent_pressed": "#2A47C8",
        "cyan": "#0088CC",
        "success": "#10AC84",
        "danger_bg": "#FFEBE9",
        "danger_text": "#D1242F",
    },
    "dracula": {
        "name": "Dracula",
        "bg_main": "#282A36",
        "bg_sidebar": "#21222C",
        "card_bg": "#44475A",
        "card_hover": "#383A59",
        "border": "#6272A4",
        "text_primary": "#F8F8F2",
        "text_muted": "#94A3B8",
        "accent": "#BD93F9",
        "accent_hover": "#A375F2",
        "accent_pressed": "#8B57E0",
        "cyan": "#8BE9FD",
        "success": "#50FA7B",
        "danger_bg": "#3B2836",
        "danger_text": "#FF5555",
    },
    "gruvbox": {
        "name": "Gruvbox",
        "bg_main": "#282828",
        "bg_sidebar": "#1D2021",
        "card_bg": "#3C3836",
        "card_hover": "#504945",
        "border": "#665C54",
        "text_primary": "#EBDBB2",
        "text_muted": "#A89984",
        "accent": "#FE8019",
        "accent_hover": "#D65D0E",
        "accent_pressed": "#AF3A03",
        "cyan": "#8EC07C",
        "success": "#B8BB26",
        "danger_bg": "#3C1F1E",
        "danger_text": "#FB4934",
    },
}


def get_theme_stylesheet(theme_key: str = "dark") -> str:
    p = THEME_PALETTES.get(theme_key.lower(), THEME_PALETTES["dark"])
    return f"""
QMainWindow {{
    background-color: {p['bg_main']};
}}

QWidget {{
    font-family: 'Segoe UI', Arial, sans-serif;
    color: {p['text_primary']};
}}

/* Sidebar */
#Sidebar {{
    background-color: {p['bg_sidebar']};
    border-right: 1px solid {p['border']};
}}

#SidebarTitle {{
    font-size: 20px;
    font-weight: bold;
    color: {p['accent']};
    padding: 15px 10px;
}}

#NavButton {{
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 12px 18px;
    text-align: left;
    font-size: 14px;
    font-weight: 600;
    color: {p['text_muted']};
}}

#NavButton:hover {{
    background-color: {p['card_hover']};
    color: {p['text_primary']};
}}

#NavButton:checked {{
    background-color: {p['accent']};
    color: #FFFFFF;
}}

/* Header & Search Bar */
#HeaderFrame {{
    background-color: {p['bg_sidebar']};
    border-bottom: 1px solid {p['border']};
    padding: 10px;
}}

QLineEdit {{
    background-color: {p['card_bg']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 8px 14px;
    color: {p['text_primary']};
    font-size: 13px;
}}

QLineEdit:focus {{
    border: 1px solid {p['accent']};
}}

QComboBox {{
    background-color: {p['card_bg']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 6px 12px;
    color: {p['text_primary']};
}}

QComboBox::drop-down {{
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: {p['bg_sidebar']};
    border: 1px solid {p['border']};
    selection-background-color: {p['accent']};
    color: {p['text_primary']};
}}

/* Action Buttons */
QPushButton#PrimaryButton {{
    background-color: {p['accent']};
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {p['accent_hover']};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: {p['accent_pressed']};
}}

QPushButton#SecondaryButton {{
    background-color: {p['card_bg']};
    color: {p['cyan']};
    border: 1px solid {p['cyan']};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
}}

QPushButton#SecondaryButton:hover {{
    background-color: {p['cyan']};
    color: {p['bg_main']};
}}

QPushButton#DangerButton {{
    background-color: {p['danger_bg']};
    color: {p['danger_text']};
    border: 1px solid {p['danger_text']};
    border-radius: 8px;
    padding: 6px 12px;
}}

QPushButton#DangerButton:hover {{
    background-color: {p['danger_text']};
    color: #FFFFFF;
}}

/* Theme Switcher Buttons */
QPushButton#ThemeButton {{
    background-color: {p['card_bg']};
    color: {p['text_primary']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
}}

QPushButton#ThemeButton:hover {{
    background-color: {p['card_hover']};
    border-color: {p['accent']};
}}

QPushButton#ThemeButton:checked {{
    background-color: {p['accent']};
    color: #FFFFFF;
    border-color: {p['accent']};
}}

/* Settings Row & Containers */
QFrame#SettingsGroupContainer {{
    background-color: {p['card_bg']};
    border: 1px solid {p['border']};
    border-radius: 10px;
}}

QFrame#SettingsRow {{
    background-color: transparent;
    border: none;
}}

QFrame#SettingsRow:hover {{
    background-color: {p['card_hover']};
}}

#SettingsRowTitle {{
    font-size: 14px;
    font-weight: 600;
    color: {p['text_primary']};
}}

#SettingsSectionHeader {{
    font-size: 11px;
    font-weight: bold;
    color: {p['accent']};
    letter-spacing: 1px;
    padding-left: 4px;
}}

/* Collapsible Library Section Header */
QFrame#SectionHeader {{
    background-color: {p['card_bg']};
    border: 1px solid {p['border']};
    border-radius: 10px;
    padding: 6px 12px;
}}

QFrame#SectionHeader:hover {{
    background-color: {p['card_hover']};
    border: 1px solid {p['accent']};
}}

#SectionHeaderArrow {{
    color: {p['accent']};
    font-size: 14px;
    font-weight: bold;
}}

#SectionHeaderTitle {{
    color: {p['text_primary']};
    font-size: 15px;
    font-weight: bold;
}}

#SectionHeaderBadge {{
    background-color: {p['bg_sidebar']};
    color: {p['text_muted']};
    border: 1px solid {p['border']};
    font-size: 11px;
    font-weight: bold;
    border-radius: 10px;
    padding: 2px 8px;
}}

/* Game Card */
QFrame#GameCard {{
    background-color: {p['card_bg']};
    border: 1px solid {p['border']};
    border-radius: 14px;
}}

QFrame#GameCard:hover {{
    background-color: {p['card_hover']};
    border: 1px solid {p['accent']};
}}

#GameTitle {{
    font-size: 14px;
    font-weight: bold;
    color: {p['text_primary']};
}}

#PlaytimeBadge {{
    background-color: {p['bg_sidebar']};
    color: {p['cyan']};
    border-radius: 6px;
    padding: 3px 6px;
    font-size: 11px;
    font-weight: 600;
}}

QFrame#GameCard QPushButton#PrimaryButton {{
    background-color: {p['accent']};
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: bold;
    font-size: 11px;
}}

QFrame#GameCard QPushButton#PrimaryButton:hover {{
    background-color: {p['accent_hover']};
}}

QFrame#GameCard QPushButton#PrimaryButton:pressed {{
    background-color: {p['accent_pressed']};
}}

QFrame#GameCard QPushButton#SecondaryButton {{
    background-color: {p['card_bg']};
    color: {p['cyan']};
    border: 1px solid {p['cyan']};
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: bold;
    font-size: 11px;
}}

QFrame#GameCard QPushButton#SecondaryButton:hover {{
    background-color: {p['cyan']};
    color: {p['bg_main']};
}}

#StatusBadgeRunning {{
    background-color: {p['success']};
    color: #FFFFFF;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}}

#StatusBadgeIdle {{
    background-color: {p['border']};
    color: {p['text_muted']};
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
}}

/* Dialogs */
QDialog {{
    background-color: {p['bg_sidebar']};
}}

QListWidget {{
    background-color: {p['card_bg']};
    border: 1px solid {p['border']};
    border-radius: 10px;
    padding: 5px;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 6px;
    color: {p['text_primary']};
}}

QListWidget::item:hover {{
    background-color: {p['card_hover']};
}}

QListWidget::item:selected {{
    background-color: {p['accent']};
    color: #FFFFFF;
}}

/* ToolTip */
QToolTip {{
    background-color: {p['bg_sidebar']};
    color: {p['text_primary']};
    border: 1px solid {p['accent']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background: {p['bg_main']};
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {p['border']};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {p['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


MAIN_STYLE = get_theme_stylesheet("dark")

