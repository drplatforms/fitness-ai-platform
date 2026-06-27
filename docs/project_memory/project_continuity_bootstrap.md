# Project Continuity Bootstrap — Daily Coach Narrative Value-Aware Provider Comparison v1

Current source of truth: `main` at `e1f7bd3`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_e1f7bd3_nutrition-actuals-provenance-debug-integration-design-v1.zip`.

Current milestone: Daily Coach Narrative Value-Aware Provider Comparison v1.

Branch: `feature/daily-coach-narrative-provider-comparison-v1`.

Status: backend implementation complete / ready for Architecture review.

Implemented normal endpoint: `GET /daily-coach/{user_id}/narrative?date=YYYY-MM-DD`.

Implemented debug endpoint: `GET /daily-coach/{user_id}/narrative/debug?date=YYYY-MM-DD`.

The milestone adds a strict provider-candidate comparison path over `DailyCoachSynthesis` with approved value context, parser, validator, approved narrative contract, deterministic renderer, and deterministic fallback.

## First files to read

1. `docs/project_memory/current_state.md`
2. `docs/project_memory/next_milestone.md`
3. `docs/project_memory/project_state.json`
4. `docs/project_memory/handoffs/architecture_handoff_current.md`
5. `docs/project_memory/handoffs/backend_handoff_current.md`
6. `docs/project_memory/handoffs/qa_handoff_current.md`
7. `models/daily_coach_value_narrative_models.py`
8. `services/daily_coach_value_narrative_service.py`
9. `services/daily_coach_narrative_validation_service.py`
10. `api/routes/daily_coach.py`

## Doctrine to preserve

Backend owns facts, validation, persistence, provenance/confidence, and safety boundaries.

Providers may produce candidate wording only.

Provider output becomes user-facing only after strict parse, backend validation, and approval.

Deterministic fallback remains mandatory.

## Current workflow reminders

- Use phase-separated delivery.
- Never stage with `git add .`.
- Temporary patch files live outside the repo, usually under `C:\projects`.
- Use `git apply --check ..\<patch>.patch` before applying patches.
- Do not run repo-wide mutating formatters for feature work.
- Long handoffs must be in one copy/paste-ready code block.
- Backend does not create final canonical accepted snapshots.
- Linux pull validation follows Windows push.

## Historical continuity anchors

- Project Continuity System v2
- Daily Coach Async Provider Runtime Design v1
- Daily Coach Async Persistence Design v1
- Provider Narrative QA Matrix v2
- qwen3:32b research / future premium async candidate only
- normal Today provider call remains disallowed unless explicitly configured
- sound right and be right

## Accepted historical workflow anchors — reference-only

Current Accepted Milestone Stack is maintained by `current_state.md` and `project_state.json`.

Sound right and be right remains the provider/coach-copy doctrine.

Daily Coach Async Service Shell / No Worker v1 remains a historical accepted milestone.

Daily Coach Async Developer-Only Prototype v1 remains a historical accepted milestone.

Developer Mode-only manual lifecycle prototype remains reference-only.

The `app` command launches Linux runtime.

qwen3 is not bridge-enabled.

Historical Daily Coach async work was service shell only with no provider runtime yet.

What Future Chats Must Do First: read current_state, project_state, next_milestone, current handoffs, and this bootstrap before acting.
