import logging
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Structured alert log history for live demonstration & auditing
ALERT_HISTORY: List[Dict[str, Any]] = []
ACTIVE_TAKEOVERS: Dict[str, Dict[str, Any]] = {}

def notify_clinician(session_id: str, reason: str, utterance: str) -> Dict[str, Any]:
    """
    Clinician Alert Hook.
    Triggers immediate emergency alert logging when the safety gate fires.
    In production, this transmits an urgent push notification to the ASHA / Medical Officer dashboard.
    """
    alert_id = f"alt_{int(time.time()*1000)}"
    ticket_id = f"TKT-2026-{int(time.time()) % 10000}"
    
    alert_record = {
        "alert_id": alert_id,
        "triage_ticket_id": ticket_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S IST"),
        "session_id": session_id,
        "reason": reason,
        "patient_utterance": utterance,
        "status": "DISPATCHED_TO_CLINICIAN",
        "priority": "HIGH_EMERGENCY",
        "patient_profile": {
            "name": "Ramesh Kumar (Rural Patient)",
            "age": 58,
            "gender": "Male",
            "location": "Nelamangala Sub-District, Bengaluru Rural",
            "ncd_conditions": ["Hypertension (BP 160/100)", "Type 2 Diabetes"],
            "assigned_asha": "ASHA Worker Sunita (Ph: +91-9845012345)",
            "nearest_phc": "Nelamangala 24x7 PHC (2.4 km)"
        },
        "taken_over_by": None,
        "takeover_note": None,
        "takeover_timestamp": None
    }
    ALERT_HISTORY.append(alert_record)
    logger.critical(f"🚨 [CLINICIAN ALERT DISPATCHED] Session: {session_id} | Ticket: {ticket_id} | Reason: {reason} | Utterance: '{utterance}'")
    return alert_record

def takeover_alert(session_id: str, clinician_name: str = "Dr. Sharma (MO)", clinician_note: str = "Taking over call for emergency protocol advice") -> Dict[str, Any]:
    """
    Human-in-the-Loop Takeover Action.
    Allows a Medical Officer / Clinician to interrupt an automated session and take direct control.
    """
    now_str = time.strftime("%Y-%m-%d %H:%M:%S IST")
    
    # Update active takeover map
    takeover_record = {
        "session_id": session_id,
        "clinician_name": clinician_name,
        "clinician_note": clinician_note,
        "timestamp": now_str,
        "active": True
    }
    ACTIVE_TAKEOVERS[session_id] = takeover_record

    # Update in ALERT_HISTORY
    for alert in ALERT_HISTORY:
        if alert["session_id"] == session_id:
            alert["status"] = "CLINICIAN_TAKEOVER_ACTIVE"
            alert["taken_over_by"] = clinician_name
            alert["takeover_note"] = clinician_note
            alert["takeover_timestamp"] = now_str

    logger.info(f"🩺 [HUMAN-IN-THE-LOOP TAKEOVER] Clinician '{clinician_name}' took over Session '{session_id}' with note: '{clinician_note}'")
    return takeover_record

def is_takeover_active(session_id: str) -> bool:
    """Returns True if a clinician has taken over this session."""
    return session_id in ACTIVE_TAKEOVERS and ACTIVE_TAKEOVERS[session_id].get("active", False)

def get_takeover_details(session_id: str) -> Dict[str, Any]:
    """Returns takeover details for an active session."""
    return ACTIVE_TAKEOVERS.get(session_id, {})

def get_alert_history():
    """Returns past dispatched alerts for UI auditing."""
    return ALERT_HISTORY
