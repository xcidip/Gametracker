import time
import logging
from typing import Callable, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QMessageBox, QScrollArea
)

from database import DatabaseManager, GameEntry

logger = logging.getLogger("DebugView")

# 6 realistic test game presets
TEST_GAMES_PRESETS = [
    {
        "name": "Cyberpunk 2077",
        "exe_path": r"C:\Games\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe",
        "process_name": "cyberpunk2077.exe",
        "playtime": 153000.0,  # 42h 30m
        "last_played": "2026-08-04 21:15:00",
        "is_favorite": True,
    },
    {
        "name": "Elden Ring",
        "exe_path": r"C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game\eldenring.exe",
        "process_name": "eldenring.exe",
        "playtime": 460800.0,  # 128h 00m
        "last_played": "2026-08-05 14:30:00",
        "is_favorite": True,
    },
    {
        "name": "The Witcher 3: Wild Hunt",
        "exe_path": r"C:\Games\The Witcher 3\bin\x64\witcher3.exe",
        "process_name": "witcher3.exe",
        "playtime": 306720.0,  # 85h 12m
        "last_played": "2026-07-28 19:45:00",
        "is_favorite": False,
    },
    {
        "name": "Hollow Knight",
        "exe_path": r"C:\Program Files (x86)\Steam\steamapps\common\Hollow Knight\hollow_knight.exe",
        "process_name": "hollow_knight.exe",
        "playtime": 114480.0,  # 31h 48m
        "last_played": "2026-08-01 11:20:00",
        "is_favorite": False,
    },
    {
        "name": "Stardew Valley",
        "exe_path": r"C:\Program Files (x86)\Steam\steamapps\common\Stardew Valley\Stardew Valley.exe",
        "process_name": "stardew valley.exe",
        "playtime": 230400.0,  # 64h 00m
        "last_played": "2026-08-03 18:00:00",
        "is_favorite": True,
    },
    {
        "name": "Portal 2",
        "exe_path": r"C:\Program Files (x86)\Steam\steamapps\common\Portal 2\portal2.exe",
        "process_name": "portal2.exe",
        "playtime": 52200.0,   # 14h 30m
        "last_played": "2026-07-15 16:10:00",
        "is_favorite": False,
    },
]


