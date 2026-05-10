from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from ..schemas import Transcript


class STTBackend(ABC):
    name: str

    @abstractmethod
    def transcribe(
        self,
        audio_path: Path,
        model_path: Path,
        language: Optional[str] = None,
        keep_temp: bool = False,
    ) -> Transcript:
        """Transcribe an audio file and return a Transcript object."""
        pass
