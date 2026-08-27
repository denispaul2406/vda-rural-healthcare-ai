import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Primary Intent Categories aligned 100% with official Medtronic Labs Brief
INTENT_UC1 = "UC1_NCD_ADHERENCE"          # Medication, Follow-up, Screening Nudges, ICMR/WHO Diet Guidance
INTENT_UC2 = "UC2_SCHEME_ENTITLEMENT"     # Ayushman Bharat, PM-JAY Eligibility, Free Treatment Awareness
INTENT_UC3 = "UC3_FACILITY_LINKAGE"       # Nearest PHC / Sub-Centre / CHC Public Facility Linkage
INTENT_UC4 = "UC4_TELECONSULT_TRIAGE"     # Teleconsultation Portal & Safety Gate Escalation
INTENT_OUT_OF_SCOPE = "OUT_OF_SCOPE"

# Intent Keywords for UC1 (NCD Care Adherence & Lifestyle Protocols)
UC1_KEYWORDS = [
    "medicine", "medicines", "dawai", "dawa", "pill", "pills", "tablet", "tablets", "dose", "timing",
    "schedule", "missed", "bhool", "kab khayein", "kab lena", "checkup", "follow up", "follow-up",
    "prescription", "salt", "namak", "diet", "food", "khana", "walk", "walking", "tahlna", "exercise",
    "screening", "blood pressure", "bp", "hypertension", "sugar", "diabetes", "goli"
]

# Intent Keywords for UC2 (Scheme Entitlement Check - PM-JAY & Ayushman Bharat)
UC2_KEYWORDS = [
    "pmjay", "pm-jay", "ayushman", "ayushman bharat", "card", "yojana", "entitlement",
    "free treatment", "free medicine", "insurance", "bima", "eligible", "eligibility",
    "enrolment", "register", "5 lakh", "lakh", "government scheme", "sarkari yojana", "golden card"
]

# Intent Keywords for UC3 (Public Health Service Linkage)
UC3_KEYWORDS = [
    "hospital", "hospitals", "phc", "hwc", "sub centre", "sub-centre", "chc", "facility", "nearest",
    "paas ka hospital", "kahan jayein", "location", "address", "center", "clinic", "doddaballapura",
    "nelamangala", "hoskote", "bengaluru", "where is", "where"
]

# Intent Keywords for UC4 (Teleconsultation & Triage)
UC4_KEYWORDS = [
    "teleconsultation", "doctor call", "esanjeevani", "online doctor", "telemedicine",
    "doctor talk", "consultation", "triage", "doctor"
]

# Out of scope topics that must be refused cleanly
OUT_OF_SCOPE_TOPICS = [
    "weather", "mausam", "cricket", "ipl", "match", "score", "movie", "cinema", "song",
    "politician", "election", "vote", "recipe", "biryani", "car", "motorbike", "engine", "stock", "crypto"
]

class IntentClassifier:
    """
    Deterministic & Keyword-Weighted Intent Classifier.
    Supports all 4 Use Cases specified in official Medtronic Labs Brief:
      - UC1: NCD Care Adherence & Health Guidance
      - UC2: Scheme Entitlement Check (PM-JAY / Ayushman Bharat)
      - UC3: Public Health Facility Linkage
      - UC4: Teleconsultation & Triage
    Enforces strict low-confidence thresholding (default 0.75).
    """

    def __init__(self, confidence_threshold: float = 0.75):
        self.threshold = confidence_threshold

    def classify(self, text: str) -> Tuple[str, float]:
        clean_text = text.lower().strip()

        # Check explicit out of scope triggers
        for oos_term in OUT_OF_SCOPE_TOPICS:
            if re.search(r"\b" + re.escape(oos_term) + r"\b", clean_text):
                logger.info(f"[IntentClassifier] Explicit Out-of-Scope match: '{oos_term}' in '{text}'")
                return (INTENT_OUT_OF_SCOPE, 0.90)

        # Count keyword occurrences across all 4 use cases
        uc1_score = sum(1 for k in UC1_KEYWORDS if re.search(r"\b" + re.escape(k) + r"\b", clean_text))
        uc2_score = sum(1 for k in UC2_KEYWORDS if re.search(r"\b" + re.escape(k) + r"\b", clean_text))
        uc3_score = sum(1 for k in UC3_KEYWORDS if re.search(r"\b" + re.escape(k) + r"\b", clean_text))
        uc4_score = sum(1 for k in UC4_KEYWORDS if re.search(r"\b" + re.escape(k) + r"\b", clean_text))

        scores = [
            (INTENT_UC2, uc2_score),
            (INTENT_UC3, uc3_score),
            (INTENT_UC4, uc4_score),
            (INTENT_UC1, uc1_score)
        ]
        best_intent, best_score = max(scores, key=lambda x: x[1])

        if best_score > 0:
            confidence = min(0.75 + (best_score * 0.10), 0.98)
            logger.info(f"[IntentClassifier] Text: '{text}' -> Intent: {best_intent} (Confidence: {confidence:.2f})")
            return (best_intent, confidence)

        # Domain Heuristics for implicit health queries
        if any(w in clean_text for w in ["bp", "sugar", "hypertension", "diabetes", "blood pressure", "medicine", "dawai"]):
            if any(w in clean_text for w in ["card", "yojana", "free", "pmjay", "ayushman", "scheme", "5 lakh"]):
                return (INTENT_UC2, 0.85)
            if any(w in clean_text for w in ["hospital", "phc", "hwc", "kahan", "near", "where", "location"]):
                return (INTENT_UC3, 0.85)
            logger.info(f"[IntentClassifier] Implicit UC1 match for text: '{text}'")
            return (INTENT_UC1, 0.85)

        # Low-confidence fallback route
        logger.info(f"[IntentClassifier] Low confidence unmatched query: '{text}'")
        return (INTENT_OUT_OF_SCOPE, 0.30)
