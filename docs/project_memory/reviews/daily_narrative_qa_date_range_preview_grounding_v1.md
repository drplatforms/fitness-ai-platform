# Review: Daily Narrative QA Date Range Preview / Grounding v1

Proposed status: `DAILY_NARRATIVE_QA_DATE_RANGE_PREVIEW_GROUNDING_V1_ACCEPTED`

The implementation creates a Developer Mode-only seeded QA date/date-range preview seam for Daily Narrative. This is intentionally a grounding milestone: it makes the selected-date facts and missing-data reasons available before any broader provider voice/model tuning.

Acceptance should be based on:

- Developer Mode-only controls.
- Typed QA user/date/lookback inputs.
- Backend-owned safe aggregate context.
- Deterministic preview grounded in selected facts.
- No normal Today behavior change.
- No provider auto-run.
- Existing Weekly Coach Summary provider prototype regressions preserved.

Provider/model quality remains a follow-up, not part of this milestone.
