# Live Interview Presentation & Demo Script — VDA

**Candidate**: Denis  
**Target Duration**: 5 to 10 Minutes  
**Focus**: Engineering Judgment, Sarvam AI Voice Integration, Intent-Routed Index Isolation, Safety Gate Architecture, Simulated EMR/FHIR Handoff, and "Slow 3G" Network Flex.

---

## 🎯 Cornerstone Opening Pitch (00:00 - 01:00)

> *"Hello! When building this system, **I refused to compromise on clinical safety and latency**. I could have given you four fragile stubs, but instead, I built **all 4 Use Cases** to live, production-grade depth alongside a 100% deterministic Safety Gate.
> 
> We integrated **Sarvam AI (Saaras ASR & Bulbul TTS)**—India's sovereign voice stack—and ingested **16 official ICMR, WHO, & Karnataka State guideline PDFs** into an isolated, intent-routed RAG index. I also designed the UI specifically for a rural Indian NCD patient using a warm light background for outdoor sunlight legibility and an ASHA-worker rose accent color."*

---

## ⏱️ Step-by-Step Live Walkthrough (10 Minutes)

```
[00:00 - 01:00]  1. Cornerstone Pitch & Intent-Routed RAG Rationale
[01:00 - 02:30]  2. Live Demo Turn 1: UC1 NCD Adherence (Sarvam AI Voice + Citable RAG)
[02:30 - 04:00]  3. Live Demo Turn 2: UC2 PM-JAY Scheme Check (Awareness & Document Checklist Router)
[04:00 - 05:30]  4. Live Demo Turn 3: UC3 Bengaluru Rural Facility Linkage (Intent-Routed Index)
[05:30 - 07:00]  5. Live Demo Turn 4: UC4 Safety Gate Red-Flag Trigger (Ambulance Action + Alert Hook)
[07:00 - 08:30]  6. Inspector Mode & Simulated EMR FHIR Payload Handoff
[08:30 - 09:30]  7. "Slow 3G" Network Throttling Flex (DevTools Demo)
[09:30 - 10:00]  8. Q&A Wrap-Up
```

---

## 🎙️ Detailed Script & Verbal Pitch Cheatsheet

### 1. Live Demo Turn 1: UC1 NCD Care Adherence (01:00 - 02:30)
* **Demo Action**: Select **`Sarvam AI (Indic Sovereign)`** in top dropdown, tap the ASHA Rose Mic Button.
* **Spoken Test Utterance**: 
  > `"What time should I take my BP medicine?"`  
  *(or in Hindi: `"BP ki dawai lene ka sahi samay kya hai?"`)*
* **What to Show Reviewer**:
  - Show clean bilingual patient guidance card rendering grounded ICMR/MoHFW protocol advice with source citations (`[ICMR 2018 Guidelines]`).

---

### 2. Live Demo Turn 2: UC2 PM-JAY Scheme Entitlement Check (02:30 - 04:00)
* **Demo Action**: Tap the UC2 scenario chip or speak:
* **Spoken Test Utterance**: 
  > `"Am I eligible for Ayushman Bharat PM-JAY 5 Lakh free hospital card?"`
* **Verbal Pitch to Reviewer**: 
  > *"For UC2, final card issuance in Karnataka requires biometric or OTP verification against Aadhaar at Common Service Centres. VDA acts as an **Awareness & Document Checklist Router**—checking demographic eligibility from voice input, calculating the ₹5 Lakh entitlement, and providing the exact physical document checklist to bring to their local CSC or PHC."*

---

### 3. Live Demo Turn 3: UC3 Bengaluru Rural Facility Linkage (04:00 - 05:30)
* **Demo Action**: Tap the UC3 scenario chip or speak:
* **Spoken Test Utterance**: 
  > `"Where is the nearest PHC hospital or Sub-Centre in Doddaballapura or Nelamangala?"`
