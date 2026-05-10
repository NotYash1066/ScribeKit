import typer
import json
from audioai import config
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Manage STT Models.")
console = Console()

def load_registry():
    if not config.REGISTRY_FILE.exists():
        console.print("[red]Registry not found. Run 'audioai init' first.[/red]")
        raise typer.Exit(code=1)
    with open(config.REGISTRY_FILE, "r") as f:
        return json.load(f)

def save_registry(registry_data):
    with open(config.REGISTRY_FILE, "w") as f:
        json.dump(registry_data, f, indent=2)

@app.command("list")
def list_models():
    """List available and installed models."""
    registry = load_registry()

    table = Table(title="AudioAI Models")
    table.add_column("Model Name", style="cyan", no_wrap=True)
    table.add_column("Backend", style="magenta")
    table.add_column("Language")
    table.add_column("Size (MB)", justify="right")
    table.add_column("Status", justify="center")

    for name, info in registry.items():
        status = "[green]Installed[/green]" if info.get("installed") else "[yellow]Available[/yellow]"
        table.add_row(
            name,
            info.get("backend", "N/A"),
            info.get("language", "N/A"),
            str(info.get("size_mb", "N/A")),
            status
        )

    console.print(table)

@app.command("install")
def install_model(model_name: str):
    """Install a specific model (simulated for v1)."""
    registry = load_registry()

    if model_name not in registry:
        console.print(f"[red]Model '{model_name}' not found in registry.[/red]")
        raise typer.Exit(code=1)

    model_info = registry[model_name]

    if model_info.get("installed"):
        console.print(f"[green]Model '{model_name}' is already installed.[/green]")
        return

    console.print(f"Installing {model_name}...")

    # Simulate download and extraction for v1 MVP
    model_path = config.MODELS_DIR / f"ggml-{model_name}.bin"

    # Touch a dummy file to simulate model presence for local testing
    model_path.touch()

    # Update registry
    model_info["installed"] = True
    model_info["path"] = str(model_path)
    save_registry(registry)

    console.print(f"[green]Successfully installed {model_name} to {model_path}[/green]")
