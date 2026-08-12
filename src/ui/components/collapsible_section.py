from typing import List
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from src.ui.components.game_card import GameCardWidget


class CollapsibleSection(QWidget):
    """
    A collapsible library section widget featuring a clickable header bar
    (icon, title, count badge, toggle arrow) and a re-flowable grid container.
    """
    toggled = pyqtSignal(bool)  # Emits True if collapsed, False if expanded

    def __init__(self, key: str, title: str, icon: str = "⭐", is_collapsed: bool = False, parent=None):
        super().__init__(parent)
        self.key = key
        self.title_text = title
        self.icon_symbol = icon
        self.is_collapsed = is_collapsed
        self.cards: List[GameCardWidget] = []

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(10)

        # Header Frame
        self.header_frame = QFrame()
        self.header_frame.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.header_frame.setObjectName("SectionHeader")

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(10)

        # Toggle Arrow Icon Label
        self.arrow_label = QLabel("▼" if not self.is_collapsed else "▶")
        self.arrow_label.setObjectName("SectionHeaderArrow")
        header_layout.addWidget(self.arrow_label)

        # Title Label (Icon + Title)
        self.title_label = QLabel(f"{self.icon_symbol} {self.title_text}")
        self.title_label.setObjectName("SectionHeaderTitle")
        header_layout.addWidget(self.title_label)

        # Count Badge Label
        self.count_badge = QLabel("0")
        self.count_badge.setObjectName("SectionHeaderBadge")
        header_layout.addWidget(self.count_badge)

        header_layout.addStretch()

        root_layout.addWidget(self.header_frame)

        # Content Grid Container Widget
        self.content_widget = QWidget()
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setContentsMargins(0, 5, 0, 10)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        root_layout.addWidget(self.content_widget)

        # Connect click on header frame
        self.header_frame.mousePressEvent = self.on_header_clicked

        # Set initial visibility
        self.content_widget.setVisible(not self.is_collapsed)

    def on_header_clicked(self, event):
        self.is_collapsed = not self.is_collapsed
        self.content_widget.setVisible(not self.is_collapsed)
        self.arrow_label.setText("▶" if self.is_collapsed else "▼")
        self.toggled.emit(self.is_collapsed)

    def set_cards(self, cards: List[GameCardWidget], columns: int):
        self.cards = cards
        self.count_badge.setText(str(len(cards)))

        # Remove previous cards from this grid (without deleting them)
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        for idx, card in enumerate(cards):
            row = idx // columns
            col = idx % columns
            self.grid_layout.addWidget(card, row, col)

    def rearrange_cards(self, columns: int):
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        for idx, card in enumerate(self.cards):
            row = idx // columns
            col = idx % columns
            self.grid_layout.addWidget(card, row, col)
