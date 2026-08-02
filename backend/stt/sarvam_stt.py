import os
import logging
import requests
from backend.stt.interface import SpeechToText
from backend.stt.mock_stt import MockSpeechToText

logger = logging.getLogger(__name__)

class SarvamSpeechToText(SpeechToText):
    """
    Sarvam AI (Saaras ASR) Provider Implementation.
    Sovereign Indian voice model optimized for regional Indian accents, code-switching, and rural audio.
    """

    def __init__(self):
        self.fallback = MockSpeechToText()
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.endpoint = "https://api.sarvam.ai/speech-to-text"
        if self.api_key:
            logger.info("[SarvamSTT] Successfully initialized Sarvam AI (Saaras ASR) provider.")

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> tuple[str, str]:
        if not self.api_key:
            logger.warning("[SarvamSTT] SARVAM_API_KEY missing. Falling back to MockSTT.")
            return self.fallback.transcribe(audio_bytes, mime_type)

        try:
            # Check if text input was passed directly in bytes
            try:
                decoded = audio_bytes.decode("utf-8").strip()
                if decoded and len(decoded) < 500 and not decoded.startswith("RIFF") and not decoded.startswith("\x00"):
                    lang = "hi-IN" if any(ord(c) > 127 for c in decoded) or any(k in decoded.lower() for k in ["mujhe", "dard", "dawai", "seene"]) else "en-IN"
                    logger.info(f"[SarvamSTT] Text string input processed: '{decoded}' ({lang})")
                    return (decoded, lang)
            except Exception:
                pass

            headers = {
                "api-subscription-key": self.api_key
            }
            files = {
                "file": ("audio.wav", audio_bytes, mime_type)
            }
            data = {
                "model": "saaras:v1",
                "language_code": "unknown",
                "with_diarization": "false"
            }

            response = requests.post(self.endpoint, headers=headers, files=files, data=data, timeout=12)
            if response.status_code == 200:
                res_data = response.json()
                transcript = res_data.get("transcript") or res_data.get("text", "")
                detected_lang = res_data.get("language_code", "hi-IN")
                logger.info(f"[SarvamSTT] Transcribed: '{transcript}' (Language: {detected_lang})")
                return (transcript, detected_lang)

            logger.warning(f"[SarvamSTT] Status {response.status_code}: {response.text[:100]}. Falling back.")
            return self.fallback.transcribe(audio_bytes, mime_type)
        except Exception as e:
            logger.error(f"[SarvamSTT] Error during API call: {e}. Executing graceful fallback.")
            return self.fallback.transcribe(audio_bytes, mime_type)
