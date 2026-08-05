import logging
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QWidget, QMessageBox
)

from src.core.tracker import scan_running_applications
from src.database import DatabaseManager

logger = logging.getLogger("DetectorDialog")

class AppListItemWidget(QWidget):
    """Custom widget for rendering a detected app item with icon, name, exe path, and Add button."""
    add_clicked = pyqtSignal(dict)

    def __init__(self, app_info: dict, parent=None):
        super().__init__(parent)
        self.app_info = app_info
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.app_info.get("icon_path"):
            pix = QPixmap(self.app_info["icon_path"])
            if not pix.isNull():
                self.icon_label.setPixmap(pix.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.icon_label.setText("💻")
        else:
            self.icon_label.setText("💻")
        layout.addWidget(self.icon_label)

        # Name & Path
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.name_label = QLabel(self.app_info["name"])
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        info_layout.addWidget(self.name_label)

        self.sub_label = QLabel(f"{self.app_info['process_name']}  •  {self.app_info['exe_path']}")
        self.sub_label.setStyleSheet("font-size: 11px; color: #8E9BB0;")
        info_layout.addWidget(self.sub_label)

        layout.addLayout(info_layout, stretch=1)

        # Add Button
        self.btn_add = QPushButton("＋ Add to Library")
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_add.setFixedSize(130, 32)
        self.btn_add.clicked.connect(lambda: self.add_clicked.emit(self.app_info))
        layout.addWidget(self.btn_add)


class RunningAppDetectorDialog(QDialog):
    """
    Dialog displaying currently running processes / open apps for quick 1-click addition to library.
    """
    game_added = pyqtSignal(dict)  # app_info dict

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Detect Active Applications & Games")
        self.setMinimumSize(650, 520)
        self.raw_apps = []

        self.init_ui()
        self.refresh_running_apps()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Title / Description
        title_label = QLabel("Detect Running Applications")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #6C5CE7;")
        layout.addWidget(title_label)

        desc_label = QLabel("Select any running application or game below to add it to your Playtime Tracking Library.")
        desc_label.setStyleSheet("color: #8E9BB0; font-size: 12px;")
        layout.addWidget(desc_label)

        # Filter bar & Refresh button
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filter running apps by name or executable...")
        self.search_input.textChanged.connect(self.filter_apps)
        filter_layout.addWidget(self.search_input)

        self.btn_refresh = QPushButton("🔄 Refresh List")
        self.btn_refresh.setObjectName("SecondaryButton")
        self.btn_refresh.clicked.connect(self.refresh_running_apps)
        filter_layout.addWidget(self.btn_refresh)

        layout.addLayout(filter_layout)

        # App List Widget
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, stretch=1)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setObjectName("SecondaryButton")
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)

        layout.addLayout(bottom_layout)

    def refresh_running_apps(self):
        self.list_widget.clear()
        self.raw_apps = scan_running_applications()
        self.populate_list(self.raw_apps)

    def populate_list(self, apps: list):
        self.list_widget.clear()

        existing_games = self.db_manager.get_all_games()
        existing_exes = {g.exe_path.lower() for g in existing_games if g.exe_path}

        for app in apps:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 56))

            item_widget = AppListItemWidget(app)
            item_widget.add_clicked.connect(self.on_add_app)

            # Highlight if already in library
            if app["exe_path"].lower() in existing_exes:
                item_widget.btn_add.setText("✓ In Library")
                item_widget.btn_add.setObjectName("SecondaryButton")
                item_widget.btn_add.setEnabled(False)

            self.list_widget.setItemWidget(item, item_widget)

    def filter_apps(self, query: str):
        q = query.lower().strip()
        if not q:
            filtered = self.raw_apps
        else:
            filtered = [
                app for app in self.raw_apps
                if q in app["name"].lower() or q in app["process_name"].lower() or q in app["exe_path"].lower()
            ]
        self.populate_list(filtered)

    def on_add_app(self, app_info: dict):
        game = self.db_manager.add_game(
            name=app_info["name"],
            exe_path=app_info["exe_path"],
            process_name=app_info["process_name"],
            icon_path=app_info["icon_path"]
        )
        self.game_added.emit(app_info)
        QMessageBox.information(self, "App Added", f"'{game.name}' has been added to your library!")
        self.refresh_running_apps()
