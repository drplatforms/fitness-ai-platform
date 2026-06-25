# Daily Narrative QA Date Range Preview / Grounding v1

Status: implemented for Architecture review.

This milestone adds a Developer Mode-only Daily Narrative QA preview path for seeded QA users and selected dates/date ranges. The goal is grounding, not model promotion or public Today behavior changes.

## Implemented behavior

- Added backend-owned QA context construction from typed QA user, selected date, and lookback days.
- Uses the verified seeded QA window `2026-05-31` through `2026-06-06` as the default preview target.
- Context includes safe aggregate fact counts, provenance, data quality, and missing-data reasons.
- Deterministic fallback text now explains the `because` for selected QA context.
- Developer Mode Streamlit preview can select QA user/date/lookback without parsing display labels as source of truth.
- Optional CLI supports dry-run deterministic preview and explicit live provider smoke.
- Normal Today behavior remains unchanged.

## Boundaries

- No public/default Daily Narrative provider behavior was added.
- No provider call occurs on page load.
- No automatic generation, worker, queue, scheduler, or polling was added.
- No CrewAI was added.
- No qwen3/qwen3:8b/14B/32B promotion was added.
- Raw rows, food logs, daily check-in notes, workout set rows, provider output, prompts, scratchpad, and secrets are not exposed.

## Follow-up

Daily Narrative Voice + Grounding v1 should tune provider voice/model behavior after this QA grounding seam is accepted.
