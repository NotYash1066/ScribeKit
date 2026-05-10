from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None


class Transcript(BaseModel):
    source_file: str
    created_at: datetime
    backend: str
    model: str
    language: str
    duration_sec: float
    segments: List[TranscriptSegment]


class TranscriptMeta(BaseModel):
    source_file: str
    normalized_audio: str
    file_size_bytes: int
    duration_sec: float
    backend: str
    model: str
    status: str
