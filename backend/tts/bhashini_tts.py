import os
import base64
import logging
import requests
from backend.tts.interface import TextToSpeech
from backend.tts.mock_tts import MockTextToSpeech

logger = logging.getLogger(__name__)

class BhashiniTextToSpeech(TextToSpeech):
    """Bhashini (ULCA API) TTS provider implementation for Indian language speech synthesis."""

    def __init__(self):
        self.fallback = MockTextToSpeech()
        self.api_key = os.getenv("BHASHINI_API_KEY")
        self.user_id = os.getenv("BHASHINI_USER_ID")
        self.endpoint = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    def synthesize(self, text: str, lang_code: str = "hi-IN") -> bytes:
        if not self.api_key or not self.user_id:
            logger.warning("[BhashiniTTS] Credentials missing. Falling back to MockTTS.")
            return self.fallback.synthesize(text, lang_code)

        try:
            lang_short = "hi" if "hi" in lang_code else "en"
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "tts",
                        "config": {
                            "language": {"sourceLanguage": lang_short},
                            "serviceId": "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4",
                            "gender": "female"
                        }
                    }
                ],
                "inputData": {
                    "input": [{"source": text}]
                }
            }
            headers = {
                "Authorization": self.api_key,
                "userID": self.user_id,
                "Content-Type": "application/json"
            }

            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                audio_b64 = res_data["pipelineResponse"][0]["audio"][0]["audioContent"]
                audio_bytes = base64.b64decode(audio_b64)
                logger.info(f"[BhashiniTTS] Synthesized {len(audio_bytes)} bytes of audio.")
                return audio_bytes

            return self.fallback.synthesize(text, lang_code)
        except Exception as e:
            logger.error(f"[BhashiniTTS] Error: {e}. Executing graceful fallback.")
            return self.fallback.synthesize(text, lang_code)
