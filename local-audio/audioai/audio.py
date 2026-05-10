import subprocess
import shutil
from pathlib import Path


def normalize_audio(input_path: Path, temp_dir: Path) -> Path:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is missing. Please install ffmpeg to proceed.")

    if not input_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_path}")

    output_path = temp_dir / f"{input_path.stem}.normalized.wav"

    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output files without asking
        "-i",
        str(input_path),  # Input file
        "-ar",
        "16000",  # Set audio sampling rate to 16kHz
        "-ac",
        "1",  # Set audio channels to 1 (mono)
        "-c:a",
        "pcm_s16le",  # Set audio codec to pcm_s16le (16-bit)
        "-loglevel",
        "error",  # Only show errors
        str(output_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg failed: {e.stderr}")
