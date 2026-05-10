import pytest
import json
import shutil
from pathlib import Path
from typer.testing import CliRunner
from audioai.cli import app
from audioai.config import DEFAULT_CONFIG_DIR

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Isolate config and models directory for testing."""
    test_config_dir = tmp_path / ".audioai"
    monkeypatch.setattr("audioai.config.DEFAULT_CONFIG_DIR", test_config_dir)
    monkeypatch.setattr(
        "audioai.config.DEFAULT_CONFIG_FILE", test_config_dir / "config.yaml"
    )
    monkeypatch.setattr("audioai.doctor.DEFAULT_CONFIG_DIR", test_config_dir)

    # Init so dirs exist
    runner.invoke(app, ["init"])
    return tmp_path


def test_init():
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Initialized AudioAI configuration" in result.stdout


def test_doctor_missing_ffmpeg(monkeypatch):
    monkeypatch.setattr(
        "shutil.which", lambda x: None if x == "ffmpeg" else "/fake/path"
    )
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0  # Doctor runs successfully but prints missing
    assert "FFmpeg: missing" in result.stdout
    assert "needs attention" in result.stdout


def test_doctor_all_present(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: "/fake/path")
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "ready" in result.stdout


def test_models_list():
    result = runner.invoke(app, ["models", "list"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "whisper-base" in data
    assert data["whisper-base"]["installed"] is False


def test_models_info():
    result = runner.invoke(app, ["models", "info", "whisper-base"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["backend"] == "whisper.cpp"


def test_config_set_and_show():
    result = runner.invoke(app, ["config", "set", "whisper.binary", "/opt/whisper-cli"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "/opt/whisper-cli" in result.stdout


def test_transcribe_missing_input():
    result = runner.invoke(app, ["transcribe", "nonexistent.mp3"])
    assert result.exit_code == 1
    assert "Input file 'nonexistent.mp3' not found" in result.stdout


def test_transcribe_missing_model(tmp_path):
    dummy_audio = tmp_path / "dummy.wav"
    dummy_audio.touch()
    result = runner.invoke(app, ["transcribe", str(dummy_audio)])
    assert result.exit_code == 1
    assert "Model 'whisper-base' is not installed" in result.stdout


@pytest.fixture
def mock_transcribe_env(monkeypatch, tmp_path):
    # Mock model as installed
    def mock_get_models_dir():
        d = tmp_path / "models"
        d.mkdir(exist_ok=True)
        return d

    monkeypatch.setattr("audioai.models.get_models_dir", mock_get_models_dir)

    (mock_get_models_dir() / "ggml-base.bin").touch()

    # Create dummy audio
    audio_path = tmp_path / "test.mp3"
    audio_path.write_bytes(b"dummy audio data")

    out_dir = tmp_path / "outputs"

    # Mock subprocess.run for ffmpeg and whisper-cli
    import subprocess

    original_run = subprocess.run

    def mocked_run(cmd, *args, **kwargs):
        if cmd[0] == "ffmpeg":
            # Just create the output file
            out_file = Path(cmd[-1])
            out_file.touch()
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="", stderr=""
            )
        elif "whisper-cli" in cmd[0]:
            # Create the json output
            of_idx = cmd.index("-of")
            prefix = cmd[of_idx + 1]
            out_json = Path(f"{prefix}.json")

            dummy_json = {
                "transcription": [
                    {"offsets": {"from": 0, "to": 500}, "text": " Hello world."}
                ]
            }
            out_json.write_text(json.dumps(dummy_json))
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="", stderr=""
            )
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mocked_run)
    monkeypatch.setattr("shutil.which", lambda x: "/fake/path")

    return audio_path, out_dir


def test_transcribe_success(mock_transcribe_env):
    audio_path, out_dir = mock_transcribe_env

    result = runner.invoke(app, ["transcribe", str(audio_path), "--out", str(out_dir)])

    assert result.exit_code == 0
    assert "Outputs saved to" in result.stdout

    assert (out_dir / "test.transcript.txt").exists()
    assert (out_dir / "test.transcript.md").exists()
    assert (out_dir / "test.segments.json").exists()
    assert (out_dir / "test.meta.json").exists()

    # Check JSON structure
    with open(out_dir / "test.segments.json") as f:
        data = json.load(f)
        assert data["source_file"] == "test.mp3"
        assert len(data["segments"]) == 1
        assert data["segments"][0]["text"] == "Hello world."
