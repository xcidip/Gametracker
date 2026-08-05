import os
import sys
import time
import logging
import psutil
from typing import List, Dict, Tuple, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from src.database import DatabaseManager, GameEntry
from src.core.icon_extractor import extract_icon_from_exe

logger = logging.getLogger("Tracker")

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32


def get_active_window_pid_and_title() -> Tuple[int, str]:
    """Returns PID and window title of current foreground window on Windows."""
    if sys.platform != "win32":
        return 0, ""

    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return 0, ""

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        length = user32.GetWindowTextLengthW(hwnd)
        title_buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title_buf, length + 1)

        return pid.value, title_buf.value
    except Exception as e:
        logger.debug(f"Error fetching active window info: {e}")
        return 0, ""


def scan_running_applications() -> List[Dict[str, str]]:
    """
    Scans running processes and open windows to return a list of active applications.
    Returns list of dicts with keys: name, title, exe_path, process_name, pid, icon_path.
    """
    detected_apps = []
    seen_paths = set()

    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            pinfo = proc.info
            pid = pinfo['pid']
            p_name = pinfo['name']
            exe_path = pinfo['exe']

            if not exe_path or not os.path.exists(exe_path):
                continue

            # Filter system background processes
            exe_lower = exe_path.lower()
            if any(sys_dir in exe_lower for sys_dir in ["c:\\windows\\system32", "c:\\windows\\syswow64"]):
                continue

            if exe_lower in seen_paths:
                continue

            seen_paths.add(exe_lower)

            # Get display title (clean filename or process name)
            app_name = os.path.splitext(os.path.basename(exe_path))[0].replace("_", " ").title()
            
            # Extract icon for display in list
            safe_id = f"proc_{pid}_{p_name}"
            icon_path = extract_icon_from_exe(exe_path, safe_id, size=48)

            detected_apps.append({
                "pid": pid,
                "name": app_name,
                "process_name": p_name,
                "exe_path": exe_path,
                "icon_path": icon_path
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort alphabetically by app name
    detected_apps.sort(key=lambda x: x["name"].lower())
    return detected_apps


class TimeTrackerThread(QThread):
    """
    Background worker thread monitoring running processes and tracking game playtime.
    """
    playtime_updated = pyqtSignal(str, float, float)  # game_id, total_seconds, session_seconds
    game_started = pyqtSignal(str, str)              # game_id, game_name
    game_stopped = pyqtSignal(str, str, float)       # game_id, game_name, total_session_seconds
    running_status_changed = pyqtSignal(dict)       # dict of {game_id: is_running}

    def __init__(self, db_manager: DatabaseManager, poll_interval: float = 1.0):
        super().__init__()
        self.db_manager = db_manager
        self.poll_interval = poll_interval
        self._running = True
        self.active_sessions: Dict[str, float] = {}  # game_id -> session_start_time
        self.session_elapsed: Dict[str, float] = {}   # game_id -> accumulated session seconds
        self.last_running_state: Dict[str, bool] = {}

    def stop(self):
        self._running = False
        self.wait()

    def run(self):
        logger.info("Playtime Tracking Engine started.")

        last_save_time = time.time()

        while self._running:
            start_loop = time.time()

            try:
                # Get set of running process names and exe paths
                running_processes: Dict[str, str] = {}  # proc_name.lower() -> exe_path.lower()
                for proc in psutil.process_iter(['name', 'exe']):
                    try:
                        p_name = proc.info['name']
                        if p_name:
                            p_lower = p_name.lower()
                            p_exe = (proc.info['exe'] or "").lower()
                            running_processes[p_lower] = p_exe
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                current_running_status = {}

                # Check all games in library against running processes
                games = self.db_manager.get_all_games()
                for game in games:
                    # Skip tracking playtime for games that are downloading or pending installer setup
                    if game.is_downloading or game.needs_installation:
                        continue

                    target_proc = game.process_name.lower()
                    target_exe = game.exe_path.lower() if game.exe_path else ""

                    is_active = False
                    if target_proc in running_processes:
                        is_active = True
                    elif target_exe and target_exe in running_processes.values():
                        is_active = True

                    current_running_status[game.id] = is_active
                    game.is_running = is_active

                    # Handle game state changes
                    was_running = self.last_running_state.get(game.id, False)

                    if is_active and not was_running:
                        # Game Started
                        self.active_sessions[game.id] = time.time()
                        self.session_elapsed[game.id] = 0.0
                        logger.info(f"Detected game start: {game.name}")
                        self.game_started.emit(game.id, game.name)

                    elif is_active and was_running:
                        # Game Ongoing - accumulate time tick
                        tick = self.poll_interval
                        self.session_elapsed[game.id] += tick
                        self.db_manager.update_playtime(game.id, tick)
                        
                        total_time = game.playtime
                        session_time = self.session_elapsed[game.id]
                        self.playtime_updated.emit(game.id, total_time, session_time)

                    elif not is_active and was_running:
                        # Game Stopped
                        sess_time = self.session_elapsed.get(game.id, 0.0)
                        logger.info(f"Detected game stop: {game.name} (Session: {sess_time:.1f}s)")
                        self.game_stopped.emit(game.id, game.name, sess_time)
                        
                        if game.id in self.active_sessions:
                            del self.active_sessions[game.id]
                        if game.id in self.session_elapsed:
                            del self.session_elapsed[game.id]

                    self.last_running_state[game.id] = is_active

                # Periodically auto-save database
                if time.time() - last_save_time >= 15.0:
                    self.db_manager.save()
                    last_save_time = time.time()

                self.running_status_changed.emit(current_running_status)

            except Exception as e:
                logger.error(f"Error in tracker thread loop: {e}", exc_info=True)

            # Sleep remaining time of poll_interval
            elapsed_loop = time.time() - start_loop
            sleep_time = max(0.1, self.poll_interval - elapsed_loop)
            time.sleep(sleep_time)

        # Final save on exit
        self.db_manager.save()
