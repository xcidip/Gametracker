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
    print("    Building GameTracker Standalone Windows Executable (.exe)")
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

    # Clean previous build dist if exists
    if dist_dir.exists():
        try:
            shutil.rmtree(dist_dir, onerror=remove_readonly)
        except Exception as e:
            print(f"[NOTE] Could not clean previous dist folder: {e}")

    # 3. Construct PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",             # Fast startup and clean structure
        "--windowed",           # GUI application without console window
        "--name", "GameTracker",
        "--collect-all", "PyQt6",
        "--hidden-import", "psutil",
        "--hidden-import", "PIL",
        "--hidden-import", "win32gui",
        "--hidden-import", "win32api",
        "--hidden-import", "win32con",
        "--hidden-import", "torrent_manager",
        "--hidden-import", "ui.torrent_dialog",
        str(main_py)
    ]

    print(f"\n[>] Running PyInstaller build command...")
    print("Command:", " ".join(cmd))

    res = subprocess.run(cmd, cwd=base_dir)

    if res.returncode == 0:
        exe_path = base_dir / "dist" / "GameTracker" / "GameTracker.exe"
        print("\n" + "=" * 60)
        print("  [SUCCESS] BUILD SUCCESSFUL!")
        print(f"  Executable created at:\n  {exe_path}")
        print("=" * 60 + "\n")
    else:
        print("\n[ERROR] PyInstaller build failed!")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build_executable()
