import os
import base64
import logging
import requests
from backend.stt.interface import SpeechToText
from backend.stt.mock_stt import MockSpeechToText

logger = logging.getLogger(__name__)

class BhashiniSpeechToText(SpeechToText):
    """Bhashini (ULCA API) ASR provider implementation for Indian language speech recognition."""

    def __init__(self):
        self.fallback = MockSpeechToText()
        self.api_key = os.getenv("BHASHINI_API_KEY")
        self.user_id = os.getenv("BHASHINI_USER_ID")
        self.pipeline_id = os.getenv("BHASHINI_PIPELINE_ID")
        self.endpoint = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> tuple[str, str]:
        if not self.api_key or not self.user_id:
            logger.warning("[BhashiniSTT] Credentials missing. Falling back to MockSTT.")
            return self.fallback.transcribe(audio_bytes, mime_type)

        try:
            encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "asr",
                        "config": {
                            "language": {"sourceLanguage": "hi"},
                            "serviceId": "ai4bharat/conformer-hi-gpu--t4",
                            "audioFormat": "wav",
                            "samplingRate": 16000
                        }
                    }
                ],
                "inputData": {
                    "audio": [{"audioContent": encoded_audio}]
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
                transcript = res_data["pipelineResponse"][0]["output"][0]["source"]
                logger.info(f"[BhashiniSTT] Transcribed: '{transcript}'")
                return (transcript, "hi-IN")

            logger.warning(f"[BhashiniSTT] Status code {response.status_code}. Falling back.")
            return self.fallback.transcribe(audio_bytes, mime_type)
        except Exception as e:
            logger.error(f"[BhashiniSTT] Error during request: {e}. Executing graceful fallback.")
            return self.fallback.transcribe(audio_bytes, mime_type)
