import os
import sys
import subprocess
import logging
from pathlib import Path

# Ensure project root is in sys.path when script is executed directly
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon, QAction, QCursor
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMenu, QMessageBox, QWidget, QProgressBar, QApplication
)

from src.database import GameEntry
from src.config import format_playtime

logger = logging.getLogger("GameCard")

class GameCardWidget(QFrame):
    """
    Card widget representing a single game or app in the library grid/list.
    """
    launch_requested = pyqtSignal(str)   # game_id
    remove_requested = pyqtSignal(str)   # game_id
    edit_requested = pyqtSignal(str)     # game_id
    cancel_download_requested = pyqtSignal(str) # game_id
    install_requested = pyqtSignal(str)  # game_id
    favorite_toggled = pyqtSignal(str)   # game_id
    card_clicked = pyqtSignal(str)       # game_id

    def __init__(self, game: GameEntry, parent=None):
        super().__init__(parent)
        self.game = game
        self.setObjectName("GameCard")
        self.setMinimumSize(QSize(190, 155))
        self.setMaximumSize(QSize(260, 185))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Top Header: Playtime badge & options menu button
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        self.playtime_label = QLabel()
        self.playtime_label.setObjectName("PlaytimeBadge")
        self.playtime_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.playtime_label, 1)

        self.btn_favorite = QPushButton()
        self.btn_favorite.setFixedSize(24, 24)
        self.btn_favorite.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_favorite.clicked.connect(self.on_favorite_clicked)
        self.update_favorite_button()
        top_layout.addWidget(self.btn_favorite)

        self.btn_menu = QPushButton("⋮")
        self.btn_menu.setFixedSize(24, 24)
        self.btn_menu.setStyleSheet("background: transparent; color: #8E9BB0; font-size: 15px; border: none;")
        self.btn_menu.clicked.connect(self.show_context_menu)
        top_layout.addWidget(self.btn_menu)

        layout.addLayout(top_layout)

        # Center: App Icon
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(50, 50)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_icon()
        icon_layout.addWidget(self.icon_label)
        icon_layout.addStretch()
        layout.addLayout(icon_layout)

        # Title
        self.title_label = QLabel(self.game.name)
        self.title_label.setObjectName("GameTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Action button (Launch / Play button)
        self.btn_action = QPushButton()
        self.btn_action.setObjectName("PrimaryButton")
        self.btn_action.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.update_action_button()
        self.btn_action.clicked.connect(self.on_action_clicked)
        layout.addWidget(self.btn_action)

        # Download Progress Bar (visible if downloading)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #141724;
                border: 1px solid #2B304A;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #00CEC9;
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Make labels transparent for mouse events so card clicks are caught by GameCardWidget
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.playtime_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.progress_bar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.update_card_display()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.card_clicked.emit(self.game.id)
        super().mousePressEvent(event)

    def load_icon(self):
        icon_path = self.game.icon_path
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.icon_label.setPixmap(scaled)
                return
        # Fallback text icon
        fallback_char = "📦" if self.game.needs_installation else "📥" if self.game.is_downloading else "🎮"
        self.icon_label.setText(fallback_char)
        self.icon_label.setStyleSheet("font-size: 28px;")

    def update_card_display(self):
        if self.game.is_downloading:
            speed_txt = f"{self.game.download_speed} • ETA: {self.game.download_eta}" if self.game.download_speed else "Downloading..."
            self.playtime_label.setText(f"{self.game.download_progress:.1f}%  ({speed_txt})")
            self.progress_bar.setValue(int(self.game.download_progress))
            self.progress_bar.show()
        elif self.game.needs_installation:
            self.progress_bar.hide()
            self.playtime_label.setText("Downloaded • Setup Ready")
        else:
            self.progress_bar.hide()
            self.playtime_label.setText(f"Playtime: {self.game.formatted_playtime()}")
        
        self.update_action_button()

    def update_status_badge(self, is_running: bool):
        self.update_action_button()

    def update_action_button(self):
        if self.game.is_downloading:
            self.btn_action.setText(f"⏬ DOWNLOADING ({int(self.game.download_progress)}%)")
            self.btn_action.setObjectName("SecondaryButton")
            self.btn_action.setEnabled(True)
        elif self.game.needs_installation:
            self.btn_action.setText("🚀 RUN INSTALLER")
            self.btn_action.setObjectName("PrimaryButton")
            self.btn_action.setEnabled(True)
        elif self.game.is_running:
            self.btn_action.setText("● RUNNING")
            self.btn_action.setObjectName("SecondaryButton")
            self.btn_action.setEnabled(False)
        else:
            self.btn_action.setText("▶ LAUNCH")
            self.btn_action.setObjectName("PrimaryButton")
            self.btn_action.setEnabled(True)
        self.btn_action.setStyle(self.btn_action.style())

    def update_download_progress(self, progress: float, speed: str, eta: str, status: str):
        self.game.download_progress = progress
        self.game.download_speed = speed
        self.game.download_eta = eta
        self.game.download_status = status
        self.update_card_display()
        self.update_action_button()

    def update_playtime_display(self, total_seconds: float):
        if not self.game.is_downloading:
            self.game.playtime = total_seconds
            self.playtime_label.setText(f"Playtime: {format_playtime(total_seconds)}")

    def on_action_clicked(self):
        if self.game.is_downloading:
            reply = QMessageBox.question(
                self,
                "Downloading Game",
                f"'{self.game.name}' is currently downloading ({self.game.download_progress:.1f}%).\nSpeed: {self.game.download_speed}\n\nWould you like to open the download folder?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.open_exe_folder()
        elif self.game.needs_installation:
            self.install_requested.emit(self.game.id)
        else:
            self.launch_requested.emit(self.game.id)

    def update_favorite_button(self):
        if self.game.is_favorite:
            self.btn_favorite.setText("★")
            self.btn_favorite.setToolTip("Remove from Favorites")
            self.btn_favorite.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #FFD700;
                    font-size: 18px;
                    border: none;
                }
                QPushButton:hover {
                    color: #FFE566;
                }
            """)
        else:
            self.btn_favorite.setText("☆")
            self.btn_favorite.setToolTip("Add to Favorites")
            self.btn_favorite.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #8E9BB0;
                    font-size: 18px;
                    border: none;
                }
                QPushButton:hover {
                    color: #FFD700;
                }
            """)

    def on_favorite_clicked(self):
        self.favorite_toggled.emit(self.game.id)

    def show_context_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E2235;
                color: #FFFFFF;
                border: 1px solid #2B304A;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #6C5CE7;
            }
        """)

        fav_label = "⭐ Remove from Favorites" if self.game.is_favorite else "★ Add to Favorites"
        action_favorite = QAction(fav_label, self)
        action_favorite.triggered.connect(self.on_favorite_clicked)
        menu.addAction(action_favorite)
        menu.addSeparator()

        if self.game.is_downloading:
            action_folder = QAction("📂 Open Download Folder", self)
            action_folder.triggered.connect(self.open_exe_folder)
            menu.addAction(action_folder)

            action_cancel = QAction("❌ Cancel Download", self)
            action_cancel.triggered.connect(lambda: self.cancel_download_requested.emit(self.game.id))
            menu.addAction(action_cancel)
        elif self.game.needs_installation:
            action_install = QAction("🚀 Run Installer (Administrator)", self)
            action_install.triggered.connect(lambda: self.install_requested.emit(self.game.id))
            menu.addAction(action_install)

            action_folder = QAction("📂 Open Download Folder", self)
            action_folder.triggered.connect(self.open_exe_folder)
            menu.addAction(action_folder)

            menu.addSeparator()

            action_remove = QAction("🗑️ Remove from Library", self)
            action_remove.triggered.connect(lambda: self.remove_requested.emit(self.game.id))
            menu.addAction(action_remove)
        else:
            action_launch = QAction("▶ Launch Game", self)
            action_launch.triggered.connect(lambda: self.launch_requested.emit(self.game.id))
            menu.addAction(action_launch)

            action_folder = QAction("📁 Open Exe Folder", self)
            action_folder.triggered.connect(self.open_exe_folder)
            menu.addAction(action_folder)

            menu.addSeparator()

            action_edit = QAction("✏️ Edit Details", self)
            action_edit.triggered.connect(lambda: self.edit_requested.emit(self.game.id))
            menu.addAction(action_edit)

            action_remove = QAction("🗑️ Remove from Library", self)
            action_remove.triggered.connect(lambda: self.remove_requested.emit(self.game.id))
            menu.addAction(action_remove)

        menu.exec(QCursor.pos())

    def open_exe_folder(self):
        target_path = self.game.download_dir if self.game.is_downloading else self.game.exe_path
        if target_path:
            folder = target_path if os.path.isdir(target_path) else os.path.dirname(target_path)
            if os.path.exists(folder):
                os.startfile(folder)
                return
        QMessageBox.warning(self, "Folder Not Found", f"Directory does not exist:\n{target_path}")
