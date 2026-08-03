import os
import logging
from backend.stt.interface import SpeechToText
from backend.stt.mock_stt import MockSpeechToText

logger = logging.getLogger(__name__)

class GoogleSpeechToText(SpeechToText):
    """Google Cloud Speech-to-Text provider implementation."""

    def __init__(self):
        self.fallback = MockSpeechToText()
        self.client = None
        try:
            from google.cloud import speech
            from google.oauth2 import service_account
            self.speech = speech
            
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path and os.path.exists(cred_path):
                abs_path = os.path.abspath(cred_path)
                self.client = speech.SpeechClient.from_service_account_file(abs_path)
                logger.info(f"[GoogleSTT] Initialized Google SpeechClient with service account: {abs_path}")
            else:
                self.client = speech.SpeechClient()
                logger.info("[GoogleSTT] Initialized Google SpeechClient with default credentials.")
        except Exception as e:
            logger.warning(f"[GoogleSTT] Could not initialize Google Cloud Speech client ({e}). Falling back to MockSTT.")

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> tuple[str, str]:
        if not self.client:
            return self.fallback.transcribe(audio_bytes, mime_type)

        try:
            encoding_map = {
                "audio/wav": self.speech.RecognitionConfig.AudioEncoding.LINEAR16,
                "audio/webm": self.speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            }
            encoding = encoding_map.get(mime_type, self.speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED)

            audio = self.speech.RecognitionAudio(content=audio_bytes)
            config = self.speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=16000,
                language_code="hi-IN",
                alternative_language_codes=["en-IN", "ta-IN", "te-IN"],
                enable_automatic_language_identification=True,
            )

            response = self.client.recognize(config=config, audio=audio)
            for result in response.results:
                transcript = result.alternatives[0].transcript
                lang = result.language_code or "hi-IN"
                logger.info(f"[GoogleSTT] Transcribed: '{transcript}' ({lang})")
                return (transcript, lang)

            return self.fallback.transcribe(audio_bytes, mime_type)
        except Exception as e:
            logger.error(f"[GoogleSTT] API call failed: {e}. Executing graceful fallback.")
            return self.fallback.transcribe(audio_bytes, mime_type)
