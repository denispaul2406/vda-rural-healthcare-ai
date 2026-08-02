import re
import logging
from dataclasses import dataclass
from typing import Optional
from backend.safety_gate.alert_hook import notify_clinician

logger = logging.getLogger(__name__)

@dataclass
class GateResult:
    escalate: bool
    reason: Optional[str] = None
    response_text: Optional[str] = None

# Escalation fixed emergency text responses (Never LLM generated)
EMERGENCY_ESCALATION_TEXT = {
    "en": "EMERGENCY ALERT: Your symptoms may require urgent medical attention. Please go immediately to the nearest hospital or emergency center, or call 108/102 for an ambulance. A clinician has been notified of your request.",
    "hi": "आपातकालीन चेतावनी: आपके लक्षण गंभीर हो सकते हैं। कृपया तुरंत नजदीकी अस्पताल या आपातकालीन केंद्र (CHC/PHC) जाएं या 108/102 पर एम्बुलेंस को कॉल करें। स्वास्थ्य कार्यकर्ता को आपकी स्थिति की सूचना भेज दी गई है।"
}

# Comprehensive Red-flag symptom regex patterns across English, Hinglish (Latin), and Pure Devanagari Hindi
RED_FLAG_PATTERNS = [
    # Cardiac Emergency (English, Hinglish, Devanagari)
    (r"\b(chest\s*pain|chest\s*heaviness|pressure\s*on\s*chest|left\s*arm|neck\s*pain)\b", "cardiac_emergency"),
    (r"(seene?|chhat[ii]|dil).*?(dard|bhari|pressure|tez)", "cardiac_emergency"),
    (r"(सीने|छाती|दिल|हृदय).*?(दर्द|भारी|दबाव|तेज|पसीना|घबराहट)", "cardiac_emergency"),
    (r"(सीने\s*में\s*दर्द|छाती\s*में\s*दर्द|दिल\s*में\s*दर्द)", "cardiac_emergency"),

    # Respiratory Emergency
    (r"\b(short(ness)?\s*of\s*breath|breathlessness|cannot\s*breathe|difficulty\s*breathing)\b", "respiratory_emergency"),
    (r"saans.*?(phool|dikkat|takleef|nahi|short)", "respiratory_emergency"),
    (r"(सांस|साँस).*?(फूल|दिक्कत|तकलीफ|नहीं|चढ़)", "respiratory_emergency"),

    # Neurological / Stroke Emergency (FAST stroke variations)
    (r"\b(face.*droop(ing)?|drooping|speech\s*(is\s*)?slurred|slurred\s*speech|one\s*side.*(weakness|numbness)|numbness)\b", "stroke_emergency"),
    (r"(ek\s*(taraf|haath|paav)|haath|pair).*?(sunn|tedha|dheele|weak|bol\s*nahi)", "stroke_emergency"),
    (r"(हाथ\s*पैर\s*ढीले|मुंह\s*टेढ़ा|सुन्न|लकवा|एक\s*तरफ|बोल\s*नहीं)", "stroke_emergency"),

    # Syncope / Loss of Consciousness
    (r"\b(faint(ed|ing)?|pass(ed)?\s*out|behosh|befeesh|unconscious|collapsed|not\s*responding)\b", "syncope_emergency"),
    (r"(बेहोश|बेहोशी|चक्कर\s*आकर|गिर\s*गया|अचेत)", "syncope_emergency"),

    # Uncontrolled Bleeding / Hemorrhage
    (r"\b(vomit(ing)?\s*blood|severe\s*bleeding)\b", "hemorrhage_emergency"),
    (r"khoon.*(beh|nikal|ulti)", "hemorrhage_emergency"),
    (r"(खून).*?(बह|निकल|उल्टी)", "hemorrhage_emergency"),

    # Hypertensive / Diabetic Crisis
    (r"\b((bp|blood\s*pressure).*?(1[89]\d|2\d\d)|sugar\s*(300|[3-9]\d\d)|hypertensive\s*crisis)\b", "metabolic_crisis"),

    # Emergency Palpitations
    (r"dil.*(dhak|dard|tez)", "cardiac_emergency"),
    (r"धड़कन.*(तेज|दर्द)", "cardiac_emergency")
]

class SafetyGate:
    """
    Deterministic, Rule-Based Safety Gate.
    Runs FIRST on every user input prior to LLM/RAG processing.
    Ensures zero LLM overrides for medical emergencies.
    """

    def __init__(self):
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), reason)
            for pattern, reason in RED_FLAG_PATTERNS
        ]

    def check(self, utterance: str, session_id: str = "default_session", lang_code: str = "en") -> GateResult:
        """
        Evaluates input text against red-flag clinical patterns.
        """
        # Exclusion exception: Cough with cold without acute crushing pressure
        if "coughing lightly" in utterance.lower() or "coughing with cold" in utterance.lower():
            if not any(k in utterance.lower() for k in ["severe", "crushing", "spreading", "sweating"]):
                logger.info(f"[SafetyGate] Excluded mild cold/cough utterance from cardiac escalation: '{utterance}'")
                return GateResult(escalate=False)

        clean_text = utterance.strip()
        for pattern, reason in self.compiled_patterns:
            if pattern.search(clean_text):
                logger.critical(f"⚠️ [SAFETY GATE TRIGGERED] Matched Red-Flag Pattern: '{reason}' in utterance: '{utterance}'")
                
                # Dispatch alert to clinician notification hook
                notify_clinician(session_id=session_id, reason=reason, utterance=utterance)
                
                lang_key = "hi" if lang_code.startswith("hi") or any(ord(c) > 127 for c in clean_text) else "en"
                response_text = EMERGENCY_ESCALATION_TEXT[lang_key]

                return GateResult(
                    escalate=True,
                    reason=reason,
                    response_text=response_text
                )

        logger.info(f"[SafetyGate] Input passed safety check: '{clean_text[:40]}...'")
        return GateResult(escalate=False)
