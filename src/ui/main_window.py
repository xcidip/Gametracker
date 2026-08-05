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

from src.database import DatabaseManager, GameEntry
from src.core.tracker import TimeTrackerThread
from src.core.startup_manager import is_startup_enabled, set_startup_enabled
from src.core.torrent_manager import ensure_aria2_installed, TorrentDownloadWorker, launch_elevated_installer, InstallerMonitorWorker
from src.ui.styles import MAIN_STYLE
from src.ui.components.game_card import GameCardWidget
from src.ui.dialogs.detector_dialog import RunningAppDetectorDialog
from src.ui.dialogs.add_game_dialog import AddGameDialog
from src.ui.dialogs.torrent_dialog import TorrentDownloadDialog
from src.ui.views.stats_view import StatsViewWidget
from src.ui.views.debug_view import DebugViewWidget
from src.ui.views.launchers_view import LaunchersViewWidget

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
        self.download_workers: Dict[str, TorrentDownloadWorker] = {}

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
        app_title = QLabel("GAME TRACKER")
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

        self.btn_nav_debug = QPushButton("🛠️ Debug")
        self.btn_nav_debug.setObjectName("NavButton")
        self.btn_nav_debug.setCheckable(True)
        self.btn_nav_debug.clicked.connect(lambda: self.switch_view(2))
        sb_layout.addWidget(self.btn_nav_debug)

        self.btn_nav_stores = QPushButton("🌐 Stores & Import")
        self.btn_nav_stores.setObjectName("NavButton")
        self.btn_nav_stores.setCheckable(True)
        self.btn_nav_stores.clicked.connect(lambda: self.switch_view(3))
        sb_layout.addWidget(self.btn_nav_stores)

        sb_layout.addSpacing(15)

        self.btn_add_exe = QPushButton("＋ Add Custom .EXE")
        self.btn_add_exe.setObjectName("PrimaryButton")
        self.btn_add_exe.clicked.connect(self.open_add_game_dialog)
        sb_layout.addWidget(self.btn_add_exe)

        self.btn_torrent = QPushButton("Download Torrent/Magnet")
        self.btn_torrent.setObjectName("SecondaryButton")
        self.btn_torrent.clicked.connect(self.open_torrent_dialog)
        sb_layout.addWidget(self.btn_torrent)

        sb_layout.addSpacing(10)

        # File Storage / Backup Actions
        self.btn_export = QPushButton("📂 Export data File")
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

        # Now Playing Active Banner (Compact & Sleek)
        self.banner_frame = QFrame()
        self.banner_frame.setFixedHeight(26)
        self.banner_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C5CE7, stop:1 #00CEC9);
                color: white;
                border: none;
            }
        """)
        self.banner_frame.hide()
        banner_layout = QHBoxLayout(self.banner_frame)
        banner_layout.setContentsMargins(14, 0, 14, 0)
        banner_layout.setSpacing(6)

        self.banner_label = QLabel("🎮 NOW PLAYING: None")
        self.banner_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #FFFFFF;")
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

        # View 2: Debug View
        self.debug_view = DebugViewWidget(self.db_manager, on_library_updated=self.reload_library_grid)
        self.stacked_widget.addWidget(self.debug_view)

        # View 3: Launchers & Stores View
        self.launchers_view = LaunchersViewWidget(self.db_manager)
        self.launchers_view.library_updated.connect(self.reload_library_grid)
        self.stacked_widget.addWidget(self.launchers_view)

        content_layout.addWidget(self.stacked_widget, stretch=1)

        root_layout.addWidget(content_frame, stretch=1)

        # Load library games into grid
        self.reload_library_grid()

    def switch_view(self, index: int):
        self.btn_nav_library.setChecked(index == 0)
        self.btn_nav_stats.setChecked(index == 1)
        self.btn_nav_debug.setChecked(index == 2)
        self.btn_nav_stores.setChecked(index == 3)
        self.stacked_widget.setCurrentIndex(index)

        if index == 1:
            self.stats_view.refresh_stats()
        elif index == 2:
            self.debug_view.refresh_info()
        elif index == 3:
            self.launchers_view.refresh_scanned_games()

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

        # Sorting logic (Favorited games always pinned at the top)
        sort_idx = self.sort_combo.currentIndex()
        if sort_idx == 0:  # Playtime
            games.sort(key=lambda g: (not g.is_favorite, -g.playtime))
        elif sort_idx == 1:  # Name A-Z
            games.sort(key=lambda g: (not g.is_favorite, g.name.lower()))
        elif sort_idx == 2:  # Recently played
            def _recent_key(g):
                if not g.last_played or g.last_played == "Never":
                    return (not g.is_favorite, 1, ())
                try:
                    parts = [int(p) for p in g.last_played.replace('-', ' ').replace(':', ' ').split()]
                    return (not g.is_favorite, 0, tuple(-p for p in parts))
                except Exception:
                    return (not g.is_favorite, 1, ())
            games.sort(key=_recent_key)

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
            card.cancel_download_requested.connect(self.cancel_torrent_download)
            card.install_requested.connect(self.run_game_installer)
            card.favorite_toggled.connect(self.toggle_favorite_game)

            row = idx // columns
            col = idx % columns
            self.grid_layout.addWidget(card, row, col)
            self.cards[game.id] = card

    def toggle_favorite_game(self, game_id: str):
        self.db_manager.toggle_favorite(game_id)
        self.reload_library_grid()

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

    def update_now_playing_banner(self):
        """Updates the top banner to list all currently running games."""
        running_games = [g for g in self.db_manager.get_all_games() if g.is_running]
        # Deduplicate running game names to prevent duplicates in banner
        unique_names = list(dict.fromkeys(g.name for g in running_games))

        if unique_names:
            game_names = ", ".join(unique_names)
            if len(unique_names) > 1:
                self.banner_label.setText(f"🎮 NOW PLAYING ({len(unique_names)}): {game_names}")
            else:
                self.banner_label.setText(f"🎮 NOW PLAYING: {game_names}")
            self.banner_frame.show()
        else:
            self.banner_frame.hide()

    def on_game_started(self, game_id: str, game_name: str):
        game = self.db_manager.get_game_by_id(game_id)
        if game:
            game.is_running = True
        if game_id in self.cards:
            self.cards[game_id].update_status_badge(True)
            self.cards[game_id].update_action_button()
        self.update_now_playing_banner()

    def on_game_stopped(self, game_id: str, game_name: str, session_seconds: float):
        game = self.db_manager.get_game_by_id(game_id)
        if game:
            game.is_running = False
        if game_id in self.cards:
            self.cards[game_id].update_status_badge(False)
            self.cards[game_id].update_action_button()
        self.update_now_playing_banner()

    def on_running_status_changed(self, status_dict: dict):
        for game_id, is_running in status_dict.items():
            game = self.db_manager.get_game_by_id(game_id)
            if game:
                game.is_running = is_running
            if game_id in self.cards:
                self.cards[game_id].update_status_badge(is_running)
                self.cards[game_id].update_action_button()
        self.update_now_playing_banner()

    def launch_game(self, game_id: str):
        game = self.db_manager.get_game_by_id(game_id)
        if not game:
            return

        if game.needs_installation:
            self.run_game_installer(game_id)
            return

        if not game.exe_path or not os.path.exists(game.exe_path):
            QMessageBox.warning(self, "File Not Found", f"Executable path does not exist:\n{game.exe_path}")
            return

        cwd = os.path.dirname(game.exe_path)
        try:
            cmd = [game.exe_path]
            if game.launch_args:
                cmd.extend(game.launch_args.split())

            subprocess.Popen(cmd, cwd=cwd)
            logger.info(f"Launched game executable: {cmd}")
            self.on_game_started(game.id, game.name)
        except OSError as e:
            # Handle WinError 740: The requested operation requires elevation
            if getattr(e, 'winerror', None) == 740 or "elevation" in str(e).lower():
                logger.info(f"WinError 740 caught, attempting elevated ShellExecute 'runas' for {game.exe_path}")
                import ctypes
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    str(game.exe_path),
                    str(game.launch_args) if game.launch_args else None,
                    str(cwd),
                    1
                )
                if ret > 32:
                    self.on_game_started(game.id, game.name)
                else:
                    QMessageBox.critical(self, "Elevation Error", f"Failed to launch elevated process (error code {ret}).")
            else:
                QMessageBox.critical(self, "Launch Error", f"Failed to launch application:\n{e}")
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

    def open_torrent_dialog(self):
        dialog = TorrentDownloadDialog(parent=self)
        dialog.torrent_started.connect(self.start_torrent_download)
        dialog.exec()

    def start_torrent_download(self, torrent_info: dict):
        game_name = torrent_info["name"]
        torrent_source = torrent_info["torrent_source"]
        download_dir = torrent_info["download_dir"]

        # Ensure aria2 CLI is installed/available
        aria2_bin = ensure_aria2_installed()

        # Create or update game entry in library
        game = self.db_manager.add_game(
            name=game_name,
            exe_path="",
            process_name=game_name.lower().replace(" ", ""),
            icon_path=None
        )
        game.is_downloading = True
        game.download_progress = 0.0
        game.download_speed = "Connecting..."
        game.download_status = "Downloading"
        game.download_dir = download_dir
        game.torrent_source = torrent_source
        self.db_manager.save()

        # Refresh grid so downloading card shows immediately
        self.reload_library_grid()

        # Start background worker thread
        worker = TorrentDownloadWorker(
            game_id=game.id,
            game_name=game.name,
            torrent_source=torrent_source,
            download_dir=download_dir,
            aria2_path=aria2_bin
        )
        worker.progress_updated.connect(self.on_torrent_progress)
        worker.download_completed.connect(self.on_torrent_completed)
        worker.download_failed.connect(self.on_torrent_failed)
        
        self.download_workers[game.id] = worker
        worker.start()

        QMessageBox.information(
            self,
            "Download Started",
            f"'{game_name}' has started downloading in the background!\nDestination: {download_dir}"
        )

    def on_torrent_progress(self, game_id: str, progress: float, speed: str, eta: str, status: str):
        game = self.db_manager.get_game_by_id(game_id)
        if game:
            game.is_downloading = (status != "Completed" and status != "Cancelled")
            game.download_progress = progress
            game.download_speed = speed
            game.download_eta = eta
            game.download_status = status

        if game_id in self.cards:
            self.cards[game_id].update_download_progress(progress, speed, eta, status)

    def on_torrent_completed(self, game_id: str, game_name: str, download_dir: str):
        game = self.db_manager.get_game_by_id(game_id)
        installer_found = ""

        if game:
            game.is_downloading = False
            game.download_progress = 100.0
            game.download_status = "Completed"

            # Auto scan downloaded folder for setup/installer executable
            if os.path.exists(download_dir):
                # Prioritize setup.exe or installer.exe
                for root, _, files in os.walk(download_dir):
                    for f in files:
                        f_lower = f.lower()
                        if f_lower.endswith(".exe") and ("setup" in f_lower or "install" in f_lower):
                            installer_found = os.path.join(root, f)
                            break
                    if installer_found:
                        break

                # Fallback: any .exe in download folder
                if not installer_found:
                    for root, _, files in os.walk(download_dir):
                        for f in files:
                            if f.lower().endswith(".exe") and not f.lower().startswith("uninstall"):
                                installer_found = os.path.join(root, f)
                                break
                        if installer_found:
                            break

            if installer_found:
                game.needs_installation = True
                game.installer_path = installer_found
                game.exe_path = installer_found

            self.db_manager.save()

        if game_id in self.download_workers:
            del self.download_workers[game_id]

        self.reload_library_grid()

        if installer_found:
            reply = QMessageBox.question(
                self,
                "Download Completed! 🎉",
                f"'{game_name}' download finished successfully!\nInstaller found:\n{installer_found}\n\nWould you like to run the elevated setup installer now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.run_game_installer(game_id)
        else:
            QMessageBox.information(
                self,
                "Download Completed! 🎉",
                f"'{game_name}' has finished downloading successfully!\nFolder: {download_dir}"
            )

    def run_game_installer(self, game_id: str):
        game = self.db_manager.get_game_by_id(game_id)
        if not game or not game.installer_path or not os.path.exists(game.installer_path):
            QMessageBox.warning(self, "Installer Not Found", "Installer executable path does not exist.")
            return

        # 1. Launch installer with Elevated Administrator Privileges (UAC prompt)
        success = launch_elevated_installer(game.installer_path)
        if not success:
            QMessageBox.warning(self, "Launch Error", f"Failed to launch elevated installer:\n{game.installer_path}")
            return

        logger.info(f"Launched elevated installer for {game.name}: {game.installer_path}")

        # 2. Monitor installer in background thread
        monitor_worker = InstallerMonitorWorker(game.id, game.name, game.installer_path)
        monitor_worker.installer_finished.connect(self.on_installer_finished)
        self.download_workers[f"inst_{game.id}"] = monitor_worker
        monitor_worker.start()

        QMessageBox.information(
            self,
            "Installer Started",
            f"The setup installer for '{game.name}' has been launched with Administrator privileges.\n\nWhen you finish the installation wizard, GameTracker will ask you to select the installed game executable."
        )

    def on_installer_finished(self, game_id: str, game_name: str):
        worker_key = f"inst_{game_id}"
        if worker_key in self.download_workers:
            del self.download_workers[worker_key]

        # Restore application window to front so popup is visible
        self.showNormal()
        self.activateWindow()
        self.raise_()

        self.prompt_select_installed_exe(game_id)

    def prompt_select_installed_exe(self, game_id: str):
        import shutil
        from PyQt6.QtWidgets import QFileDialog
        from src.core.icon_extractor import extract_icon_from_exe

        game = self.db_manager.get_game_by_id(game_id)
        if not game:
            return

        # 1. Popup to select installed game executable (.exe)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select Installed Main Executable (.exe) for '{game.name}'",
            "C:\\Program Files",
            "Executable Files (*.exe);;All Files (*.*)"
        )

        download_dir_to_clean = game.download_dir

        if file_path and os.path.exists(file_path):
            # Update library entry with installed game executable & icon
            game.exe_path = file_path
            game.process_name = os.path.basename(file_path).lower()
            game.needs_installation = False
            game.installer_path = ""
            game.icon_path = extract_icon_from_exe(file_path, game.id)
            self.db_manager.save()
            self.reload_library_grid()

            QMessageBox.information(
                self,
                "Game Added to Library! 🎮",
                f"'{game.name}' is now added to your library and ready to play!\nExecutable: {file_path}"
            )

            # 2. Ask user if they want to delete the downloaded torrent folder
            if download_dir_to_clean and os.path.exists(download_dir_to_clean):
                reply = QMessageBox.question(
                    self,
                    "Clean Up Downloaded Torrent Folder",
                    f"Would you like to delete the temporary downloaded torrent folder to free up disk space?\n\nFolder Path:\n{download_dir_to_clean}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        shutil.rmtree(download_dir_to_clean, ignore_errors=True)
                        game.download_dir = ""
                        self.db_manager.save()
                        QMessageBox.information(self, "Cleaned Up", "Temporary downloaded torrent folder has been deleted.")
                    except Exception as e:
                        logger.error(f"Error deleting download directory {download_dir_to_clean}: {e}")
        else:
            QMessageBox.information(
                self,
                "Installation Pending",
                f"No executable selected for '{game.name}'. You can click '🚀 RUN INSTALLER' or right-click the card to select the installed executable anytime."
            )
            self.reload_library_grid()

    def on_torrent_failed(self, game_id: str, game_name: str, error_msg: str):
        game = self.db_manager.get_game_by_id(game_id)
        if game:
            game.is_downloading = False
            game.download_status = "Failed"
            self.db_manager.save()

        if game_id in self.download_workers:
            del self.download_workers[game_id]

        self.reload_library_grid()
        QMessageBox.warning(self, "Download Failed", f"Torrent download for '{game_name}' failed:\n{error_msg}")

    def cancel_torrent_download(self, game_id: str):
        game = self.db_manager.get_game_by_id(game_id)
        if not game:
            return

        reply = QMessageBox.question(
            self,
            "Cancel Download",
            f"Are you sure you want to cancel the download for '{game.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if game_id in self.download_workers:
                worker = self.download_workers[game_id]
                worker.cancel()
                del self.download_workers[game_id]

            game.is_downloading = False
            game.download_status = "Cancelled"
            self.db_manager.save()
            self.reload_library_grid()

    def force_quit(self):
        # Cancel all active torrent download workers on quit
        for worker in self.download_workers.values():
            worker.cancel()
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

