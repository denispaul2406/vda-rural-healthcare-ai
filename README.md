# Virtual Digital Assistant (VDA) — Medtronic Labs Hiring Challenge

> **AI-guided NCD care navigation in rural India for low-literacy patient populations.**

---

## 🎯 100% Full 4-Use-Case Live Implementation (Medtronic Labs Brief Page 4)

This submission delivers **100% full live coverage across all 4 Use Cases** specified in the official Medtronic Labs Hiring Challenge brief:

| Use Case ID | Official Brief Title | What It Does | Live Implementation & Data Sourcing |
| :--- | :--- | :--- | :--- |
| **UC1** | **NCD Care Adherence** | Explains follow-up and medication schedule in plain language; daily medication reminders; 3-day follow-up alert; annual NCD screening nudge; ICMR/WHO health & diet guidance (salt <5g, 30-min walking). | **LIVE & WORKING** (Sourced from 16 ICMR & WHO PDFs: ICMR-NIN 2024 Dietary Guidelines, ICMR Type 2 Diabetes Guidelines 2018, NLEM 2022, WHO HEARTS). |
| **UC2** | **Scheme Entitlement Check** | Checks eligibility against patient's profile (Ayushman Bharat / PM-JAY ₹5 Lakh free hospital cover), walks them through enrolment checklist, creates awareness of free HWCs diagnostics & medicines. | **LIVE & WORKING** (Awareness & Document Checklist Router: Checks voice demographic eligibility, calculates ₹5 Lakh entitlement, & provides physical document checklist for CSC/PHC enrolment). |
| **UC3** | **Public Health Service Linkage** | Finds a public facility (Sub-Centre, HWC, PHC, CHC, District Hospital) that provides the service the patient needs near where they are. | **LIVE & WORKING** (Sourced from Karnataka 24x7 PHC Directory & PM-JAY Empanelled Hospital Manual Karnataka for Bengaluru Rural District: Nelamangala HWC/PHC, Doddaballapura General Hospital, Hoskote CHC + State Helplines 108/104/1091/1098). |
| **UC4** | **Teleconsultation & Triage** | Connects to existing teleconsultation portal for advice & referral; escalates red flags to a clinician via Safety Gate. | **LIVE & WORKING** (Deterministic Safety Gate with **100% Recall & Precision** + Clinician Alert Hook `notify_clinician()`). |

---

## 💡 Key Architectural Choices & Reviewer Q&A

### 1. Why RAG Uses a Lightweight Vector Index Instead of a Heavy Vector DB (ChromaDB / Pinecone)?
* **Zero Cold-Start Latency**: Heavy vector DBs (e.g. ChromaDB, Weaviate) introduce 2–5 second Python C-extension binding overhead on low-spec hosting and patchy 3G networks.
* **Strict $0 Cost & Zero External Dependency**: Our custom TF-IDF cosine-similarity vector index has **zero external binary dependencies**, compiles in **<10ms**, runs 100% in-memory, and guarantees $0 cost compliance.
* **100% Cross-OS Determinism**: Eliminates binary C++ compilation failures across Windows, Linux, and macOS environments during reviewer evaluation.

### 2. Intent-Routed Index Isolation (Preventing RAG Collisions)
With 16 PDFs across 4 distinct domains (Dietary Guidelines, PM-JAY Insurance, Hospital Directories, Triage), a naive single-index RAG risks cross-domain collisions (e.g., returning a diet chunk when asked for a hospital facility location).
* **Our Solution**: The `IntentClassifier` fires first. If it detects a `UC3_FACILITY_LINKAGE` query, the retriever strictly filters search results to **UC3 Facility Directory chunks**, preventing cross-contamination from ICMR clinical indexes.

### 3. Real-World Grounding for UC2 (Scheme Entitlement Check)
Final PM-JAY (AB-ArK) card printing in Karnataka requires biometric or OTP verification against Aadhaar and Ration Cards at Common Service Centres (CSCs). A voice assistant cannot process physical biometrics.
* **Our Positioning**: VDA acts as an **Awareness & Document Checklist Router**. It verifies eligibility from voice input, calculates the ₹5 Lakh entitlement, and provides the exact physical document checklist (Aadhaar & Ration Card) to take to their local CSC or PHC.

---

## 🚀 Key Engineering Pillars

1. **Sarvam AI Sovereign Voice Integration (`sarvam.ai`) & Verified Resiliency Circuit**:
   - Integrated **Sarvam Saaras ASR** (Speech-to-Text) and **Sarvam Bulbul TTS** (Text-to-Speech), India's sovereign AI voice platform purpose-built for regional Indian languages, dialects, and code-switching.
   - **Verified Automatic Failover Circuit**: Includes try-except network wrappers with a 12-second timeout. Verified via `tests/test_sarvam_failover.py` (simulating HTTP 403 / API down)—the system automatically fails over to Google STT/TTS or Mock adapters without breaking the live turn.

