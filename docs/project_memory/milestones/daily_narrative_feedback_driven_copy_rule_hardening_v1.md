# Daily Narrative Feedback-Driven Copy Rule Hardening v1

Status: implemented / ready for validation.

Branch: `feature/daily-narrative-feedback-driven-copy-rule-hardening-v1`

Baseline: `main` at `644792d` after Daily Narrative User Feedback Capture + Preferred Rewrite Loop v1 was accepted and merged.

## Goal

Use captured bad / better / approved Daily Narrative Voice Lab feedback to harden deterministic copy families, copy-quality checks, app-side voice examples, and scenario-specific rewrite guidance.

## Implemented scope

- Hardened banned and awkward Daily Narrative phrase checks.
- Added rejection coverage for:
  - `let how you move decide`
  - `session stays heavy`
  - `does not support expended energy`
  - `optimal results`
- Replaced rich all-domain day copy with full-day review language.
- Replaced high-soreness lower-body planned copy with body-reaction progression language.
- Replaced mixed-signals copy with readiness / recovery-limiting-factor language.
- Updated Voice Lab quality notes with scenario-specific feedback guidance.
- Updated Daily Narrative voice contract and examples.
- Added tests for scenario-specific hardening.

## Preserved boundaries

- No normal Today behavior change.
- No provider call added.
- No provider/model promotion.
- No public/default provider display.
- No CrewAI.
- No worker, queue, scheduler, or polling.
- No raw rows/logs/notes/set rows exposed.
- No prompt, scratchpad, chain-of-thought, or secret exposure.
- No runtime feedback artifact committed.
- No Streamlit theme or layout cleanup.

## Acceptance focus

- Daily Narrative deterministic copy no longer emits known rejected phrases.
- Rich all-domain scenario uses full-day view language without overclaiming optimal results.
- High-soreness lower-body planned scenario uses body-reaction progression language.
- Mixed-signals scenario avoids unsupported physiology and uses readiness as the check.
- Existing feedback capture remains safe and Developer Mode-only.
