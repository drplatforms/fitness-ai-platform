# Architecture Handoff Current

Current milestone: Daily Coach Async Developer-Only Prototype v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: DAILY_COACH_ASYNC_DEVELOPER_ONLY_PROTOTYPE_V1_ACCEPTED

Branch: `feature/daily-coach-async-developer-only-prototype-v1`

Baseline accepted before this milestone: Daily Coach Async Service Shell / No Worker v1

Baseline main commit: `54131ea Merge project memory transition packet v1`

## Summary

Daily Coach Async Developer-Only Prototype v1 adds a manual Developer Mode lifecycle harness around the accepted Daily Coach async service shell.

The prototype can create, inspect, and safely simulate in-memory async narrative job shell state for QA/developer inspection.

Normal Today behavior remains unchanged.

## Implemented

- Developer-only FastAPI route to create an async narrative job shell.
- Developer-only FastAPI route to inspect latest/job status.
- Developer-only FastAPI route to simulate deterministic lifecycle transitions:
  - `approve_deterministic`
  - `mark_stale`
  - `expire`
- Streamlit Developer Mode panel:
  - `Developer Prototype: Async Daily Coach Lifecycle`
- Sanitized job/context diagnostics for Developer Mode only.
- Focused tests for API lifecycle behavior, service-shell boundary, normal Today response shape, and Streamlit Developer Mode visibility.
- Project memory milestone/review docs.

## Boundary confirmation

- developer-only path only: CONFIRMED
- normal Today behavior unchanged: CONFIRMED
- service shell reused: CONFIRMED
- no provider execution: CONFIRMED
- no direct_ollama call: CONFIRMED
- no CrewAI call: CONFIRMED
- no qwen3 call: CONFIRMED
- no qwen3:32b call: CONFIRMED
- no worker: CONFIRMED
- no queue: CONFIRMED
- no scheduler: CONFIRMED
- no polling: CONFIRMED
- no DB schema: CONFIRMED
- no async persistence: CONFIRMED
- no normal Today provider call: CONFIRMED
- no public async narrative display: CONFIRMED
- no model promoted: CONFIRMED
- qwen3 remains not bridge-enabled: CONFIRMED
- deterministic Daily Next Action remains primary: CONFIRMED
- app/wapp runtime split preserved: CONFIRMED

## Files changed

- `api/routes/daily_coach.py`
- `ui/streamlit_app.py`
- `tests/test_daily_coach_async_developer_only_prototype_v1.py`
- `tests/test_daily_coach_async_service_shell_v1.py`
- `tests/test_streamlit_daily_coach_narrative_developer_panel.py`
- `docs/project_memory/current_state.md`
- `docs/project_memory/project_continuity_bootstrap.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/milestones/daily_coach_async_developer_only_prototype_v1.md`
- `docs/project_memory/reviews/daily_coach_async_developer_only_prototype_v1.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`
- `tools/project_memory_check.py`
- `tests/test_project_memory_check.py`

## Validation requested

```powershell
git diff --check
pytest tests/test_daily_coach_async_developer_only_prototype_v1.py -q
pytest tests/test_daily_coach_async_service_shell_v1.py -q
pytest tests/test_async_daily_coach_narrative_contracts_v1.py -q
pytest tests/test_streamlit_daily_coach_narrative_developer_panel.py -q
pytest tests/test_local_developer_command_menu_v1.py -q
pytest tests/test_project_memory_check.py -q
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
. .\scripts\fitness_commands.ps1
fsweep
scripts/dev_commit_check.ps1 -Mode code
```

## Non-goals preserved

- no provider runtime
- no direct Ollama async runtime
- no CrewAI async runtime
- no qwen3 bridge
- no model promotion
- no DB persistence
- no worker / queue / scheduler
- no normal Today provider call
- no public async narrative display
- no report/nutrition/workout changes
- no command-menu behavior changes

## Recommended next milestone after acceptance

Architecture should choose one of:

1. Daily Coach Async Provider Runtime Design v1
2. Daily Coach Narrative Premium Voice Research v1
3. Daily Coach Async Persistence Design v1

None are authorized by this handoff.
