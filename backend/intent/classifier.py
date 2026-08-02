import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Primary Intent Categories
INTENT_UC1 = "UC1_NCD_ADHERENCE"
INTENT_UC2 = "UC2_LIFESTYLE_COACHING"
INTENT_UC3 = "UC3_DOCTOR_DISPATCH"
INTENT_UC4 = "UC4_COMMUNITY_WORKFLOW"
INTENT_OUT_OF_SCOPE = "OUT_OF_SCOPE"

# Comprehensive Intent Keywords for UC1 (Medication & Follow-Up)
UC1_KEYWORDS = [
    "medicine", "dawai", "dawa", "pill", "tablet", "dose", "timing", "schedule", "missed",
    "bhool", "kab khayein", "kab lena", "checkup", "hospital", "phc", "hwc", "sub centre",
    "doctor", "anm", "asha", "follow up", "follow-up", "prescription", "refill"
]

# Comprehensive Intent Keywords for UC2 (Lifestyle & Diet Guidance)
UC2_KEYWORDS = [
    "salt", "namak", "diet", "food", "khana", "kya khayein", "kya na khayein", "rice", "chawal",
    "walk", "walking", "tahlna", "exercise", "vyayam", "physical activity", "tobacco", "tambaku",
    "gutka", "khaini", "bidi", "smoking", "alcohol", "sharab", "weight", "wazan", "stress", "sleep"
]

# Out of scope topics that must be refused cleanly
OUT_OF_SCOPE_TOPICS = [
    "weather", "mausam", "cricket", "ipl", "match", "score", "movie", "cinema", "song",
    "politician", "election", "vote", "recipe", "biryani", "car", "bike", "stock", "crypto"
]

class IntentClassifier:
    """
    Deterministic & Keyword-Weighted Intent Classifier.
    Supports Use Case 1 (Medication & Follow-up Adherence) and Use Case 2 (Lifestyle & Diet Guidance).
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

        # Count keyword occurrences for UC1 vs UC2
        uc1_score = sum(1 for k in UC1_KEYWORDS if re.search(r"\b" + re.escape(k) + r"\b", clean_text))
        uc2_score = sum(1 for k in UC2_KEYWORDS if re.search(r"\b" + re.escape(k) + r"\b", clean_text))

        # Direct domain matching heuristics
        if uc2_score > uc1_score:
            confidence = min(0.75 + (uc2_score * 0.10), 0.98)
            logger.info(f"[IntentClassifier] Text: '{text}' -> Intent: {INTENT_UC2} (Confidence: {confidence:.2f})")
            return (INTENT_UC2, confidence)

        if uc1_score > 0:
            confidence = min(0.75 + (uc1_score * 0.10), 0.98)
            logger.info(f"[IntentClassifier] Text: '{text}' -> Intent: {INTENT_UC1} (Confidence: {confidence:.2f})")
            return (INTENT_UC1, confidence)

        # Domain Heuristics for implicit health queries
        if any(w in clean_text for w in ["bp", "sugar", "hypertension", "diabetes", "blood pressure"]):
            if any(w in clean_text for w in ["namak", "salt", "walk", "khana", "diet", "rice"]):
                logger.info(f"[IntentClassifier] Implicit UC2 match for text: '{text}'")
                return (INTENT_UC2, 0.85)
            logger.info(f"[IntentClassifier] Implicit UC1 match for text: '{text}'")
            return (INTENT_UC1, 0.85)

        # Low-confidence fallback route
        logger.info(f"[IntentClassifier] Low confidence unmatched query: '{text}'")
        return (INTENT_OUT_OF_SCOPE, 0.30)
