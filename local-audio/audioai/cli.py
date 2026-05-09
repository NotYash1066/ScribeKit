import typer
import json
from audioai import config
from audioai.doctor import check_dependencies

app = typer.Typer(help="Local Audio Intelligence Toolkit")

@app.command()
def init():
    """Initialize the AudioAI configuration and directories."""
    config.init_dirs()
    print(f"Created directories in {config.APP_DIR}")

    if not config.REGISTRY_FILE.exists():
        # Create an empty or default registry
        default_registry = {
            "whisper-base": {
                "backend": "whisper.cpp",
                "language": "multi",
                "size_mb": 142,
                "recommended_for": ["general", "mixed language"],
                "installed": False,
                "path": ""
            }
        }
        with open(config.REGISTRY_FILE, "w") as f:
            json.dump(default_registry, f, indent=2)
        print(f"Created default model registry at {config.REGISTRY_FILE}")
    else:
        print("Registry already exists.")

    print("Initialization complete!")

@app.command()
def doctor():
    """Check system dependencies (ffmpeg, whisper.cpp, etc.)."""
    check_dependencies()

if __name__ == "__main__":
    app()


from audioai import models
app.add_typer(models.app, name="models")

# Map the transcribe command directly onto the main app
from audioai import transcribe
app.command("transcribe")(transcribe.transcribe)
