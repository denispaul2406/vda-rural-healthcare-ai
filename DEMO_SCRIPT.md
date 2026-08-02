# Live Interview Presentation & Demo Script — VDA

**Candidate**: Denis  
**Target Duration**: 5 to 10 Minutes  
**Focus**: Engineering Judgment, Sarvam AI Voice Integration, Safety Gate V1/V2 Architecture, Simulated EMR/FHIR Handoff, 12-PDF RAG Ingestion, and "Slow 3G" Network Flex.

---

## 🎯 Cornerstone Opening Pitch (00:00 - 01:00)

> *"Hello! When building this system, **I refused to compromise on clinical safety and latency**. I could have given you four fragile stubs, but instead, I built **Use Case 1 (NCD Care Adherence)** and **Use Case 2 (Lifestyle & Salt Guidance)** to live, production-grade depth alongside a 100% deterministic Safety Gate. **I compromised on feature breadth to guarantee patient safety.**
> 
> We integrated **Sarvam AI (Saaras ASR & Bulbul TTS)**—India's sovereign voice stack—and ingested **12 official ICMR & WHO guideline PDFs** (including ICMR-NIN 2024 Dietary Guidelines) into a citable RAG index. I also designed the UI specifically for a rural Indian NCD patient using a warm light background for outdoor sunlight legibility and an ASHA-worker rose accent color."*

---

## ⏱️ Step-by-Step Live Walkthrough (10 Minutes)

```
[00:00 - 01:00]  1. Cornerstone Pitch & Scope Justification
[01:00 - 03:00]  2. Live Demo Turn 1: UC1 NCD Adherence (Sarvam AI Voice + Citable RAG)
[03:00 - 04:30]  3. Live Demo Turn 2: UC2 Lifestyle & Salt Guidance (WHO HEARTS & NIN 2024 Diet)
[04:30 - 06:30]  4. Live Demo Turn 3: Safety Gate Red-Flag Trigger (Ambulance Action + Alert Hook)
[06:30 - 08:00]  5. Live Demo Turn 4: Inspector Mode & Simulated EMR FHIR Payload Handoff
[08:00 - 09:00]  6. "Slow 3G" Network Throttling Flex (DevTools Demo)
[09:00 - 10:00]  7. Q&A Wrap-Up
```

---

## 🎙️ Detailed Script & Utterance Cheatsheet

### 1. Live Demo Turn 1: UC1 NCD Care Adherence (01:00 - 03:00)
* **Demo Action**: Select **`Sarvam AI (Indic Sovereign)`** in the top dropdown, tap the ASHA Rose Microphone Button.
* **Spoken Test Utterance**: 
  > `"What time should I take my BP medicine?"`  
  *(or in Hindi: `"BP ki dawai lene ka sahi samay kya hai?"`)*
* **What to Show Reviewer**:
  - Show clean bilingual patient guidance card rendering grounded ICMR/MoHFW protocol advice with source citations (`[ICMR 2018 Guidelines]`).

---

### 2. Live Demo Turn 2: UC2 Lifestyle & Salt Guidance (03:00 - 04:30)
* **Demo Action**: Tap the UC2 scenario chip or speak:
* **Spoken Test Utterance**: 
  > `"How much salt can I eat daily with high blood pressure?"`  
  *(or in Hindi: `"Namak kitna khana chahiye hypertension mein?"`)*
* **What to Show Reviewer**:
  - Show response citing **ICMR-NIN 2024 Dietary Guidelines** and **WHO HEARTS Module** ($<5\text{ g/day}$, avoiding pickles/papad).

---

### 3. Live Demo Turn 3: Safety Gate Emergency Trigger (04:30 - 06:30)
* **Demo Action**: Tap the Emergency red chip or speak:
* **Spoken Test Utterance**: 
  > `"सीने में दर्द हो रहा है"` *(or `"I am having severe chest pain spreading to my left arm"`)*
* **What to Show Reviewer**:
  - **CRITICAL**: Show that Safety Gate triggers **FIRST**.
  - Show the high-contrast **Emergency Warning Card** appearing with the **Call Ambulance (108 / 102)** button.
  - Explain V2 Semantic Net Concept: *"Regex is our V1 deterministic catch. To handle complex rural idioms, V2 uses a fast, local quantized embedding model (SentenceTransformer) running deterministic cosine-similarity checks against a vector DB of 1,000+ red-flag phrases—without letting an LLM make the safety call."*

---

### 4. Live Demo Turn 4: Inspector Mode & Simulated EMR FHIR Payload (06:30 - 08:00)
* **Demo Action**: Flip to **`Inspector Mode 🔍`** in the navbar.
* **What to Show Reviewer**:
  - Surface turn latency.
  - Show STT transcript & detected language code.
  - Show Intent classification confidence (`UC1` vs `UC2`).
  - Show 42 citable RAG chunk sources.
  - **Show Simulated EMR / FHIR Payload Card**: Show the structured HL7/FHIR R4 JSON bundle (`ClinicalImpression` & `Observation` resources) transmitted to the hospital dashboard before session RAM wipe!

---

### 5. The "Slow 3G" Network Flex (08:00 - 09:00)
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
   * **01:00 - 01:30**: Toggle Inspector Mode showing telemetry console, FHIR EMR payload, and 42 citable RAG sources.
   * Save video as `VDA_Demo_Backup.mp4` in the project root directory.

2. **Offline Fallback Execution**:
   * Select **`Local Dev Fallback`** in provider dropdown. The system runs 100% offline using synthetic voice and local grounded RAG.
