"""
Configuration and constants for the Autonomous Faceless Content Engine.
"""
import os
from pathlib import Path
from typing import Final

# ============================================================================
# ENVIRONMENT VARIABLES & API KEYS
# ============================================================================
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")
YOUTUBE_CREDENTIALS_PATH: str = os.getenv("YOUTUBE_CREDENTIALS_PATH", "./credentials.json")
YOUTUBE_TOKEN_PATH: str = os.getenv("YOUTUBE_TOKEN_PATH", "./token.json")

# LLM Configuration for script generation
LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")

# ============================================================================
# VIDEO SPECIFICATIONS
# ============================================================================
VIDEO_WIDTH: Final[int] = 1080
VIDEO_HEIGHT: Final[int] = 1920
VIDEO_FPS: Final[int] = 30
VIDEO_RESOLUTION: Final[tuple] = (VIDEO_WIDTH, VIDEO_HEIGHT)

# Target duration for content (in seconds) - adjustable per topic
TARGET_DURATION: Final[int] = 30

# ============================================================================
# SCRIPT GENERATION CONFIG
# ============================================================================
SCRIPT_WORD_COUNT: Final[int] = 150
HOOK_DURATION: Final[float] = 3.0  # seconds
SCRIPT_TEMPERATURE: Final[float] = 0.7

# ============================================================================
# AUDIO & TTS CONFIG
# ============================================================================
TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-AriaNeural")
TTS_RATE: str = os.getenv("TTS_RATE", "+0%")
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
AUDIO_SAMPLE_RATE: Final[int] = 16000

# ============================================================================
# VIDEO ASSET FETCHER CONFIG
# ============================================================================
PEXELS_VIDEO_COUNT: Final[int] = 4
PEXELS_MIN_DURATION: Final[int] = 3
PEXELS_VIDEO_QUALITY: str = "hd"  # 'sd' or 'hd'
PEXELS_SEARCH_LIMIT: Final[int] = 80

# ============================================================================
# YOUTUBE PUBLISHER CONFIG
# ============================================================================
YOUTUBE_PRIVACY_STATUS: str = os.getenv("YOUTUBE_PRIVACY_STATUS", "private")
YOUTUBE_CATEGORY_ID: str = os.getenv("YOUTUBE_CATEGORY_ID", "27")  # 27 = Education
YOUTUBE_AFFILIATE_LINK: str = os.getenv("YOUTUBE_AFFILIATE_LINK", "")
YOUTUBE_MAX_RETRIES: Final[int] = 3

# ============================================================================
# FILE & DIRECTORY MANAGEMENT
# ============================================================================
PROJECT_ROOT: Path = Path(__file__).parent
TEMP_DIR: Path = PROJECT_ROOT / "temp"
OUTPUT_DIR: Path = PROJECT_ROOT / "output"
LOGS_DIR: Path = PROJECT_ROOT / "logs"

# Ensure directories exist
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ============================================================================
# RESOURCE CLEANUP CONFIG
# ============================================================================
CLEANUP_ON_ERROR: bool = True
MAX_RETRIES: Final[int] = 3
RETRY_DELAY: Final[float] = 2.0  # seconds

# ============================================================================
# LOGGING CONFIG
# ============================================================================
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
