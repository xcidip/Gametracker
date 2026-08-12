import logging
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QPushButton, QFrame
)

from src.database import GameEntry

logger = logging.getLogger("SetLimitDialog")


class SetLimitDialog(QDialog):
    """
    Dialog for configuring the weekly hour play time limit for a game (Monday to Sunday).
    """
    limit_saved = pyqtSignal(str, float)  # game_id, limit_hours

    def __init__(self, game: GameEntry, parent=None):
        super().__init__(parent)
        self.game = game
        self.setWindowTitle(f"Set Weekly Play Time Limit - {game.name}")
        self.setFixedWidth(440)
        self.setStyleSheet("""
            QDialog {
                background-color: #141724;
                color: #FFFFFF;
            }
            QLabel {
                color: #E1E7ED;
            }
            QDoubleSpinBox {
                background-color: #1E2235;
                color: #00CEC9;
                border: 1px solid #2B304A;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
            }
            QPushButton#PrimaryButton {
                background-color: #6C5CE7;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#PrimaryButton:hover {
                background-color: #5B4BC4;
            }
            QPushButton#SecondaryButton {
                background-color: #1E2235;
                color: #8E9BB0;
                border: 1px solid #2B304A;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton#SecondaryButton:hover {
                background-color: #2B304A;
                color: #FFFFFF;
            }
            QPushButton#PresetButton {
                background-color: #1E2235;
                color: #00CEC9;
                border: 1px solid #2B304A;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#PresetButton:hover {
                background-color: #00CEC9;
                color: #0F111A;
            }
        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        title_label = QLabel("⏱️ Set Weekly Play Time Limit")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #6C5CE7;")
        layout.addWidget(title_label)

        sub_info = QLabel(
            f"Set maximum allowed play time for <b>{self.game.name}</b> during the current week.<br>"
            "<span style='color: #8E9BB0; font-size: 11px;'>* Note: Weekly cycles start on <b>Monday</b> and end on <b>Sunday</b>.</span>"
        )
        sub_info.setWordWrap(True)
        layout.addWidget(sub_info)

        # Current Playtime Info Box
        info_box = QFrame()
        info_box.setStyleSheet("background-color: #1E2235; border: 1px solid #2B304A; border-radius: 10px; padding: 10px;")
        info_layout = QVBoxLayout(info_box)
        info_layout.setSpacing(4)

        cur_weekly = self.game.formatted_weekly_playtime(verbose=True)
        lbl_cur = QLabel(f"<b>Played this week:</b> {cur_weekly}")
        lbl_cur.setStyleSheet("font-size: 13px; color: #00CEC9;")
        info_layout.addWidget(lbl_cur)

        if self.game.play_time_limit > 0:
            lbl_cur_limit = QLabel(f"<b>Current limit:</b> {self.game.play_time_limit:.1f} hours / week")
        else:
            lbl_cur_limit = QLabel("<b>Current limit:</b> No limit set")
        lbl_cur_limit.setStyleSheet("font-size: 12px; color: #8E9BB0;")
        info_layout.addWidget(lbl_cur_limit)

        layout.addWidget(info_box)

        # Spin box input layout
        spin_layout = QVBoxLayout()
        spin_layout.setSpacing(6)
        
        spin_label = QLabel("Weekly Limit (Hours):")
        spin_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        spin_layout.addWidget(spin_label)

        self.spin_limit = QDoubleSpinBox()
        self.spin_limit.setRange(0.0, 168.0)
        self.spin_limit.setSingleStep(0.5)
        self.spin_limit.setDecimals(1)
        self.spin_limit.setSuffix(" hrs")
        self.spin_limit.setValue(self.game.play_time_limit)
        spin_layout.addWidget(self.spin_limit)

        layout.addLayout(spin_layout)

        # Preset Quick Choice Buttons
        preset_label = QLabel("Quick Presets:")
        preset_label.setStyleSheet("font-size: 11px; color: #8E9BB0; font-weight: bold;")
        layout.addWidget(preset_label)

        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(8)

        presets = [("1 Hr", 1.0), ("2 Hrs", 2.0), ("5 Hrs", 5.0), ("10 Hrs", 10.0), ("No Limit", 0.0)]
        for label, hrs in presets:
            btn = QPushButton(label)
            btn.setObjectName("PresetButton")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda _, h=hrs: self.spin_limit.setValue(h))
            preset_layout.addWidget(btn)

        layout.addLayout(preset_layout)

        # Action Buttons (Save / Cancel)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("SecondaryButton")
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Save Limit")
        btn_save.setObjectName("PrimaryButton")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.clicked.connect(self.on_save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def on_save(self):
        new_limit = self.spin_limit.value()
        self.limit_saved.emit(self.game.id, new_limit)
        self.accept()
