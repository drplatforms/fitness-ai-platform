# Project Memory Alignment + North Star Architecture v1 Review

Status: IMPLEMENTED / PENDING ARCHITECTURE REVIEW

## Review summary

The branch performs a project-memory alignment sweep and creates a north-star future architecture ledger.

## Files reviewed

Reviewed project memory, handoff, AI boundary, section registry, README/status, milestone, and review docs with emphasis on current accepted main and provider boundaries.

## Files changed

- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/ai_boundaries.md`
- `docs/project_memory/section_registry_summary.md`
- `docs/project_memory/product_vision.md`
- `docs/project_memory/future_architecture_ledger.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`
- `docs/project_memory/handoffs/ai_provider_handoff_current.md`
- `docs/project_memory/handoffs/codex_handoff_rules.md`
- `docs/project_memory/milestones/project_memory_alignment_north_star_architecture_v1.md`
- `docs/project_memory/reviews/project_memory_alignment_north_star_architecture_v1.md`
- `docs/project_memory/README.md`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `readme.md`
- `tools/project_memory_check.py`
- `tests/test_project_memory_check.py`

## Stale claims removed or corrected

- old current branch references
- old latest accepted milestone references
- confusing Daily Coach status notes
- outdated provider wording implying older Nutrition/Training states
- missing failed-bridge classification
- missing future architecture ledger

## Conflicts resolved

- Coach's Read, Today Coach Note, Daily Grounded Recommendation, and Developer Preview are now described as separate surfaces.
- The failed same-session bridge is recorded as reference-only, not accepted.
- qwen3 models are recorded as experimental/future candidates, not promoted.
- Provider persistence remains not approved for Daily Coach narrative.

## Docs intentionally left unchanged

Historical milestone, review, runtime QA, and architecture docs are preserved unless they were current-state or handoff docs. Historical files remain useful record artifacts and should not be rewritten to hide project history.

## Remaining open questions

Remaining questions are tracked in `docs/project_memory/open_questions.md` under active, parked, resolved, and reference-only sections.

## Boundary confirmation

- docs/tooling-only
- no app runtime behavior changed
- no provider behavior changed
- no UI behavior changed
- no schema changes
- no persistence changes
- no model promotion
- no same-session approval added
- no provider defaults changed
- no workout/nutrition/catalog/report behavior changed
- `qa_artifacts/` not committed
