import json
import os
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from src.config import DATA_FILE, format_playtime
from src.core.icon_extractor import extract_icon_from_exe

logger = logging.getLogger("Database")

def get_current_week_start() -> str:
    """Returns ISO date string (YYYY-MM-DD) of Monday of current week (Monday-Sunday)."""
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat()

class GameEntry:
    def __init__(
        self,
        name: str,
        exe_path: str = "",
        process_name: Optional[str] = None,
        icon_path: Optional[str] = None,
        game_id: Optional[str] = None,
        playtime: float = 0.0,
        last_played: Optional[str] = None,
        is_favorite: bool = False,
        launch_args: str = "",
        is_downloading: bool = False,
        download_progress: float = 0.0,
        download_speed: str = "0 B/s",
        download_eta: str = "--",
        download_status: str = "Idle",
        download_dir: str = "",
        torrent_source: str = "",
        needs_installation: bool = False,
        installer_path: str = "",
        weekly_playtime: float = 0.0,
        weekly_start_date: str = "",
        play_time_limit: float = 0.0,
        play_sessions: Optional[List[dict]] = None,
    ):
        self.id = game_id or str(uuid.uuid4())
        self.name = name
        self.exe_path = exe_path
        self.process_name = (process_name or (os.path.basename(exe_path) if exe_path else name)).lower()
        self.icon_path = icon_path or (extract_icon_from_exe(exe_path, self.id) if exe_path else None)
        self.playtime = float(playtime)
        self.last_played = last_played or "Never"
        self.is_favorite = is_favorite
        self.launch_args = launch_args
        self.is_running = False

        # Weekly limit & tracking properties
        self.weekly_playtime = float(weekly_playtime)
        self.weekly_start_date = weekly_start_date or get_current_week_start()
        self.play_time_limit = float(play_time_limit)

        # Download properties
        self.is_downloading = is_downloading
        self.download_progress = download_progress
        self.download_speed = download_speed
        self.download_eta = download_eta
        self.download_status = download_status
        self.download_dir = download_dir
        self.torrent_source = torrent_source
        self.needs_installation = needs_installation
        self.installer_path = installer_path

        # Play session launch history
        self.play_sessions: List[dict] = play_sessions if play_sessions is not None else []

    def check_and_reset_weekly_playtime(self):
        """Resets weekly playtime if current week has rolled over (new week starting Monday)."""
        current_week = get_current_week_start()
        if self.weekly_start_date != current_week:
            self.weekly_playtime = 0.0
            self.weekly_start_date = current_week

    def is_limit_reached(self) -> bool:
        """Returns True if user has set a weekly playtime limit > 0 and reached/exceeded it."""
        if self.play_time_limit <= 0:
            return False
        self.check_and_reset_weekly_playtime()
        return (self.weekly_playtime / 3600.0) >= self.play_time_limit

    def add_play_session(self, start_time: str, end_time: str, duration: float):
        """Records a completed app launch session with start time, end time, and duration."""
        if duration <= 0:
            return
        self.play_sessions.append({
            "start_time": start_time,
            "end_time": end_time,
            "duration": round(float(duration), 2)
        })

    def get_current_week_daily_breakdown(self) -> Dict[str, float]:
        """
        Returns a dictionary mapping ISO date strings (YYYY-MM-DD) for each day of the current week
        (Monday to Sunday) to total playtime in seconds on that day.
        """
        self.check_and_reset_weekly_playtime()
        current_monday = datetime.strptime(get_current_week_start(), "%Y-%m-%d").date()
        daily_totals = {}
        for i in range(7):
            day_date = current_monday + timedelta(days=i)
            daily_totals[day_date.isoformat()] = 0.0

        for sess in self.play_sessions:
            st_raw = sess.get("start_time", "")
            duration = float(sess.get("duration", 0.0))
            if not st_raw or duration <= 0:
                continue
            try:
                if "T" in st_raw:
                    dt = datetime.fromisoformat(st_raw)
                else:
                    dt = datetime.strptime(st_raw, "%Y-%m-%d %H:%M:%S")
                sess_date_str = dt.date().isoformat()
                if sess_date_str in daily_totals:
                    daily_totals[sess_date_str] += duration
            except Exception:
                continue

        # If total calculated from sessions is 0 but weekly_playtime > 0, attribute weekly_playtime to today
        if sum(daily_totals.values()) == 0 and self.weekly_playtime > 0:
            today_str = datetime.now().date().isoformat()
            if today_str in daily_totals:
                daily_totals[today_str] = self.weekly_playtime

        return daily_totals

    def get_current_week_stats(self) -> Dict[str, Any]:
        """
        Calculates comprehensive current week statistics from recorded play sessions.
        """
        daily = self.get_current_week_daily_breakdown()
        current_monday = datetime.strptime(get_current_week_start(), "%Y-%m-%d").date()
        current_sunday = current_monday + timedelta(days=6)

        week_sessions = []
        for sess in self.play_sessions:
            st_raw = sess.get("start_time", "")
            duration = float(sess.get("duration", 0.0))
            if not st_raw:
                continue
            try:
                if "T" in st_raw:
                    dt = datetime.fromisoformat(st_raw)
                else:
                    dt = datetime.strptime(st_raw, "%Y-%m-%d %H:%M:%S")
                if current_monday <= dt.date() <= current_sunday:
                    week_sessions.append(sess)
            except Exception:
                continue

        total_weekly_secs = max(self.weekly_playtime, sum(daily.values()))
        session_count = len(week_sessions)
        avg_session = total_weekly_secs / session_count if session_count > 0 else 0.0

        peak_date_str = max(daily, key=daily.get) if daily else ""
        peak_secs = daily.get(peak_date_str, 0.0) if peak_date_str else 0.0
        if peak_date_str and peak_secs > 0:
            peak_dt = datetime.strptime(peak_date_str, "%Y-%m-%d")
            peak_day_name = peak_dt.strftime("%A")
        else:
            peak_day_name = "N/A"

        return {
            "total_playtime": total_weekly_secs,
            "session_count": session_count,
            "avg_session_duration": avg_session,
            "peak_day_name": peak_day_name,
            "peak_day_seconds": peak_secs,
            "daily_breakdown": daily,
            "sessions": week_sessions,
        }

    def to_dict(self) -> dict:
        self.check_and_reset_weekly_playtime()
        return {
            "id": self.id,
            "name": self.name,
            "exe_path": self.exe_path,
            "process_name": self.process_name,
            "icon_path": self.icon_path,
            "playtime": self.playtime,
            "last_played": self.last_played,
            "is_favorite": self.is_favorite,
            "launch_args": self.launch_args,
            "weekly_playtime": self.weekly_playtime,
            "weekly_start_date": self.weekly_start_date,
            "play_time_limit": self.play_time_limit,
            "is_downloading": self.is_downloading,
            "download_progress": self.download_progress,
            "download_speed": self.download_speed,
            "download_eta": self.download_eta,
            "download_status": self.download_status,
            "download_dir": self.download_dir,
            "torrent_source": self.torrent_source,
            "needs_installation": self.needs_installation,
            "installer_path": self.installer_path,
            "play_sessions": self.play_sessions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameEntry":
        return cls(
            name=data.get("name", "Unknown Game"),
            exe_path=data.get("exe_path", ""),
            process_name=data.get("process_name"),
            icon_path=data.get("icon_path"),
            game_id=data.get("id"),
            playtime=data.get("playtime", 0.0),
            last_played=data.get("last_played", "Never"),
            is_favorite=data.get("is_favorite", False),
            launch_args=data.get("launch_args", ""),
            weekly_playtime=data.get("weekly_playtime", 0.0),
            weekly_start_date=data.get("weekly_start_date", ""),
            play_time_limit=data.get("play_time_limit", 0.0),
            is_downloading=data.get("is_downloading", False),
            download_progress=data.get("download_progress", 0.0),
            download_speed=data.get("download_speed", "0 B/s"),
            download_eta=data.get("download_eta", "--"),
            download_status=data.get("download_status", "Idle"),
            download_dir=data.get("download_dir", ""),
            torrent_source=data.get("torrent_source", ""),
            needs_installation=data.get("needs_installation", False),
            installer_path=data.get("installer_path", ""),
            play_sessions=data.get("play_sessions", []),
        )

    def formatted_playtime(self, verbose: bool = False) -> str:
        return format_playtime(self.playtime, verbose)

    def formatted_weekly_playtime(self, verbose: bool = False) -> str:
        self.check_and_reset_weekly_playtime()
        return format_playtime(self.weekly_playtime, verbose)


def _normalize_path(p: str) -> str:
    if not p:
        return ""
    try:
        return os.path.normpath(p).replace("/", "\\").lower()
    except Exception:
        return p.lower()


class DatabaseManager:
    def __init__(self, data_file: Path = DATA_FILE):
        self.data_file = Path(data_file)
        self.games: Dict[str, GameEntry] = {}
        self.load()

    def load(self, target_path: Optional[Path] = None):
        """Loads database from specified JSON file or default data_file."""
        path = target_path or self.data_file
        if not path.exists():
            self.save(path)
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                games_list = data.get("games", [])
                self.games = {g["id"]: GameEntry.from_dict(g) for g in games_list}
            self.deduplicate()
            logger.info(f"Loaded {len(self.games)} games from library database file: {path}")
        except Exception as e:
            logger.error(f"Error loading database file '{path}': {e}")

    def deduplicate(self):
        """Merges duplicate game entries matching by normalized exe_path or lowercased name."""
        unique_games: Dict[str, GameEntry] = {}
        seen_keys: Dict[str, str] = {}  # key -> game_id

        for g in list(self.games.values()):
            norm_exe = _normalize_path(g.exe_path)
            norm_name = g.name.strip().lower()
            key = f"exe:{norm_exe}" if norm_exe else f"name:{norm_name}"

            if key in seen_keys:
                existing_id = seen_keys[key]
                existing = unique_games[existing_id]
                # Merge stats & properties into existing entry
                existing.playtime = max(existing.playtime, g.playtime)
                existing.is_favorite = existing.is_favorite or g.is_favorite
                if g.last_played != "Never" and (existing.last_played == "Never" or g.last_played > existing.last_played):
                    existing.last_played = g.last_played
                if not existing.exe_path and g.exe_path:
                    existing.exe_path = g.exe_path
                if not existing.icon_path and g.icon_path:
                    existing.icon_path = g.icon_path
                if not existing.launch_args and g.launch_args:
                    existing.launch_args = g.launch_args
                for sess in g.play_sessions:
                    if sess not in existing.play_sessions:
                        existing.play_sessions.append(sess)
            else:
                seen_keys[key] = g.id
                unique_games[g.id] = g

        if len(unique_games) != len(self.games):
            logger.info(f"Deduplicated library from {len(self.games)} games to {len(unique_games)} games.")
            self.games = unique_games
            self.save()

    def save(self, target_path: Optional[Path] = None):
        """Saves database atomically to JSON file."""
        path = target_path or self.data_file
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".json.tmp")

        try:
            data = {
                "version": 1.0,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "games": [game.to_dict() for game in self.games.values()]
            }
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            if tmp_path.exists():
                tmp_path.replace(path)
            logger.info(f"Saved library database to file: {path}")
        except Exception as e:
            logger.error(f"Error saving database file '{path}': {e}")
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    def export_to_file(self, export_file_path: str):
        """Exports the library database to a user-selected file path."""
        self.save(Path(export_file_path))

    def import_from_file(self, import_file_path: str):
        """Imports/Merges games from an external JSON library file."""
        path = Path(import_file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {import_file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            games_list = data.get("games", [])
            for g_dict in games_list:
                entry = GameEntry.from_dict(g_dict)
                # Merge or update
                if entry.id not in self.games:
                    self.games[entry.id] = entry
                else:
                    existing = self.games[entry.id]
                    existing.playtime = max(existing.playtime, entry.playtime)
                    if entry.last_played != "Never":
                        existing.last_played = entry.last_played
        self.deduplicate()

    def add_game(
        self,
        name: str,
        exe_path: str,
        process_name: Optional[str] = None,
        icon_path: Optional[str] = None,
        launch_args: str = "",
    ) -> GameEntry:
        """Adds a new game entry or updates existing one if exe or name matches."""
        norm_exe = _normalize_path(exe_path)
        norm_name = name.strip().lower()

        for existing in self.games.values():
            ext_norm_exe = _normalize_path(existing.exe_path)
            ext_norm_name = existing.name.strip().lower()

            if (norm_exe and ext_norm_exe and norm_exe == ext_norm_exe) or (norm_name and ext_norm_name and norm_name == ext_norm_name):
                existing.name = name
                if exe_path:
                    existing.exe_path = exe_path
                if process_name:
                    existing.process_name = process_name.lower()
                if icon_path:
                    existing.icon_path = icon_path
                if launch_args:
                    existing.launch_args = launch_args
                self.save()
                return existing

        game = GameEntry(
            name=name,
            exe_path=exe_path,
            process_name=process_name,
            icon_path=icon_path,
            launch_args=launch_args
        )
        self.games[game.id] = game
        self.save()
        return game

    def remove_game(self, game_id: str):
        """Removes a game entry from the database."""
        if game_id in self.games:
            del self.games[game_id]
            self.save()

    def toggle_favorite(self, game_id: str) -> bool:
        """Toggles the favorite status of a game entry."""
        game = self.games.get(game_id)
        if game:
            game.is_favorite = not game.is_favorite
            self.save()
            return game.is_favorite
        return False

    def update_playtime(self, game_id: str, elapsed_seconds: float):
        """Adds elapsed seconds to game playtime and weekly playtime, and updates last played timestamp."""
        game = self.games.get(game_id)
        if game:
            game.check_and_reset_weekly_playtime()
            game.playtime += elapsed_seconds
            game.weekly_playtime += elapsed_seconds
            game.last_played = time.strftime("%Y-%m-%d %H:%M:%S")

    def record_game_session(self, game_id: str, start_time: str, end_time: str, duration: float):
        """Records a launch session for a game and saves the database."""
        game = self.games.get(game_id)
        if game:
            game.add_play_session(start_time, end_time, duration)
            self.save()

    def set_play_time_limit(self, game_id: str, limit_hours: float):
        """Sets the weekly play limit in hours for a specific game and saves the database."""
        game = self.games.get(game_id)
        if game:
            game.play_time_limit = max(0.0, float(limit_hours))
            self.save()

    def get_all_games(self) -> List[GameEntry]:
        """Returns list of all games in library."""
        return list(self.games.values())

    def get_recent_games(self, limit: int = 5) -> List[GameEntry]:
        """Returns the top 'limit' games sorted by last_played timestamp descending."""
        games = list(self.games.values())

        def _recent_key(g):
            if not g.last_played or g.last_played == "Never":
                return (1, -g.playtime)
            try:
                parts = [int(p) for p in g.last_played.replace('-', ' ').replace(':', ' ').split()]
                return (0, tuple(-p for p in parts))
            except Exception:
                return (1, -g.playtime)

        games.sort(key=_recent_key)
        return games[:limit]

    def get_game_by_id(self, game_id: str) -> Optional[GameEntry]:
        return self.games.get(game_id)

    def find_game_by_process(self, process_name: str, exe_path: str = "") -> Optional[GameEntry]:
        """Finds game matching process name or executable path."""
        p_name = process_name.lower()
        e_path = exe_path.lower() if exe_path else ""

        for game in self.games.values():
            if game.process_name and game.process_name == p_name:
                return game
            if game.exe_path and e_path and game.exe_path.lower() == e_path:
                return game
        return None
