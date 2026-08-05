# 🎮 GameTracker - App & Game Playtime Tracker

A modern Python desktop application that tracks playtime for games and applications in real time, extracts native high-resolution executable icons, provides 1-click running app detection, downloads games via built-in CLI Torrent engine, runs elevated setup installers, and runs silently in the Windows system tray.

---

## ✨ Features

- **📦 100% Single-File Executable**: Compiles into a single standalone `GameTracker.exe`.
- **📥 Background Torrent & Magnet Downloader**: Built-in Torrent CLI engine (`aria2c`) that downloads games from magnet links or `.torrent` files in the background, displaying live progress bars, speed, and ETA inside your game library cards.
- **🚀 Elevated Installer & Exe Assignment**: Launches downloaded setup installers with Administrator privileges (`runas`), monitors installer completion, prompts to select the installed game `.exe`, and offers to delete the temporary torrent download folder to free up disk space.
- **⏱️ Playtime Tracking (Finished Games Only)**: Monitors active processes in real time down to the second. Automatically excludes setup installers and active downloads from playtime tracking.
- **⚡ Active App Detector**: Scans running Windows processes and open windows, allowing you to add any application to your library with 1 click.
- **🎨 Native Executable Icon Extraction**: Pulls high-resolution icons directly from `.exe` files using 64-bit Win32 C APIs (`PrivateExtractIconsW` & `ExtractIconExW`) and converts them into crisp PNG images.
- **🔔 Silent System Tray Mode**: Closing the window minimizes the app to the Windows System Tray, allowing silent background time tracking without clogging your taskbar.
- **💻 Run at Windows Startup**: Built-in toggle to launch GameTracker automatically when Windows boots up (starts minimized in the system tray).
- **💾 JSON Data Export & Import**: Automatically saves to `%APPDATA%\GameTracker\library.json` with UI options to export or import database backups anytime.

---

## 🛠️ Installation & Setup

### Prerequisites
- Windows 10 / 11
- Python 3.10+

### 1. Install Dependencies
```bash
pip install PyQt6 psutil pillow pywin32
```

### 2. Run the Application
```bash
python main.py
```

---

## 📦 Building Single Standalone Executable (.exe)

You can build a single standalone `GameTracker.exe` file that runs cleanly without requiring Python or any external `_internal` folder:

### Option A: Double-Click Batch File
Double-click `build.bat` in Windows Explorer.

### Option B: Run Python Build Script
```bash
python build_exe.py
```

The single standalone executable will be created at:
`dist\GameTracker.exe`

---

## 📁 Project Structure

```
Gametracker/
├── main.py                # Application entry point
├── config.py              # Configuration paths & UI color palette
├── database.py            # Persistence layer (JSON library storage & import/export)
├── tracker.py             # Background process monitoring thread (playtime tracker)
├── icon_extractor.py      # Win32 C API icon extraction & fallback generator
├── torrent_manager.py     # Background CLI torrent engine & installer monitor
├── startup_manager.py     # Windows Registry startup key integration
├── build_exe.py           # Single-file PyInstaller packaging script (--onefile)
├── build.bat              # 1-Click batch build launcher
├── ui/
│   ├── main_window.py     # Main application window & system tray logic
│   ├── game_card.py       # Library grid card component with torrent progress bars
│   ├── detector_dialog.py # Active app scanner dialog
│   ├── torrent_dialog.py  # Magnet link & .torrent file downloader modal
│   ├── add_game_dialog.py # Custom .exe file picker dialog
│   ├── stats_view.py      # Playtime analytics & leaderboard view
│   └── styles.py          # Dark theme QSS stylesheet
├── .gitignore
└── README.md
```

---

## 📄 License
MIT License