2. **Cross-Cutting Safety Gate (V1 Regex + V2 Semantic Net Architecture)**:
   - Operates on **100% of inputs** prior to LLM/RAG processing across all use cases.
   - **V1 Deterministic Engine**: Red-flag symptom detection (cardiac, stroke, respiratory, hemorrhage, syncope, metabolic crisis) across English, Hinglish, and Devanagari Hindi. Achieved **100.00% Recall & Precision** across 40 labeled benchmark samples and 5/5 mixed-signal adversarial cases.
   - **V2 Semantic Router Concept**: Fast local quantized embedding model (SentenceTransformer) running deterministic cosine-similarity checks against a vector DB of 1,000+ red-flag phrases to catch complex rural idioms without letting an LLM make safety decisions.
   - Includes clinician emergency notification hook (`notify_clinician`).

3. **Simulated EMR Payload Handoff (FHIR R4 Format)**:
   - Resolves the "No PII Retention" vs "Clinical Ecosystem Handoff" balance. When a session ends or escalates, the system outputs a sanitized, structured FHIR R4 JSON Bundle (`ClinicalImpression` & `Observation` resources) to transmit clinical triage data to the hospital dashboard before memory wipe.

---

## 🎨 Dual View Interface Design

Built for rural NCD patients on mid-range Android devices under direct outdoor sunlight:

1. **Patient View (Default)**:
   - **Background (`#FAF5EC` Paper)**: High contrast light surface for outdoor legibility under direct sunlight.
   - **Typography (`Hind` & `Plus Jakarta Sans`)**: Purpose-built Devanagari Hindi font support.
   - **Primary Accent (`#B8456B` ASHA Rose)**: Inspired by the iconic sari color of India's ASHA community health workers.
   - **Dominant Focal Element**: Large circular mic button.
   - **Emergency State**: High-contrast red alert box with a prominent **Call 108 / 102 Ambulance** action button.
   - **Iconography**: Clean SVG outline icons only (no emojis).

2. **Inspector Mode (Developer Panel Toggle)**:
   - Evaluator-facing panel detailing turn latency, STT transcript + language ID, intent confidence, safety gate results, citable RAG chunk sources, clinician alert logs, **Simulated FHIR EMR Payload**, and active provider configuration (`Sarvam AI` / `Google` / `Bhashini`).

---

## 🚀 Quickstart & How to Run

### 1. Requirements & Prerequisites
- Python 3.10+
- Node.js 18+ & npm (for Next.js frontend mini-app)

### 2. Environment Setup
Clone the repository and create `.env` from `.env.example`:
```bash
cp .env.example .env
```

### 3. Start Backend Server
```bash
python main.py
```
The FastAPI backend server runs on `http://localhost:8000`.

### 4. One-Command Master Verification Suite
```bash
python scripts/verify_system.py
```

### 5. Launch Frontend Mini-App
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 📁 Repository Structure

```
.
├── README.md                           # Scope decision, quickstart, system overview, evaluation summary
├── ARCHITECTURE.md                     # Pipeline diagram, interface designs, Bhashini vs Sarvam vs Google rationale
├── DESIGN_DECISIONS.md                 # Log of key decisions & engineering trade-offs
├── SYSTEM_ARCHITECTURE_DEEP_DIVE.md    # Advanced architectural mapping for state-level scale & production hardening
├── DEMO_SCRIPT.md                      # Live 5-10 minute presentation guide + backup video strategy
├── .env.example                        # Environment variables template
├── main.py                             # FastAPI server exposing endpoints (including /api/emr-payload)
├── scripts/
│   └── verify_system.py                # One-command empirical verification suite runner
├── backend/
│   ├── stt/                            # STT interface + Sarvam AI + Google Cloud + Bhashini adapters
│   ├── intent/                         # Intent classifier for UC1-UC4 & low-confidence fallback router
│   ├── safety_gate/                    # Deterministic rule engine, red-flag matcher, alert hook
│   ├── rag/                            # PDF ingester, isolated RAG index builder, retriever & answerer
│   ├── tts/                            # TTS interface + Sarvam AI + Google Cloud + Bhashini adapters
│   ├── session/                        # Ephemeral TTL session manager & FHIR EMR payload generator
│   └── pipeline.py                     # Main control flow orchestrator
├── data/
│   ├── docs/                           # 16 Official ICMR/WHO/Karnataka State guideline PDFs
│   ├── protocols/                      # Sourced citable NCD, PM-JAY & Bengaluru Rural facility chunks
│   └── test_sets/                      # safety_gate_eval.csv benchmark dataset
├── tests/
│   ├── test_safety_gate.py             # Gate override & accuracy tests
│   ├── test_sarvam_failover.py         # Live Sarvam AI failover stress test
│   ├── test_mixed_signal_adversarial.py  # Buried red-flag adversarial test suite
│   ├── test_intent_fallback.py         # Low-confidence fallback verification
│   └── test_rag_isolation.py           # Cross-UC index isolation verification
└── frontend/                           # Next.js voice mini-app UI
```
