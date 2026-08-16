"""Build and package Python FastAPI sidecar binary with PyInstaller for Tauri."""

import os
import sys
import subprocess
import shutil
import platform

def get_target_triple() -> str:
    try:
        output = subprocess.check_output(["rustc", "-vV"], text=True)
        for line in output.splitlines():
            if line.startswith("host:"):
                return line.split(":", 1)[1].strip()
    except Exception as e:
        print(f"Warning: Failed to get target triple from rustc ({e}), falling back to platform detection.")
    
    machine = platform.machine().lower()
    system = platform.system().lower()
    if system == "windows":
        return f"{machine}-pc-windows-msvc"
    elif system == "darwin":
        return f"{machine}-apple-darwin"
    else:
        return f"{machine}-unknown-linux-gnu"

def build():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_main = os.path.join(current_dir, "app", "main.py")
    target_triple = get_target_triple()
    print(f"Building sidecar for target triple: {target_triple}")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--console",
        "--name",
        "maxume_backend",
        app_main,
    ]
    print(f"Executing: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=current_dir)

    dist_dir = os.path.abspath(os.path.join(current_dir, "dist"))
    exe_suffix = ".exe" if platform.system() == "windows" else ""
    built_binary = os.path.join(dist_dir, f"maxume_backend{exe_suffix}")
    
    # Tauri expects externalBin at `src-tauri/binaries/maxume_backend-<triple>.exe` or relative path configured
    binaries_dir = os.path.abspath(os.path.join(os.path.dirname(current_dir), "src-tauri", "binaries"))
    os.makedirs(binaries_dir, exist_ok=True)
    
    target_binary = os.path.join(binaries_dir, f"maxume_backend-{target_triple}{exe_suffix}")
    shutil.copy2(built_binary, target_binary)
    print(f"Successfully packaged sidecar binary to: {target_binary}")

if __name__ == "__main__":
    build()