* **Verbal Pitch to Reviewer (Intent-Routed Index Isolation)**: 
  > *"Because we ingested 16 PDFs across 4 different domains, we built **Intent-Routed Index Isolation**. The Intent Classifier fires first. If it detects a UC3 Facility query, it ONLY searches the isolated Karnataka PHC Index, preventing cross-contamination from clinical ICMR diet or insurance indexes."*

---

### 4. Live Demo Turn 4: UC4 Safety Gate Emergency Trigger (05:30 - 07:00)
* **Demo Action**: Tap the Emergency red chip or speak:
* **Spoken Test Utterance**: 
  > `"सीने में दर्द हो रहा है"` *(or `"I am having severe chest pain spreading to my left arm"`)*
* **What to Show Reviewer**:
  - **CRITICAL**: Show that Safety Gate triggers **FIRST**.
  - Show the high-contrast **Emergency Warning Card** appearing with the **Call Ambulance (108 / 102)** button.
  - Explain V2 Semantic Net Concept: *"Regex is our V1 deterministic catch. To handle complex rural idioms, V2 uses a fast, local quantized embedding model (SentenceTransformer) running deterministic cosine-similarity checks against a vector DB of 1,000+ red-flag phrases—without letting an LLM make the safety call."*

---

### 5. Inspector Mode & Simulated EMR FHIR Payload (07:00 - 08:30)
* **Demo Action**: Flip to **`Inspector Mode 🔍`** in navbar.
* **What to Show Reviewer**:
  - Surface turn latency.
  - Show STT transcript & detected language code.
  - Show Intent classification confidence (`UC1`, `UC2`, `UC3`, `UC4`).
  - Show citable RAG chunk sources.
  - **Show Simulated EMR / FHIR Payload Card**: Show the structured HL7/FHIR R4 JSON bundle (`ClinicalImpression` & `Observation` resources) transmitted to the hospital dashboard before session RAM wipe!

---

### 6. The "Slow 3G" Network Flex (08:30 - 09:30)
* **Demo Action**: Open Chrome DevTools (`F12`), navigate to **Network** tab, change throttling from *No Throttling* to **Slow 3G**.
* **Run Turn**: Speak a query.
* **Script**: *"Notice how the Next.js mini-app handles patchy rural mobile connectivity gracefully with optimistic UI states and audio stream buffering under 3G latency constraints."*

---

## 📱 Real Phone & Mobile Network Testing Strategy

To test live on a physical Android/iOS phone over 4G/5G or local Wi-Fi:

1. **Local Wi-Fi Network Setup**:
   * Run `python main.py` (listens on `0.0.0.0:8000`).
   * Find your laptop local IP via `ipconfig` (e.g., `192.168.1.5`).
   * Connect mobile device to the same Wi-Fi and visit `http://192.168.1.5:3000`.

2. **Mobile Data Tunnel (4G/5G Testing)**:
   * Run `npx localtunnel --port 3000` or `ngrok http 3000`.
   * Open the generated HTTPS URL on your phone to test native mobile Web Speech API and mic input under real cellular data latency.

---

## 📹 Backup Demonstration Video Strategy

In case live room Wi-Fi or interview connectivity fails:

1. **Pre-Recording Cheatsheet (90 Seconds MP4)**:
   * Press **`Win + Alt + R`** on Windows (Game Bar) or use OBS.
   * **00:00 - 00:30**: Record voice input turn on Sarvam AI provider in Hindi.
   * **00:30 - 01:00**: Trigger emergency red-flag utterance and show Ambulance Call button.
   * **01:00 - 01:30**: Toggle Inspector Mode showing telemetry console, FHIR EMR payload, and citable RAG sources.
   * Save video as `VDA_Demo_Backup.mp4` in the project root directory.

2. **Offline Fallback Execution**:
   * Select **`Local Dev Fallback`** in provider dropdown. The system runs 100% offline using synthetic voice and local grounded RAG.
