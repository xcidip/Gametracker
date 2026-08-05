# 🎮 GameTracker - App & Game Playtime Tracker

A modern Python desktop application that tracks playtime for games and applications in real time, extracts native high-resolution executable icons, provides 1-click running app detection, and runs silently in the Windows system tray.

---

## ✨ Features

- **⚡ Active App Detector**: Scans running Windows processes and open windows, allowing you to add any application to your library with 1 click.
- **🎨 Native Executable Icon Extraction**: Pulls high-resolution icons directly from `.exe` files using 64-bit Win32 C APIs (`PrivateExtractIconsW` & `ExtractIconExW`) and converts them into crisp PNG images.
- **⏱️ Real-Time Playtime Tracking**: Monitors active processes with a lightweight background thread and updates total playtime down to the second.
- **🚀 Game Launcher**: Launch games directly from the library grid with custom arguments and automatic working directory resolution.
- **🔔 Silent System Tray Mode**: Closing the window minimizes the app to the Windows System Tray, allowing silent background time tracking without clogging your taskbar.
- **💻 Run at Windows Startup**: Built-in toggle to launch GameTracker automatically when Windows boots up (starts minimized in the system tray).
- **💾 JSON Data Export & Import**: Automatically saves to `%APPDATA%\GameTracker\library.json` with UI options to export or import database backups anytime.
- **📊 Analytics Leaderboard**: View total library stats and rank games by playtime (`#1 Most Played`).

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

## 📦 Building Standalone Executable (.exe)

You can build a standalone `GameTracker.exe` that runs without requiring Python installed:

### Option A: Double-Click Batch File
Double-click `build.bat` in Windows Explorer.

### Option B: Run Python Build Script
```bash
python build_exe.py
```

The resulting executable will be created at:
`dist\GameTracker\GameTracker.exe`

---

## 📁 Project Structure

```
Gametracker/
├── main.py                # Application entry point
├── config.py              # Configuration paths & UI color palette
├── database.py            # Persistence layer (JSON library storage & import/export)
├── tracker.py             # Background process monitoring thread
├── icon_extractor.py      # Win32 C API icon extraction & fallback generator
├── startup_manager.py     # Windows Registry startup key integration
├── build_exe.py           # Automated PyInstaller packaging script
├── build.bat              # 1-Click batch build launcher
├── ui/
│   ├── main_window.py     # Main application window & system tray logic
│   ├── game_card.py       # Library grid card component
│   ├── detector_dialog.py # Active app scanner dialog
│   ├── add_game_dialog.py # Custom .exe file picker dialog
│   ├── stats_view.py      # Playtime analytics & leaderboard view
│   └── styles.py          # Dark theme QSS stylesheet
├── .gitignore
└── README.md
```

---

## 📄 License
MIT License
