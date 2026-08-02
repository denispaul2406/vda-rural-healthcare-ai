# Build Brief: VDA — Medtronic Labs Hiring Challenge

**Read this alongside the attached PDF (`VDA_Candidate_Brief.pdf`). The PDF is the source of truth for
requirements; this document tells you how to execute against it, in what order, and to what bar.
Where the two conflict, the PDF wins — flag the conflict instead of silently picking one.**

Candidate: Denis. Deadline: submission + in-person discussion, Monday 3 August 2026, 12:00 noon IST.
That means the working window is roughly 2.5 days from when this is handed to you. Build in an order
where something demoable exists after every session, not just at the very end.

---

## 0. What "professional" means for this specific exercise

This is not a hackathon judged on feature count. The brief says explicitly: *"You are being asked to
show us how you think, where you choose to spend your judgement, and what you refuse to compromise
on."* That means:

- A narrow, fully-working, well-reasoned slice beats four shallow, half-working ones.
- Every non-trivial decision needs a one-line "why" recorded somewhere a reviewer will actually see it
  (not buried in commit messages).
- Code should read like something written by someone who has shipped healthcare-adjacent software
  before: defensive about failure modes, honest in its logging, boring where boring is correct.
- Nothing should claim to work that hasn't actually been run and observed working.

If you (Antigravity) hit a point where you're guessing at a requirement instead of finding it in the
PDF or this brief, stop and surface the question rather than inventing an assumption silently.

---

## 1. Scope decision — build this, don't build everything

Do **not** attempt all four use cases at full depth. Given the time budget and free-tier-only
constraint, that produces four broken demos instead of one strong one. Build:

1. **UC1 (NCD care adherence) — fully working, end to end, voice in → voice out.**
   This is the hero flow for the live demo.
2. **The safety gate — fully working, and wired as a cross-cutting layer that runs on every input,
   not scoped to UC1.** This is arguably more important than UC1 itself: the brief states a missed
   escalation is "the failure that matters most." The gate must be demonstrably able to fire and
   override the LLM regardless of which use case the utterance superficially resembles.
3. **UC2, UC3, UC4 — design-only.** Produce a clear architecture + rationale document for each
   (see §8). Do not write throwaway stub code that looks unfinished; either it's real or it's a
   diagram and a paragraph.

This split should be stated up front in the README so a reviewer immediately understands it was a
deliberate scoping choice, not something that ran out of time.

---

## 2. Non-negotiables (copied and made unambiguous from the source brief)

These are hard constraints. Nothing in this document overrides them, and no feature request should be
allowed to erode them:

1. **Low-confidence intent → deterministic fallback.** If intent classification confidence falls below
   a defined threshold, the system routes to a fixed "I'm not sure I understood — here are your
   options" response. It never lets the LLM guess and answer anyway.
2. **RAG-only answers.** Every substantive answer must be grounded in retrieved content from the
   relevant knowledge base. The LLM must not answer UC1 questions from parametric memory. If retrieval
   returns nothing relevant, say so — don't let the model fill the gap.
3. **Safety gate is deterministic, runs first, and cannot be overridden by the LLM.** This must be true
   architecturally, not just true by convention. The LLM should not be the thing deciding whether an
   escalation happens; a rule-based check runs before or in parallel to generation and the escalation
   decision short-circuits the pipeline. The LLM's job is producing what the patient hears once safety
   has cleared the input, not deciding whether safety clears it.
4. **No PII retention after session end.** Session state lives in memory (or a TTL-bounded store) and
   is discarded on session close. No conversation transcript, phone number, name, or health detail
   should persist to disk in the demo build. Say this out loud in the code, don't just imply it.
5. **Scope refusal.** Anything outside the four use cases gets a fixed, polite decline — never a
   fluent, plausible, wrong answer to an out-of-scope question.
6. **Never diagnose, prescribe, or interpret lab results.** Guardrail this at the prompt level *and*
   verify it's actually held during testing — add a few adversarial test utterances that try to get a
   diagnosis out of the system and confirm they get declined.

---

## 3. Reference architecture

Six stages, matching the brief's reference pipeline, but every stage should sit behind an interface so
the underlying provider is swappable without touching callers:

```
[Patient speech, mini-app]
        |
        v
[1. STT + language ID]  --  interface: SpeechToText.transcribe(audio) -> (text, detected_lang)
        |
        v
[2. Intent classification]  --  interface: IntentClassifier.classify(text) -> (intent, confidence)
        |                                    if confidence < THRESHOLD -> deterministic fallback, stop here
        v
[3. Safety gate]  --  interface: SafetyGate.check(text, intent) -> GateResult(escalate: bool, reason)
        |                                    if escalate -> fixed escalation response + alert hook, stop here
        |                                    (this stage MUST run regardless of intent/UC routing)
        v
[4. Agent + RAG]  --  interface: Answerer.answer(text, intent, retrieved_context) -> response_text
        |                                    retrieval is per-use-case, indexes isolated (see §6)
        v
[5. TTS]  --  interface: TextToSpeech.synthesize(text, lang) -> audio
        |
        v
[Patient hears response, mini-app]
```

