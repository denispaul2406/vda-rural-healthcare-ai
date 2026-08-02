# System Architecture & Technical Specifications — VDA

## 1. Reference Architecture Pipeline

```
[ Patient Voice Input / Web Audio ]
               │
               ▼
┌─────────────────────────────────────────┐
│ 1. STT + Language Identification        │  Interface: SpeechToText.transcribe(bytes) -> (text, lang)
└────────────────────┬────────────────────┘  Implementations: SarvamSpeechToText, GoogleSpeechToText, BhashiniSpeechToText
                     │
                     ▼
┌─────────────────────────────────────────┐
│ 2. Intent Classification                │  Interface: IntentClassifier.classify(text) -> (intent, confidence)
└────────────────────┬────────────────────┘  Supported: UC1 (Adherence), UC2 (Scheme Check), UC3 (Facility Linkage), UC4 (Triage)
                     │                       Rule: If confidence < 0.75 -> Fixed Fallback, STOP
                     ▼
┌─────────────────────────────────────────┐
│ 3. Safety Gate (Deterministic Rule Check)│  Interface: SafetyGate.check(text) -> GateResult(escalate, reason)
└────────────────────┬────────────────────┘  Rule: IF escalate == True:
                     │                              - Dispatch notify_clinician()
                     │                              - Return Emergency Audio
                     │                              - BYPASS LLM GENERATION ENTIRELY
                     ▼
┌─────────────────────────────────────────┐
│ 4. Grounded RAG + Agent                 │  Interface: Answerer.answer(text, retrieved_context) -> answer_text
└────────────────────┬────────────────────┘  Index Isolation: 49 Citable Chunks from 16 ICMR/WHO/State PDFs
                     │
                     ▼
┌─────────────────────────────────────────┐
│ 5. TTS Audio Synthesizer                │  Interface: TextToSpeech.synthesize(text, lang) -> audio_bytes
└────────────────────┬────────────────────┘  Implementations: SarvamTextToSpeech, GoogleTextToSpeech, BhashiniTextToSpeech
                     │
                     ▼
[ Patient Hears Response / Audio Player ]
```

---

## 2. Interface Specifications & Decoupling

All core pipeline steps sit behind clean Python Abstract Base Classes (ABCs):

### A. Speech-to-Text (`backend/stt/interface.py`)
```python
class SpeechToText(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> tuple[str, str]:
        """Returns (transcribed_text, detected_language_code)"""
```

### B. Text-to-Speech (`backend/tts/interface.py`)
```python
class TextToSpeech(ABC):
    @abstractmethod
    def synthesize(self, text: str, lang_code: str = "en-IN") -> bytes:
        """Returns audio binary bytes (WAV/MP3)"""
```

### C. Safety Gate (`backend/safety_gate/gate.py`)
```python
class SafetyGate:
    def check(self, utterance: str, session_id: str, lang_code: str) -> GateResult:
        """Returns GateResult(escalate: bool, reason: str, response_text: str)"""
```

---

## 3. Sovereign Indic Voice Stack: Sarvam AI vs Bhashini vs Google Cloud

| Provider | Role in VDA System | Dialect & Code-Switching Capability | Voice Naturalness |
| :--- | :--- | :--- | :--- |
| **Sarvam AI (`sarvam.ai`)** | **Primary Sovereign Indic Stack** | State-of-the-art Saaras ASR trained on regional Indian accents & Hinglish | High naturalness Bulbul TTS (`meera` speaker) |
| **Bhashini (ULCA API)** | **Government Infrastructure Target** | Purpose-built for Indian government rails (ABHA / PM-JAY) | Indic TTS coqui models |
| **Google Cloud** | **Enterprise Fallback** | Strong general ASR | WaveNet / Standard voices |

---

## 4. Multi-Document RAG Knowledge Base & Sourced PDF Specifications

The RAG Knowledge Base is built by parsing and indexing **16 official government & WHO guideline PDFs** stored in `data/docs/`:

