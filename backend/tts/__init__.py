from backend.tts.interface import TextToSpeech
from backend.tts.sarvam_tts import SarvamTextToSpeech
from backend.tts.google_tts import GoogleTextToSpeech
from backend.tts.bhashini_tts import BhashiniTextToSpeech
from backend.tts.mock_tts import MockTextToSpeech

def get_tts_provider(provider_name: str = "sarvam") -> TextToSpeech:
    """Factory function returning configured TTS provider."""
    provider_name = provider_name.lower()
    if provider_name == "sarvam":
        return SarvamTextToSpeech()
    elif provider_name == "google":
        return GoogleTextToSpeech()
    elif provider_name == "bhashini":
        return BhashiniTextToSpeech()
    else:
        return MockTextToSpeech()
