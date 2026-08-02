import os
import time
import logging
import base64
from typing import Dict, Any, Optional

from backend.stt import get_stt_provider
from backend.intent import IntentClassifier, get_deterministic_fallback, get_out_of_scope_decline, INTENT_UC1, INTENT_OUT_OF_SCOPE
from backend.safety_gate import SafetyGate
from backend.rag import UC1Retriever, Answerer
from backend.tts import get_tts_provider
from backend.session import session_store

logger = logging.getLogger(__name__)

class VDAPipeline:
    """
    Main Orchestration Pipeline for Virtual Digital Assistant (VDA).
    
    Pipeline Stages:
    1. STT (Speech-to-Text) & Language Identification
    2. Intent Classification & Confidence Check
    3. Safety Gate (Deterministic Red-Flag Rule Check) -> SHORT-CIRCUITS ON EMERGENCY
    4. RAG Retrieval (with Intent-Routed Index Isolation) & Grounded LLM Agent
    5. TTS (Text-to-Speech) Audio Generation
    6. Ephemeral Session Context Update
    """

    def __init__(self, confidence_threshold: float = 0.75):
        stt_name = os.getenv("STT_PROVIDER", "google")
        tts_name = os.getenv("TTS_PROVIDER", "google")
        
        self.stt_provider = get_stt_provider(stt_name)
        self.intent_classifier = IntentClassifier(confidence_threshold=confidence_threshold)
        self.safety_gate = SafetyGate()
        self.rag_retriever = UC1Retriever()
        self.answerer = Answerer()
        self.tts_provider = get_tts_provider(tts_name)
        self.confidence_threshold = confidence_threshold

    def process_turn(
        self,
        session_id: str,
        audio_bytes: Optional[bytes] = None,
        text_input: Optional[str] = None,
        mime_type: str = "audio/wav"
    ) -> Dict[str, Any]:
        """
        Executes a single voice/text dialogue turn through the pipeline.
        """
        start_time = time.time()
        pipeline_log = []

        # -------------------------------------------------------------
        # STAGE 1: STT & Language Identification
        # -------------------------------------------------------------
        if text_input and text_input.strip():
            transcript = text_input.strip()
            lang_code = "hi-IN" if any(ord(c) > 127 for c in transcript) or "mujhe" in transcript.lower() or "dard" in transcript.lower() else "en-IN"
            pipeline_log.append(f"[STAGE 1] Direct Text Input Provided: '{transcript}' ({lang_code})")
        elif audio_bytes:
            transcript, lang_code = self.stt_provider.transcribe(audio_bytes, mime_type)
            pipeline_log.append(f"[STAGE 1] STT Transcribed: '{transcript}' (Language: {lang_code})")
        else:
            return {"error": "No audio bytes or text input provided."}

        # -------------------------------------------------------------
        # STAGE 2: Intent Classification
        # -------------------------------------------------------------
        intent, confidence = self.intent_classifier.classify(transcript)
        pipeline_log.append(f"[STAGE 2] Intent: '{intent}' (Confidence: {confidence:.2f})")

        # -------------------------------------------------------------
        # STAGE 3: Safety Gate (CRITICAL: RUNS DETERMINISTICALLY FIRST)
        # -------------------------------------------------------------
        gate_result = self.safety_gate.check(transcript, session_id=session_id, lang_code=lang_code)
        
        if gate_result.escalate:
            # SAFETY SHORT-CIRCUIT: LLM is NEVER called when safety gate fires!
            pipeline_log.append(f"[STAGE 3] 🚨 SAFETY GATE ESCALATION TRIGGERED: '{gate_result.reason}'. Bypass LLM!")
            
            response_text = gate_result.response_text
            audio_response = self.tts_provider.synthesize(response_text, lang_code=lang_code)
            audio_b64 = base64.b64encode(audio_response).decode("utf-8")
            
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            
            result = {
                "session_id": session_id,
                "transcript": transcript,
                "language": lang_code,
                "intent": intent,
                "confidence": confidence,
                "safety_escalated": True,
                "safety_reason": gate_result.reason,
                "response_text": response_text,
                "audio_b64": audio_b64,
                "sources": ["SAFETY_RULE_ENGINE"],
                "latency_ms": elapsed_ms,
                "pipeline_log": pipeline_log
            }
            session_store.add_turn(session_id, result)
            return result

        pipeline_log.append("[STAGE 3] Safety Gate Passed (No red-flag emergency detected).")

        # -------------------------------------------------------------
        # STAGE 2 (Contd): Low Confidence Fallback & Out-of-Scope Refusal
        # -------------------------------------------------------------
        if intent == INTENT_OUT_OF_SCOPE:
            pipeline_log.append("[STAGE 2] Out-of-Scope question detected. Returning fixed decline.")
            response_text = get_out_of_scope_decline(lang_code)
            audio_response = self.tts_provider.synthesize(response_text, lang_code=lang_code)
            audio_b64 = base64.b64encode(audio_response).decode("utf-8")
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "session_id": session_id,
                "transcript": transcript,
                "language": lang_code,
                "intent": intent,
                "confidence": confidence,
                "safety_escalated": False,
                "response_text": response_text,
                "audio_b64": audio_b64,
                "sources": ["OUT_OF_SCOPE_DECLINE"],
                "latency_ms": elapsed_ms,
                "pipeline_log": pipeline_log
            }

        if confidence < self.confidence_threshold:
            pipeline_log.append(f"[STAGE 2] Low Confidence ({confidence:.2f} < {self.confidence_threshold}). Returning deterministic fallback.")
            response_text = get_deterministic_fallback(lang_code)
            audio_response = self.tts_provider.synthesize(response_text, lang_code=lang_code)
            audio_b64 = base64.b64encode(audio_response).decode("utf-8")
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "session_id": session_id,
                "transcript": transcript,
                "language": lang_code,
                "intent": intent,
                "confidence": confidence,
                "safety_escalated": False,
                "response_text": response_text,
                "audio_b64": audio_b64,
                "sources": ["LOW_CONFIDENCE_FALLBACK"],
                "latency_ms": elapsed_ms,
                "pipeline_log": pipeline_log
            }

        # -------------------------------------------------------------
        # STAGE 4: RAG Retrieval (with Intent-Routed Index Isolation)
        # -------------------------------------------------------------
        pipeline_log.append(f"[STAGE 4] Executing Intent-Routed RAG retrieval for intent: {intent}.")
        retrieved_chunks, meets_thresh = self.rag_retriever.retrieve(transcript, target_intent=intent)
        
        if not meets_thresh:
            pipeline_log.append("[STAGE 4] RAG similarity score below threshold. Returning grounded refusal.")

        response_text, source_ids = self.answerer.generate_answer(transcript, retrieved_chunks, lang_code=lang_code)
        pipeline_log.append(f"[STAGE 4] Generated RAG Response. Sources: {source_ids}")

        # -------------------------------------------------------------
        # STAGE 5: TTS Speech Synthesis
        # -------------------------------------------------------------
        pipeline_log.append(f"[STAGE 5] Synthesizing TTS audio ({lang_code}).")
        audio_response = self.tts_provider.synthesize(response_text, lang_code=lang_code)
        audio_b64 = base64.b64encode(audio_response).decode("utf-8")

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        pipeline_log.append(f"[COMPLETE] Turn processed in {elapsed_ms} ms.")

        turn_result = {
            "session_id": session_id,
            "transcript": transcript,
            "language": lang_code,
            "intent": intent,
            "confidence": confidence,
            "safety_escalated": False,
            "response_text": response_text,
            "audio_b64": audio_b64,
            "sources": source_ids,
            "latency_ms": elapsed_ms,
            "pipeline_log": pipeline_log
        }

        # -------------------------------------------------------------
        # STAGE 6: Update Ephemeral Session Store
        # -------------------------------------------------------------
        session_store.add_turn(session_id, turn_result)
        return turn_result
