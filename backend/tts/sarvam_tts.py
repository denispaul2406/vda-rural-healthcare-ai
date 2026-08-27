import os
import base64
import logging
import requests
from backend.tts.interface import TextToSpeech
from backend.tts.mock_tts import MockTextToSpeech

logger = logging.getLogger(__name__)

class SarvamTextToSpeech(TextToSpeech):
    """
    Sarvam AI (Bulbul TTS) Provider Implementation.
    Sovereign Indian voice model providing natural, empathetic voice synthesis for Indian languages.
    """

    def __init__(self):
        self.fallback = MockTextToSpeech()
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.endpoint = "https://api.sarvam.ai/text-to-speech"
        if self.api_key:
            logger.info("[SarvamTTS] Successfully initialized Sarvam AI (Bulbul TTS) provider.")

    def synthesize(self, text: str, lang_code: str = "en-IN") -> bytes:
        if not self.api_key:
            logger.warning("[SarvamTTS] SARVAM_API_KEY missing. Falling back to MockTTS.")
            return self.fallback.synthesize(text, lang_code)

        try:
            target_lang = "hi-IN" if (lang_code.startswith("hi") or any(ord(c) > 127 for c in text)) else "en-IN"
            
            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "inputs": [text[:500]], # Max length safety cap
                "target_language_code": target_lang,
                "speaker": "anushka",
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.5,
                "speech_sample_rate": 8000,
                "enable_preprocessing": True,
                "model": "bulbul:v1"
            }

            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=12)
            if response.status_code == 200:
                res_data = response.json()
                audios = res_data.get("audios", [])
                if audios:
                    audio_bytes = base64.b64decode(audios[0])
                    logger.info(f"[SarvamTTS] Synthesized {len(audio_bytes)} bytes of Indic audio.")
                    return audio_bytes

            logger.warning(f"[SarvamTTS] Status {response.status_code}: {response.text[:100]}. Falling back.")
            return self.fallback.synthesize(text, lang_code)
        except Exception as e:
            logger.error(f"[SarvamTTS] Error during API call: {e}. Executing graceful fallback.")
            return self.fallback.synthesize(text, lang_code)
