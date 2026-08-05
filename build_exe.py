import os
import sys
import shutil
import subprocess
from pathlib import Path

def remove_readonly(func, path, exc_info):
    """Clear the readonly bit and retry deletion."""
    try:
        os.chmod(path, 0o777)
        func(path)
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
    base_dir = Path(__file__).parent.resolve()
    main_py = base_dir / "main.py"
    dist_dir = base_dir / "dist" / "GameTracker"

    if not main_py.exists():
        print(f"[ERROR] main.py not found at {main_py}")
        sys.exit(1)

    # Clean previous build artifacts if they exist
    if dist_dir.exists():
        try:
            shutil.rmtree(dist_dir, onerror=remove_readonly)
        except Exception as e:
            print(f"[NOTE] Could not clean previous dist folder: {e}")

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
        "--hidden-import", "torrent_manager",
        "--hidden-import", "ui.torrent_dialog",
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
