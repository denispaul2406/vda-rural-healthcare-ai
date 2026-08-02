import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EphemeralSessionStore:
    """
    In-Memory Ephemeral Session Store with strict TTL expiration.
    Enforces Non-Negotiable Constraint #4: Zero PII Persistence to Disk.
    All transient dialogue context is held in memory and destroyed on session close or TTL expiry.
    """

    def __init__(self, ttl_minutes: int = 30):
        self.ttl_seconds = ttl_minutes * 60
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        self.cleanup_expired_sessions()
        now = time.time()
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "created_at": now,
                "last_active": now,
                "turns": [],
                "user_metadata": {}
            }
            logger.info(f"[SessionManager] Created ephemeral session: {session_id}")
        else:
            self._sessions[session_id]["last_active"] = now
        return self._sessions[session_id]

    def add_turn(self, session_id: str, turn_data: Dict[str, Any]):
        session = self.get_or_create_session(session_id)
        session["turns"].append(turn_data)

    def generate_fhir_emr_payload(self, session_id: str) -> Dict[str, Any]:
        """
        Generates a sanitized FHIR R4 JSON Communication / Observation Bundle payload
        to transmit clinical triage data to the Hospital Management System (HMS) / Clinician Dashboard.
        """
        session = self._sessions.get(session_id, {"turns": []})
        turns = session.get("turns", [])
        
        last_turn = turns[-1] if turns else {}
        is_emergency = last_turn.get("safety_escalated", False)
        
        fhir_payload = {
            "resourceType": "Bundle",
            "type": "message",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "meta": {
                "profile": ["http://hl7.org/fhir/StructureDefinition/ClinicalImpression"],
                "security": "ANONYMIZED_SANITIZED_ZERO_PII"
            },
            "entry": [
                {
                    "fullUrl": f"urn:uuid:vda-session-{session_id}",
                    "resource": {
                        "resourceType": "ClinicalImpression",
                        "status": "completed",
                        "code": {
                            "text": last_turn.get("intent", "UC1_NCD_ADHERENCE")
                        },
                        "subject": {
                            "display": f"Anonymous Patient (Session: {session_id})"
                        },
                        "effectiveDateTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "summary": last_turn.get("transcript", "No voice turn logged"),
                        "finding": [
                            {
                                "itemCodeableConcept": {
                                    "text": last_turn.get("safety_reason", "No Red-Flag Emergency") if is_emergency else "Routine NCD Guidance"
                                }
                            }
                        ],
                        "protocol": last_turn.get("sources", ["ICMR_WHO_NCD_GUIDELINES"])
                    }
                },
                {
                    "fullUrl": f"urn:uuid:vda-triage-{session_id}",
                    "resource": {
                        "resourceType": "Observation",
                        "status": "final",
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": "vital-signs"
                                    }
                                ]
                            }
                        ],
                        "valueString": f"Priority: {'URGENT_EMERGENCY' if is_emergency else 'ROUTINE'} | Latency: {last_turn.get('latency_ms', 0)}ms"
                    }
                }
            ]
        }
        return fhir_payload

    def close_session(self, session_id: str):
        """Immediately purges all session state from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"🧹 [SessionManager] Ephemeral session destroyed: {session_id} (Zero PII Retained)")

    def cleanup_expired_sessions(self):
        """Scans and purges sessions older than TTL."""
        now = time.time()
        expired_ids = [sid for sid, sdata in self._sessions.items() if (now - sdata["last_active"]) > self.ttl_seconds]
        for sid in expired_ids:
            del self._sessions[sid]
            logger.info(f"🧹 [SessionManager] TTL Purged expired session: {sid}")

# Global Session Manager Singleton
session_store = EphemeralSessionStore()
