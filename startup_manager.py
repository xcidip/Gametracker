import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger("StartupManager")

if sys.platform == "win32":
    import winreg

    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_KEY_NAME = "GameTracker"

    def is_startup_enabled() -> bool:
        """Checks if GameTracker is set to launch on Windows startup."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, APP_KEY_NAME)
            winreg.CloseKey(key)
            return bool(value)
        except (FileNotFoundError, OSError):
            return False
        except Exception as e:
            logger.error(f"Error checking startup registry key: {e}")
            return False

    def set_startup_enabled(enabled: bool, minimized: bool = True) -> bool:
        """Adds or removes Windows Registry Run key for GameTracker."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_ALL_ACCESS)
            if enabled:
                # Path to compiled exe or python main.py
                if getattr(sys, 'frozen', False):
                    cmd = f'"{sys.executable}"'
                else:
                    main_py = Path(__file__).parent / "main.py"
                    cmd = f'"{sys.executable}" "{main_py.resolve()}"'

                if minimized:
                    cmd += " --minimized"

                winreg.SetValueEx(key, APP_KEY_NAME, 0, winreg.REG_SZ, cmd)
                logger.info(f"Enabled Windows Startup Registry Key: {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, APP_KEY_NAME)
                    logger.info("Removed Windows Startup Registry Key.")
                except FileNotFoundError:
                    pass

            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"Failed to update Windows startup registry: {e}")
            return False
else:
    def is_startup_enabled() -> bool:
        return False

    def set_startup_enabled(enabled: bool, minimized: bool = True) -> bool:
        return False
