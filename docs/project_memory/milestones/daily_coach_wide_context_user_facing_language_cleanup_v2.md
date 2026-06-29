# Daily Coach Wide Context User-Facing Language Cleanup v2

Status: Backend implementation patch ready for local validation.

Baseline: `main` at `490d2ae Merge daily coach wide context copy cleanup qa readability v1`.

Baseline snapshot: `fitness_ai_snapshot_2026-06-28_490d2ae_main_merge-daily-coach-wide-context-copy-cleanup-qa-readability-v1.zip`.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_USER_FACING_LANGUAGE_CLEANUP_V2_IMPLEMENTATION_COMPLETE`.

## Purpose

QA found that v1 readability helped and wide-context remains the best Daily Coach provider-copy direction so far, but the best first-pass output still leaked backend-shaped wording such as `approved option`, `remaining protein gap`, `green-light day`, and generic `planned session` / `planned workout` phrasing.

This milestone keeps the architecture and readability infrastructure, but cleans provider-facing language so the model sees plain food/session guidance instead of backend words likely to be repeated.

## Implemented direction

- Sanitize writer-facing context for v2 phrases.
- Keep food choices as simple food ideas, not approval terminology.
- Prefer `if protein is still short` / `if calories are still short` style language.
- Replace `green-light day` with recovery-supportive training wording.
- Replace generic planned-session phrasing with today/session language where possible.
- Expand product-language findings for v2 copy leaks.
- Preserve exact first-pass draft capture.
- Expand pasteback report with full exact deterministic baseline, current narrow path, and best wide-context variant.

## Boundaries

- Developer-only diagnostic tooling.
- Normal Today behavior unchanged.
- Deterministic remains default.
- OpenAI remains opt-in/evaluation-only.
- No provider promotion.
- No raw provider envelope persistence.
- No product approval-gate rewrite.
- No Streamlit/API/report/database behavior changes.

## Known baseline drift

`tests/test_daily_narrative_rich_day_service.py` remains known copy-expectation drift and is not patched in this milestone. Full-suite green must not be claimed if that drift remains.
