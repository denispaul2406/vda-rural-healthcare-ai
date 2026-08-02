from backend.stt.interface import SpeechToText
from backend.stt.sarvam_stt import SarvamSpeechToText
from backend.stt.google_stt import GoogleSpeechToText
from backend.stt.bhashini_stt import BhashiniSpeechToText
from backend.stt.mock_stt import MockSpeechToText

def get_stt_provider(provider_name: str = "sarvam") -> SpeechToText:
    """Factory function returning the configured STT provider."""
    provider_name = provider_name.lower()
    if provider_name == "sarvam":
        return SarvamSpeechToText()
    elif provider_name == "google":
        return GoogleSpeechToText()
    elif provider_name == "bhashini":
        return BhashiniSpeechToText()
    else:
        return MockSpeechToText()
