"""
Data models and type definitions for the Autonomous Faceless Content Engine.
"""
from typing import Optional, List
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field
import json


class ScriptData(BaseModel):
    """Generated script data model."""
    title: str = Field(..., description="Video title (max 100 chars)")
    description: str = Field(..., description="Video description for YouTube")
    script_text: str = Field(..., description="Main script content (150 words target)")
    keywords: List[str] = Field(..., description="SEO keywords and video search terms")
    hook: Optional[str] = Field(None, description="3-second hook at video start")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Amazing AI Facts",
                "description": "Learn incredible facts about artificial intelligence",
                "script_text": "Today we're exploring...",
                "keywords": ["AI", "facts", "technology"],
                "hook": "Did you know?"
            }
        }


class WhisperTimestamp(BaseModel):
    """Word-level timestamp from Whisper transcription."""
    word: str = Field(..., description="Spoken word")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")


class AudioMetadata(BaseModel):
    """Audio file metadata."""
    file_path: str = Field(..., description="Path to audio file")
    duration: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(..., description="Sample rate in Hz")
    timestamps: List[WhisperTimestamp] = Field(..., description="Word-level timestamps")


@dataclass
class VideoClip:
    """Video clip information from Pexels."""
    id: int
    url: str
    file_path: Optional[str] = None
    duration: float = 0.0
    width: int = 0
    height: int = 0
    
    def to_dict(self):
        return asdict(self)


@dataclass
class TextOverlay:
    """Text overlay configuration for video composition."""
    text: str
    start_time: float
    end_time: float
    font_size: int = 60
    color: str = "white"
    font: str = "Arial"
    position: tuple = (0.5, 0.7)  # (x, y) normalized to (0-1)
    
    def to_dict(self):
        return asdict(self)


class PublishMetadata(BaseModel):
    """Metadata for YouTube publishing."""
    title: str = Field(..., description="Video title")
    description: str = Field(..., description="Video description")
    tags: List[str] = Field(default_factory=list, description="Video tags")
    category_id: str = Field(default="27", description="YouTube category ID")
    privacy_status: str = Field(default="private", description="Video privacy status")
    thumbnail_path: Optional[str] = Field(None, description="Custom thumbnail path")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Amazing AI Facts",
                "description": "Learn incredible facts about artificial intelligence",
                "tags": ["AI", "facts", "technology"],
                "category_id": "27",
                "privacy_status": "unlisted",
                "thumbnail_path": None
            }
        }
