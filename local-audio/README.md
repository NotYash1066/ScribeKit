# Local Audio Intelligence Toolkit (AudioAI)

Phase 1 implementation for the Local Audio Intelligence Toolkit CLI.

## Installation

You can install this directly for development using pip or pipx:

```bash
git clone <repo>
cd local-audio
pip install -e ".[dev]"
```

## Features
- **One-file transcription polish**: Clean Markdown, `.txt`, and JSON segments output.
- **Normalization**: Built-in ffmpeg wrapper normalizes audio automatically to 16kHz mono WAV for stability.
- **Language support**: Includes `--lang auto` and specific language support.
- **Offline**: Entirely offline processing using whisper.cpp under the hood.

## Getting Started

1. **Initialize the toolkit**:
   ```bash
   audioai init
   ```
2. **Check your environment dependencies**:
   ```bash
   audioai doctor
   ```
   *Note: If `ffmpeg` or `whisper-cli` are missing, please install them via your package manager or built from source.*

3. **Install the default STT model (whisper-base)**:
   ```bash
   audioai models install whisper-base
   ```

4. **Transcribe your audio file**:
   *Please provide your own audio file, like an `.mp3`, `.m4a`, or `.wav`.*
   ```bash
   audioai transcribe path/to/your/audio.mp3 --lang auto
   ```
   Outputs will be saved in your configured `./outputs` directory (e.g. `./outputs/audio.transcript.md`).

## Testing

Tests utilize `pytest` and a mocked STT backend to bypass downloading real models during test suites. Run tests:

```bash
pytest tests/
```
