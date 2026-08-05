import os
import sys
import subprocess
import logging
from typing import Dict, List, Optional
from pathlib import Path

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QStackedWidget,
    QScrollArea, QGridLayout, QMessageBox, QFrame,
    QSystemTrayIcon, QMenu
)

from database import DatabaseManager, GameEntry
from tracker import TimeTrackerThread
from startup_manager import is_startup_enabled, set_startup_enabled
from ui.styles import MAIN_STYLE
from ui.game_card import GameCardWidget
from ui.detector_dialog import RunningAppDetectorDialog
from ui.add_game_dialog import AddGameDialog
from ui.stats_view import StatsViewWidget

logger = logging.getLogger("MainWindow")

class MainWindow(QMainWindow):
    """
    Main application window for Game & App Playtime Tracker.
    """
    def __init__(self, db_manager: DatabaseManager, tracker_thread: TimeTrackerThread):
        super().__init__()
        self.db_manager = db_manager
        self.tracker_thread = tracker_thread
        self.is_force_quitting = False

        self.setWindowTitle("Game & App Playtime Tracker")
        self.resize(1100, 720)
        self.setMinimumSize(900, 600)

        # Apply dark theme style
        self.setStyleSheet(MAIN_STYLE)

        self.cards: Dict[str, GameCardWidget] = {}

        self.init_ui()
        self.init_system_tray()
        self.connect_tracker_signals()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        root_layout = QHBoxLayout(main_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Left Sidebar Navigation
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)

        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(14, 20, 14, 20)
        sb_layout.setSpacing(10)

        # Logo / App Title
        app_title = QLabel("🎮 GAME TRACKER")
        app_title.setObjectName("SidebarTitle")
        sb_layout.addWidget(app_title)

        sb_layout.addSpacing(15)

        # Navigation Buttons
        self.btn_nav_library = QPushButton("📚 My Library")
        self.btn_nav_library.setObjectName("NavButton")
        self.btn_nav_library.setCheckable(True)
        self.btn_nav_library.setChecked(True)
        self.btn_nav_library.clicked.connect(lambda: self.switch_view(0))
        sb_layout.addWidget(self.btn_nav_library)

        self.btn_nav_detect = QPushButton("⚡ Detect Apps")
        self.btn_nav_detect.setObjectName("NavButton")
        self.btn_nav_detect.clicked.connect(self.open_app_detector)
        sb_layout.addWidget(self.btn_nav_detect)

        self.btn_nav_stats = QPushButton("📊 Analytics")
        self.btn_nav_stats.setObjectName("NavButton")
        self.btn_nav_stats.setCheckable(True)
        self.btn_nav_stats.clicked.connect(lambda: self.switch_view(1))
        sb_layout.addWidget(self.btn_nav_stats)

        sb_layout.addSpacing(15)

        self.btn_add_exe = QPushButton("＋ Add Custom .EXE")
        self.btn_add_exe.setObjectName("PrimaryButton")
        self.btn_add_exe.clicked.connect(self.open_add_game_dialog)
        sb_layout.addWidget(self.btn_add_exe)

        sb_layout.addSpacing(10)

        # File Storage / Backup Actions
        self.btn_export = QPushButton("💾 Save / Export File")
        self.btn_export.setObjectName("SecondaryButton")
        self.btn_export.clicked.connect(self.export_data_file)
        sb_layout.addWidget(self.btn_export)

        self.btn_import = QPushButton("📂 Import Data File")
        self.btn_import.setObjectName("SecondaryButton")
        self.btn_import.clicked.connect(self.import_data_file)
        sb_layout.addWidget(self.btn_import)

        sb_layout.addSpacing(10)

        # Windows Startup Toggle Button
        self.btn_startup = QPushButton()
        self.btn_startup.setCheckable(True)
        self.update_startup_button_state()
        self.btn_startup.clicked.connect(self.toggle_startup)
        sb_layout.addWidget(self.btn_startup)

        sb_layout.addStretch()

        # Footer status in sidebar
        self.sidebar_status = QLabel("Engine: Running")
        self.sidebar_status.setStyleSheet("color: #00B894; font-size: 11px; font-weight: bold;")
        sb_layout.addWidget(self.sidebar_status)

        root_layout.addWidget(sidebar)

        # Right Main Content Workspace
        content_frame = QWidget()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top Bar (Search, Sort, Active Game Banner)
        top_bar = QFrame()
        top_bar.setObjectName("HeaderFrame")
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(18, 12, 18, 12)
        tb_layout.setSpacing(14)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search games & apps in library...")
        self.search_bar.textChanged.connect(self.filter_library)
        tb_layout.addWidget(self.search_bar, stretch=1)

        tb_layout.addWidget(QLabel("Sort By:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Playtime (High to Low)", "Name (A-Z)", "Recently Played"])
        self.sort_combo.currentIndexChanged.connect(self.reload_library_grid)
        tb_layout.addWidget(self.sort_combo)

        content_layout.addWidget(top_bar)

        # Now Playing Active Banner
        self.banner_frame = QFrame()
        self.banner_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C5CE7, stop:1 #00CEC9);
                color: white;
                padding: 10px 18px;
            }
        """)
        self.banner_frame.hide()
        banner_layout = QHBoxLayout(self.banner_frame)
        banner_layout.setContentsMargins(10, 4, 10, 4)

        self.banner_label = QLabel("NOW PLAYING: None")
        self.banner_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        banner_layout.addWidget(self.banner_label)

        content_layout.addWidget(self.banner_frame)

        # Stacked Views (0 = Library Grid, 1 = Stats)
        self.stacked_widget = QStackedWidget()

        # View 0: Library Scroll Area & Grid
        self.library_scroll = QScrollArea()
        self.library_scroll.setWidgetResizable(True)
        self.library_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.library_scroll.setWidget(self.grid_container)
        self.stacked_widget.addWidget(self.library_scroll)

        # View 1: Stats View
        self.stats_view = StatsViewWidget(self.db_manager)
        self.stacked_widget.addWidget(self.stats_view)

        content_layout.addWidget(self.stacked_widget, stretch=1)

        root_layout.addWidget(content_frame, stretch=1)

        # Load library games into grid
        self.reload_library_grid()

    def switch_view(self, index: int):
        self.btn_nav_library.setChecked(index == 0)
        self.btn_nav_stats.setChecked(index == 1)
        self.stacked_widget.setCurrentIndex(index)

        if index == 1:
            self.stats_view.refresh_stats()

    def reload_library_grid(self):
        # Clear existing card widgets
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.cards.clear()

        games = self.db_manager.get_all_games()
        query = self.search_bar.text().lower().strip()

        if query:
            games = [g for g in games if query in g.name.lower() or query in g.process_name.lower()]

        # Sorting logic
        sort_idx = self.sort_combo.currentIndex()
        if sort_idx == 0:  # Playtime
            games.sort(key=lambda g: g.playtime, reverse=True)
        elif sort_idx == 1:  # Name A-Z
            games.sort(key=lambda g: g.name.lower())
        elif sort_idx == 2:  # Recently played
            games.sort(key=lambda g: g.last_played, reverse=True)

        if not games:
            empty_msg = QLabel("No games or apps found in library.\nClick '⚡ Detect Apps' or '＋ Add Custom .EXE' to get started!")
            empty_msg.setStyleSheet("color: #8E9BB0; font-size: 15px; text-align: center; padding: 50px;")
            empty_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(empty_msg, 0, 0, 1, 3)
            return

        columns = max(3, (self.width() - 260) // 250)
        for idx, game in enumerate(games):
            card = GameCardWidget(game)
            card.launch_requested.connect(self.launch_game)
            card.remove_requested.connect(self.remove_game)
            card.edit_requested.connect(self.edit_game)

            row = idx // columns
            col = idx % columns
            self.grid_layout.addWidget(card, row, col)
            self.cards[game.id] = card

    def filter_library(self):
        self.reload_library_grid()

    def connect_tracker_signals(self):
        self.tracker_thread.playtime_updated.connect(self.on_playtime_updated)
        self.tracker_thread.game_started.connect(self.on_game_started)
        self.tracker_thread.game_stopped.connect(self.on_game_stopped)
        self.tracker_thread.running_status_changed.connect(self.on_running_status_changed)

    def on_playtime_updated(self, game_id: str, total_seconds: float, session_seconds: float):
        if game_id in self.cards:
            self.cards[game_id].update_playtime_display(total_seconds)

    def on_game_started(self, game_id: str, game_name: str):
        self.banner_label.setText(f"🎮 NOW PLAYING: {game_name}")
        self.banner_frame.show()
        if game_id in self.cards:
            self.cards[game_id].update_status_badge(True)
            self.cards[game_id].update_action_button()

    def on_game_stopped(self, game_id: str, game_name: str, session_seconds: float):
        self.banner_frame.hide()
        if game_id in self.cards:
            self.cards[game_id].update_status_badge(False)
            self.cards[game_id].update_action_button()

    def on_running_status_changed(self, status_dict: dict):
        any_running = False
        for game_id, is_running in status_dict.items():
            if game_id in self.cards:
                self.cards[game_id].update_status_badge(is_running)
                self.cards[game_id].update_action_button()
            if is_running:
                any_running = True
                game = self.db_manager.get_game_by_id(game_id)
                if game:
                    self.banner_label.setText(f"🎮 NOW PLAYING: {game.name}")

        if any_running:
            self.banner_frame.show()
        else:
            self.banner_frame.hide()

    def launch_game(self, game_id: str):
        game = self.db_manager.get_game_by_id(game_id)
        if not game or not game.exe_path:
            QMessageBox.warning(self, "Cannot Launch", "Executable path is not configured for this app.")
            return

        if not os.path.exists(game.exe_path):
            QMessageBox.warning(self, "File Not Found", f"Executable does not exist:\n{game.exe_path}")
            return

        try:
            cwd = os.path.dirname(game.exe_path)
            cmd = [game.exe_path]
            if game.launch_args:
                cmd.extend(game.launch_args.split())

            subprocess.Popen(cmd, cwd=cwd)
            logger.info(f"Launched game executable: {cmd}")
            self.on_game_started(game.id, game.name)
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch application:\n{e}")

    def remove_game(self, game_id: str):
        game = self.db_manager.get_game_by_id(game_id)
        if not game:
            return

        reply = QMessageBox.question(
            self,
            "Remove Game",
            f"Are you sure you want to remove '{game.name}' from your library?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db_manager.remove_game(game_id)
            self.reload_library_grid()

    def edit_game(self, game_id: str):
        game = self.db_manager.get_game_by_id(game_id)
        if not game:
            return

        dialog = AddGameDialog(self.db_manager, game_to_edit=game, parent=self)
        dialog.game_saved.connect(lambda _: self.reload_library_grid())
        dialog.exec()

    def open_app_detector(self):
        dialog = RunningAppDetectorDialog(self.db_manager, parent=self)
        dialog.game_added.connect(lambda _: self.reload_library_grid())
        dialog.exec()

    def open_add_game_dialog(self):
        dialog = AddGameDialog(self.db_manager, parent=self)
        dialog.game_saved.connect(lambda _: self.reload_library_grid())
        dialog.exec()

    def export_data_file(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save / Export Library Data File",
            "library_backup.json",
            "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            try:
                self.db_manager.export_to_file(file_path)
                QMessageBox.information(self, "Data Saved", f"Library data successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error Saving Data", f"Failed to save data file:\n{e}")

    def import_data_file(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Library Data File",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            try:
                self.db_manager.import_from_file(file_path)
                self.reload_library_grid()
                QMessageBox.information(self, "Data Imported", f"Library data successfully imported from:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error Importing Data", f"Failed to import data file:\n{e}")

    def init_system_tray(self):
        """Initializes system tray icon and context menu for silent background tracking."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use window icon or create default icon
        app_icon = self.windowIcon()
        if app_icon.isNull():
            app_icon = QIcon()
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.setToolTip("GameTracker - Playtime Tracking Engine Running")

        tray_menu = QMenu(self)
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #1E2235;
                color: #FFFFFF;
                border: 1px solid #2B304A;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #6C5CE7;
            }
        """)

        action_show = tray_menu.addAction("🎮 Open GameTracker")
        action_show.triggered.connect(self.restore_from_tray)

        action_detect = tray_menu.addAction("⚡ Detect Active Apps")
        action_detect.triggered.connect(self.open_app_detector)

        tray_menu.addSeparator()

        action_startup = tray_menu.addAction("🚀 Launch on Startup")
        action_startup.setCheckable(True)
        action_startup.setChecked(is_startup_enabled())
        action_startup.triggered.connect(self.toggle_startup)

        tray_menu.addSeparator()

        action_quit = tray_menu.addAction("❌ Exit Application")
        action_quit.triggered.connect(self.force_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger or reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.restore_from_tray()

    def update_startup_button_state(self):
        enabled = is_startup_enabled()
        self.btn_startup.setChecked(enabled)
        if enabled:
            self.btn_startup.setText("🚀 Startup: ENABLED")
            self.btn_startup.setObjectName("SecondaryButton")
        else:
            self.btn_startup.setText("🚀 Launch at Startup")
            self.btn_startup.setObjectName("PrimaryButton")
        self.btn_startup.setStyle(self.btn_startup.style())

    def toggle_startup(self):
        current = is_startup_enabled()
        new_state = not current
        success = set_startup_enabled(new_state, minimized=True)
        if success:
            self.update_startup_button_state()
            status_str = "ENABLED (starts minimized in background)" if new_state else "DISABLED"
            QMessageBox.information(self, "Startup Setting Updated", f"Windows Startup has been {status_str}.")
        else:
            QMessageBox.warning(self, "Error", "Failed to update Windows Startup registry key.")

    def force_quit(self):
        self.is_force_quitting = True
        self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reload_library_grid()

    def closeEvent(self, event):
        if self.is_force_quitting:
            self.tray_icon.hide()
            self.tracker_thread.stop()
            self.db_manager.save()
            event.accept()
        else:
            # Hide to system tray instead of exiting
            event.ignore()
            self.hide()
            if self.tray_icon.isSystemTrayAvailable():
                self.tray_icon.showMessage(
                    "GameTracker Running in Background",
                    "GameTracker is still actively tracking your app & game playtime in the background. Click the system tray icon to open.",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )

