import os
import logging
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QTabWidget, QWidget
)

logger = logging.getLogger("TorrentDialog")

class TorrentDownloadDialog(QDialog):
    """
    Dialog window for entering a magnet link or picking a .torrent file to download in the background.
    """
    torrent_started = pyqtSignal(dict)  # returns dict with game_name, torrent_source, download_dir

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Game via Torrent / Magnet Link")
        self.setMinimumWidth(550)

        # Default download path: Downloads / GameTrackerDownloads
        user_downloads = Path(os.path.expanduser("~/Downloads")) / "GameTrackerDownloads"
        self.default_dir = str(user_downloads.resolve())

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Title
        title_lbl = QLabel("📥 Add Torrent / Magnet Download")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #00CEC9;")
        layout.addWidget(title_lbl)

        subtitle_lbl = QLabel("Enter a magnet link or select a .torrent file. The game will automatically download in the background and show up in your library.")
        subtitle_lbl.setStyleSheet("font-size: 12px; color: #8E9BB0;")
        subtitle_lbl.setWordWrap(True)
        layout.addWidget(subtitle_lbl)

        # Tab Widget: Magnet Link vs Torrent File
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2B304A;
                border-radius: 8px;
                background: #181B28;
                padding: 10px;
            }
            QTabBar::tab {
                background: #1E2235;
                color: #8E9BB0;
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #6C5CE7;
                color: #FFFFFF;
            }
        """)

        # Tab 1: Magnet Link
        magnet_tab = QWidget()
        m_layout = QVBoxLayout(magnet_tab)
        m_layout.addWidget(QLabel("Magnet Link / URL:"))
        self.input_magnet = QLineEdit()
        self.input_magnet.setPlaceholderText("magnet:?xt=urn:btih:...")
        self.input_magnet.textChanged.connect(self.on_magnet_text_changed)
        m_layout.addWidget(self.input_magnet)

        self.btn_paste = QPushButton("📋 Paste Clipboard")
        self.btn_paste.setObjectName("SecondaryButton")
        self.btn_paste.clicked.connect(self.paste_clipboard)
        m_layout.addWidget(self.btn_paste)

        self.tabs.addTab(magnet_tab, "🧲 Magnet Link")

        # Tab 2: Torrent File
        torrent_file_tab = QWidget()
        tf_layout = QVBoxLayout(torrent_file_tab)
        tf_layout.addWidget(QLabel("Torrent File (.torrent):"))

        tf_file_layout = QHBoxLayout()
        self.input_torrent_path = QLineEdit()
        self.input_torrent_path.setPlaceholderText("C:\\Downloads\\mygame.torrent")
        tf_file_layout.addWidget(self.input_torrent_path)

        btn_browse_torrent = QPushButton("📁 Browse...")
        btn_browse_torrent.setObjectName("SecondaryButton")
        btn_browse_torrent.clicked.connect(self.browse_torrent_file)
        tf_file_layout.addWidget(btn_browse_torrent)

        tf_layout.addLayout(tf_file_layout)
        self.tabs.addTab(torrent_file_tab, "📄 .Torrent File")

        layout.addWidget(self.tabs)

        # Game Title Name
        layout.addWidget(QLabel("Game / App Title Name:"))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Cyberpunk 2077")
        layout.addWidget(self.input_name)

        # Download Destination Directory
        layout.addWidget(QLabel("Save Download To Folder:"))
        dir_layout = QHBoxLayout()
        self.input_dir = QLineEdit()
        self.input_dir.setText(self.default_dir)
        dir_layout.addWidget(self.input_dir)

        btn_browse_dir = QPushButton("📂 Browse Folder...")
        btn_browse_dir.setObjectName("SecondaryButton")
        btn_browse_dir.clicked.connect(self.browse_download_folder)
        dir_layout.addWidget(btn_browse_dir)

        layout.addLayout(dir_layout)

        # Bottom Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("SecondaryButton")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        self.btn_start = QPushButton("⏬ Start Download")
        self.btn_start.setObjectName("PrimaryButton")
        self.btn_start.clicked.connect(self.on_start_clicked)
        btn_layout.addWidget(self.btn_start)

        layout.addLayout(btn_layout)

    def paste_clipboard(self):
        from PyQt6.QtWidgets import QApplication
        clipboard_text = QApplication.clipboard().text().strip()
        if clipboard_text:
            self.input_magnet.setText(clipboard_text)

    def browse_torrent_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Torrent File",
            "",
            "Torrent Files (*.torrent);;All Files (*.*)"
        )
        if file_path:
            self.input_torrent_path.setText(file_path)
            if not self.input_name.text():
                base_name = Path(file_path).stem.replace(".", " ").replace("_", " ").title()
                self.input_name.setText(base_name)

    def browse_download_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.input_dir.text())
        if folder_path:
            self.input_dir.setText(folder_path)

    def on_magnet_text_changed(self, text: str):
        if text.startswith("magnet:?") and not self.input_name.text():
            # Try parsing dn= display name parameter from magnet URI
            import urllib.parse
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(text).query)
            if "dn" in parsed and parsed["dn"]:
                clean_dn = parsed["dn"][0].replace("+", " ").replace(".", " ").replace("_", " ").title()
                self.input_name.setText(clean_dn)

    def on_start_clicked(self):
        current_tab_idx = self.tabs.currentIndex()

        if current_tab_idx == 0:  # Magnet tab
            torrent_source = self.input_magnet.text().strip()
            if not torrent_source or not torrent_source.startswith("magnet:?"):
                QMessageBox.warning(self, "Invalid Magnet Link", "Please enter a valid magnet:? link.")
                return
        else:  # File tab
            torrent_source = self.input_torrent_path.text().strip()
            if not torrent_source or not os.path.exists(torrent_source):
                QMessageBox.warning(self, "File Not Found", "Please select a valid .torrent file.")
                return

        game_name = self.input_name.text().strip()
        if not game_name:
            QMessageBox.warning(self, "Missing Title", "Please enter a Game/App Title name.")
            return

        download_dir = self.input_dir.text().strip()
        if not download_dir:
            download_dir = self.default_dir

        self.torrent_started.emit({
            "name": game_name,
            "torrent_source": torrent_source,
            "download_dir": download_dir
        })
        self.accept()
