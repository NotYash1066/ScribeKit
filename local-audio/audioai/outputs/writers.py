import json
from pathlib import Path
from ..schemas import Transcript, TranscriptMeta


def write_txt(transcript: Transcript, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        for seg in transcript.segments:
            f.write(f"{seg.text}\n")


def _format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def write_md(transcript: Transcript, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Transcript: {Path(transcript.source_file).stem}\n\n")
        f.write("## Metadata\n\n")
        f.write(f"- Source: `{transcript.source_file}`\n")
        f.write(f"- Backend: {transcript.backend}\n")
        f.write(f"- Model: {transcript.model}\n")
        f.write(f"- Language: {transcript.language}\n")
        f.write(f"- Duration: {_format_time(transcript.duration_sec)}\n\n")
        f.write("## Transcript\n\n")

        for seg in transcript.segments:
            t_start = _format_time(seg.start)
            t_end = _format_time(seg.end)
            f.write(f"[{t_start} - {t_end}] {seg.text}\n\n")


def write_json(transcript: Transcript, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(transcript.model_dump_json(indent=2))


def write_meta(meta: TranscriptMeta, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(meta.model_dump_json(indent=2))
