import os
import logging
from backend.tts.interface import TextToSpeech
from backend.tts.mock_tts import MockTextToSpeech

logger = logging.getLogger(__name__)

class GoogleTextToSpeech(TextToSpeech):
    """Google Cloud Text-to-Speech provider implementation."""

    def __init__(self):
        self.fallback = MockTextToSpeech()
        self.client = None
        try:
            from google.cloud import texttospeech
            from google.oauth2 import service_account
            self.tts = texttospeech
            
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path and os.path.exists(cred_path):
                abs_path = os.path.abspath(cred_path)
                credentials = service_account.Credentials.from_service_account_file(abs_path)
                self.client = texttospeech.TextToSpeechClient(credentials=credentials)
                logger.info(f"[GoogleTTS] Initialized Google TextToSpeechClient with service account: {abs_path}")
            else:
                self.client = texttospeech.TextToSpeechClient()
                logger.info("[GoogleTTS] Initialized Google TextToSpeechClient with default credentials.")
        except Exception as e:
            logger.warning(f"[GoogleTTS] Could not initialize Google Cloud TTS client ({e}). Falling back to MockTTS.")

    def synthesize(self, text: str, lang_code: str = "en-IN") -> bytes:
        if not self.client:
            return self.fallback.synthesize(text, lang_code)

        try:
            synthesis_input = self.tts.SynthesisInput(text=text)
            voice = self.tts.VoiceSelectionParams(
                language_code=lang_code,
                ssml_gender=self.tts.SsmlVoiceGender.FEMALE
            )
            audio_config = self.tts.AudioConfig(
                audio_encoding=self.tts.AudioEncoding.MP3
            )

            response = self.client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            logger.info(f"[GoogleTTS] Synthesized {len(response.audio_content)} bytes of audio.")
            return response.audio_content
        except Exception as e:
            logger.error(f"[GoogleTTS] API call failed: {e}. Executing graceful fallback.")
            return self.fallback.synthesize(text, lang_code)
