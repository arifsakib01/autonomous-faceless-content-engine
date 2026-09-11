"""
Custom exception classes for the Autonomous Faceless Content Engine.
"""


class ContentEngineError(Exception):
    """Base exception for all content engine errors."""
    pass


class ScriptGenerationError(ContentEngineError):
    """Raised when script generation fails."""
    pass


class AudioGenerationError(ContentEngineError):
    """Raised when TTS or audio processing fails."""
    pass


class TranscriptionError(ContentEngineError):
    """Raised when Whisper transcription fails."""
    pass


class VideoAssetError(ContentEngineError):
    """Raised when video asset fetching fails."""
    pass


class VideoCompositionError(ContentEngineError):
    """Raised when video composition/rendering fails."""
    pass


class YouTubePublishError(ContentEngineError):
    """Raised when YouTube publishing fails."""
    pass


class ResourceCleanupError(ContentEngineError):
    """Raised when resource cleanup fails."""
    pass


class AuthenticationError(ContentEngineError):
    """Raised when authentication/authorization fails."""
    pass


class ConfigurationError(ContentEngineError):
    """Raised when configuration is invalid."""
    pass
