import os
import sys
import logging
from pathlib import Path

# Ensure project root is in sys.path when script is executed directly
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QCursor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QMessageBox, QApplication
)

from src.database import GameEntry
from src.config import format_playtime

logger = logging.getLogger("GameDetailView")


class GameDetailViewWidget(QWidget):
    """
    Full-screen detailed view of a game/app occupying the entire library screen area.
    Shows basic info including play time, launch button, file location, process name, etc.
    """
    back_requested = pyqtSignal()
    launch_requested = pyqtSignal(str)          # game_id
    install_requested = pyqtSignal(str)         # game_id
    cancel_download_requested = pyqtSignal(str)# game_id
    edit_requested = pyqtSignal(str)            # game_id
    remove_requested = pyqtSignal(str)          # game_id
    favorite_toggled = pyqtSignal(str)          # game_id
    set_limit_requested = pyqtSignal(str)       # game_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game: GameEntry = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area container so it handles all window sizes cleanly
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(20)

        # 1. Top Navigation Bar with Back Button
        nav_layout = QHBoxLayout()
        self.btn_back = QPushButton("← Back to Library")
        self.btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #1E2235;
                color: #00CEC9;
                border: 1px solid #2B304A;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #00CEC9;
                color: #0F111A;
            }
        """)
        self.btn_back.clicked.connect(lambda: self.back_requested.emit())
        nav_layout.addWidget(self.btn_back)

        nav_layout.addStretch()

        self.btn_favorite = QPushButton()
        self.btn_favorite.setFixedSize(36, 36)
        self.btn_favorite.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_favorite.clicked.connect(self.on_favorite_clicked)
        nav_layout.addWidget(self.btn_favorite)

        layout.addLayout(nav_layout)

        # 2. Header Hero Section (Icon, Title, Status & Primary Action Button)
        hero_card = QFrame()
        hero_card.setObjectName("HeroCard")
        hero_card.setStyleSheet("""
            QFrame#HeroCard {
                background-color: #141724;
                border: 1px solid #2B304A;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(20, 20, 20, 20)
        hero_layout.setSpacing(24)

        # Game Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(84, 84)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("background: #1E2235; border-radius: 14px;")
        hero_layout.addWidget(self.icon_label)

        # Title & Quick Info
        title_box = QVBoxLayout()
        title_box.setSpacing(6)

        self.lbl_title = QLabel("Game Title")
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: bold; color: #FFFFFF;")
        title_box.addWidget(self.lbl_title)

        self.lbl_status_badge = QLabel("Installed & Ready")
        self.lbl_status_badge.setStyleSheet("""
            background-color: #1E2235;
            color: #00CEC9;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: bold;
        """)
        self.lbl_status_badge.setFixedWidth(180)
        title_box.addWidget(self.lbl_status_badge)

        hero_layout.addLayout(title_box, stretch=1)

        # Actions on the right side of Hero (Launch, Open Folder, Edit, Remove)
        action_box = QVBoxLayout()
        action_box.setSpacing(10)
        action_box.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.btn_action = QPushButton("▶ LAUNCH GAME")
        self.btn_action.setMinimumWidth(200)
        self.btn_action.setMinimumHeight(44)
        self.btn_action.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_action.setStyleSheet("""
            QPushButton {
                background-color: #6C5CE7;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background-color: #5B4BC4;
            }
            QPushButton:disabled {
                background-color: #2B304A;
                color: #8E9BB0;
            }
        """)
        self.btn_action.clicked.connect(self.on_action_clicked)
        action_box.addWidget(self.btn_action)

        secondary_actions = QHBoxLayout()
        secondary_actions.setSpacing(8)

        self.btn_open_folder = QPushButton("📁 Open Folder")
        self.btn_open_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #1E2235;
                color: #FFFFFF;
                border: 1px solid #2B304A;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2B304A;
                border-color: #6C5CE7;
            }
        """)
        self.btn_open_folder.clicked.connect(self.open_exe_folder)
        secondary_actions.addWidget(self.btn_open_folder)

        self.btn_edit = QPushButton("✏️ Edit")
        self.btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #1E2235;
                color: #FFFFFF;
                border: 1px solid #2B304A;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2B304A;
                border-color: #6C5CE7;
            }
        """)
        self.btn_edit.clicked.connect(lambda: self.game and self.edit_requested.emit(self.game.id))
        secondary_actions.addWidget(self.btn_edit)

        self.btn_limit = QPushButton("⏱️ Set Play Limit")
        self.btn_limit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_limit.setStyleSheet("""
            QPushButton {
                background-color: #1E2235;
                color: #FFFFFF;
                border: 1px solid #2B304A;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2B304A;
                border-color: #00CEC9;
            }
        """)
        self.btn_limit.clicked.connect(lambda: self.game and self.set_limit_requested.emit(self.game.id))
        secondary_actions.addWidget(self.btn_limit)

        self.btn_remove = QPushButton("🗑️ Remove")
        self.btn_remove.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_remove.setStyleSheet("""
            QPushButton {
                background-color: #272C45;
                color: #FF7675;
                border: 1px solid #FF7675;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #FF7675;
                color: #FFFFFF;
            }
        """)
        self.btn_remove.clicked.connect(self.on_remove_clicked)
        secondary_actions.addWidget(self.btn_remove)

        action_box.addLayout(secondary_actions)
        hero_layout.addLayout(action_box)

        layout.addWidget(hero_card)

        # 3. Details & Information Cards Grid
        info_label = QLabel("GAME STATISTICS & DETAILS")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #8E9BB0; letter-spacing: 1px;")
        layout.addWidget(info_label)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)

        # Playtime Card
        self.card_playtime = self._create_info_card("⏱️ TOTAL PLAY TIME", "--", "#6C5CE7")
        grid_layout.addWidget(self.card_playtime, 0, 0)

        # Weekly Limit Card (Separate dedicated box)
        self.card_limit = self._create_info_card("⏳ WEEKLY PLAY LIMIT", "No limit set", "#FF7675")
        grid_layout.addWidget(self.card_limit, 0, 1)

        # File Location Card
        self.card_location = self._create_location_card("📁 FILE LOCATION", "--")
        grid_layout.addWidget(self.card_location, 1, 0)

        # Process Name Card
        self.card_process = self._create_info_card("⚙️ PROCESS EXECUTABLE", "--", "#00CEC9")
        grid_layout.addWidget(self.card_process, 1, 1)

        # Last Played Card
        self.card_last_played = self._create_info_card("📅 LAST PLAYED", "--", "#FDCB6E")
        grid_layout.addWidget(self.card_last_played, 2, 0)

        # Launch Arguments Card
        self.card_launch_args = self._create_info_card("🚀 LAUNCH PARAMETERS", "None", "#A29BFE")
        grid_layout.addWidget(self.card_launch_args, 2, 1)

        layout.addLayout(grid_layout)
        layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    def _create_info_card(self, title: str, value: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #141724;
                border: 1px solid #2B304A;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        vbox = QVBoxLayout(card)
        vbox.setSpacing(8)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {accent_color}; letter-spacing: 1px;")
        vbox.addWidget(lbl_t)

        lbl_v = QLabel(value)
        lbl_v.setObjectName("CardValue")
        lbl_v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl_v.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        lbl_v.setWordWrap(True)
        vbox.addWidget(lbl_v)

        return card

    def _create_location_card(self, title: str, path_value: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #141724;
                border: 1px solid #2B304A;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        vbox = QVBoxLayout(card)
        vbox.setSpacing(8)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 11px; font-weight: bold; color: #00CEC9; letter-spacing: 1px;")
        vbox.addWidget(lbl_t)

        path_box = QHBoxLayout()
        path_box.setSpacing(8)

        self.lbl_location = QLabel(path_value)
        self.lbl_location.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_location.setStyleSheet("font-size: 13px; font-family: 'Consolas', monospace; color: #E1E7ED;")
        self.lbl_location.setWordWrap(True)
        path_box.addWidget(self.lbl_location, stretch=1)

        btn_copy = QPushButton("📋 Copy")
        btn_copy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #1E2235;
                color: #8E9BB0;
                border: 1px solid #2B304A;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #6C5CE7;
                color: #FFFFFF;
                border-color: #6C5CE7;
            }
        """)
        btn_copy.clicked.connect(self.copy_location_to_clipboard)
        path_box.addWidget(btn_copy)

        vbox.addLayout(path_box)
        return card

    def set_game(self, game: GameEntry):
        self.game = game
        self.update_display()

    def update_display(self):
        if not self.game:
            return

        self.lbl_title.setText(self.game.name)

        # Load Icon
        if self.game.icon_path and os.path.exists(self.game.icon_path):
            pixmap = QPixmap(self.game.icon_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.icon_label.setPixmap(scaled)
            else:
                self.icon_label.setText("🎮")
                self.icon_label.setStyleSheet("font-size: 40px;")
        else:
            fallback = "📦" if self.game.needs_installation else "📥" if self.game.is_downloading else "🎮"
            self.icon_label.setText(fallback)
            self.icon_label.setStyleSheet("font-size: 40px;")

        # Update Favorite button state
        if self.game.is_favorite:
            self.btn_favorite.setText("★")
            self.btn_favorite.setToolTip("Remove from Favorites")
            self.btn_favorite.setStyleSheet("""
                QPushButton {
                    background: #1E2235;
                    color: #FFD700;
                    font-size: 20px;
                    border: 1px solid #FFD700;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: #FFD700;
                    color: #0F111A;
                }
            """)
        else:
            self.btn_favorite.setText("☆")
            self.btn_favorite.setToolTip("Add to Favorites")
            self.btn_favorite.setStyleSheet("""
                QPushButton {
                    background: #1E2235;
                    color: #8E9BB0;
                    font-size: 20px;
                    border: 1px solid #2B304A;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    color: #FFD700;
                    border-color: #FFD700;
                }
            """)

        # Action Button & Status Badge
        if self.game.is_downloading:
            speed_txt = f"{self.game.download_speed} • ETA: {self.game.download_eta}" if self.game.download_speed else "Downloading..."
            self.lbl_status_badge.setText(f"Downloading ({int(self.game.download_progress)}%)")
            self.lbl_status_badge.setStyleSheet("background-color: #141724; color: #00CEC9; border: 1px solid #00CEC9; border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 12px;")
            self.btn_action.setText(f"⏬ DOWNLOADING ({int(self.game.download_progress)}%)")
            self.btn_action.setEnabled(True)
        elif self.game.needs_installation:
            self.lbl_status_badge.setText("Setup Ready")
            self.lbl_status_badge.setStyleSheet("background-color: #141724; color: #FDCB6E; border: 1px solid #FDCB6E; border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 12px;")
            self.btn_action.setText("🚀 RUN INSTALLER")
            self.btn_action.setEnabled(True)
        elif self.game.is_running:
            self.lbl_status_badge.setText("● Currently Running")
            self.lbl_status_badge.setStyleSheet("background-color: #00B894; color: #FFFFFF; border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 12px;")
            self.btn_action.setText("● GAME IS RUNNING")
            self.btn_action.setEnabled(False)
        elif self.game.is_limit_reached():
            self.lbl_status_badge.setText("Playtime Limit Reached")
            self.lbl_status_badge.setStyleSheet("background-color: #272C45; color: #FF7675; border: 1px solid #FF7675; border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 12px;")
            self.btn_action.setText("PLAYTIME REACHED")
            self.btn_action.setEnabled(False)
        else:
            self.lbl_status_badge.setText("Ready to Play")
            self.lbl_status_badge.setStyleSheet("background-color: #1E2235; color: #00CEC9; border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 12px;")
            self.btn_action.setText("▶ LAUNCH GAME")
            self.btn_action.setEnabled(True)

        # Update Info Cards
        val_playtime = self.card_playtime.findChild(QLabel, "CardValue")
        if val_playtime:
            val_playtime.setText(self.game.formatted_playtime())

        val_limit = self.card_limit.findChild(QLabel, "CardValue")
        if val_limit:
            if self.game.play_time_limit > 0:
                wk_str = self.game.formatted_weekly_playtime()
                limit_str = format_playtime(self.game.play_time_limit * 3600)
                if self.game.is_limit_reached():
                    val_limit.setText(f"{wk_str} / {limit_str}\n(Limit Reached)")
                else:
                    rem_seconds = max(0.0, (self.game.play_time_limit * 3600.0) - self.game.weekly_playtime)
                    rem_str = format_playtime(rem_seconds)
                    val_limit.setText(f"{wk_str} / {limit_str}\n({rem_str} remaining)")
            else:
                val_limit.setText("No limit set")

        loc_path = self.game.exe_path or self.game.download_dir or self.game.installer_path or "Not specified"
        self.lbl_location.setText(loc_path)

        val_process = self.card_process.findChild(QLabel, "CardValue")
        if val_process:
            val_process.setText(self.game.process_name or "Not specified")

        val_last = self.card_last_played.findChild(QLabel, "CardValue")
        if val_last:
            val_last.setText(self.game.last_played or "Never")

        val_args = self.card_launch_args.findChild(QLabel, "CardValue")
        if val_args:
            val_args.setText(self.game.launch_args if self.game.launch_args else "None")

    def update_playtime_display(self, total_seconds: float):
        if self.game and not self.game.is_downloading:
            self.game.playtime = total_seconds
            self.update_display()

    def copy_location_to_clipboard(self):
        path_text = self.lbl_location.text()
        if path_text and path_text != "Not specified":
            QApplication.clipboard().setText(path_text)

    def open_exe_folder(self):
        if not self.game:
            return
        target_path = self.game.download_dir if self.game.is_downloading else self.game.exe_path
        if not target_path and self.game.installer_path:
            target_path = self.game.installer_path

        if target_path:
            folder = target_path if os.path.isdir(target_path) else os.path.dirname(target_path)
            if os.path.exists(folder):
                os.startfile(folder)
                return
        QMessageBox.warning(self, "Folder Not Found", f"Directory does not exist:\n{target_path}")

    def on_action_clicked(self):
        if not self.game:
            return
        if self.game.is_limit_reached():
            QMessageBox.warning(
                self,
                "Playtime Limit Reached",
                f"Weekly playtime limit of {self.game.play_time_limit:.1f} hrs reached for '{self.game.name}'.\nLimit resets on Monday."
            )
            return
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

    def on_favorite_clicked(self):
        if self.game:
            self.favorite_toggled.emit(self.game.id)
            self.game.is_favorite = not self.game.is_favorite
            self.update_display()

    def on_remove_clicked(self):
        if self.game:
            if self.game.is_downloading:
                self.cancel_download_requested.emit(self.game.id)
            else:
                self.remove_requested.emit(self.game.id)
