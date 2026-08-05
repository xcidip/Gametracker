import os
import sys
import re
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger("PlatformImporter")

# Winreg standard library import for Windows
try:
    import winreg
except ImportError:
    winreg = None

# Official Launcher Download / Info URLs
LAUNCHER_DOWNLOADS = {
    "Steam": {
        "name": "Steam",
        "url": "https://cdn.cloudflare.steamstatic.com/client/installer/SteamSetup.exe",
        "website": "https://store.steampowered.com/about/",
        "icon": "🎮",
        "color": "#171A21",
        "badge_color": "#66C0F4",
        "description": "The ultimate destination for playing, discussing, and creating games."
    },
    "Epic Games": {
        "name": "Epic Games Launcher",
        "url": "https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/installer/download/EpicGamesLauncherInstaller.msi",
        "website": "https://store.epicgames.com/download",
        "icon": "⚡",
        "color": "#121212",
        "badge_color": "#0078F2",
        "description": "Discover and play thousands of free and premium PC games."
    },
    "GOG": {
        "name": "GOG Galaxy",
        "url": "https://cdn.gog.com/open/galaxy/client/2.0.73.27/setup_galaxy_2.0.73.27.exe",
        "website": "https://www.gog.com/galaxy",
        "icon": "🌌",
        "color": "#2B0B3F",
        "badge_color": "#A020F0",
        "description": "All your games and friends in one place. DRM-free gaming experience."
    }
}


def is_steam_installed() -> bool:
    """Checks if Steam is installed on the local system."""
    return get_steam_path() is not None


def get_steam_path() -> Optional[str]:
    """Retrieves Steam installation root path from Registry or standard locations."""
    if winreg:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            winreg.CloseKey(key)
            if path and os.path.exists(path):
                return path
        except Exception:
            pass

    # Common fallbacks
    default_paths = [
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files\Steam",
        r"D:\Steam",
        r"E:\Steam"
    ]
    for p in default_paths:
        if os.path.exists(p):
            return p
    return None


def is_epic_installed() -> bool:
    """Checks if Epic Games Launcher is installed."""
    program_data = os.environ.get("ALLUSERSPROFILE", r"C:\ProgramData")
    epic_manifests_dir = os.path.join(program_data, "Epic", "EpicGamesLauncher", "Data", "Manifests")
    if os.path.exists(epic_manifests_dir):
        return True
    
    if winreg:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Epic Games\EpicGamesLauncher")
            winreg.CloseKey(key)
            return True
        except Exception:
            pass
    return False


def is_gog_installed() -> bool:
    """Checks if GOG Galaxy is installed."""
    if winreg:
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for key_path in (
                r"SOFTWARE\WOW6432Node\GOG.com\Galaxy",
                r"SOFTWARE\GOG.com\Galaxy",
                r"SOFTWARE\WOW6432Node\GOG.com\Games",
                r"SOFTWARE\GOG.com\Games"
            ):
                try:
                    k = winreg.OpenKey(root, key_path)
                    winreg.CloseKey(k)
                    return True
                except Exception:
                    pass
    return False


