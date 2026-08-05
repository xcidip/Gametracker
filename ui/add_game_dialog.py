import os
import logging
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QFrame
)

from icon_extractor import extract_icon_from_exe
from database import DatabaseManager, GameEntry

logger = logging.getLogger("AddGameDialog")

class AddGameDialog(QDialog):
    """
    Dialog for manually selecting an .exe file or editing game properties.
    """
    game_saved = pyqtSignal(object)  # GameEntry

    def __init__(self, db_manager: DatabaseManager, game_to_edit: GameEntry = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.game_to_edit = game_to_edit
        self.extracted_icon_path = ""

        self.setWindowTitle("Edit Game" if game_to_edit else "Add New Game / App")
        self.setMinimumWidth(500)

        self.init_ui()

        if game_to_edit:
            self.load_game_data(game_to_edit)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title_text = "Edit Game Details" if self.game_to_edit else "Add Custom Game / Executable"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #6C5CE7;")
        layout.addWidget(title_label)

        # Executable File Picker
        layout.addWidget(QLabel("Executable Path (.exe):"))
        exe_layout = QHBoxLayout()
        self.input_exe = QLineEdit()
        self.input_exe.setPlaceholderText("C:\\Games\\MyGame\\game.exe")
        self.input_exe.textChanged.connect(self.on_exe_changed)
        exe_layout.addWidget(self.input_exe)

        btn_browse = QPushButton("📁 Browse...")
        btn_browse.setObjectName("SecondaryButton")
        btn_browse.clicked.connect(self.browse_exe)
        exe_layout.addWidget(btn_browse)
        layout.addLayout(exe_layout)

        # App Display Name
        layout.addWidget(QLabel("Game / App Title:"))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Cyberpunk 2077")
        layout.addWidget(self.input_name)

        # Target Process Name
        layout.addWidget(QLabel("Target Process Name (for time tracking):"))
        self.input_process = QLineEdit()
        self.input_process.setPlaceholderText("e.g. Cyberpunk2077.exe")
        layout.addWidget(self.input_process)

        # Optional Launch Arguments
        layout.addWidget(QLabel("Launch Arguments (Optional):"))
        self.input_args = QLineEdit()
        self.input_args.setPlaceholderText("e.g. -fullscreen -novid")
        layout.addWidget(self.input_args)

        # Icon Preview Frame
        icon_frame = QHBoxLayout()
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(56, 56)
        self.icon_preview.setStyleSheet("border: 1px solid #2B304A; border-radius: 8px;")
        self.icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_preview.setText("🎮")
        icon_frame.addWidget(self.icon_preview)

        self.btn_icon_browse = QPushButton("Change Icon...")
        self.btn_icon_browse.setObjectName("SecondaryButton")
        self.btn_icon_browse.clicked.connect(self.browse_custom_icon)
        icon_frame.addWidget(self.btn_icon_browse)
        icon_frame.addStretch()

        layout.addLayout(icon_frame)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("SecondaryButton")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        self.btn_save = QPushButton("Save to Library")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.clicked.connect(self.save_game)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def browse_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Game Executable",
            "",
            "Executable Files (*.exe);;All Files (*.*)"
        )
        if file_path:
            self.input_exe.setText(file_path)

    def browse_custom_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Custom Icon Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.ico *.bmp);;All Files (*.*)"
        )
        if file_path:
            self.extracted_icon_path = file_path
            self.update_icon_preview(file_path)

    def on_exe_changed(self, exe_path: str):
        if exe_path and os.path.exists(exe_path):
            filename = os.path.basename(exe_path)
            if not self.input_name.text():
                clean_name = os.path.splitext(filename)[0].replace("_", " ").title()
                self.input_name.setText(clean_name)

            if not self.input_process.text():
                self.input_process.setText(filename)

            # Auto extract icon
            safe_name = os.path.splitext(filename)[0]
            self.extracted_icon_path = extract_icon_from_exe(exe_path, safe_name)
            self.update_icon_preview(self.extracted_icon_path)

    def update_icon_preview(self, icon_path: str):
        if icon_path and os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            if not pix.isNull():
                self.icon_preview.setPixmap(pix.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def load_game_data(self, game: GameEntry):
        self.input_exe.setText(game.exe_path)
        self.input_name.setText(game.name)
        self.input_process.setText(game.process_name)
        self.input_args.setText(game.launch_args)
        self.extracted_icon_path = game.icon_path
        self.update_icon_preview(game.icon_path)

    def save_game(self):
        exe_path = self.input_exe.text().strip()
        name = self.input_name.text().strip()
        proc_name = self.input_process.text().strip()
        args = self.input_args.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a game/app title.")
            return

        if self.game_to_edit:
            self.game_to_edit.name = name
            self.game_to_edit.exe_path = exe_path
            self.game_to_edit.process_name = proc_name or os.path.basename(exe_path)
            self.game_to_edit.launch_args = args
            if self.extracted_icon_path:
                self.game_to_edit.icon_path = self.extracted_icon_path
            self.db_manager.save()
            game_entry = self.game_to_edit
        else:
            game_entry = self.db_manager.add_game(
                name=name,
                exe_path=exe_path,
                process_name=proc_name or (os.path.basename(exe_path) if exe_path else name),
                icon_path=self.extracted_icon_path,
                launch_args=args
            )

        self.game_saved.emit(game_entry)
        self.accept()
