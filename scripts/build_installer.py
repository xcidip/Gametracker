import os
import sys
import shutil
import subprocess
from pathlib import Path

ISCC_PATHS = [
    r"C:\Users\x\AppData\Local\Programs\Antigravity IDE\resources\app\node_modules\innosetup\bin\ISCC.exe",
    r"C:\Users\x\AppData\Local\Programs\Antigravity\resources\app\node_modules\innosetup\bin\ISCC.exe",
    r"C:\Program Files\Inno Setup 7\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 7\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
]

def find_iscc() -> str:
    for path in ISCC_PATHS:
        if os.path.exists(path):
            return path
    # Try finding in PATH
    try:
        res = subprocess.run(["where", "iscc"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return res.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return ""

def build_windows_setup_installer():
    print("=" * 60)
    print("    Building GameTracker Windows Setup Installer")
    print("=" * 60)

    base_dir = Path(__file__).parent.resolve()

    # Step 1: Build PyInstaller distribution directory
    print("\n[Step 1/2] Building executable distribution binaries...")
    build_script = base_dir / "build_exe.py"
    res = subprocess.run([sys.executable, str(build_script)], cwd=base_dir)
    if res.returncode != 0:
        print("[ERROR] PyInstaller build failed!")
        sys.exit(res.returncode)

    # Step 2: Locate Inno Setup Compiler
    print("\n[Step 2/2] Compiling Windows Setup Installer (.exe)...")
    iscc_bin = find_iscc()
    if not iscc_bin:
        print("[ERROR] Inno Setup compiler (ISCC.exe) not found!")
        sys.exit(1)

    print(f"[OK] Found Inno Setup Compiler: {iscc_bin}")

    iss_script = base_dir / "installer.iss"
    if not iss_script.exists():
        print(f"[ERROR] installer.iss script not found at {iss_script}")
        sys.exit(1)

    cmd = [iscc_bin, str(iss_script)]
    print(f"[>] Running Inno Setup command: {' '.join(cmd)}")
    res_iscc = subprocess.run(cmd, cwd=base_dir)

    if res_iscc.returncode == 0:
        output_installer = base_dir / "dist_installer" / "GameTracker_Setup.exe"
        print("\n" + "=" * 60)
        print("  [SUCCESS] WINDOWS SETUP INSTALLER CREATED!")
        print(f"  Installer file created at:\n  {output_installer}")
        print("  Features:")
        print("  - Choose Custom Installation Directory (Browse...)")
        print("  - Create Desktop Shortcut")
        print("  - Create Start Menu Shortcut")
        print("  - Full Uninstaller Registration in Control Panel / Settings")
        print("=" * 60 + "\n")
    else:
        print("\n[ERROR] Inno Setup compilation failed!")
        sys.exit(res_iscc.returncode)

if __name__ == "__main__":
    build_windows_setup_installer()
