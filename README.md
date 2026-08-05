# GameTracker

GameTracker is a Windows desktop application for tracking playtime and usage across games and applications. It features native executable icon extraction, background torrent downloading via `aria2c`, automated setup installer handling, and silent system tray integration.

## Features

- **Real-Time Playtime Tracking**: Monitors active processes per second. Automatically filters out installer setup wizards and active downloads to measure actual play time.
- **Icon Extraction**: Extracts high-resolution icons directly from `.exe` binaries using Win32 C APIs (`PrivateExtractIconsW` and `ExtractIconExW`).
- **Torrent & Magnet Downloads**: Built-in background downloading powered by `aria2c`, showing real-time progress, speed, and ETA directly on library cards.
- **Installer Automation**: Launches downloaded setup files with Administrator privileges (`runas`), tracks completion, prompts for the installed executable path, and offers to clean up temporary installer files.
- **Active Application Scanner**: Scans open windows and running processes to allow adding apps to the library in one click.
- **System Tray Integration**: Minimizes silently to the Windows System Tray to maintain tracking in the background without taskbar clutter.
- **Windows Startup**: Built-in toggle to automatically launch minimized when Windows boots.
- **Data Backup & Import**: Stores library data in `%APPDATA%\GameTracker\library.json` with options to export or restore database backups.

## Requirements

- Windows 10 or Windows 11 (64-bit)
- Python 3.10+

## Quick Start

1. **Clone the repository and install dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```cmd
   python main.py
   ```

## Building Executables & Setup Installers

GameTracker includes automated build scripts to generate standalone executables and Windows installer wizards.

### Option 1: Standalone Executable (`dist/GameTracker/`)
Generates a fast-booting, directory-bundled executable using PyInstaller:
```cmd
python build_exe.py
```

### Option 2: Full Setup Installer (`dist_installer/GameTracker_Setup.exe`)
Compiles the application into a single setup installer wizard using Inno Setup:
```cmd
python build_installer.py
```
*(Alternatively, run `build.bat` on Windows)*

## Project Structure

```text
Gametracker/
├── main.py                # Application entry point & Qt initialization
├── config.py              # Application settings, paths, and color palette
├── database.py            # Persistence layer (JSON storage & backup/restore)
├── tracker.py             # Real-time process monitoring & active window tracker
├── icon_extractor.py      # Win32 C API icon extractor & fallback image generator
├── torrent_manager.py     # Background aria2c torrent manager & installer monitor
├── startup_manager.py     # Windows Registry startup integration
├── build_exe.py           # PyInstaller packaging script
├── build_installer.py     # Inno Setup installer build script
├── installer.iss          # Inno Setup script configuration
├── build.bat              # Batch build launcher
├── requirements.txt       # Python dependencies
└── ui/
    ├── main_window.py     # Main UI window and system tray handler
    ├── game_card.py       # Library card component with progress tracking
    ├── detector_dialog.py # Active process detector modal
    ├── torrent_dialog.py  # Magnet link & .torrent file download modal
    ├── add_game_dialog.py # Manual .exe selection dialog
    ├── stats_view.py      # Analytics & playtime statistics view
    └── styles.py          # Dark theme Qt stylesheet
```

## License

Distributed under the MIT License.
