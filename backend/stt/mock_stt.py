import logging
from backend.stt.interface import SpeechToText

logger = logging.getLogger(__name__)

class MockSpeechToText(SpeechToText):
    """Mock STT implementation for local development, fallback, and automated testing."""

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> tuple[str, str]:
        """
        Mock transcription. If audio_bytes is encoded string, decode it.
        Otherwise return a default test utterance.
        """
        try:
            # Check if text was passed directly for demo/testing convenience
            decoded_text = audio_bytes.decode("utf-8").strip()
            if decoded_text:
                lang = "hi-IN" if any(ord(char) > 127 for char in decoded_text) or "mujhe" in decoded_text.lower() or "dard" in decoded_text.lower() else "en-IN"
                logger.info(f"[MockSTT] Transcribed text string input: '{decoded_text}' ({lang})")
                return (decoded_text, lang)
        except Exception:
            pass

        logger.info("[MockSTT] Audio binary input processed.")
        return ("What is my daily BP medicine schedule?", "en-IN")
