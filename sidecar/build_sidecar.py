"""Build and package Python FastAPI sidecar binary with PyInstaller for Tauri."""

import os
import sys
import time
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
    if system == "windows" or os.name == "nt":
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
    is_win = platform.system().lower() == "windows" or os.name == "nt"
    exe_suffix = ".exe" if is_win else ""
    built_binary = os.path.join(dist_dir, f"maxume_backend{exe_suffix}")
    
    # Tauri expects externalBin at `src-tauri/binaries/maxume_backend-<triple>.exe`
    binaries_dir = os.path.abspath(os.path.join(os.path.dirname(current_dir), "src-tauri", "binaries"))
    os.makedirs(binaries_dir, exist_ok=True)
    target_binary = os.path.join(binaries_dir, f"maxume_backend-{target_triple}{exe_suffix}")

    print(f"Transferring {built_binary} -> {target_binary} ...")
    time.sleep(1.0)

    # Copy binary using raw chunked streams for Windows / OneDrive filesystem safety
    for attempt in range(5):
        try:
            with open(built_binary, "rb") as f_src:
                with open(target_binary, "wb") as f_dst:
                    while chunk := f_src.read(1024 * 1024):
                        f_dst.write(chunk)
            print(f"Successfully packaged sidecar binary to: {target_binary}")
            break
        except Exception as err:
            if attempt == 4:
                raise err
            time.sleep(1.0)

if __name__ == "__main__":
    build()