Build stages 1, 3, 5 with real provider calls (Bhashini or Google Cloud, see §4). Build stages 2 and 4
as real code with a real small model call, not mocked.

---

## 4. Provider choices (free tier only — cost must stay at $0)

**STT/TTS — implement against an interface, default to whichever gets you running fastest, but document
both:**

- **Google Cloud Speech-to-Text / Text-to-Speech.** Free tier: roughly 60 minutes/month of STT, and
  several million characters/month of TTS depending on voice tier (Standard/WaveNet/Neural2 each carry
  their own free allowance). Reliable SDKs, good latency, straightforward to get working this weekend.
  Use this as the **default provider for the live demo**, since reliability under time pressure matters
  more than narrative points during the actual build.
- **Bhashini (bhashini.gov.in, ULCA API).** India's government-run ASR/MT/TTS platform, free for
  developers, purpose-built for Indian languages and code-switching, and — critically for this
  interview — the same public-infrastructure lineage a real deployment of VDA would eventually need to
  interoperate with (ABHA-adjacent, PM-JAY-adjacent government rails). Implement it as a second
  concrete class behind the same interface even if it's not what's wired up for the live demo. Note in
  `ARCHITECTURE.md` that Bhashini is the intended production choice and Google Cloud is the dev/demo
  fallback — this is a real, defensible piece of judgment to show in the discussion.

**Vector store:** Chroma or FAISS, local, free, no external service dependency (matters for a patchy
network during a live demo).

**LLM:** keep the provider configurable via environment variable behind an interface, same pattern as
STT/TTS. Whatever is used for building, make sure this could be swapped without touching business logic.

**Frontend:** a minimal Next.js "mini-app" shell simulating the embedded voice-first experience — mic
button, waveform or simple listening indicator, text captions rendered for the *demoer's* benefit only
(not required by the patient persona, but useful for showing a reviewer what's happening under the
hood).

---

## 5. Intent classification + fallback

- Small, explainable classifier: either an embedding-similarity match against labeled example
  utterances per use case, or a constrained LLM call that must return one of a fixed enum plus a
  confidence score — no free-form intent labels.
- Pick and hard-code a confidence threshold. Document why that number (not just "0.7 felt right" —
  reference the test set results in §9).
- Fallback response must be **fixed text**, not model-generated, so it can never itself be wrong or
  off-scope.

---

## 6. RAG design

- One retrieval index per use case, physically or logically separated (`data/protocols/uc1/`, etc.),
  so a UC1 query cannot retrieve UC2 content and vice versa. Write one sentence in
  `ARCHITECTURE.md` on why isolation matters here (answer: cross-contamination between "your medicine
  schedule" and "your scheme eligibility" is exactly the kind of confident-but-wrong answer this system
  exists to prevent).
- Seed the UC1 index with real public material: pull actual NCD/hypertension follow-up and medication
  adherence guidance from a government source (e.g. NPCDCS/NPCF materials) rather than inventing
  content. Cite the source in `data/protocols/uc1/SOURCES.md`.
- Retrieval failure (nothing relevant found above a similarity threshold) must produce an honest "I
  don't have information on that" — never a generated answer with no grounding.
- Every generated answer should be traceable back to which retrieved chunk(s) it came from — log this
  even if it's not shown to the patient, since it's exactly what a reviewer will ask to see.

---

## 7. Safety gate — build this with the most care of anything in the repo

- Rule-based, not model-based: a curated list of red-flag symptom phrases/patterns (chest pain,
  breathlessness, one-sided weakness, fainting, severe bleeding, etc., in the languages you're
  supporting) checked against the transcribed text before generation happens.
- Structurally unoverridable: the escalation branch must be a code path the LLM's output cannot alter —
  i.e., if the gate fires, the LLM is never called for that turn, or its output is discarded outright.
  Prove this with a test that force-feeds a "helpful, safe-sounding" LLM response and confirms the gate
  still wins.
- Include an "alert hook" — even a stub function `notify_clinician(session_id, reason)` that logs to
  console/file — so the design story ("a human being is alerted") is actually represented in code, not
  just claimed in prose.
- **Build and run an evaluation.** Create `data/test_sets/safety_gate_eval.csv` with ~30-50 labeled
  utterances (red-flag / not-red-flag), including hard negatives (mentions pain/illness but not
  urgent) and hard positives (colloquial, dialectal, or code-switched phrasing of an emergency). Run
  it, report recall and precision, and be honest if recall isn't 100% — say what you'd do to close the
  gap with more time. A believable 92% recall with a clear plan to improve it is more credible than a
  claimed, unverified 100%.

---

## 8. Design-only deliverables for UC2–UC4

For each of UC2 (scheme entitlement), UC3 (facility linkage), UC4 (teleconsultation & triage), produce
a one-to-two-page section (can live in one `UC2_UC4_DESIGN.md`) covering:

- What data it needs that UC1 didn't (patient profile/eligibility data for UC2, geolocation + facility
  capability data for UC3, live portal integration for UC4).
- Where it plugs into the existing pipeline (same intent classifier, same safety gate, same session
  model) vs. where it needs something new.
