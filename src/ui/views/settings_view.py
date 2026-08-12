import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
)

from src.core.startup_manager import is_startup_enabled


class SettingsRow(QFrame):
    """
    Android-style sleek compact list item row for settings options.
    Shows title and action control inline, with full description displayed on hover.
    """
    def __init__(self, title: str, description: str, icon_symbol: str = "⚙️", action_widget: QWidget = None, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsRow")
        self.description = description
        
        # Set ToolTip for hover description
        self.setToolTip(description)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(14)

        # Left Icon
        icon_lbl = QLabel(icon_symbol)
        icon_lbl.setStyleSheet("font-size: 18px;")
        icon_lbl.setFixedWidth(28)
        icon_lbl.setToolTip(description)
        layout.addWidget(icon_lbl)

        # Middle Title Label
        title_lbl = QLabel(title)
        title_lbl.setObjectName("SettingsRowTitle")
        title_lbl.setToolTip(description)
        layout.addWidget(title_lbl, stretch=1)

        # Right Action Control Widget
        if action_widget:
            action_widget.setToolTip(description)
            layout.addWidget(action_widget)


class SettingsGroupContainer(QFrame):
    """
    Android-style grouped settings container box with rounded corners.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsGroupContainer")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def add_row(self, row: SettingsRow, is_last: bool = False):
        self.layout.addWidget(row)
        if not is_last:
            divider = QFrame()
            divider.setFixedHeight(1)
            divider.setObjectName("SettingsRowDivider")
            divider.setStyleSheet("background-color: rgba(150, 150, 150, 0.2); border: none;")
            self.layout.addWidget(divider)


class SettingsViewWidget(QWidget):
    """
    Android-style compact Settings view.
    """
    add_exe_requested = pyqtSignal()
    torrent_requested = pyqtSignal()
    export_requested = pyqtSignal()
    import_requested = pyqtSignal()
    startup_toggled = pyqtSignal()
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_buttons = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Title
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header_layout.addWidget(title)

        subtitle = QLabel("Hover over any option to view its description.")
        subtitle.setStyleSheet("font-size: 12px; opacity: 0.8;")
        header_layout.addWidget(subtitle)

        main_layout.addLayout(header_layout)

        # Scroll Area for settings list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)

        # ----------------------------------------------------
        # Section 0: Appearance & Theme
        # ----------------------------------------------------
        sec0_title = QLabel("APPEARANCE & THEME")
        sec0_title.setObjectName("SettingsSectionHeader")
        scroll_layout.addWidget(sec0_title)

        group0 = SettingsGroupContainer()

        theme_widget = QWidget()
        theme_layout = QHBoxLayout(theme_widget)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(8)

        themes_info = [
            ("dark", "🌙 Dark"),
            ("white", "☀️ White"),
            ("dracula", "🔮 Dracula"),
            ("gruvbox", "🪵 Gruvbox"),
        ]

        for theme_key, display_name in themes_info:
            btn = QPushButton(display_name)
            btn.setObjectName("ThemeButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, key=theme_key: self.theme_changed.emit(key))
            theme_layout.addWidget(btn)
            self.theme_buttons[theme_key] = btn

        row_theme = SettingsRow(
            title="Color Theme",
            description="Select application color theme (Dark, White, Dracula, Gruvbox).",
            icon_symbol="🎨",
            action_widget=theme_widget
        )
        group0.add_row(row_theme, is_last=True)
        scroll_layout.addWidget(group0)

        # ----------------------------------------------------
        # Section 1: Game & App Additions
        # ----------------------------------------------------
        sec1_title = QLabel("GAME & APP ADDITIONS")
        sec1_title.setObjectName("SettingsSectionHeader")
        scroll_layout.addWidget(sec1_title)

        group1 = SettingsGroupContainer()

        # Add Custom EXE Row
        self.btn_add_exe = QPushButton("＋ Add .EXE")
        self.btn_add_exe.setObjectName("PrimaryButton")
        self.btn_add_exe.setFixedWidth(130)
        self.btn_add_exe.clicked.connect(self.add_exe_requested.emit)
        row_add = SettingsRow(
            title="Add Custom Executable",
            description="Manually select and add any game or application executable (.exe) from your computer drive.",
            icon_symbol="＋",
            action_widget=self.btn_add_exe
        )
        group1.add_row(row_add, is_last=False)

        # Download Torrent Row
        self.btn_torrent = QPushButton("Download")
        self.btn_torrent.setObjectName("SecondaryButton")
        self.btn_torrent.setFixedWidth(130)
        self.btn_torrent.clicked.connect(self.torrent_requested.emit)
        row_torrent = SettingsRow(
            title="Download Torrent / Magnet Link",
            description="Download games directly via torrent files or magnet links using built-in high-speed aria2 engine.",
            icon_symbol="📥",
            action_widget=self.btn_torrent
        )
        group1.add_row(row_torrent, is_last=True)

        scroll_layout.addWidget(group1)

        # ----------------------------------------------------
        # Section 2: Data & Backup
        # ----------------------------------------------------
        sec2_title = QLabel("DATA & BACKUP MANAGEMENT")
        sec2_title.setObjectName("SettingsSectionHeader")
        scroll_layout.addWidget(sec2_title)

        group2 = SettingsGroupContainer()

        # Export Data Row
        self.btn_export = QPushButton("📂 Export")
        self.btn_export.setObjectName("SecondaryButton")
        self.btn_export.setFixedWidth(130)
        self.btn_export.clicked.connect(self.export_requested.emit)
        row_export = SettingsRow(
            title="Export Library Data File",
            description="Save a JSON backup file containing all tracked games, playtime records, and configuration data.",
            icon_symbol="📂",
            action_widget=self.btn_export
        )
        group2.add_row(row_export, is_last=False)

        # Import Data Row
        self.btn_import = QPushButton("📂 Import")
        self.btn_import.setObjectName("SecondaryButton")
        self.btn_import.setFixedWidth(130)
        self.btn_import.clicked.connect(self.import_requested.emit)
        row_import = SettingsRow(
            title="Import Library Data File",
            description="Restore your game library and playtime history from a previously saved JSON backup file.",
            icon_symbol="📂",
            action_widget=self.btn_import
        )
        group2.add_row(row_import, is_last=True)

        scroll_layout.addWidget(group2)

        # ----------------------------------------------------
        # Section 3: System Preferences
        # ----------------------------------------------------
        sec3_title = QLabel("SYSTEM PREFERENCES")
        sec3_title.setObjectName("SettingsSectionHeader")
        scroll_layout.addWidget(sec3_title)

        group3 = SettingsGroupContainer()

        # Startup Row
        self.btn_startup = QPushButton()
        self.btn_startup.setCheckable(True)
        self.btn_startup.setFixedWidth(130)
        self.btn_startup.clicked.connect(self.startup_toggled.emit)

        row_startup = SettingsRow(
            title="Launch at Windows Startup",
            description="Automatically run GameTracker in the background when Windows boots up so all playtime is tracked.",
            icon_symbol="🚀",
            action_widget=self.btn_startup
        )
        group3.add_row(row_startup, is_last=True)

        scroll_layout.addWidget(group3)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)

        main_layout.addWidget(scroll, stretch=1)

        self.update_startup_state()

    def set_active_theme(self, active_theme_key: str):
        active_theme_key = active_theme_key.lower()
        for key, btn in self.theme_buttons.items():
            is_active = (key == active_theme_key)
            btn.setChecked(is_active)

    def update_startup_state(self):
        enabled = is_startup_enabled()
        self.btn_startup.setChecked(enabled)
        if enabled:
            self.btn_startup.setText("🚀 ENABLED")
            self.btn_startup.setObjectName("SecondaryButton")
        else:
            self.btn_startup.setText("Enable")
            self.btn_startup.setObjectName("PrimaryButton")
        self.btn_startup.setStyle(self.btn_startup.style())

    def refresh_settings(self):
        self.update_startup_state()

