# VDA — UI redesign & production hardening (follow-up brief)

Read alongside the original build brief. This pass has two goals: make the patient-facing UI feel
considered rather than templated, and close remaining production-readiness gaps before the Monday
noon deadline. Do the credential check in §4 first — it's the only item here with real downside risk
if skipped.

---

## 1. Why this pass exists

The current UI (obsidian background, Apple System Blue/Red, glassmorphism, emoji icons, described in
the docs as "Apple & Notion styled") reads as unexamined default AI-generated output, not a considered
design choice — evaluators who build with AI tools daily will recognize this pattern immediately.

More importantly: it's a UI built to impress someone looking at a dashboard, not to work for a patient
who can't read. Those are different design problems. Fix: split into two clearly separated views with
different jobs.

---

## 2. Patient view (default — what actually ships)

Designed for: a rural or semi-urban NCD patient, often older, low literacy, on a mid-range Android
phone, frequently outdoors in bright light.

**Color tokens** (literal hex, this is the product's own brand, not a design-system reference):
- `paper` `#FAF5EC` — page background. Light, not dark: a dark UI has real legibility problems in
  direct outdoor sun, which is a functional reason, not just an aesthetic one.
- `ink` `#3A2E28` / `ink-secondary` `#6B5D53` — text, warm dark brown rather than pure black (softer,
  easier to read for longer, less harsh in bright light).
- `rose` `#B8456B` / `rose-light` `#F4DDE5` — primary accent, used for the mic affordance and active
  states. Consider grounding this choice explicitly: it echoes the sari color associated with ASHA
  workers, India's real rural community health workers — the person this product is effectively
  standing in for. Worth one line in `ARCHITECTURE.md` either way, so the color choice reads as
  reasoned rather than arbitrary.
- `leaf` `#4C7A5E` / `leaf-light` `#E1EDE4` — confirmations, positive/safe states.
- `alert` `#B23A24` / `alert-light` `#F5DCD5` — reserved only for the emergency/escalation state, so it
  stays rare and meaningful.
- `sand` `#EDE4D3` — card borders, dividers, inactive chip backgrounds.

**Layout**
- One dominant focal element: a large circular mic button. Nothing else on screen competes with it.
- Sample-question shortcuts (the four use-case chips) exist only as a live-demo convenience for
  triggering scenarios quickly — keep them visually secondary (smaller, lower on the screen, quieter
  color) since a real patient never taps a labeled button, they just speak.
- Minimal on-screen text; anything shown is bilingual (English + Devanagari) and short — captions, not
  labels.
- Typography needs real Devanagari support, tested with actual Hindi text, not just Latin placeholder
  copy. Google Fonts' Hind (designed specifically for Indian-language interfaces) or Noto Sans are
  solid, purpose-appropriate choices — avoid defaulting to a generic system-UI font that was never
  checked against the Hindi content it actually has to render.
- Iconography: simple outline icons (pill, calendar, shield, map pin), never emoji. Emoji reads as
  prototype/hackathon output, not a shipped product.
- Motion: restrained. A single gentle pulse on the mic while listening is enough — no floating gradient
  blobs or decorative ambient animation, which is one of the strongest "AI-generated" tells.
- Emergency state: high-contrast and unmistakable, built around one clear action (a large "call now"
  button with the ambulance number) rather than a decorative alert banner. Urgency should live in
  clarity, not visual noise.

---

## 3. Judge / inspector view (secondary, explicitly toggled, off by default)

This view is for the evaluator, not the patient, and it's fine — good, even — for it to look and feel
different: denser, monospace, numbers visible. That contrast is itself worth narrating live: "the
patient never sees this; you're seeing it because you're the one evaluating the engineering."

- The toggle should be a real, visible control, not a hidden dev flag — flipping it live is a demo beat.
- Per turn, surface: STT transcript + detected language, intent + confidence, safety gate result, which
  RAG chunks (or bypass reason) fed the answer, clinician-alert status, and turn latency.
- Fine to use a dark, dense, monospace-flavored treatment here specifically — that's a different
  register serving a different audience, not the same mistake as defaulting the *patient* view to dark.

---

## 4. Do this first: credential exposure check

`gcp_service_account.json` (referenced directly in the build summary) must be confirmed excluded from
version control before anything is pushed publicly.

```bash
# confirm it's ignored going forward
cat .gitignore | grep -i "service_account\|\.env"

# confirm it was never committed in the past — .gitignore only stops future commits
git log --all --full-history -- "*service_account*" "*.env"
git log --all --full-history --source -- "**/*.json" | grep -i credential
```

If anything shows up in history, treat that key as burned — rotate it in the GCP console rather than
trusting a `git rm` to undo it. This is a five-minute check with real downside if skipped.

---

## 5. Remaining production hardening

1. Loading and error states for STT/TTS failure — a graceful "sorry, please try again" beats a silent
   crash, and the brief explicitly calls out patchy mobile connections as a real condition to design for.
2. Confirm `notify_clinician` only renders a "you've been notified" message to the patient when the
   alert call actually succeeded, not unconditionally.
3. Touch targets at least 44px; don't rely on color alone to convey state — pair color with an icon or
   short label, relevant given the target demographic may include older patients with reduced vision.
4. Once the UI lands, update README.md / ARCHITECTURE.md so the written description matches reality —
   docs that still describe an "Apple & Notion styled glassmorphic obsidian theme" after a redesign
   signal the docs weren't re-checked, which is its own credibility problem.

---

## 6. Explicit remove list

- Emoji used as primary iconography.
- Glassmorphism / heavy blur cards.
- Any doc or UI language describing the design as "Apple styled" or "Notion styled" — naming a borrowed
  brand identity undercuts the claim that this is your design, and it's an easy thing for an evaluator
  to notice and ask about.
- Decorative background gradients or animated blobs with no functional meaning.
- Dark-obsidian default backdrop specifically for the patient-facing view (the judge/inspector panel
  can stay dark deliberately — that's a different register, not the same mistake).

---

## 7. Time-boxing

Given the deadline: credential check first (§4, zero UI work, real risk if skipped) → patient-view
redesign (§2, this is the first thing the panel reacts to) → doc sync (§5.4) → judge-view polish (§3) →
remaining hardening items (§5.1-5.3) as time allows. A slightly-less-polished inspector panel costs
less than a leaked key or a first impression that still looks templated.
