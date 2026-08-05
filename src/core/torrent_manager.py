import os
import sys
import io
import re
import time
import zipfile
import urllib.request
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, Callable

from PyQt6.QtCore import QThread, pyqtSignal, QObject

from config import APP_DIR
from database import DatabaseManager, GameEntry

logger = logging.getLogger("TorrentManager")

BIN_DIR = APP_DIR / "bin"
BIN_DIR.mkdir(parents=True, exist_ok=True)
ARIA2_EXE = BIN_DIR / "aria2c.exe"

ARIA2_ZIP_URL = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"


def ensure_aria2_installed(status_callback: Optional[Callable[[str], None]] = None) -> str:
    """
    Ensures portable aria2c.exe exists in BIN_DIR or system PATH.
    Downloads official 64-bit aria2 binary if not present.
    """
    if ARIA2_EXE.exists():
        return str(ARIA2_EXE)

    try:
        res = subprocess.run(["aria2c", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return "aria2c"
    except Exception:
        pass

    if status_callback:
        status_callback("Downloading Torrent Engine (aria2c)...")

    logger.info(f"Downloading portable aria2 engine from {ARIA2_ZIP_URL}...")
    try:
        req = urllib.request.Request(
            ARIA2_ZIP_URL,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            zip_bytes = response.read()

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for filename in z.namelist():
                if filename.endswith("aria2c.exe"):
                    with z.open(filename) as source, open(ARIA2_EXE, "wb") as target:
                        target.write(source.read())
                    logger.info(f"Successfully extracted aria2c.exe to {ARIA2_EXE}")
                    return str(ARIA2_EXE)
    except Exception as e:
        logger.error(f"Failed to download portable aria2c: {e}")

    return str(ARIA2_EXE)


class TorrentDownloadWorker(QThread):
    """
    Background worker thread running aria2c CLI and emitting live progress updates.
    """
    progress_updated = pyqtSignal(str, float, str, str, str)  # game_id, progress_pct, speed_str, eta_str, status_str
    download_completed = pyqtSignal(str, str, str)            # game_id, game_name, download_dir
    download_failed = pyqtSignal(str, str, str)               # game_id, game_name, error_msg

    def __init__(
        self,
        game_id: str,
        game_name: str,
        torrent_source: str,      # magnet link or .torrent file path
        download_dir: str,
        aria2_path: str = str(ARIA2_EXE)
    ):
        super().__init__()
        self.game_id = game_id
        self.game_name = game_name
        self.torrent_source = torrent_source
        self.download_dir = download_dir
        self.aria2_path = aria2_path
        self._is_cancelled = False
        self.process = None

    def cancel(self):
        self._is_cancelled = True
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass

    def run(self):
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir, exist_ok=True)

        cmd = [
            self.aria2_path,
            f"--dir={self.download_dir}",
            "--enable-dht=true",
            "--summary-interval=1",
            "--seed-time=0",
            "--bt-metadata-only=false",
            "--follow-torrent=mem",
            "--file-allocation=none",
            self.torrent_source
        ]

        logger.info(f"Starting torrent download CLI command for {self.game_name}: {' '.join(cmd)}")
        self.progress_updated.emit(self.game_id, 0.0, "Connecting...", "Calculating", "Downloading Metadata")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            progress_regex = re.compile(r"\((\d+)%\).*?DL:(.*?)(?:\s+ETA:(.*?))?\]")

            for line in self.process.stdout:
                if self._is_cancelled:
                    break

                line_str = line.strip()

                if "%" in line_str:
                    match = progress_regex.search(line_str)
                    if match:
                        pct = float(match.group(1))
                        speed = match.group(2).strip()
                        eta = match.group(3).strip() if match.group(3) else "Calculating"
                        self.progress_updated.emit(self.game_id, pct, f"{speed}/s", eta, "Downloading")
                    else:
                        pct_match = re.search(r"\((\d+)%\)", line_str)
                        if pct_match:
                            pct = float(pct_match.group(1))
                            self.progress_updated.emit(self.game_id, pct, "Downloading...", "--", "Downloading")

            self.process.wait()

            if self._is_cancelled:
                logger.info(f"Torrent download for {self.game_name} was cancelled.")
                self.progress_updated.emit(self.game_id, 0.0, "0 B/s", "--", "Cancelled")
            elif self.process.returncode == 0:
                logger.info(f"Torrent download completed for {self.game_name}!")
                self.progress_updated.emit(self.game_id, 100.0, "0 B/s", "Done", "Completed")
                self.download_completed.emit(self.game_id, self.game_name, self.download_dir)
            else:
                logger.error(f"Torrent download failed for {self.game_name} with return code {self.process.returncode}")
                self.download_failed.emit(self.game_id, self.game_name, f"Process exited with code {self.process.returncode}")

        except Exception as e:
            logger.error(f"Error executing aria2 torrent downloader: {e}")
            self.download_failed.emit(self.game_id, self.game_name, str(e))


def launch_elevated_installer(installer_path: str) -> bool:
    """
    Launches an installer executable with elevated Administrator privileges (UAC prompt).
    """
    if not os.path.exists(installer_path):
        return False

    if sys.platform == "win32":
        import ctypes
        try:
            installer_dir = os.path.dirname(installer_path)
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",        # Elevated Administrator verb
                str(installer_path),
                None,
                str(installer_dir),
                1               # SW_SHOWNORMAL
            )
            return ret > 32
        except Exception as e:
            logger.error(f"Error launching elevated installer with runas: {e}")
            return False
    else:
        try:
            subprocess.Popen([installer_path])
            return True
        except Exception as e:
            logger.error(f"Error launching installer: {e}")
            return False


class InstallerMonitorWorker(QThread):
    """
    Monitors background installer processes until ALL setup/installer instances exit.
    """
    installer_finished = pyqtSignal(str, str)  # game_id, game_name

    def __init__(self, game_id: str, game_name: str, installer_path: str):
        super().__init__()
        self.game_id = game_id
        self.game_name = game_name
        self.installer_path = os.path.abspath(installer_path)
        self.installer_dir = os.path.abspath(os.path.dirname(installer_path))

    def run(self):
        logger.info(f"Installer monitor worker started for {self.game_name} (Installer Dir: {self.installer_dir})")

        # Step 1: Wait up to 30 seconds for any installer process to register
        start_wait = time.time()
        installer_started = False

        while time.time() - start_wait < 30:
            if self._is_any_installer_running():
                installer_started = True
                logger.info(f"Active installer process detected for {self.game_name}!")
                break
            time.sleep(1.5)

        if not installer_started:
            logger.warning(f"No active installer process detected within 30s for {self.game_name}.")
            time.sleep(3)
            self.installer_finished.emit(self.game_id, self.game_name)
            return

        # Step 2: Monitor until ALL installer processes in folder/temp exit
        time.sleep(3.0)  # Initial grace period

        while True:
            if not self._is_any_installer_running():
                # Double check after 2.5 seconds to avoid premature exit during step transitions
                time.sleep(2.5)
                if not self._is_any_installer_running():
                    break
            time.sleep(2.0)

        logger.info(f"All installer processes for {self.game_name} have finished/exited.")
        self.installer_finished.emit(self.game_id, self.game_name)

    def _is_any_installer_running(self) -> bool:
        """Checks if any setup/installer process matching the directory or installer name is running."""
        import psutil
        installer_basename = os.path.basename(self.installer_path).lower()
        dir_lower = self.installer_dir.lower()

        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                p_name = (proc.info['name'] or "").lower()
                p_exe = (proc.info['exe'] or "").lower()

                if not p_name and not p_exe:
                    continue

                # Check if executable path is inside installer directory
                if p_exe and dir_lower in p_exe:
                    return True

                # Check if process name matches installer file
                if p_name == installer_basename or p_name in ["setup.exe", "installer.exe", "install.exe"]:
                    return True

                # Check for common installer temp processes (Inno Setup, InstallShield, NSIS, FitGirl)
                if ("is-" in p_name or "setup" in p_name or "_iu" in p_name) and "temp" in p_exe:
                    return True

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return False
