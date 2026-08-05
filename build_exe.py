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
    print("    Building Single-File GameTracker Executable (.exe)")
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
    dist_file = base_dir / "dist" / "GameTracker.exe"
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

    if dist_file.exists():
        try:
            os.remove(dist_file)
        except Exception as e:
            print(f"[NOTE] Could not clean previous dist executable: {e}")

    # 3. Construct PyInstaller single-file command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",            # Single standalone .exe file (no _internal folder needed!)
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

    print(f"\n[>] Running PyInstaller single-file build command...")
    print("Command:", " ".join(cmd))

    res = subprocess.run(cmd, cwd=base_dir)

    if res.returncode == 0:
        exe_path = base_dir / "dist" / "GameTracker.exe"
        print("\n" + "=" * 60)
        print("  [SUCCESS] SINGLE-FILE BUILD SUCCESSFUL!")
        print(f"  Single Standalone Executable created at:\n  {exe_path}")
        print("  (No _internal folder required - 100% self-contained!)")
        print("=" * 60 + "\n")
    else:
        print("\n[ERROR] PyInstaller build failed!")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build_executable()
