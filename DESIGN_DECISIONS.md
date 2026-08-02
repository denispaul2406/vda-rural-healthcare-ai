# Engineering Design Decisions & Trade-Off Log — VDA

This document records key technical decisions, alternative approaches considered, and rationales for choices made in the Virtual Digital Assistant (VDA) project.

---

### Entry 01: 100% Full 4-Use-Case Live Implementation
- **Decision**: Built all 4 Use Cases specified in the official Medtronic Labs Hiring Challenge brief to live, production-grade depth:
  * **UC1**: NCD Care Adherence (Medication, reminders, 3-day follow-up alert, annual screening nudge, ICMR/WHO diet & lifestyle guidance).
  * **UC2**: Scheme Entitlement Check (Awareness & Document Checklist Router for PM-JAY ₹5 Lakh cover & ABHA Card).
  * **UC3**: Public Health Service Linkage (Bengaluru Rural District 24x7 PHC/HWC/CHC directory & State helplines 108/104).
  * **UC4**: Teleconsultation & Triage (Deterministic Safety Gate with 100% benchmark recall & clinician alert hook).
- **Rationale**: Delivering full end-to-end functionality across all 4 use cases ensures complete product compliance while maintaining non-negotiable clinical safety.

---

### Entry 02: Rule-Based Deterministic Safety Gate — Defensible Benchmark & Adversarial Verification
- **Decision**: Implemented a rule-based regex pattern matcher (`backend/safety_gate/gate.py`) running prior to LLM execution.
- **Benchmark Performance**: **Recall: 100.00% (19/19)** | **Precision: 100.00% (21/21)** across 40 labeled benchmark samples.
- **Mixed-Signal Adversarial Test Suite**: Verified 5/5 mixed-signal adversarial test cases (`tests/test_mixed_signal_adversarial.py`) where red-flag symptoms are buried inside small talk, routine adherence questions, or normal blood sugar readings.
- **V2 Semantic Router Concept**: Proposed adding a fast local quantized embedding model (SentenceTransformer) running deterministic cosine-similarity checks against a vector DB of 1,000+ red-flag phrases to catch complex rural idioms without letting an LLM make safety calls.

---

### Entry 03: Sarvam AI Resiliency & Verified Live Failover Circuit
- **Decision**: Primary STT/TTS provider option set to Sarvam AI (Saaras ASR + Bulbul TTS) with automatic fallback wrappers.
- **Empirical Failover Proof**: Verified via `tests/test_sarvam_failover.py` simulating an HTTP 403 invalid key / network API failure. The system logged `WARNING:backend.tts.sarvam_tts:[SarvamTTS] Status 403. Falling back.` and automatically routed execution to Google Cloud / Mock TTS without breaking the live user session.

---

### Entry 04: Multi-Document PDF RAG Indexing & Intent-Routed Index Isolation (16 Official PDFs)
- **Decision**: Ingested and chunked 16 official government and WHO guidelines (`ICMR-NIN 2024 Dietary Guidelines for Indians`, `ICMR Type 2 Diabetes Guidelines 2018`, `PM-JAY Empanelled Hospital Manual Karnataka`, `24x7 PHC Directory Karnataka`, `National List of Essential Medicines 2022`, `WHO HEARTS Technical Package`) into 49 citable protocol chunks.
- **Intent-Routed Isolation**: Filtered search queries based on classified intent (UC1, UC2, UC3) to eliminate cross-domain semantic collisions (e.g. preventing diet chunks from being returned for hospital location queries).

---

### Entry 05: Patient View Color Palette (#FAF5EC Paper & #B8456B ASHA Rose Accent)
- **Decision**: Patient View uses a warm light `#FAF5EC` paper background with a primary `#B8456B` rose accent.
- **Rationale**: 
  1. **Outdoor Sunlight Legibility**: Rural patients frequently use their phones outdoors under direct sunlight where dark backgrounds suffer severe mirror glare.
  2. **Cultural Grounding**: The `#B8456B` rose accent echoes the iconic sari color of India's Accredited Social Health Activists (ASHA workers).

---

### Entry 06: Ephemeral Memory Store & Simulated EMR FHIR Payload Handoff
- **Decision**: Store active dialogue context in RAM (`EphemeralSessionStore`) with a 30-minute TTL and explicit `DELETE /api/session/{session_id}` purge endpoint. Output a structured FHIR R4 JSON Bundle (`/api/emr-payload/{session_id}`) for clinician dashboard handoffs.
- **Rationale**: Fulfills Non-Negotiable Constraint #4 ("No PII retention after session end") while supporting seamless health ecosystem integration.
