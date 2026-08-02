import logging
from backend.tts.interface import TextToSpeech

logger = logging.getLogger(__name__)

class MockTextToSpeech(TextToSpeech):
    """Mock TTS implementation for local development and offline testing."""

    def synthesize(self, text: str, lang_code: str = "en-IN") -> bytes:
        logger.info(f"[MockTTS] Synthesizing audio for text: '{text[:50]}...' ({lang_code})")
        # Return dummy audio payload header or encoded text byte marker
        return f"[AUDIO_WAV_SIMULATED: {text[:60]}]".encode("utf-8")
