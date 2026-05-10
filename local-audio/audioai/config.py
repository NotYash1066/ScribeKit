import os
import yaml
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_DIR = Path.home() / ".audioai"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "paths": {
        "models_dir": str(DEFAULT_CONFIG_DIR / "models"),
        "outputs_dir": "./outputs",
        "temp_dir": str(DEFAULT_CONFIG_DIR / "temp"),
    },
    "whisper": {"binary": "whisper-cli", "default_model": "whisper-base"},
    "transcription": {"default_language": "auto", "keep_temp": False},
}


def load_config() -> Dict[str, Any]:
    if not DEFAULT_CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with open(DEFAULT_CONFIG_FILE, "r") as f:
            user_config = yaml.safe_load(f) or {}
            # Merge logic for simplicity (1 level deep)
            config = DEFAULT_CONFIG.copy()
            for k, v in user_config.items():
                if isinstance(v, dict) and k in config:
                    config[k].update(v)
                else:
                    config[k] = v
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(DEFAULT_CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_config_value(key_path: str) -> Any:
    config = load_config()
    keys = key_path.split(".")
    val = config
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return None
    return val


def set_config_value(key_path: str, value: Any) -> None:
    config = load_config()
    keys = key_path.split(".")
    target = config
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]

    # Convert bools and ints correctly
    if isinstance(value, str):
        if value.lower() in ("true", "yes", "1"):
            value = True
        elif value.lower() in ("false", "no", "0"):
            value = False
        elif value.isdigit():
            value = int(value)

    target[keys[-1]] = value
    save_config(config)


def init_directories() -> None:
    config = load_config()
    paths = config.get("paths", {})
    for k, v in paths.items():
        Path(v).mkdir(parents=True, exist_ok=True)