class DebugViewWidget(QWidget):
    """
    Debug & Developer Console View for testing card management and database actions.
    """
    def __init__(self, db_manager: DatabaseManager, on_library_updated: Optional[Callable[[], None]] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.on_library_updated = on_library_updated
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header Title
        header_layout = QHBoxLayout()
        title_lbl = QLabel("🛠️ Debug & Developer Tools")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(title_lbl)

        badge_lbl = QLabel("DEBUG MODE")
        badge_lbl.setStyleSheet("background-color: #E67E22; color: #FFFFFF; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 4px 8px;")
        header_layout.addWidget(badge_lbl)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        desc_lbl = QLabel("Use this tab to generate test game cards, simulate game data, and inspect database state for testing UI components.")
        desc_lbl.setStyleSheet("color: #8E9BB0; font-size: 13px;")
        desc_lbl.setWordWrap(True)
        main_layout.addWidget(desc_lbl)

        # Main Actions Frame
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: #1E2235;
                border: 1px solid #2B304A;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setSpacing(14)

        sec_title = QLabel("CARD GENERATION CONTROLS")
        sec_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #6C5CE7; letter-spacing: 1px;")
        actions_layout.addWidget(sec_title)

        # Row 1: Primary Action Button - Add 6 Test Game Cards
        btn_row1 = QHBoxLayout()
        self.btn_add_6_cards = QPushButton("➕ Add 6 Test Game Cards")
        self.btn_add_6_cards.setObjectName("PrimaryButton")
        self.btn_add_6_cards.setMinimumHeight(42)
        self.btn_add_6_cards.setStyleSheet("""
            QPushButton {
                background-color: #6C5CE7;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5B4BC4;
            }
            QPushButton:pressed {
                background-color: #4A3BB3;
            }
        """)
        self.btn_add_6_cards.clicked.connect(self.add_6_test_game_cards)
        btn_row1.addWidget(self.btn_add_6_cards)

        self.btn_add_single = QPushButton("＋ Add 1 Custom Test Card")
        self.btn_add_single.setMinimumHeight(42)
        self.btn_add_single.setStyleSheet("""
            QPushButton {
                background-color: #1E2235;
                color: #00CEC9;
                border: 1px solid #00CEC9;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #00CEC9;
                color: #0F111A;
            }
        """)
        self.btn_add_single.clicked.connect(self.add_single_test_card)
        btn_row1.addWidget(self.btn_add_single)

        actions_layout.addLayout(btn_row1)

        # Row 2: Cleanup Actions
        btn_row2 = QHBoxLayout()
        self.btn_clear_test = QPushButton("🗑️ Clear Test Cards")
        self.btn_clear_test.setStyleSheet("""
            QPushButton {
                background-color: #272C45;
                color: #E67E22;
                border: 1px solid #E67E22;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #E67E22;
                color: #FFFFFF;
            }
        """)
        self.btn_clear_test.clicked.connect(self.clear_test_cards)
        btn_row2.addWidget(self.btn_clear_test)

        self.btn_clear_all = QPushButton("⚠️ Clear Entire Library")
        self.btn_clear_all.setObjectName("DangerButton")
        self.btn_clear_all.setStyleSheet("""
            QPushButton {
                background-color: #272C45;
                color: #FF7675;
                border: 1px solid #FF7675;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FF7675;
                color: #FFFFFF;
            }
        """)
        self.btn_clear_all.clicked.connect(self.clear_entire_library)
        btn_row2.addWidget(self.btn_clear_all)

        btn_row2.addStretch()
        actions_layout.addLayout(btn_row2)

        main_layout.addWidget(actions_frame)

        # Information & Stats Summary
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #1E2235;
                border: 1px solid #2B304A;
                border-radius: 12px;
                padding: 14px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)

        self.stat_count_lbl = QLabel("Library Games: 0")
        self.stat_count_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #00CEC9;")
        info_layout.addWidget(self.stat_count_lbl)

        info_layout.addStretch()

        self.db_path_lbl = QLabel(f"DB Path: {self.db_manager.data_file}")
        self.db_path_lbl.setStyleSheet("font-size: 11px; color: #8E9BB0;")
        info_layout.addWidget(self.db_path_lbl)

        main_layout.addWidget(info_frame)

        # Log Output Box
        log_label = QLabel("DEBUG EVENT LOG")
        log_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #8E9BB0; letter-spacing: 1px;")
        main_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #141724;
                color: #00FFC6;
                border: 1px solid #2B304A;
                border-radius: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        main_layout.addWidget(self.log_text, stretch=1)

        self.log_event("Debug console initialized.")
        self.refresh_info()

    def log_event(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def refresh_info(self):
        count = len(self.db_manager.get_all_games())
        self.stat_count_lbl.setText(f"Library Games: {count}")

    def add_6_test_game_cards(self):
        """Adds 6 preset test game cards to the database library."""
        added_names = []
        for preset in TEST_GAMES_PRESETS:
            # Check if game with same name or process already exists to avoid duplicates or update them
            game = GameEntry(
                name=preset["name"],
                exe_path=preset["exe_path"],
                process_name=preset["process_name"],
                playtime=preset["playtime"],
                last_played=preset["last_played"],
                is_favorite=preset["is_favorite"],
            )
            self.db_manager.games[game.id] = game
            added_names.append(game.name)

        self.db_manager.save()
        
        self.log_event(f"Successfully added 6 test game cards:\n  • " + "\n  • ".join(added_names))
        self.refresh_info()

        if self.on_library_updated:
            self.on_library_updated()

        if self.isVisible():
            QMessageBox.information(
                self,
                "Test Cards Added",
                f"Added 6 test game cards to your library!\n\nGames added:\n" + "\n".join(f"• {name}" for name in added_names)
            )

    def add_single_test_card(self):
        """Adds a single randomized test game card."""
        count = len(self.db_manager.get_all_games()) + 1
        preset_idx = (count - 1) % len(TEST_GAMES_PRESETS)
        base = TEST_GAMES_PRESETS[preset_idx]
        
        name = f"{base['name']} (Test #{count})"
        game = GameEntry(
            name=name,
            exe_path=base["exe_path"],
            process_name=base["process_name"],
            playtime=float(count * 3600),
            last_played=time.strftime("%Y-%m-%d %H:%M:%S"),
            is_favorite=bool(count % 2 == 0),
        )
        self.db_manager.games[game.id] = game
        self.db_manager.save()

        self.log_event(f"Added single test game card: '{name}'")
        self.refresh_info()

        if self.on_library_updated:
            self.on_library_updated()

    def clear_test_cards(self):
        """Removes test cards matching preset names or test naming pattern."""
        preset_names = {p["name"].lower() for p in TEST_GAMES_PRESETS}
        to_delete = []
        for g_id, game in self.db_manager.games.items():
            if game.name.lower() in preset_names or "test #" in game.name.lower():
                to_delete.append(g_id)

        if not to_delete:
            self.log_event("No test game cards found to remove.")
            return

        for g_id in to_delete:
            del self.db_manager.games[g_id]

        self.db_manager.save()
        self.log_event(f"Cleared {len(to_delete)} test game cards.")
        self.refresh_info()

        if self.on_library_updated:
            self.on_library_updated()

    def clear_entire_library(self):
        """Empties all games from the database after confirmation."""
        reply = QMessageBox.question(
            self,
            "Clear Entire Library",
            "Are you sure you want to remove ALL games from the library database?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            count = len(self.db_manager.games)
            self.db_manager.games.clear()
            self.db_manager.save()
            self.log_event(f"Cleared entire library database ({count} entries deleted).")
            self.refresh_info()

            if self.on_library_updated:
                self.on_library_updated()
