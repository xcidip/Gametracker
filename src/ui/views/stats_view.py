import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout
)

from database import DatabaseManager
from config import format_playtime

class StatSummaryCard(QFrame):
    """Stat KPI metric box (e.g. Total Playtime, Total Games)."""
    def __init__(self, title: str, value: str, icon_symbol: str = "⏱️", accent_color: str = "#6C5CE7", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1E2235;
                border: 1px solid #2B304A;
                border-radius: 12px;
                padding: 12px;
            }}
        """)

        layout = QHBoxLayout(self)
        
        icon_lbl = QLabel(icon_symbol)
        icon_lbl.setStyleSheet("font-size: 32px;")
        layout.addWidget(icon_lbl)

        v_layout = QVBoxLayout()
        v_layout.setSpacing(2)

        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #8E9BB0;")
        v_layout.addWidget(title_lbl)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {accent_color};")
        v_layout.addWidget(val_lbl)

        layout.addLayout(v_layout, stretch=1)


class StatsViewWidget(QWidget):
    """
    Analytics View showing total playtime stats and top played games leaderboard.
    """
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        title = QLabel("Playtime Analytics & Leaderboard")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF;")
        main_layout.addWidget(title)

        # Top Summary KPIs
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(14)
        main_layout.addLayout(self.kpi_layout)

        # Scroll Area for Leaderboard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(12)

        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll, stretch=1)

        self.refresh_stats()

    def refresh_stats(self):
        # Clear KPI layout
        while self.kpi_layout.count():
            item = self.kpi_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear scroll content
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        games = self.db_manager.get_all_games()
        total_playtime_secs = sum(g.playtime for g in games)
        total_games = len(games)

        most_played = max(games, key=lambda g: g.playtime) if games else None
        top_game_name = most_played.name if (most_played and most_played.playtime > 0) else "None"

        # KPIs
        card_total_time = StatSummaryCard("Total Playtime", format_playtime(total_playtime_secs, verbose=True), "⏱️", "#00CEC9")
        card_total_games = StatSummaryCard("Games Tracked", str(total_games), "🎮", "#6C5CE7")
        card_top_game = StatSummaryCard("Most Played", top_game_name, "🏆", "#FFD700")

        self.kpi_layout.addWidget(card_total_time)
        self.kpi_layout.addWidget(card_total_games)
        self.kpi_layout.addWidget(card_top_game)

        # Leaderboard Header
        lb_title = QLabel("Playtime Ranking")
        lb_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #6C5CE7; margin-top: 10px;")
        self.scroll_layout.addWidget(lb_title)

        if not games:
            empty_lbl = QLabel("No games in library yet. Add games to see rankings!")
            empty_lbl.setStyleSheet("color: #8E9BB0; font-style: italic; padding: 20px;")
            self.scroll_layout.addWidget(empty_lbl)
            return

        sorted_games = sorted(games, key=lambda g: g.playtime, reverse=True)

        for rank, game in enumerate(sorted_games, 1):
            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background-color: #1E2235;
                    border: 1px solid #2B304A;
                    border-radius: 10px;
                    padding: 10px;
                }
            """)
            r_layout = QHBoxLayout(row)
            r_layout.setSpacing(14)

            # Rank Badge
            rank_lbl = QLabel(f"#{rank}")
            rank_color = "#FFD700" if rank == 1 else "#C0C0C0" if rank == 2 else "#CD7F32" if rank == 3 else "#8E9BB0"
            rank_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {rank_color}; min-width: 35px;")
            r_layout.addWidget(rank_lbl)

            # Icon
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(36, 36)
            if game.icon_path and os.path.exists(game.icon_path):
                pix = QPixmap(game.icon_path)
                if not pix.isNull():
                    icon_lbl.setPixmap(pix.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            r_layout.addWidget(icon_lbl)

            # Name & Exe
            n_layout = QVBoxLayout()
            n_layout.setSpacing(2)

            name_lbl = QLabel(game.name)
            name_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
            n_layout.addWidget(name_lbl)

            last_lbl = QLabel(f"Last Played: {game.last_played}")
            last_lbl.setStyleSheet("font-size: 11px; color: #8E9BB0;")
            n_layout.addWidget(last_lbl)

            r_layout.addLayout(n_layout, stretch=1)

            # Playtime
            time_lbl = QLabel(format_playtime(game.playtime, verbose=False))
            time_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #00CEC9;")
            r_layout.addWidget(time_lbl)

            self.scroll_layout.addWidget(row)

        self.scroll_layout.addStretch()