- The one hardest engineering problem in that use case and how you'd approach it (e.g., for UC3: facility
  capability data is almost certainly incomplete/stale in the real world — what does the system do when
  it isn't sure a facility can actually treat the condition?).
- What you would *not* attempt to solve in a first production version, and why.

This section is where a lot of interview credibility gets built — it should read like engineering
judgment, not a wishlist.

---

## 9. Repository structure

```
vda-build-challenge/
  README.md                      <- start here: what this is, scope decision, how to run it
  ARCHITECTURE.md                <- pipeline diagram in text, interface rationale, provider choices
  DESIGN_DECISIONS.md            <- running log of non-obvious choices and why (see §10)
  UC2_UC4_DESIGN.md              <- design-only sections per §8
  DEMO_SCRIPT.md                 <- exact walkthrough for the live 5-10 min discussion, plus backup plan
  .env.example
  backend/
    stt/            (interface + Google + Bhashini implementations)
    intent/         (classifier + fallback logic)
    safety_gate/    (rules + eval harness)
    rag/            (retrieval, per-use-case index builders)
    tts/            (interface + implementations)
    session/        (ephemeral session store, explicit TTL/no-persistence)
    pipeline.py     (wires stages 1-5 together; this file should make the "gate can't be
                     overridden" property visually obvious just from reading control flow)
  frontend/
    (Next.js mini-app: mic input, listening state, caption display for demo visibility)
  data/
    protocols/uc1/  (real sourced guidance text + SOURCES.md)
    test_sets/      (safety_gate_eval.csv + intent classification eval set)
  tests/
    test_safety_gate.py
    test_intent_fallback.py
    test_rag_isolation.py   (confirms UC1 retrieval never surfaces non-UC1 content)
```

---

## 10. `DESIGN_DECISIONS.md` — keep this updated as you build, not after

Every time a non-obvious call gets made, add a 2-4 line entry: what was decided, what the alternative
was, why this one won. This file is what turns "I built a thing" into "I can defend every choice in a
5-10 minute grilling." Suggested seed entries to fill in as you go:

- Why UC1 + safety gate, not broader shallow coverage.
- Why the confidence threshold is set where it is (tie to eval numbers).
- Why Bhashini is the intended production STT/TTS path but Google Cloud is what's live in the demo.
- Why the safety gate is rule-based rather than a fine-tuned classifier or LLM call (auditability,
  zero-training-data-needed, deterministic behavior under regulatory scrutiny).
- What "no PII retention" actually means in this build vs. what it would need to mean in production
  (e.g., real deployment would need this enforced at the infra/logging level too, not just app code).

---

## 11. Code quality bar

- Type hints throughout (Python) or TypeScript (frontend) — no untyped free-for-all.
- Docstrings on every public function/class explaining intent, not just parameters.
- No bare `except:` swallowing errors; provider calls (STT/TTS/LLM) should fail loudly and gracefully,
  with a fallback path a user actually experiences as "sorry, please try again" rather than a crash —
  this matters given the brief's own emphasis on patchy mobile connections.
- No hardcoded secrets; everything provider-related comes from environment variables, with
  `.env.example` documenting every key needed.
- No debug `print()` left in final code — use structured logging so a reviewer skimming logs during the
  demo can actually see the pipeline stages executing.

---

## 12. Definition of done — self-check before calling this finished

- [ ] UC1 runs end to end with real audio in, real audio out, on a fresh clone with just `.env` filled in.
- [ ] Safety gate fires on a red-flag utterance and the escalation response plays even when the
      underlying LLM would have generated something else — demonstrated by an actual test, not asserted.
- [ ] Safety gate eval numbers exist, are real, and are written into `DESIGN_DECISIONS.md` or the README.
- [ ] Low-confidence input produces the fixed fallback, not a guess.
- [ ] An out-of-scope question (e.g., "what's the weather") gets a fixed decline, not an answer.
- [ ] An attempted diagnosis/prescription request gets declined, tested with at least 2-3 adversarial
      phrasings.
- [ ] No session data persists after the session ends — demonstrated, not just claimed.
- [ ] UC2-4 design doc exists and each section names its hardest unsolved problem honestly.
- [ ] `DEMO_SCRIPT.md` has: the live walkthrough steps, the safety-gate trigger phrase to use live, and
      a backup recorded video path in case live audio fails during the actual discussion.
- [ ] README opens with the scope decision in the first paragraph, so a reviewer understands the
      shape of the submission in the first 10 seconds.

---

## 13. What not to do

- Don't build a fifth use case or add features beyond the four scoped ones — the brief explicitly
  forbids the system from doing anything outside them, and a submission that quietly does more misses
  the point of the exercise.
- Don't reach for a heavyweight multi-agent framework to look sophisticated; a clear linear pipeline
  that's easy to reason about live is worth more here than orchestration complexity.
- Don't fabricate protocol source content — use real, citable government guidance text for the RAG
  index, even if it's a small curated set rather than exhaustive.
- Don't let the LLM touch the escalation decision, ever, even as a "double-check" layer — the brief is
  explicit that this must never happen.
