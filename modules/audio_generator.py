"""
MODULE 2: Audio & Timestamp Module
Handles TTS generation using edge-tts and local Whisper transcription.
"""
import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Optional
import edge_tts
import whisper

from models import AudioMetadata, WhisperTimestamp
from exceptions import AudioGenerationError, TranscriptionError
from config import (
    TTS_VOICE, TTS_RATE, WHISPER_MODEL, AUDIO_SAMPLE_RATE,
    TEMP_DIR, MAX_RETRIES, RETRY_DELAY
)
import time


logger = logging.getLogger(__name__)


class AudioGenerator:
    """Handles TTS generation and audio processing."""
    
    def __init__(self, voice: str = TTS_VOICE, rate: str = TTS_RATE):
        """
        Initialize the audio generator.
        
        Args:
            voice: Edge TTS voice identifier
            rate: Speech rate (+/-X%)
        """
        self.voice = voice
        self.rate = rate
        logger.info(f"AudioGenerator initialized with voice: {voice}, rate: {rate}")
    
    async def generate_audio_async(self, script_text: str, output_path: Optional[Path] = None) -> Path:
        """
        Generate audio from script text asynchronously using edge-tts.
        
        Args:
            script_text: Script text to convert to speech
            output_path: Optional output file path (auto-generated if not provided)
        
        Returns:
            Path to generated MP3 file
        
        Raises:
            AudioGenerationError: If TTS generation fails
        """
        if not output_path:
            output_path = TEMP_DIR / f"audio_{int(time.time())}.mp3"
        
        output_path = Path(output_path)
        
        try:
            logger.info(f"Generating audio to: {output_path}")
            
            # Create communicate instance
            communicate = edge_tts.Communicate(
                text=script_text,
                voice=self.voice,
                rate=self.rate
            )
            
            # Save audio file
            await communicate.save(str(output_path))
            
            if not output_path.exists():
                raise AudioGenerationError(f"Audio file not created at {output_path}")
            
            file_size = output_path.stat().st_size
            logger.info(f"Audio generated successfully: {file_size} bytes")
            
            return output_path
            
        except Exception as e:
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup audio file: {cleanup_error}")
            
            raise AudioGenerationError(f"TTS generation failed: {str(e)}")
    
    def generate_audio(self, script_text: str, output_path: Optional[Path] = None) -> Path:
        """
        Synchronous wrapper for generate_audio_async.
        
        Args:
            script_text: Script text to convert to speech
            output_path: Optional output file path
        
        Returns:
            Path to generated MP3 file
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.generate_audio_async(script_text, output_path))
        finally:
            loop.close()


class WhisperTranscriber:
    """Handles Whisper transcription and timestamp extraction."""
    
    def __init__(self, model_name: str = WHISPER_MODEL):
        """
        Initialize Whisper transcriber.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None
        logger.info(f"WhisperTranscriber initialized with model: {model_name}")
    
    def _load_model(self) -> None:
        """Load Whisper model (lazy loading)."""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded successfully")
    
    def transcribe(self, audio_path: Path, language: str = "en") -> AudioMetadata:
        """
        Transcribe audio file and extract word-level timestamps.
        
        Args:
            audio_path: Path to audio file
            language: ISO-639-1 language code (default: English)
        
        Returns:
            AudioMetadata with word-level timestamps
        
        Raises:
            TranscriptionError: If transcription fails
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")
        
        try:
            logger.info(f"Starting transcription: {audio_path}")
            
            # Load model if needed
            self._load_model()
            
            # Transcribe with verbose output for timestamps
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                verbose=False,
                word_level=True
            )
            
            # Extract audio duration
            duration = self._get_audio_duration(audio_path)
            
            # Parse timestamps from Whisper output
            timestamps = self._extract_timestamps(result)
            
            logger.info(f"Transcription complete: {len(timestamps)} words detected")
            
            # Create metadata
            metadata = AudioMetadata(
                file_path=str(audio_path),
                duration=duration,
                sample_rate=AUDIO_SAMPLE_RATE,
                timestamps=timestamps
            )
            
            return metadata
            
        except Exception as e:
            raise TranscriptionError(f"Whisper transcription failed: {str(e)}")
    
    def _extract_timestamps(self, whisper_result: dict) -> List[WhisperTimestamp]:
        """
        Extract word-level timestamps from Whisper result.
        
        Args:
            whisper_result: Raw Whisper transcription result
        
        Returns:
            List of WhisperTimestamp objects
        """
        timestamps = []
        
        try:
            # Iterate through segments
            for segment in whisper_result.get("segments", []):
                words = segment.get("words", [])
                
                # If word-level data available, use it
                if words:
                    for word_data in words:
                        timestamps.append(
                            WhisperTimestamp(
                                word=word_data.get("word", "").strip(),
                                start=float(word_data.get("start", 0)),
                                end=float(word_data.get("end", 0))
                            )
                        )
                
                # Fallback: create word-level from segment if needed
                elif segment.get("text"):
                    text = segment["text"].strip()
                    seg_start = segment.get("start", 0)
                    seg_end = segment.get("end", 0)
                    
                    # Simple word split with linear time distribution
                    words_list = text.split()
                    if words_list:
                        time_per_word = (seg_end - seg_start) / len(words_list)
                        
                        for i, word in enumerate(words_list):
                            word_start = seg_start + (i * time_per_word)
                            word_end = word_start + time_per_word
                            
                            timestamps.append(
                                WhisperTimestamp(
                                    word=word,
                                    start=word_start,
                                    end=word_end
                                )
                            )
            
            logger.debug(f"Extracted {len(timestamps)} word timestamps")
            return timestamps
            
        except Exception as e:
            logger.error(f"Error extracting timestamps: {str(e)}")
            return []
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """
        Get audio file duration using ffprobe.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Duration in seconds
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1:noprint_wrappers=1",
                    str(audio_path)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            
        except Exception as e:
            logger.warning(f"Could not get audio duration via ffprobe: {str(e)}")
        
        # Fallback: estimate from timestamps or return 0
        return 0.0


# Convenience functions
def generate_audio(script_text: str, output_path: Optional[Path] = None) -> Path:
    """
    Convenience function to generate audio from script.
    
    Args:
        script_text: Script text
        output_path: Optional output path
    
    Returns:
        Path to audio file
    """
    generator = AudioGenerator()
    return generator.generate_audio(script_text, output_path)


def transcribe_audio(audio_path: Path, language: str = "en") -> AudioMetadata:
    """
    Convenience function to transcribe audio and get timestamps.
    
    Args:
        audio_path: Path to audio file
        language: Language code
    
    Returns:
        AudioMetadata with timestamps
    """
    transcriber = WhisperTranscriber()
    return transcriber.transcribe(audio_path, language)
