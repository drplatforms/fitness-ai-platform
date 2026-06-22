# Backend Handoff Current

Current milestone: Daily Coach Async Developer-Only Prototype v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Branch: `feature/daily-coach-async-developer-only-prototype-v1`

Baseline accepted before this milestone: Daily Coach Async Service Shell / No Worker v1

## Backend implementation summary

Backend implemented a developer-only manual lifecycle harness around the accepted Daily Coach async service shell.

This is not a provider runtime milestone. It does not change normal Today behavior.

## Backend behavior added

- `POST /daily-coach/{user_id}/async-narrative/developer/jobs`
  - creates an in-memory async narrative job shell
  - uses deterministic Daily Next Action context identity
  - does not call a provider

- `GET /daily-coach/{user_id}/async-narrative/developer/jobs/latest`
  - inspects latest matching in-memory developer job shell

- `GET /daily-coach/{user_id}/async-narrative/developer/jobs/{job_id}`
  - inspects one developer job shell and displayability against current context identity

- `POST /daily-coach/{user_id}/async-narrative/developer/jobs/{job_id}/simulate`
  - supports manual developer-only simulation actions:
    - `approve_deterministic`
    - `mark_stale`
    - `expire`

## Streamlit Developer Mode behavior added

Added Developer Mode panel:

`Developer Prototype: Async Daily Coach Lifecycle`

The panel can manually:

- create a job shell
- inspect latest job shell
- view display state
- view sanitized job/context metadata
- simulate deterministic approval/stale/expired state

## Runtime boundary

- No provider execution.
- No direct_ollama call.
- No CrewAI call.
- No qwen3 call.
- No qwen3:32b call.
- No background worker.
- No queue.
- No scheduler.
- No polling.
- No DB schema or persistence.
- No FastAPI provider runtime.
- No normal Today provider call.
- No public Streamlit async display behavior.
- No model promotion.
- app/wapp Linux runtime split remains intact.

## Expected validation

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

## Next after Architecture acceptance

Recommended options:

1. Daily Coach Async Provider Runtime Design v1
2. Daily Coach Narrative Premium Voice Research v1
3. Daily Coach Async Persistence Design v1

Not authorized by this handoff:

- provider runtime
- qwen3 promotion
- qwen3 bridge
- worker / queue / scheduler
- DB persistence
- normal Today provider call
- public Streamlit async display
