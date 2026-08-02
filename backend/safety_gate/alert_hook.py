import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Structured alert log history for live demonstration & auditing
ALERT_HISTORY = []

def notify_clinician(session_id: str, reason: str, utterance: str) -> Dict[str, Any]:
    """
    Clinician Alert Hook.
    Triggers immediate emergency alert logging when the safety gate fires.
    In production, this would transmit an urgent push notification / SMS to the ASHA / Medical Officer.
    """
    alert_record = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S IST"),
        "session_id": session_id,
        "reason": reason,
        "patient_utterance": utterance,
        "status": "DISPATCHED_TO_CLINICIAN",
        "priority": "HIGH_EMERGENCY"
    }
    ALERT_HISTORY.append(alert_record)
    logger.critical(f"🚨 [CLINICIAN ALERT DISPATCHED] Session: {session_id} | Reason: {reason} | Utterance: '{utterance}'")
    return alert_record

def get_alert_history():
    """Returns past dispatched alerts for UI auditing."""
    return ALERT_HISTORY
