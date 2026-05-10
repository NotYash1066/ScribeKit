import sys
import shutil
from rich.console import Console
from .config import load_config, DEFAULT_CONFIG_DIR

console = Console()


def check_python_version():
    version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    if sys.version_info >= (3, 9):
        console.print(f"Python: {version} [green]✅[/green]")
        return True
    else:
        console.print(f"Python: {version} [red]❌ (Requires >= 3.9)[/red]")
        return False


def check_ffmpeg():
    if shutil.which("ffmpeg"):
        console.print("FFmpeg: found [green]✅[/green]")
        return True
    else:
        console.print("FFmpeg: missing [red]❌[/red]")
        console.print("Install FFmpeg, then run audioai doctor again.", style="yellow")
        return False


def check_whisper_cli():
    config = load_config()
    binary = config.get("whisper", {}).get("binary", "whisper-cli")
    if shutil.which(binary):
        console.print(f"whisper.cpp binary: found ({binary}) [green]✅[/green]")
        return True
    else:
        console.print(f"whisper.cpp binary: missing ({binary}) [red]❌[/red]")
        console.print(
            "Set path with:\naudioai config set whisper.binary /path/to/whisper-cli",
            style="yellow",
        )
        return False


def check_directories():
    config = load_config()
    console.print(f"Config directory: {DEFAULT_CONFIG_DIR} [green]✅[/green]")

    models_dir = config.get("paths", {}).get("models_dir")
    if models_dir:
        console.print(f"Models directory: {models_dir} [green]✅[/green]")
    else:
        console.print("Models directory: not configured [red]❌[/red]")


def check_default_model():
    config = load_config()
    model = config.get("whisper", {}).get("default_model")
    if model:
        console.print(f"Default model: {model} [green]✅[/green]")
    else:
        console.print("Default model: missing [red]❌[/red]")


def run_doctor():
    console.print("\n[bold]AudioAI Doctor[/bold]\n")
    checks = [check_python_version(), check_ffmpeg(), check_whisper_cli()]
    check_directories()
    check_default_model()

    console.print(
        "\nStatus: "
        + ("[green]ready[/green]" if all(checks) else "[red]needs attention[/red]")
    )
    return all(checks)
