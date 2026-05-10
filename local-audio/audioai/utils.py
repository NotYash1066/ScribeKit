import subprocess
import shutil


def run_command(
    command: list[str], capture_output: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command safely."""
    try:
        result = subprocess.run(
            command, capture_output=capture_output, text=True, check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(command)}")
        if capture_output:
            print(f"Error output:\n{e.stderr}")
        raise


def is_tool_installed(name: str) -> bool:
    """Check whether a tool is available on the system PATH."""
    return shutil.which(name) is not None
