# Comprehensive Architectural Design — UC2, UC3 & UC4

This document presents the technical architecture, data flow, integration strategy, and core engineering challenges for the three design-only use cases.

---

## 1. Use Case 2: Scheme Entitlement Check (PM-JAY / ABHA)

### Goal
Walk rural patients through Ayushman Bharat (PM-JAY) and state health insurance entitlements based on their demographic profile, creating awareness of covered treatments and assisting enrollment.

```
[ Spoken Profile Info ] ──▶ [ Intent Classifier ] ──▶ [ Profile Matcher ] ──▶ [ Scheme Rules Engine ] ──▶ Spoken Entitlement Summary
```

### Data & Integration Requirements
- **Demographic & Eligibility Data**: Household BPL status, SECC 2011 category, ration card tier, age, disability status.
- **Scheme Knowledge Base**: PM-JAY covered specialty packages (1,949+ procedures), state-specific add-ons (e.g., Mahatma Jyotirao Phule Jan Arogya Yojana in MH).
- **ABHA Integration**: OAuth 2.0 API connection to Ayushman Bharat Digital Mission (ABDM) sandbox to verify ABHA ID.

### Integration with Core VDA Pipeline
- Plugs into the existing **Intent Classifier** under `UC2_SCHEME_ENTITLEMENT`.
- Bypasses RAG for structured eligibility rules; uses a deterministic **Scheme Decision Tree Rules Engine** to avoid hallucinating coverage for uncovered surgeries.

### Hardest Engineering Bottleneck
- **Incomplete / Discrepant Patient Documentation**: In rural settings, names/birth dates often differ between Aadhaar, Ration Cards, and SECC databases.
- **Solution Strategy**: Implement fuzzy demographic matching with confidence scoring. If matching confidence is below 85%, VDA guides the patient to their local Common Service Centre (CSC) or PM-JAY Mitra at the nearest District Hospital rather than confirming entitlement prematurely.

### What NOT to Solve in V1
- Direct automated claim submission or financial disbursement. V1 focuses strictly on entitlement awareness and document checklist guidance.

---

## 2. Use Case 3: Public Health Service Linkage (Facility & Geolocation Routing)

### Goal
Locate and guide patients to the nearest public health facility (Sub-Centre / HWC, PHC, CHC, District Hospital) that possesses the specific operational capability required (e.g., active ECG machine, available anti-snake venom, cold-chain insulin storage).

```
[ Service Request + Location ] ──▶ [ Geolocation Resolver ] ──▶ [ Facility Capability Registry ] ──▶ Nearby Verified Facility
```

### Data & Integration Requirements
- **Facility Registry**: National Health Facility Registry (HFR) GIS database containing coordinates, facility level, and basic infrastructure.
- **Live Capability Data**: Equipment operational status (e.g. functioning X-ray), specialist availability (e.g. gynecologist on duty), drug stock levels (DVDMS / e-Aushadhi integration).

### Integration with Core VDA Pipeline
- Utilizes the same **Safety Gate** (if a user asks for a facility while experiencing an active emergency, Safety Gate short-circuits to dispatch immediate 108 ambulance routing).
- Uses `UC3_FACILITY_LINKAGE` intent to trigger GIS proximity search bounded by capability tags.

### Hardest Engineering Bottleneck
- **Stale & Inaccurate Facility Capability Data**: Government registry data often claims a PHC has an ECG machine, but in reality, the machine is broken or the technician is absent.
- **Solution Strategy**: Implement a **Confidence-Weighted Capability Score**. Combine static HFR registry data with crowd-sourced verification signals from ASHA workers' daily mobile syncs. If capability freshness > 48 hours is unverified, VDA provides a fallback recommendation to the CHC level (which has guaranteed staffing) alongside the local PHC.

### What NOT to Solve in V1
- Real-time turn-by-turn navigation (maps). Rural users require landmark-based verbal routing (e.g., "500m past the Panchayat Bhavan").

---

## 3. Use Case 4: Teleconsultation & Triage (eSanjeevani Integration)

### Goal
Connect patients requiring clinical advice to the national teleconsultation portal (eSanjeevani), preparing structured triage summaries for medical officers while escalating red-flag symptoms.

```
[ Patient Voice Triage ] ──▶ [ Triage Summarizer ] ──▶ [ eSanjeevani API Queue ] ──▶ Clinician Video/Voice Consultation
```

### Data & Integration Requirements
- **eSanjeevani ABDM API**: FHIR-compliant API endpoints for creating consultation tickets, uploading patient summaries, and fetching queue status.
- **Triage Protocol**: Standardized clinical symptom questionnaire (WHO/MoHFW triage guidelines).

### Integration with Core VDA Pipeline
- Shares the **Safety Gate**. Red-flag symptoms trigger immediate clinician phone alert dispatch (`notify_clinician`) rather than placing the patient in a routine teleconsultation queue.
- Voice dialogue constructs a structured **FHIR Encounter Resource** sent to the clinician's dashboard prior to call connection.

### Hardest Engineering Bottleneck
- **Network Bandwidth & Video Call Drops in Remote Areas**: 2G/patchy 3G mobile connections cannot sustain video streaming.
- **Solution Strategy**: Implement **Store-and-Forward Voice Triage**. VDA collects and compresses the patient's spoken symptom summary locally, transmits the audio payload asynchronously over low-bandwidth SMS/data, and connects a standard PSTN voice call when bandwidth is insufficient for WebRTC video.

### What NOT to Solve in V1
- Automated AI prescription generation. All prescriptions must originate from a licensed RMP on the eSanjeevani platform.
