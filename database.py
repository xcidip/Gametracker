import json
import os
import time
import uuid
import logging
from typing import Dict, List, Optional
from pathlib import Path
from config import DATA_FILE, format_playtime
from icon_extractor import extract_icon_from_exe

logger = logging.getLogger("Database")

class GameEntry:
    def __init__(
        self,
        name: str,
        exe_path: str,
        process_name: Optional[str] = None,
        icon_path: Optional[str] = None,
        game_id: Optional[str] = None,
        playtime: float = 0.0,
        last_played: Optional[str] = None,
        is_favorite: bool = False,
        launch_args: str = "",
    ):
        self.id = game_id or str(uuid.uuid4())
        self.name = name
        self.exe_path = exe_path
        self.process_name = (process_name or os.path.basename(exe_path)).lower()
        self.icon_path = icon_path or extract_icon_from_exe(exe_path, self.id)
        self.playtime = float(playtime)
        self.last_played = last_played or "Never"
        self.is_favorite = is_favorite
        self.launch_args = launch_args
        self.is_running = False

    def to_dict(self) -> dict:
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
        )

    def formatted_playtime(self, verbose: bool = False) -> str:
        return format_playtime(self.playtime, verbose)


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
            logger.info(f"Loaded {len(self.games)} games from library database file: {path}")
        except Exception as e:
            logger.error(f"Error loading database file '{path}': {e}")

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
        self.save()

    def add_game(
        self,
        name: str,
        exe_path: str,
        process_name: Optional[str] = None,
        icon_path: Optional[str] = None,
        launch_args: str = "",
    ) -> GameEntry:
        """Adds a new game entry or updates existing one if exe matches."""
        for existing in self.games.values():
            if existing.exe_path.lower() == exe_path.lower() and exe_path != "":
                existing.name = name
                if process_name:
                    existing.process_name = process_name.lower()
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

    def update_playtime(self, game_id: str, elapsed_seconds: float):
        """Adds elapsed seconds to game playtime and updates last played timestamp."""
        game = self.games.get(game_id)
        if game:
            game.playtime += elapsed_seconds
            game.last_played = time.strftime("%Y-%m-%d %H:%M:%S")

    def get_all_games(self) -> List[GameEntry]:
        """Returns list of all games in library."""
        return list(self.games.values())

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
