import typer
import shutil
import json
from pathlib import Path
from audioai import config
from audioai.utils import run_command, is_tool_installed
from audioai.models import load_registry
from rich.console import Console

app = typer.Typer(help="Transcribe audio files.")
console = Console()

def normalize_audio(input_file: Path, output_file: Path):
    """Normalize audio to 16kHz mono WAV using FFmpeg."""
    if not is_tool_installed("ffmpeg"):
        console.print("[red]FFmpeg is not installed. Please install it first.[/red]")
        raise typer.Exit(code=1)

    console.print(f"Normalizing audio: {input_file.name} -> {output_file.name}")
    command = [
        "ffmpeg", "-y", "-i", str(input_file),
        "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000",
        str(output_file)
    ]
    # For MVP we just run it and let ffmpeg output go to stdout/stderr or capture it.
    run_command(command, capture_output=True)
    console.print("[green]Audio normalization complete.[/green]")

def run_whisper(audio_file: Path, model_path: Path, output_base: Path, lang: str = "auto"):
    """Run whisper.cpp via subprocess."""

    # Determine whisper binary
    whisper_bin = "whisper-cli"
    if not is_tool_installed("whisper-cli"):
        if (config.BIN_DIR / "whisper-cli").exists():
             whisper_bin = str(config.BIN_DIR / "whisper-cli")
        elif (config.BIN_DIR / "main").exists():
             whisper_bin = str(config.BIN_DIR / "main")
        else:
             console.print("[red]whisper-cli binary not found.[/red]")
             raise typer.Exit(code=1)

    console.print(f"Transcribing {audio_file.name} with model {model_path.name}...")

    # whisper-cli arguments for output files (-otxt, -oj, -osrt)
    # Note: we use -otxt (text), -oj (json) to get structured output
    command = [
        whisper_bin,
        "-m", str(model_path),
        "-f", str(audio_file),
        "-otxt", "-oj",
        "-of", str(output_base)
    ]
    if lang != "auto":
        command.extend(["-l", lang])


    # In a real environment, this might take a while, so we might not want to capture_output
    # entirely without showing progress, but for MVP capture_output=True is okay for testing
    run_command(command, capture_output=True)

    # Create simple markdown from text
    txt_file = Path(f"{output_base}.txt")
    md_file = Path(f"{output_base}.md")
    if txt_file.exists():
        with open(txt_file, "r") as f:
            text = f.read()
        with open(md_file, "w") as f:
            f.write("# Transcript\n\n")
            f.write(text)

    console.print("[green]Transcription complete![/green]")

@app.command("transcribe")
def transcribe(
    audio_file: Path = typer.Argument(..., help="Path to the audio file"),
    model: str = typer.Option("whisper-base", "--model", "-m", help="STT model to use"),
    lang: str = typer.Option("auto", "--lang", "-l", help="Language code (e.g. en, hi)")
):
    """Transcribe an audio file."""
    if not audio_file.exists():
        console.print(f"[red]File not found: {audio_file}[/red]")
        raise typer.Exit(code=1)

    registry = load_registry()
    if model not in registry or not registry[model].get("installed"):
        console.print(f"[red]Model '{model}' is not installed or not found.[/red]")
        console.print(f"Run 'audioai models install {model}' to install it.")
        raise typer.Exit(code=1)

    model_path = Path(registry[model]["path"])

    # Prepare output directory
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    normalized_wav = output_dir / f"{audio_file.stem}_normalized.wav"
    output_base = output_dir / f"{audio_file.stem}.transcript"

    try:
        normalize_audio(audio_file, normalized_wav)
        run_whisper(normalized_wav, model_path, output_base, lang)

        console.print(f"\nOutputs saved to {output_dir}/")
        console.print(f"- {output_base.name}.txt")
        console.print(f"- {output_base.name}.json")
        console.print(f"- {output_base.name}.md")

    except Exception as e:
        console.print(f"[red]Transcription failed: {e}[/red]")
    finally:
        # Cleanup normalized temp file
        if normalized_wav.exists():
            normalized_wav.unlink()
