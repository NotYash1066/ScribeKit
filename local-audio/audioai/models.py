import urllib.request
from pathlib import Path
from typing import Dict, Any
from .config import load_config
from rich.console import Console

console = Console()

MODELS_REGISTRY = {
    "whisper-base": {
        "backend": "whisper.cpp",
        "language": "multi",
        "filename": "ggml-base.bin",
        "size_mb": 142,
        "sha1": "465707469ff3a37a2b9b8d8f89f2f99de7299dac",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
    }
}


def get_models_dir() -> Path:
    config = load_config()
    models_dir = Path(
        config.get("paths", {}).get(
            "models_dir", str(Path.home() / ".audioai" / "models")
        )
    )
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def list_models(installed_only: bool = False) -> Dict[str, Any]:
    models_dir = get_models_dir()
    result = {}
    for name, info in MODELS_REGISTRY.items():
        is_installed = (models_dir / info["filename"]).exists()
        if installed_only and not is_installed:
            continue

        info_copy = info.copy()
        info_copy["installed"] = is_installed
        result[name] = info_copy
    return result


def get_model_info(model_name: str) -> Dict[str, Any]:
    if model_name not in MODELS_REGISTRY:
        raise ValueError(f"Model '{model_name}' not found in registry.")

    models_dir = get_models_dir()
    info = MODELS_REGISTRY[model_name].copy()
    info["installed"] = (models_dir / info["filename"]).exists()
    return info


def install_model(model_name: str):
    if model_name not in MODELS_REGISTRY:
        raise ValueError(f"Model '{model_name}' not found in registry.")

    info = MODELS_REGISTRY[model_name]
    models_dir = get_models_dir()
    dest_path = models_dir / info["filename"]

    if dest_path.exists():
        console.print(
            f"Model [bold]{model_name}[/bold] is already installed at {dest_path}"
        )
        return

    url = info["url"]
    console.print(
        f"Downloading [bold]{model_name}[/bold] ({info['size_mb']} MB) from {url}..."
    )

    try:
        # Using urllib.request.urlretrieve to download the file directly to the destination path
        urllib.request.urlretrieve(url, dest_path)
        console.print(
            f"Successfully installed [bold]{model_name}[/bold] to {dest_path} [green]✅[/green]"
        )
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        raise RuntimeError(f"Failed to download model '{model_name}': {e}")
