import os
import subprocess
import logging
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon, QAction, QCursor
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMenu, QMessageBox, QWidget
)

from database import GameEntry
from config import format_playtime

logger = logging.getLogger("GameCard")

class GameCardWidget(QFrame):
    """
    Card widget representing a single game or app in the library grid/list.
    """
    launch_requested = pyqtSignal(str)   # game_id
    remove_requested = pyqtSignal(str)   # game_id
    edit_requested = pyqtSignal(str)     # game_id

    def __init__(self, game: GameEntry, parent=None):
        super().__init__(parent)
        self.game = game
        self.setObjectName("GameCard")
        self.setMinimumSize(QSize(220, 260))
        self.setMaximumSize(QSize(280, 300))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Top Header: Status badge & options menu button
        top_layout = QHBoxLayout()
        self.status_label = QLabel()
        self.update_status_badge(self.game.is_running)
        top_layout.addWidget(self.status_label)

        top_layout.addStretch()

        self.btn_menu = QPushButton("⋮")
        self.btn_menu.setFixedSize(28, 28)
        self.btn_menu.setStyleSheet("background: transparent; color: #8E9BB0; font-size: 16px; border: none;")
        self.btn_menu.clicked.connect(self.show_context_menu)
        top_layout.addWidget(self.btn_menu)

        layout.addLayout(top_layout)

        # Center: App Icon
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(72, 72)
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

        # Playtime badge & Last played
        self.playtime_label = QLabel(f"Playtime: {self.game.formatted_playtime()}")
        self.playtime_label.setObjectName("PlaytimeBadge")
        self.playtime_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.playtime_label)

        layout.addStretch()

        # Action Launch Button
        self.btn_action = QPushButton()
        self.btn_action.setObjectName("PrimaryButton")
        self.update_action_button()
        self.btn_action.clicked.connect(self.on_action_clicked)
        layout.addWidget(self.btn_action)

    def load_icon(self):
        icon_path = self.game.icon_path
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.icon_label.setPixmap(scaled)
                return
        # Fallback text icon
        self.icon_label.setText("🎮")
        self.icon_label.setStyleSheet("font-size: 36px;")

    def update_status_badge(self, is_running: bool):
        if is_running:
            self.status_label.setText("● PLAYING")
            self.status_label.setObjectName("StatusBadgeRunning")
        else:
            self.status_label.setText("OFFLINE")
            self.status_label.setObjectName("StatusBadgeIdle")
        
        # Re-apply QSS style for dynamic selector
        self.status_label.setStyle(self.status_label.style())

    def update_action_button(self):
        if self.game.is_running:
            self.btn_action.setText("● RUNNING")
            self.btn_action.setObjectName("SecondaryButton")
            self.btn_action.setEnabled(False)
        else:
            self.btn_action.setText("▶ LAUNCH")
            self.btn_action.setObjectName("PrimaryButton")
            self.btn_action.setEnabled(True)
        self.btn_action.setStyle(self.btn_action.style())

    def update_playtime_display(self, total_seconds: float):
        self.game.playtime = total_seconds
        self.playtime_label.setText(f"Playtime: {format_playtime(total_seconds)}")

    def on_action_clicked(self):
        self.launch_requested.emit(self.game.id)

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
        if self.game.exe_path and os.path.exists(self.game.exe_path):
            folder = os.path.dirname(self.game.exe_path)
            os.startfile(folder)
        else:
            QMessageBox.warning(self, "Folder Not Found", f"Executable path does not exist:\n{self.game.exe_path}")
