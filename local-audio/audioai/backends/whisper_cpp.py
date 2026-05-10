import subprocess
import tempfile
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from rich.console import Console
from .base import STTBackend
from ..schemas import Transcript, TranscriptSegment
from ..audio import normalize_audio
from ..config import load_config

console = Console()


class WhisperCppBackend(STTBackend):
    name = "whisper.cpp"

    def transcribe(
        self,
        audio_path: Path,
        model_path: Path,
        language: Optional[str] = None,
        keep_temp: bool = False,
    ) -> Transcript:

        config = load_config()
        whisper_binary = config.get("whisper", {}).get("binary", "whisper-cli")

        if not shutil.which(whisper_binary):
            raise RuntimeError(
                f"{whisper_binary} not found. Please install it or configure the correct path."
            )

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        if not audio_path.exists():
            raise FileNotFoundError(f"Input audio file not found: {audio_path}")

        temp_base_dir = Path(
            config.get("paths", {}).get(
                "temp_dir", str(Path.home() / ".audioai" / "temp")
            )
        )
        temp_base_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(
            prefix="audioai_", dir=temp_base_dir
        ) as tmpdir_str:
            tmpdir = Path(tmpdir_str)

            # 1. Normalize audio
            normalized_wav = normalize_audio(audio_path, tmpdir)

            # 2. Call whisper-cli
            output_prefix = tmpdir / "whisper_out"
            cmd = [
                whisper_binary,
                "-m",
                str(model_path),
                "-f",
                str(normalized_wav),
                "-oj",
                "-of",
                str(output_prefix),
                "-np",  # no prints
            ]

            if language and language.lower() != "auto":
                cmd.extend(["-l", language])

            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"whisper-cli failed: {e.stderr}")

            # 3. Read JSON output
            json_path = Path(f"{output_prefix}.json")
            if not json_path.exists():
                raise RuntimeError(
                    f"whisper-cli completed but {json_path} was not found."
                )

            with open(json_path, "r", encoding="utf-8") as f:
                try:
                    whisper_output = json.load(f)
                except json.JSONDecodeError:
                    raise RuntimeError("Failed to parse JSON output from whisper-cli.")

            # 4. Convert to Transcript models
            segments_data = whisper_output.get("transcription", [])
            segments = []

            # whisper-cli json output uses ms or specific timestamps.
            # Example JSON structure for whisper.cpp:
            # "transcription": [{"timestamps": {"from": "00:00:00,000", "to": "00:00:05,800"}, "offsets": {"from": 0, "to": 5800}, "text": "...", ...}]
            # We'll adapt depending on the exact schema structure of whisper.cpp JSON.
            # Typical recent whisper.cpp json:
            # {"transcription": [{"offsets": {"from": 0, "to": 300}, "text": " hi"}]} where offsets are in 10ms units.
            # We will use offsets and multiply by 10 to get ms, then divide by 1000 for seconds, or if `timestamps` exists use that.

            duration_sec = 0.0

            for i, seg in enumerate(segments_data):
                # Handle start/end
                offsets = seg.get("offsets", {})
                start_sec = offsets.get("from", 0) * 0.001  # milliseconds -> seconds
                end_sec = offsets.get("to", 0) * 0.001

                text = seg.get("text", "").strip()

                # Update total duration based on last segment
                if end_sec > duration_sec:
                    duration_sec = end_sec

                segments.append(
                    TranscriptSegment(
                        id=i,
                        start=start_sec,
                        end=end_sec,
                        text=text,
                        language=(
                            language if language and language != "auto" else "auto"
                        ),  # whisper.cpp JSON doesn't reliably give per-segment lang
                        confidence=None,  # not populated accurately by default in json
                    )
                )

            transcript = Transcript(
                source_file=audio_path.name,
                created_at=datetime.now(timezone.utc),
                backend=self.name,
                model=model_path.name,
                language=language if language else "auto",
                duration_sec=duration_sec,
                segments=segments,
            )

            # If keep_temp, we copy the files out before tmpdir is destroyed
            if keep_temp:
                dest_dir = Path.cwd() / "temp_debug"
                dest_dir.mkdir(exist_ok=True)
                shutil.copy(normalized_wav, dest_dir / normalized_wav.name)
                shutil.copy(json_path, dest_dir / json_path.name)
                console.print(f"Kept temp files in {dest_dir}")

            return transcript
