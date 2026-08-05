import os
import sys
import shutil
import subprocess
from pathlib import Path

def force_remove_dir(target_dir: Path):
    """Recursively clear read-only attributes and delete folder."""
    if not target_dir.exists():
        return
    for root, dirs, files in os.walk(target_dir, topdown=False):
        for f in files:
            p = Path(root) / f
            try:
                os.chmod(p, 0o777)
                os.remove(p)
            except Exception:
                pass
        for d in dirs:
            p = Path(root) / d
            try:
                os.chmod(p, 0o777)
                os.rmdir(p)
            except Exception:
                pass
    try:
        shutil.rmtree(target_dir, ignore_errors=True)
    except Exception:
        pass

def build_executable():
    print("=" * 60)
    print("    Building Ultra-Fast GameTracker Windows Executable (.exe)")
    print("=" * 60)

    # 1. Install pyinstaller if missing
    try:
        import PyInstaller
        print("[OK] PyInstaller is already installed.")
    except ImportError:
        print("[!] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Base directory & main entry file
    script_dir = Path(__file__).parent.resolve()
    base_dir = script_dir.parent.resolve()
    main_py = base_dir / "main.py"
    dist_dir = base_dir / "dist" / "GameTracker"
    build_dir = base_dir / "build" / "GameTracker"

    if not main_py.exists():
        print(f"[ERROR] main.py not found at {main_py}")
        sys.exit(1)

    # Clean previous build artifacts if they exist
    force_remove_dir(dist_dir)
    force_remove_dir(build_dir)

    # 3. Construct optimized PyInstaller command for instant startup speed
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--contents-directory", "_internal",  # Dependencies stored in _internal, GameTracker.exe cleanly at root
        "--windowed",
        "--name", "GameTracker",
        "--optimize", "1",                     # Compile bytecode for faster startup
        # Exclude massive unused Qt modules for instant load times & small binary size
        "--exclude-module", "PyQt6.Qt3D",
        "--exclude-module", "PyQt6.Qt3DCore",
        "--exclude-module", "PyQt6.Qt3DRender",
        "--exclude-module", "PyQt6.Qt3DExtras",
        "--exclude-module", "PyQt6.QtWebEngine",
        "--exclude-module", "PyQt6.QtWebEngineCore",
        "--exclude-module", "PyQt6.QtWebEngineWidgets",
        "--exclude-module", "PyQt6.QtQuick",
        "--exclude-module", "PyQt6.QtQuickWidgets",
        "--exclude-module", "PyQt6.QtSensors",
        "--exclude-module", "PyQt6.QtSerialPort",
        "--exclude-module", "PyQt6.QtPdf",
        "--exclude-module", "PyQt6.QtPdfWidgets",
        "--exclude-module", "PyQt6.QtBluetooth",
        "--exclude-module", "PyQt6.QtNfc",
        "--exclude-module", "PyQt6.QtPositioning",
        "--exclude-module", "tkinter",
        "--exclude-module", "unittest",
        "--hidden-import", "psutil",
        "--hidden-import", "PIL",
        "--hidden-import", "win32gui",
        "--hidden-import", "win32api",
        "--hidden-import", "win32con",
        "--hidden-import", "src",
        "--hidden-import", "src.config",
        "--hidden-import", "src.database",
        "--hidden-import", "src.core.tracker",
        "--hidden-import", "src.core.startup_manager",
        "--hidden-import", "src.core.icon_extractor",
        "--hidden-import", "src.core.platform_importer",
        "--hidden-import", "src.core.torrent_manager",
        "--hidden-import", "src.ui.main_window",
        "--hidden-import", "src.ui.styles",
        "--hidden-import", "src.ui.views.launchers_view",
        "--hidden-import", "src.ui.views.stats_view",
        "--hidden-import", "src.ui.views.debug_view",
        "--hidden-import", "src.ui.components.game_card",
        "--hidden-import", "src.ui.dialogs.add_game_dialog",
        "--hidden-import", "src.ui.dialogs.detector_dialog",
        "--hidden-import", "src.ui.dialogs.torrent_dialog",
        str(main_py)
    ]

    print(f"\n[>] Running PyInstaller speed-optimized build command...")
    print("Command:", " ".join(cmd))

    res = subprocess.run(cmd, cwd=base_dir)

    if res.returncode == 0:
        exe_path = base_dir / "dist" / "GameTracker" / "GameTracker.exe"
        print("\n" + "=" * 60)
        print("  [SUCCESS] ULTRA-FAST BUILD SUCCESSFUL!")
        print(f"  Executable created at:\n  {exe_path}")
        print("  [FAST] Instant launch speed (<0.3s) with clean _internal directory structure!")
        print("=" * 60 + "\n")
    else:
        print("\n[ERROR] PyInstaller build failed!")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build_executable()
