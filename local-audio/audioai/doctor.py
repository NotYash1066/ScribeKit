import os
import sys
from audioai import config
from audioai.utils import is_tool_installed

def check_dependencies():
    """Check for system dependencies and print report."""
    issues_found = False

    print("🩺 Running AudioAI Doctor...\n")

    # Check Python version
    python_version = sys.version.split()[0]
    print(f"[✓] Python version: {python_version}")

    # Check FFmpeg
    if is_tool_installed("ffmpeg"):
        print("[✓] FFmpeg is installed.")
    else:
        print("[✗] FFmpeg is missing.")
        print("    Please install FFmpeg:")
        print("    - Mac: brew install ffmpeg")
        print("    - Ubuntu/Debian: sudo apt install ffmpeg")
        print("    - Windows: winget install ffmpeg")
        issues_found = True

    # Check whisper-cli (or whisper.cpp binary)
    # We will assume 'whisper-cli' is the binary name for this MVP
    if is_tool_installed("whisper-cli"):
        print("[✓] whisper-cli is installed in PATH.")
    elif (config.BIN_DIR / "whisper-cli").exists() or (config.BIN_DIR / "main").exists():
         print("[✓] whisper-cli found in AudioAI bin directory.")
    else:
        print("[✗] whisper-cli (whisper.cpp) is missing.")
        print("    Please download or build whisper.cpp and ensure 'whisper-cli' is in your PATH")
        print(f"    or placed in {config.BIN_DIR}.")
        issues_found = True

    # Check directories
    if config.APP_DIR.exists() and os.access(config.APP_DIR, os.W_OK):
         print(f"[✓] App directory is writable: {config.APP_DIR}")
    else:
         print(f"[✗] App directory is not writable or missing: {config.APP_DIR}")
         print("    Run 'audioai init' to create it.")
         issues_found = True

    if config.is_initialized():
        print(f"[✓] Model registry found: {config.REGISTRY_FILE}")
    else:
        print("[✗] Model registry is missing.")
        print("    Run 'audioai init' to initialize the registry.")
        issues_found = True

    print("\n")
    if issues_found:
        print("⚠️  Some issues were found. Please fix them before transcribing.")
    else:
        print("✅ You are ready to go!")
