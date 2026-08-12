import logging
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QDoubleSpinBox
)

from src.database import DatabaseManager
from src.config import format_playtime

logger = logging.getLogger("LimitsView")


class LimitsViewWidget(QWidget):
    """
    Theme-aware View widget for setting and managing COLLECTIVE daily and weekly playtime limits across all games combined.
    Uses src/ui/styles.py for all visual styling and color themes.
    """
    limits_updated = pyqtSignal()

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Title & Description
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        title = QLabel("⏱️ Collective Playtime Limits")
        title.setObjectName("LimitsHeaderTitle")
        header_layout.addWidget(title)

        subtitle = QLabel(
            "Set shared maximum daily and weekly playtime limits across ALL games combined "
            "(e.g., playing Skyrim and Stardew Valley together shares the total allowed time)."
        )
        subtitle.setObjectName("LimitsHeaderSubtitle")
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)

        main_layout.addLayout(header_layout)

        # Scroll Area Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 10, 10)
        layout.setSpacing(20)

        # Status Feedback Toast/Banner
        self.status_banner = QFrame()
        self.status_banner.setObjectName("LimitsStatusBanner")
        sb_layout = QHBoxLayout(self.status_banner)
        sb_layout.setContentsMargins(14, 10, 14, 10)

        self.lbl_status = QLabel("ℹ️ Select a preset or set custom shared limits below.")
        self.lbl_status.setObjectName("LimitsStatusLabel")
        sb_layout.addWidget(self.lbl_status)
        layout.addWidget(self.status_banner)

        # Active Overview Summary Card
        self.summary_card = QFrame()
        self.summary_card.setObjectName("LimitsCard")
        sum_layout = QVBoxLayout(self.summary_card)
        sum_layout.setContentsMargins(18, 16, 18, 16)
        sum_layout.setSpacing(8)

        sum_title = QLabel("📊 Shared Collective Limits Overview")
        sum_title.setObjectName("LimitsOverviewTitle")
        sum_layout.addWidget(sum_title)

        self.lbl_overview_info = QLabel()
        self.lbl_overview_info.setObjectName("LimitsOverviewInfo")
        sum_layout.addWidget(self.lbl_overview_info)

        layout.addWidget(self.summary_card)

        # -------------------------------------------------------------
        # Section 1: Maximum Collective Daily Playtime Limits
        # -------------------------------------------------------------
        daily_card = QFrame()
        daily_card.setObjectName("LimitsCard")
        daily_layout = QVBoxLayout(daily_card)
        daily_layout.setContentsMargins(18, 18, 18, 18)
        daily_layout.setSpacing(14)

        d_title = QLabel("☀️ Maximum Daily Playtime (All Games Combined)")
        d_title.setObjectName("LimitsCardTitle")
        daily_layout.addWidget(d_title)

        d_desc = QLabel("Total allowed gaming time per day across all games in your library combined.")
        d_desc.setObjectName("LimitsCardDesc")
        daily_layout.addWidget(d_desc)

        # Presets for Collective Daily
        d_preset_lbl = QLabel("Quick Presets (Combined Daily Limit):")
        d_preset_lbl.setObjectName("LimitsCardDesc")
        daily_layout.addWidget(d_preset_lbl)

        d_preset_layout = QHBoxLayout()
        d_preset_layout.setSpacing(10)

        daily_presets = [
            ("30 Mins", 0.5),
            ("1 Hour", 1.0),
            ("2 Hours", 2.0),
            ("3 Hours", 3.0),
            ("5 Hours", 5.0),
            ("Unlimited", 0.0)
        ]

        for label, hrs in daily_presets:
            btn = QPushButton(label)
            btn.setObjectName("PresetButton")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda _, h=hrs: self.apply_daily_limit(h))
            d_preset_layout.addWidget(btn)

        daily_layout.addLayout(d_preset_layout)

        # Custom Spinbox + Apply Button
        custom_daily_layout = QHBoxLayout()
        custom_daily_layout.setSpacing(12)

        lbl_spin_d = QLabel("Custom Shared Daily Limit (Hours):")
        lbl_spin_d.setObjectName("LimitsOverviewTitle")
        custom_daily_layout.addWidget(lbl_spin_d)

        self.spin_daily = QDoubleSpinBox()
        self.spin_daily.setRange(0.0, 24.0)
        self.spin_daily.setSingleStep(0.5)
        self.spin_daily.setDecimals(1)
        self.spin_daily.setSuffix(" hrs/day")
        self.spin_daily.setValue(self.db_manager.collective_daily_limit or 2.0)
        self.spin_daily.setFixedWidth(140)
        custom_daily_layout.addWidget(self.spin_daily)

        btn_apply_daily = QPushButton("Set Collective Daily Limit")
        btn_apply_daily.setObjectName("PrimaryButton")
        btn_apply_daily.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_apply_daily.clicked.connect(lambda: self.apply_daily_limit(self.spin_daily.value()))
        custom_daily_layout.addWidget(btn_apply_daily)
        custom_daily_layout.addStretch()

        daily_layout.addLayout(custom_daily_layout)
        layout.addWidget(daily_card)

        # -------------------------------------------------------------
        # Section 2: Maximum Collective Weekly Playtime Limits
        # -------------------------------------------------------------
        weekly_card = QFrame()
        weekly_card.setObjectName("LimitsCard")
        weekly_layout = QVBoxLayout(weekly_card)
        weekly_layout.setContentsMargins(18, 18, 18, 18)
        weekly_layout.setSpacing(14)

        w_title = QLabel("📅 Maximum Weekly Playtime (All Games Combined)")
        w_title.setObjectName("LimitsCardWeeklyTitle")
        weekly_layout.addWidget(w_title)

        w_desc = QLabel("Total allowed gaming time per week (Monday - Sunday) across all games combined.")
        w_desc.setObjectName("LimitsCardDesc")
        weekly_layout.addWidget(w_desc)

        # Presets for Collective Weekly
        w_preset_lbl = QLabel("Quick Presets (Combined Weekly Limit):")
        w_preset_lbl.setObjectName("LimitsCardDesc")
        weekly_layout.addWidget(w_preset_lbl)

        w_preset_layout = QHBoxLayout()
        w_preset_layout.setSpacing(10)

        weekly_presets = [
            ("2 Hours", 2.0),
            ("5 Hours", 5.0),
            ("10 Hours", 10.0),
            ("20 Hours", 20.0),
            ("40 Hours", 40.0),
            ("Unlimited", 0.0)
        ]

        for label, hrs in weekly_presets:
            btn = QPushButton(label)
            btn.setObjectName("PresetButton")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda _, h=hrs: self.apply_weekly_limit(h))
            w_preset_layout.addWidget(btn)

        weekly_layout.addLayout(w_preset_layout)

        # Custom Spinbox + Apply Button
        custom_weekly_layout = QHBoxLayout()
        custom_weekly_layout.setSpacing(12)

        lbl_spin_w = QLabel("Custom Shared Weekly Limit (Hours):")
        lbl_spin_w.setObjectName("LimitsOverviewTitle")
        custom_weekly_layout.addWidget(lbl_spin_w)

        self.spin_weekly = QDoubleSpinBox()
        self.spin_weekly.setRange(0.0, 168.0)
        self.spin_weekly.setSingleStep(1.0)
        self.spin_weekly.setDecimals(1)
        self.spin_weekly.setSuffix(" hrs/week")
        self.spin_weekly.setValue(self.db_manager.collective_weekly_limit or 10.0)
        self.spin_weekly.setFixedWidth(140)
        custom_weekly_layout.addWidget(self.spin_weekly)

        btn_apply_weekly = QPushButton("Set Collective Weekly Limit")
        btn_apply_weekly.setObjectName("PrimaryButton")
        btn_apply_weekly.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_apply_weekly.clicked.connect(lambda: self.apply_weekly_limit(self.spin_weekly.value()))
        custom_weekly_layout.addWidget(btn_apply_weekly)
        custom_weekly_layout.addStretch()

        weekly_layout.addLayout(custom_weekly_layout)
        layout.addWidget(weekly_card)

        # -------------------------------------------------------------
        # Section 3: Combined Collective Combo Presets
        # -------------------------------------------------------------
        combo_card = QFrame()
        combo_card.setObjectName("LimitsCard")
        combo_layout = QVBoxLayout(combo_card)
        combo_layout.setContentsMargins(18, 18, 18, 18)
        combo_layout.setSpacing(14)

        c_title = QLabel("⚡ Quick Batch Combo Presets")
        c_title.setObjectName("LimitsCardComboTitle")
        combo_layout.addWidget(c_title)

        c_desc = QLabel("Apply both Daily & Weekly collective limits at once in a single click.")
        c_desc.setObjectName("LimitsCardDesc")
        combo_layout.addWidget(c_desc)

        combo_btn_layout = QHBoxLayout()
        combo_btn_layout.setSpacing(12)

        combos = [
            ("🔒 Strict Mode\n(1h/day, 5h/week)", 1.0, 5.0, "SecondaryButton"),
            ("⚖️ Balanced Mode\n(2h/day, 12h/week)", 2.0, 12.0, "SecondaryButton"),
            ("🎮 Gamer Mode\n(4h/day, 25h/week)", 4.0, 25.0, "SecondaryButton"),
            ("🔓 Clear Limits\n(Unlimited)", 0.0, 0.0, "DangerButton")
        ]

        for label, d_hrs, w_hrs, style_name in combos:
            btn = QPushButton(label)
            btn.setObjectName(style_name)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(50)
            btn.clicked.connect(lambda _, d=d_hrs, w=w_hrs: self.apply_combo_limits(d, w))
            combo_btn_layout.addWidget(btn)

        combo_layout.addLayout(combo_btn_layout)
        layout.addWidget(combo_card)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.refresh_overview()

    def refresh_overview(self):
        total_games = len(self.db_manager.get_all_games())

        today_secs = self.db_manager.get_collective_today_playtime_seconds()
        weekly_secs = self.db_manager.get_collective_weekly_playtime_seconds()

        today_hrs = today_secs / 3600.0
        weekly_hrs = weekly_secs / 3600.0

        daily_limit = self.db_manager.collective_daily_limit
        weekly_limit = self.db_manager.collective_weekly_limit

        daily_limit_str = f"{daily_limit:.1f} hours/day" if daily_limit > 0 else "Unlimited"
        weekly_limit_str = f"{weekly_limit:.1f} hours/week" if weekly_limit > 0 else "Unlimited"

        today_fmt = format_playtime(today_secs)
        weekly_fmt = format_playtime(weekly_secs)

        d_status = f"{today_fmt} / {daily_limit_str}"
        w_status = f"{weekly_fmt} / {weekly_limit_str}"

        self.lbl_overview_info.setText(
            f"<b>Library Size:</b> {total_games} games combined<br>"
            f"<b>Collective Playtime Today:</b> {d_status}<br>"
            f"<b>Collective Playtime This Week:</b> {w_status}"
        )

        d_reached = self.db_manager.is_collective_daily_limit_reached()
        w_reached = self.db_manager.is_collective_weekly_limit_reached()

        if d_reached:
            self.lbl_status.setText(f"⚠️ Collective Daily Playtime Limit Reached! ({today_hrs:.1f}h / {daily_limit:.1f}h limit reached today)")
        elif w_reached:
            self.lbl_status.setText(f"⚠️ Collective Weekly Playtime Limit Reached! ({weekly_hrs:.1f}h / {weekly_limit:.1f}h limit reached this week)")
        elif daily_limit > 0 or weekly_limit > 0:
            self.lbl_status.setText("🟢 Playable — Shared gaming time is under set limits.")
        else:
            self.lbl_status.setText("ℹ️ Unlimited — No shared playtime limits active.")

    def apply_daily_limit(self, hours: float):
        self.db_manager.set_collective_daily_limit(hours)
        if hours > 0:
            msg = f"✅ Collective daily limit of {hours:.1f} hour(s) set for all games combined."
        else:
            msg = "✅ Collective daily limit cleared (Unlimited)."
        self.lbl_status.setText(msg)
        self.spin_daily.setValue(hours)
        self.refresh_overview()
        self.limits_updated.emit()

    def apply_weekly_limit(self, hours: float):
        self.db_manager.set_collective_weekly_limit(hours)
        if hours > 0:
            msg = f"✅ Collective weekly limit of {hours:.1f} hour(s) set for all games combined."
        else:
            msg = "✅ Collective weekly limit cleared (Unlimited)."
        self.lbl_status.setText(msg)
        self.spin_weekly.setValue(hours)
        self.refresh_overview()
        self.limits_updated.emit()

    def apply_combo_limits(self, daily_hours: float, weekly_hours: float):
        self.db_manager.set_collective_limits(daily_hours, weekly_hours)
        if daily_hours > 0 or weekly_hours > 0:
            msg = f"✅ Collective limits set: {daily_hours:.1f}h/day, {weekly_hours:.1f}h/week for all games combined."
        else:
            msg = "✅ All collective playtime limits cleared (Unlimited)."
        self.lbl_status.setText(msg)
        self.spin_daily.setValue(daily_hours)
        self.spin_weekly.setValue(weekly_hours)
        self.refresh_overview()
        self.limits_updated.emit()
