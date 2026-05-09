import os
from pathlib import Path

# Base directories
USER_HOME = Path.home()
APP_DIR = USER_HOME / ".audioai"
MODELS_DIR = APP_DIR / "models"
REGISTRY_FILE = APP_DIR / "registry.json"
BIN_DIR = APP_DIR / "bin"

def init_dirs():
    """Create necessary application directories."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)

def is_initialized() -> bool:
    """Check if the app has been initialized (registry file exists)."""
    return REGISTRY_FILE.exists()
