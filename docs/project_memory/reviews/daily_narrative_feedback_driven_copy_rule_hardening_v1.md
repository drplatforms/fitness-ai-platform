# Daily Narrative Feedback-Driven Copy Rule Hardening v1 Review

Status: implementation ready for Architecture / QA review.

## Summary

This milestone applies the first captured Voice Lab feedback to deterministic Daily Narrative copy. It improves the specific scenarios the user reviewed instead of treating the problem as model size, provider selection, or generic prompt tuning.

## Confirmed changes

- Rich all-domain copy now uses a full-day view that considers training load, food intake, and recovery together.
- Rich all-domain copy avoids claiming alignment or `optimal results` unless backend facts prove it.
- Recovery-present/planned-workout copy keeps the direct recovery-based intensity planning direction.
- High-soreness/lower-body planned copy now says to keep first sets conservative and let body response guide progression.
- Mixed-signals copy now frames recovery as the weaker point and lets readiness guide the next training push.
- Copy-quality checks now flag additional user-rejected phrases.
- Voice examples now preserve scenario-specific bad/preferred examples for future provider/deterministic work.

## Regression expectations

- Voice Lab candidates remain public-safe.
- Feedback capture remains Developer Mode-only.
- Saving feedback does not call providers or regenerate candidates.
- Runtime feedback JSONL remains local and unstaged.
- Normal Today remains unchanged.
- Workout selection and Weekly Summary regressions remain unaffected.

## Review notes

This is a copy-rule hardening milestone, not a provider milestone. The right QA question is whether deterministic candidates and quality checks now reflect the user's copy feedback while preserving factual grounding.
