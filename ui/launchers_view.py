import os
import re
import logging
import webbrowser
from typing import List, Dict

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QScrollArea, QLineEdit,
    QMessageBox, QButtonGroup
)

from database import DatabaseManager
from icon_extractor import extract_icon_from_exe
from platform_importer import (
    LAUNCHER_DOWNLOADS,
    is_steam_installed,
    is_epic_installed,
    is_gog_installed,
    scan_all_platform_games,
    scan_steam_games,
    scan_epic_games,
    scan_gog_games
)

logger = logging.getLogger("LaunchersView")


class LauncherCardWidget(QFrame):
    """Card widget for displaying a launcher (Steam, Epic, GOG) with status and download link."""

    def __init__(self, key: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.data = LAUNCHER_DOWNLOADS[key]
        self.init_ui()

    def init_ui(self):
        self.setObjectName("GameCard")
        self.setStyleSheet("""
            QFrame#GameCard {
                background-color: #1E2235;
                border: 1px solid #2B304A;
                border-radius: 14px;
                padding: 16px;
            }
            QFrame#GameCard:hover {
                border: 1px solid #6C5CE7;
                background-color: #24293E;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header: Icon & Title & Installed Badge
        top_layout = QHBoxLayout()

        icon_label = QLabel(self.data["icon"])
        icon_label.setStyleSheet("font-size: 28px;")
        top_layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_label = QLabel(self.data["name"])
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        title_layout.addWidget(title_label)

        # Installed status
        is_installed = False
        if self.key == "Steam":
            is_installed = is_steam_installed()
        elif self.key == "Epic Games":
            is_installed = is_epic_installed()
        elif self.key == "GOG":
            is_installed = is_gog_installed()

        status_label = QLabel()
        if is_installed:
            status_label.setText("✓ Installed")
            status_label.setStyleSheet("color: #00B894; font-weight: bold; font-size: 11px;")
        else:
            status_label.setText("❌ Not Installed")
            status_label.setStyleSheet("color: #FF7675; font-weight: bold; font-size: 11px;")
        title_layout.addWidget(status_label)

        top_layout.addLayout(title_layout, stretch=1)
        layout.addLayout(top_layout)

        # Description
        desc_label = QLabel(self.data["description"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #8E9BB0; font-size: 12px; min-height: 36px;")
        layout.addWidget(desc_label)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_download = QPushButton("⬇️ Download Installer")
        btn_download.setObjectName("PrimaryButton")
        btn_download.setToolTip(f"Download official installer for {self.data['name']}")
        btn_download.clicked.connect(self.on_download_clicked)
        btn_layout.addWidget(btn_download, stretch=1)

        btn_website = QPushButton("🌐 Website")
        btn_website.setObjectName("SecondaryButton")
        btn_website.clicked.connect(self.on_website_clicked)
        btn_layout.addWidget(btn_website)

        layout.addLayout(btn_layout)

    def on_download_clicked(self):
        url = self.data["url"]
        webbrowser.open(url)

    def on_website_clicked(self):
        url = self.data["website"]
        webbrowser.open(url)


class ImportedGameListItemWidget(QWidget):
    """List item widget for an imported/scanned game."""
    import_clicked = pyqtSignal(dict)

    def __init__(self, game_info: dict, parent=None):
        super().__init__(parent)
        self.game_info = game_info
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        # Platform Badge
        platform = self.game_info.get("platform", "Game")
        badge = QLabel(f" {platform} ")
        badge_style = "border-radius: 6px; font-weight: bold; font-size: 11px; padding: 4px 8px; color: white;"
        if platform == "Steam":
            badge_style += " background-color: #171A21; border: 1px solid #66C0F4; color: #66C0F4;"
        elif platform == "Epic Games":
            badge_style += " background-color: #0078F2; color: white;"
        elif platform == "GOG":
            badge_style += " background-color: #7B1FA2; color: white;"
        else:
            badge_style += " background-color: #6C5CE7; color: white;"
        badge.setStyleSheet(badge_style)
        layout.addWidget(badge)

        # Game Details
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_label = QLabel(self.game_info["name"])
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        info_layout.addWidget(name_label)

        sub_label = QLabel(f"{self.game_info['exe_path']}")
        sub_label.setStyleSheet("font-size: 11px; color: #8E9BB0;")
        info_layout.addWidget(sub_label)

        layout.addLayout(info_layout, stretch=1)

        # Action Button
        self.btn_add = QPushButton("＋ Import to Library")
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_add.setFixedSize(140, 32)
        self.btn_add.clicked.connect(lambda: self.import_clicked.emit(self.game_info))
        layout.addWidget(self.btn_add)


class LaunchersViewWidget(QWidget):
    """
    Main view widget for downloading Store Launchers and importing games from Steam, Epic, GOG.
    """
    library_updated = pyqtSignal()

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.scanned_games: List[dict] = []
        self.current_platform_filter = "All"

        self.init_ui()
        self.refresh_scanned_games()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(20)

        # 1. Header Section
        header_layout = QVBoxLayout()
        title_label = QLabel("🌐 Store Launchers & Platform Game Importer")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #6C5CE7;")
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("Download official launchers or scan and import your installed Steam, Epic Games, and GOG library games in 1 click.")
        subtitle_label.setStyleSheet("color: #8E9BB0; font-size: 13px;")
        header_layout.addWidget(subtitle_label)

        root_layout.addLayout(header_layout)

        # 2. Launcher Download Cards (Steam, Epic, GOG)
        launchers_layout = QHBoxLayout()
        launchers_layout.setSpacing(16)

        for key in ["Steam", "Epic Games", "GOG"]:
            card = LauncherCardWidget(key)
            launchers_layout.addWidget(card)

        root_layout.addLayout(launchers_layout)

        # 3. Game Import Section Header
        import_header = QLabel("📥 Import Games from Platforms")
        import_header.setStyleSheet("font-size: 17px; font-weight: bold; color: #FFFFFF; margin-top: 10px;")
        root_layout.addWidget(import_header)

        # Filter & Action Bar
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)

        # Platform Filter Buttons
        self.btn_filter_all = QPushButton("All Platforms")
        self.btn_filter_steam = QPushButton("🎮 Steam")
        self.btn_filter_epic = QPushButton("⚡ Epic Games")
        self.btn_filter_gog = QPushButton("🌌 GOG")

        filter_buttons = [self.btn_filter_all, self.btn_filter_steam, self.btn_filter_epic, self.btn_filter_gog]
        for btn in filter_buttons:
            btn.setObjectName("SecondaryButton")
            btn.setCheckable(True)

        self.btn_filter_all.setChecked(True)
        self.btn_filter_all.clicked.connect(lambda: self.set_platform_filter("All"))
        self.btn_filter_steam.clicked.connect(lambda: self.set_platform_filter("Steam"))
        self.btn_filter_epic.clicked.connect(lambda: self.set_platform_filter("Epic Games"))
        self.btn_filter_gog.clicked.connect(lambda: self.set_platform_filter("GOG"))

        for btn in filter_buttons:
            action_bar.addWidget(btn)

        action_bar.addStretch()

        # Search filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filter games by title...")
        self.search_input.textChanged.connect(self.filter_and_populate_list)
        action_bar.addWidget(self.search_input, stretch=1)

        # Scan & Import All Buttons
        self.btn_scan = QPushButton("🔄 Scan Games")
        self.btn_scan.setObjectName("SecondaryButton")
        self.btn_scan.clicked.connect(self.refresh_scanned_games)
        action_bar.addWidget(self.btn_scan)

        self.btn_import_all = QPushButton("📥 Import All")
        self.btn_import_all.setObjectName("PrimaryButton")
        self.btn_import_all.clicked.connect(self.import_all_games)
        action_bar.addWidget(self.btn_import_all)

        root_layout.addLayout(action_bar)

        # 4. Scanned Games List
        self.list_widget = QListWidget()
        root_layout.addWidget(self.list_widget, stretch=1)

    def set_platform_filter(self, platform: str):
        self.current_platform_filter = platform
        self.btn_filter_all.setChecked(platform == "All")
        self.btn_filter_steam.setChecked(platform == "Steam")
        self.btn_filter_epic.setChecked(platform == "Epic Games")
        self.btn_filter_gog.setChecked(platform == "GOG")
        self.filter_and_populate_list()

    def refresh_scanned_games(self):
        self.scanned_games = scan_all_platform_games()
        self.filter_and_populate_list()

    def filter_and_populate_list(self):
        self.list_widget.clear()

        query = self.search_input.text().lower().strip()
        existing_games = self.db_manager.get_all_games()
        existing_exes = {g.exe_path.lower() for g in existing_games if g.exe_path}
        existing_names = {g.name.lower() for g in existing_games}

        filtered = []
        for g in self.scanned_games:
            if self.current_platform_filter != "All" and g["platform"] != self.current_platform_filter:
                continue
            if query and query not in g["name"].lower() and query not in g["exe_path"].lower():
                continue
            filtered.append(g)

        if not filtered:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 80))
            empty_label = QLabel("No installed platform games found.\nClick '🔄 Scan Games' or install launchers above.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #8E9BB0; font-size: 13px; padding: 20px;")
            self.list_widget.setItemWidget(item, empty_label)
            return

        for game_info in filtered:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 56))

            widget = ImportedGameListItemWidget(game_info)
            widget.import_clicked.connect(self.import_single_game)

            # Check if already added
            if game_info["exe_path"].lower() in existing_exes or game_info["name"].lower() in existing_names:
                widget.btn_add.setText("✓ In Library")
                widget.btn_add.setObjectName("SecondaryButton")
                widget.btn_add.setEnabled(False)

            self.list_widget.setItemWidget(item, widget)

    def import_single_game(self, game_info: dict):
        exe = game_info["exe_path"]
        name = game_info["name"]
        proc_name = game_info.get("process_name")

        safe_icon_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        icon_path = extract_icon_from_exe(exe, safe_icon_name) if exe and os.path.exists(exe) else None

        game = self.db_manager.add_game(
            name=name,
            exe_path=exe,
            process_name=proc_name,
            icon_path=icon_path
        )
        self.library_updated.emit()
        QMessageBox.information(self, "Game Imported! 🎮", f"'{game.name}' ({game_info['platform']}) has been added to your library!")
        self.filter_and_populate_list()

    def import_all_games(self):
        query = self.search_input.text().lower().strip()
        existing_games = self.db_manager.get_all_games()
        existing_exes = {g.exe_path.lower() for g in existing_games if g.exe_path}
        existing_names = {g.name.lower() for g in existing_games}

        added_count = 0
        for game_info in self.scanned_games:
            if self.current_platform_filter != "All" and game_info["platform"] != self.current_platform_filter:
                continue
            if query and query not in game_info["name"].lower() and query not in game_info["exe_path"].lower():
                continue

            exe = game_info["exe_path"]
            name = game_info["name"]

            if exe.lower() in existing_exes or name.lower() in existing_names:
                continue

            safe_icon_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
            icon_path = extract_icon_from_exe(exe, safe_icon_name) if exe and os.path.exists(exe) else None
            self.db_manager.add_game(
                name=name,
                exe_path=exe,
                process_name=game_info.get("process_name"),
                icon_path=icon_path
            )
            added_count += 1

        if added_count > 0:
            self.library_updated.emit()
            QMessageBox.information(self, "Import Complete 🎉", f"Successfully imported {added_count} games into your library!")
            self.filter_and_populate_list()
        else:
            QMessageBox.information(self, "No New Games", "All detected games are already in your library.")
