import logging

logger = logging.getLogger(__name__)

# Fixed non-negotiable deterministic fallback responses (never LLM generated)
DETERMINISTIC_LOW_CONFIDENCE_FALLBACK = {
    "en": "I'm sorry, I am not sure I understood your question clearly. You can ask me about: 1) Your daily medicine and BP/Sugar schedule, 2) Follow-up visit reminders, 3) Salt and lifestyle tips for high blood pressure.",
    "hi": "माफ़ कीजिये, मैं आपका सवाल पूरी तरह से नहीं समझ पाया। आप मुझसे पूछ सकते हैं: 1) अपनी BP या शुगर की दवाई की जानकारी, 2) अगली जांच (Follow-up) की तारीख, 3) नमक और परहेज के नियम।"
}

DETERMINISTIC_OUT_OF_SCOPE_DECLINE = {
    "en": "I am a health care navigation assistant and I can only help with your blood pressure, diabetes, medication schedule, and follow-up guidance.",
    "hi": "मैं केवल आपके बीपी, शुगर, दवाई की समय सारणी और स्वास्थ्य परामर्श में मदद कर सकता हूँ। मैं इस सवाल का जवाब नहीं दे सकता।"
}

def get_deterministic_fallback(lang_code: str = "en") -> str:
    """Returns fixed low-confidence fallback text."""
    logger.info(f"[Fallback] Triggered deterministic low-confidence fallback (lang: {lang_code}).")
    if lang_code.startswith("hi"):
        return DETERMINISTIC_LOW_CONFIDENCE_FALLBACK["hi"]
    return DETERMINISTIC_LOW_CONFIDENCE_FALLBACK["en"]

def get_out_of_scope_decline(lang_code: str = "en") -> str:
    """Returns fixed out-of-scope decline text."""
    logger.info(f"[Fallback] Triggered deterministic out-of-scope decline (lang: {lang_code}).")
    if lang_code.startswith("hi"):
        return DETERMINISTIC_OUT_OF_SCOPE_DECLINE["hi"]
    return DETERMINISTIC_OUT_OF_SCOPE_DECLINE["en"]