| # | File Name | Document Authority & Content Summary |
| :---: | :--- | :--- |
| 1 | `PM-JAY Empanelled Hospital Manual-karnataka.pdf` | **National Health Authority / SAST Karnataka**: Official directory of PM-JAY empanelled public & private hospitals in Karnataka offering cashless secondary/tertiary care for NCD complications. |
| 2 | `24x7-phc-karnataka.pdf` | **Department of Health & Family Welfare, Govt of Karnataka**: Official directory of 24/7 Primary Health Centres (PHCs) and Community Health Centres (CHCs) across Karnataka districts. |
| 3 | `National List of Essential Medicines (NLEM) 2022.pdf` | **Ministry of Health & Family Welfare (MoHFW), Govt of India**: Specifies free essential NCD drugs (Amlodipine, Telmisartan, Metformin, Insulin) mandated for free distribution at Sub-Centres, HWCs, and PHCs. |
| 4 | `OG on Welness interventions for ABHWC_eng_Final.pdf` | **MoHFW Ayushman Bharat HWC Division**: Operational guidelines for wellness interventions, yoga, and annual NCD screening protocols at Health and Wellness Centres. |
| 5 | `DietaryGuidelinesforNINwebsite.pdf` | **ICMR - National Institute of Nutrition (NIN 2024)**: Flagship dietary guidelines for Indians detailing salt reduction (<5g/day), coarse millets (ragi, bajra, jowar), and oil limits. |
| 6 | `ICMR_GuidelinesType2diabetes2018_0.pdf` | **Indian Council of Medical Research (ICMR)**: Clinical guidelines for screening, diagnosis, monitoring, and medication schedule for Type 2 Diabetes Mellitus. |
| 7 | `WHO Guidelines on Physical Activity and Sedentary Behaviour (2020).pdf` | **World Health Organization**: Global recommendations for physical activity (150–300 mins/week moderate exercise) for adults living with chronic NCDs. |
| 8 | `WHO HEARTS Technical Package – Healthy Lifestyle Counselling Module (2018).pdf` | **World Health Organization**: Brief counseling protocols for salt reduction, tobacco cessation, alcohol avoidance, and physical activity in primary care. |
| 9 | `WHO HEARTS Technical Package.pdf` | **World Health Organization**: Global operational framework for cardiovascular disease management in primary health care settings. |
| 10 | `WHO HEARTS – Evidence-Based Treatment Protocols.pdf` | **World Health Organization**: Standardized step-by-step clinical treatment algorithms for hypertension and diabetes management. |
| 11 | `WHO HEARTS Healthy Lifestyle Counselling Module.pdf` | **World Health Organization**: Patient-facing lifestyle counseling tools for primary healthcare workers. |
| 12 | `WHO HEARTS Risk-Based CVD Management.pdf` | **World Health Organization**: Risk-stratification protocols and referral algorithms for cardiovascular disease prevention. |
| 13 | `Guidelines for NPPCF.pdf` | **MoHFW National Programme Guidelines**: Operational guidelines for prevention, screening, and control of chronic non-communicable health conditions. |
| 14 | `WHO-NMH-NVI-18.14-eng.pdf` | **World Health Organization**: Technical guidance on integrated NCD care delivery in primary healthcare systems. |
| 15 | `WHO-NMH-NVI-18.4-eng.pdf` | **World Health Organization**: Guidelines on team-based care and task-sharing among non-physician healthcare workers (ANMs/ASHAs). |
| 16 | `WHO-UCN-NCD-20.1-eng.pdf` | **World Health Organization**: Global guidelines on diagnosis and management of Type 2 Diabetes in low-resource primary care settings. |

Every retrieved chunk includes source attribution metadata (`[Source: ICMR-NIN 2024 Dietary Guidelines]`, `[Source: WHO HEARTS Technical Package, p. 12]`, `[Source: Karnataka 24x7 PHC Directory]`), allowing evaluators to verify the clinical grounding of generated answers.

---

## 5. Ephemeral Session & Zero PII Architecture

```
[ User Dialogue Turn ]
       │
       ▼
[ Ephemeral Session Store (RAM) ] ──(TTL 30 mins / Close Session)──▶ [ Complete Memory Destruction ]
       │
       ❌ Zero Database Writes / Zero Disk Transcripts Saved
```
Session data lives strictly in RAM within `EphemeralSessionStore`. Calling `DELETE /api/session/{session_id}` immediately destroys all in-memory dialog state, ensuring compliance with health data privacy guidelines.
