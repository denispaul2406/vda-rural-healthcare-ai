import logging
from backend.stt.sarvam_stt import SarvamSpeechToText
from backend.tts.sarvam_tts import SarvamTextToSpeech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sarvam_stt_failover():
    logger.info("=== STRESS TEST 1: Sarvam STT Invalid Key / Network Error Failover ===")
    sarvam_stt = SarvamSpeechToText()
    sarvam_stt.api_key = "sk_invalid_test_key_failover_check" # Force invalid key to simulate API 401/403/500 failure
    
    dummy_audio = b"Hello, this is a test audio byte"
    text, lang = sarvam_stt.transcribe(dummy_audio, mime_type="audio/wav")
    logger.info(f"SUCCESS: Failover caught error gracefully! Returned fallback transcript: '{text}' ({lang})\n")
    assert text is not None

def test_sarvam_tts_failover():
    logger.info("=== STRESS TEST 2: Sarvam TTS Network Error / Timeout Failover ===")
    sarvam_tts = SarvamTextToSpeech()
    sarvam_tts.api_key = "sk_invalid_test_key_failover_check" # Force invalid key
    
    audio_bytes = sarvam_tts.synthesize("Emergency alert test", lang_code="en-IN")
    logger.info(f"SUCCESS: Failover caught error gracefully! Returned fallback audio bytes: {len(audio_bytes)} bytes\n")
    assert len(audio_bytes) > 0

if __name__ == "__main__":
    test_sarvam_stt_failover()
    test_sarvam_tts_failover()
    print("=======================================================")
    print(" ALL SARVAM FAILOVER STRESS TESTS PASSED SUCCESSFULLY! ")
    print("=======================================================")
