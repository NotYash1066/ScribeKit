import pytest
import os
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch

from audioai.cli import app
from audioai import config

runner = CliRunner()

@pytest.fixture
def mock_env(monkeypatch, tmp_path):
    """Mock the config directories to use a temp dir for testing."""
    test_app_dir = tmp_path / ".audioai"
    monkeypatch.setattr(config, "APP_DIR", test_app_dir)
    monkeypatch.setattr(config, "MODELS_DIR", test_app_dir / "models")
    monkeypatch.setattr(config, "BIN_DIR", test_app_dir / "bin")
    monkeypatch.setattr(config, "REGISTRY_FILE", test_app_dir / "registry.json")
    return test_app_dir

def test_init_creates_directories(mock_env):
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Created directories in" in result.output
    assert config.APP_DIR.exists()
    assert config.MODELS_DIR.exists()
    assert config.BIN_DIR.exists()
    assert config.REGISTRY_FILE.exists()

def test_doctor_detects_missing_tools(mock_env):
    runner.invoke(app, ["init"])

    with patch("audioai.doctor.is_tool_installed", return_value=False):
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "[✗] FFmpeg is missing" in result.output
        assert "[✗] whisper-cli (whisper.cpp) is missing" in result.output

def test_models_list(mock_env):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["models", "list"])
    assert result.exit_code == 0
    assert "whisper-base" in result.output
    assert "Available" in result.output

def test_models_install(mock_env):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["models", "install", "whisper-base"])
    assert result.exit_code == 0
    assert "Successfully installed whisper-base" in result.output

    # Check that list now shows it as installed
    result_list = runner.invoke(app, ["models", "list"])
    assert "Installed" in result_list.output

def test_transcribe_missing_model(mock_env, tmp_path):
    runner.invoke(app, ["init"])
    test_audio = tmp_path / "test.wav"
    test_audio.touch()

    result = runner.invoke(app, ["transcribe", str(test_audio), "--model", "nonexistent"])
    assert result.exit_code == 1
    assert "not installed or not found" in result.output

@patch("audioai.transcribe.is_tool_installed")
@patch("audioai.transcribe.run_command")
def test_transcribe_success(mock_run, mock_is_tool, mock_env, tmp_path):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["models", "install", "whisper-base"])

    test_audio = tmp_path / "test.wav"
    test_audio.touch()

    mock_is_tool.return_value = True
    mock_run.return_value = None

    # Run from a specific directory so 'outputs/' goes to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = runner.invoke(app, ["transcribe", str(test_audio)])
        assert result.exit_code == 0
        assert "Audio normalization complete." in result.output
        assert "Transcription complete!" in result.output

        output_dir = Path("outputs")
        assert output_dir.exists()
    finally:
        os.chdir(original_cwd)