def scan_steam_games() -> List[Dict]:
    """
    Scans Steam library folders and appmanifest files to discover installed Steam games.
    """
    games = []
    steam_path = get_steam_path()
    if not steam_path:
        return games

    library_folders = [os.path.join(steam_path, "steamapps")]
    vdf_file = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")

    # Discover secondary library paths from libraryfolders.vdf
    if os.path.exists(vdf_file):
        try:
            with open(vdf_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                matches = re.findall(r'"path"\s+"([^"]+)"', content)
                for m in matches:
                    clean_p = m.replace("\\\\", "\\")
                    s_apps = os.path.join(clean_p, "steamapps")
                    if os.path.exists(s_apps) and s_apps not in library_folders:
                        library_folders.append(s_apps)
        except Exception as e:
            logger.error(f"Error parsing Steam libraryfolders.vdf: {e}")

    for s_apps in library_folders:
        if not os.path.exists(s_apps):
            continue

        for item in os.listdir(s_apps):
            if item.startswith("appmanifest_") and item.endswith(".acf"):
                acf_path = os.path.join(s_apps, item)
                try:
                    with open(acf_path, "r", encoding="utf-8", errors="ignore") as f:
                        data = f.read()

                    appid_m = re.search(r'"appid"\s+"([^"]+)"', data)
                    name_m = re.search(r'"name"\s+"([^"]+)"', data)
                    installdir_m = re.search(r'"installdir"\s+"([^"]+)"', data)

                    if not name_m or not installdir_m:
                        continue

                    name = name_m.group(1).strip()
                    appid = appid_m.group(1).strip() if appid_m else ""
                    installdir = installdir_m.group(1).strip()

                    # Filter Steam runtime tools and common redistributables
                    if any(skip in name.lower() for skip in [
                        "steamworks common redistributables", "steamvr", "proton", "steam linux runtime"
                    ]):
                        continue

                    game_dir = os.path.join(s_apps, "common", installdir)
                    exe_path = _find_best_executable(game_dir, name)

                    if exe_path:
                        games.append({
                            "name": name,
                            "exe_path": exe_path,
                            "process_name": os.path.basename(exe_path).lower(),
                            "platform": "Steam",
                            "app_id": appid,
                            "install_dir": game_dir,
                            "icon": "🎮"
                        })
                except Exception as e:
                    logger.error(f"Error parsing Steam manifest {acf_path}: {e}")

    return games


def scan_epic_games() -> List[Dict]:
    """
    Scans Epic Games Launcher JSON manifests to discover installed games.
    """
    games = []
    program_data = os.environ.get("ALLUSERSPROFILE", r"C:\ProgramData")
    manifests_dir = os.path.join(program_data, "Epic", "EpicGamesLauncher", "Data", "Manifests")

    if not os.path.exists(manifests_dir):
        return games

    for fname in os.listdir(manifests_dir):
        if fname.endswith(".item"):
            item_path = os.path.join(manifests_dir, fname)
            try:
                with open(item_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)

                display_name = data.get("DisplayName")
                install_loc = data.get("InstallLocation")
                launch_exe = data.get("LaunchExecutable")

                if not display_name or not install_loc or not launch_exe:
                    continue

                full_exe = os.path.join(install_loc, launch_exe)
                if os.path.exists(full_exe):
                    games.append({
                        "name": display_name,
                        "exe_path": full_exe,
                        "process_name": os.path.basename(full_exe).lower(),
                        "platform": "Epic Games",
                        "app_id": data.get("AppName", ""),
                        "install_dir": install_loc,
                        "icon": "⚡"
                    })
            except Exception as e:
                logger.error(f"Error parsing Epic manifest {item_path}: {e}")

    return games


def scan_gog_games() -> List[Dict]:
    """
    Scans Windows Registry for installed GOG games.
    """
    games = []
    if not winreg:
        return games

    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\GOG.com\Games"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GOG.com\Games"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\GOG.com\Games")
    ]

    found_ids = set()

    for root_key, path in registry_paths:
        try:
            games_key = winreg.OpenKey(root_key, path)
            num_subkeys = winreg.QueryInfoKey(games_key)[0]
            for i in range(num_subkeys):
                subkey_name = winreg.EnumKey(games_key, i)
                if subkey_name in found_ids:
                    continue

                try:
                    game_key = winreg.OpenKey(games_key, subkey_name)
                    game_name = _query_reg_value(game_key, ["gameName", "title"])
                    working_dir = _query_reg_value(game_key, ["path", "workingDir"])
                    exe_name = _query_reg_value(game_key, ["exe", "executable"])

                    winreg.CloseKey(game_key)

                    if game_name and working_dir:
                        found_ids.add(subkey_name)
                        exe_path = ""
                        if exe_name:
                            exe_path = exe_name if os.path.isabs(exe_name) else os.path.join(working_dir, exe_name)

                        if not exe_path or not os.path.exists(exe_path):
                            exe_path = _find_best_executable(working_dir, game_name)

                        if exe_path and os.path.exists(exe_path):
                            games.append({
                                "name": game_name,
                                "exe_path": exe_path,
                                "process_name": os.path.basename(exe_path).lower(),
                                "platform": "GOG",
                                "app_id": subkey_name,
                                "install_dir": working_dir,
                                "icon": "🌌"
                            })
                except Exception:
                    pass
            winreg.CloseKey(games_key)
        except Exception:
            pass

    return games


def scan_all_platform_games() -> List[Dict]:
    """
    Scans and aggregates games from Steam, Epic Games, and GOG.
    """
    all_games = []
    all_games.extend(scan_steam_games())
    all_games.extend(scan_epic_games())
    all_games.extend(scan_gog_games())
    return all_games


def _query_reg_value(key, value_names: List[str]) -> Optional[str]:
    """Helper to query first available registry key value."""
    for v_name in value_names:
        try:
            val, _ = winreg.QueryValueEx(key, v_name)
            if val:
                return str(val)
        except Exception:
            pass
    return None


def _find_best_executable(directory: str, game_name: str) -> Optional[str]:
    """
    Scans directory to find the main game executable file, ignoring crash reporters and uninstallers.
    """
    if not os.path.exists(directory):
        return None

    exes = []
    ignored_keywords = [
        "unins", "setup", "crash", "bugreport", "redist", "unitycrash", "easyanticheat",
        "dxsetup", "vcredist", "dotnet", "launcher_admin", "updater"
    ]

    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(".exe"):
                f_lower = f.lower()
                if any(kw in f_lower for kw in ignored_keywords):
                    continue
                full_path = os.path.join(root, f)
                try:
                    size = os.path.getsize(full_path)
                    exes.append((full_path, f, size))
                except Exception:
                    pass

    if not exes:
        return None

    # Score exes: preference to exe matching game name or largest file size
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', game_name.lower())
    for path, fname, size in exes:
        clean_fname = re.sub(r'[^a-zA-Z0-9]', '', fname.lower().replace('.exe', ''))
        if clean_fname and (clean_fname in clean_name or clean_name in clean_fname):
            return path

    # Fallback to largest executable file
    exes.sort(key=lambda x: x[2], reverse=True)
    return exes[0][0]
