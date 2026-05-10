import typer
from rich.console import Console
from . import config, doctor

app = typer.Typer(help="Local Audio Intelligence Toolkit", no_args_is_help=True)
console = Console()

config_app = typer.Typer(help="Manage configuration", no_args_is_help=True)
app.add_typer(config_app, name="config")


@app.command()
def init():
    """Initialize the AudioAI configuration and directories."""
    config.init_directories()
    # Save default config if not exists
    _ = config.load_config()
    config.save_config(_)
    console.print(
        "Initialized AudioAI configuration and directories. [green]✅[/green]"
    )


@app.command("doctor")
def doctor_cmd():
    """Check system dependencies (ffmpeg, whisper.cpp, etc.)."""
    doctor.run_doctor()


@config_app.command("show")
def config_show():
    """Show current configuration."""
    cfg = config.load_config()
    import yaml

    console.print(yaml.dump(cfg, default_flow_style=False))


@config_app.command("set")
def config_set(key: str, value: str):
    """Set a configuration value."""
    config.set_config_value(key, value)
    console.print(f"Set {key} to {value} [green]✅[/green]")


models_app = typer.Typer(help="Manage STT Models", no_args_is_help=True)
app.add_typer(models_app, name="models")


@models_app.command("list")
def models_list(installed: bool = False):
    """List available models in the registry."""
    from . import models
    import json

    console.print(json.dumps(models.list_models(installed_only=installed), indent=2))


@models_app.command("info")
def models_info(model: str):
    """Get information about a specific model."""
    from . import models
    import json

    try:
        console.print(json.dumps(models.get_model_info(model), indent=2))
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


@models_app.command("install")
def models_install(model: str):
    """Install a model."""
    from . import models

    try:
        models.install_model(model)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def transcribe(
    input_file: str = typer.Argument(..., help="Path to the audio file to transcribe"),
    model: str = typer.Option(None, help="Model to use (defaults to config)"),
    lang: str = typer.Option("auto", help="Language code or 'auto'"),
    out: str = typer.Option(None, help="Output directory (defaults to config)"),
    keep_temp: bool = typer.Option(False, help="Keep temporary files for debugging"),
):
    """Transcribe an audio file."""
    from pathlib import Path
    from . import config, models
    from .backends import WhisperCppBackend
    from .outputs import write_txt, write_md, write_json, write_meta
    from .schemas import TranscriptMeta
    import os

    input_path = Path(input_file)
    if not input_path.exists():
        console.print(f"[red]Error:[/red] Input file '{input_file}' not found.")
        raise typer.Exit(code=1)

    cfg = config.load_config()
    target_model_name = model or cfg.get("whisper", {}).get(
        "default_model", "whisper-base"
    )

    try:
        model_info = models.get_model_info(target_model_name)
        if not model_info["installed"]:
            console.print(
                f"[red]Error:[/red] Model '{target_model_name}' is not installed. Run 'audioai models install {target_model_name}'"
            )
            raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    models_dir = models.get_models_dir()
    model_path = models_dir / model_info["filename"]

    out_dir_str = out or cfg.get("paths", {}).get("outputs_dir", "./outputs")
    out_dir = Path(out_dir_str)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        f"Transcribing {input_file} using {target_model_name} (language: {lang})..."
    )

    backend = WhisperCppBackend()

    try:
        transcript = backend.transcribe(
            audio_path=input_path,
            model_path=model_path,
            language=lang,
            keep_temp=keep_temp,
        )

        stem = input_path.stem

        txt_path = out_dir / f"{stem}.transcript.txt"
        md_path = out_dir / f"{stem}.transcript.md"
        segments_path = out_dir / f"{stem}.segments.json"
        meta_path = out_dir / f"{stem}.meta.json"

        write_txt(transcript, txt_path)
        write_md(transcript, md_path)
        write_json(transcript, segments_path)

        file_size = input_path.stat().st_size
        meta = TranscriptMeta(
            source_file=input_path.name,
            normalized_audio=f"temp/{stem}.normalized.wav",  # Logical reference, might be deleted
            file_size_bytes=file_size,
            duration_sec=transcript.duration_sec,
            backend=backend.name,
            model=target_model_name,
            status="completed",
        )

        write_meta(meta, meta_path)

        console.print(
            f"[green]Transcription complete![/green] Outputs saved to {out_dir}"
        )
        console.print(f"  - {txt_path}")
        console.print(f"  - {md_path}")
        console.print(f"  - {segments_path}")
        console.print(f"  - {meta_path}")

    except Exception as e:
        console.print(f"[red]Transcription failed:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
