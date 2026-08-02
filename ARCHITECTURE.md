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
└────────────────────┬────────────────────┘  Supported: UC1 (Adherence), UC2 (Lifestyle & Diet), Out-of-Scope
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
└────────────────────┬────────────────────┘  Index Isolation: 42 Citable Chunks from 12 ICMR/WHO PDFs
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

## 4. Multi-Document RAG Knowledge Base Architecture

The RAG Knowledge Base is built by parsing and indexing **12 official government & WHO guideline PDFs** stored in `data/docs/`:
1. `DietaryGuidelinesforNINwebsite.pdf` (ICMR-NIN 2024 Dietary Guidelines for Indians)
2. `ICMR_GuidelinesType2diabetes2018_0.pdf` (ICMR Type 2 Diabetes Guidelines)
3. `WHO Guidelines on Physical Activity and Sedentary Behaviour (2020).pdf`
4. `WHO HEARTS Technical Package – Healthy Lifestyle Counselling Module (2018).pdf`
5. `WHO HEARTS Technical Package.pdf`
6. `WHO HEARTS – Evidence-Based Treatment Protocols.pdf`
7. `WHO HEARTS Healthy Lifestyle Counselling Module.pdf`
8. `WHO HEARTS Risk-Based CVD Management.pdf`
9. `Guidelines for NPPCF.pdf` (MoHFW Guidelines)
10. `WHO-NMH-NVI-18.14-eng.pdf`
11. `WHO-NMH-NVI-18.4-eng.pdf`
12. `WHO-UCN-NCD-20.1-eng.pdf`

Every retrieved chunk includes source attribution metadata (`[Source: ICMR-NIN 2024 Dietary Guidelines]`, `[Source: WHO HEARTS Technical Package, p. 12]`), allowing evaluators to verify the clinical grounding of generated answers.

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
