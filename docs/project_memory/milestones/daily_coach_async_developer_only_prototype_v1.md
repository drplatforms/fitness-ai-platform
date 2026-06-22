# Daily Coach Async Developer-Only Prototype v1

Date: 2026-06-22

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Branch: `feature/daily-coach-async-developer-only-prototype-v1`

Previous accepted baseline: `Daily Coach Async Service Shell / No Worker v1`

## Purpose

Add a manual Developer Mode lifecycle harness around the accepted Daily Coach async service shell.

This milestone lets developers create, inspect, and safely simulate async narrative job shell state before any provider runtime, worker, scheduler, queue, persistence, or normal Today-page async behavior is introduced.

## Implemented

- Added developer-only FastAPI route to create an in-memory async Daily Coach narrative job shell.
- Added developer-only FastAPI route to inspect latest/job status.
- Added developer-only FastAPI route to simulate deterministic lifecycle transitions:
  - deterministic simulated approval
  - stale
  - expired
- Added Streamlit Developer Mode panel:
  - `Developer Prototype: Async Daily Coach Lifecycle`
- Reused the accepted `DailyCoachAsyncNarrativeService` shell.
- Reused deterministic context identity/hash behavior from `build_daily_coach_narrative_context_identity`.
- Returned sanitized developer-only job metadata.
- Added focused API/service/UI/static tests.

## Developer-only route behavior

The route/panel can expose sanitized lifecycle metadata in Developer Mode only:

- job id
- status
- user id
- target date
- next action id
- workflow target
- context hash
- prompt contract version
- validator version
- requested provider/model metadata
- model lane
- bridge eligibility
- displayability state
- expiration metadata
- deterministic simulated approval payload when manually requested

## Boundary preserved

- no provider execution
- no direct_ollama call
- no CrewAI call
- no qwen3 call
- no qwen3:32b call
- no background worker
- no queue
- no scheduler
- no polling
- no DB schema
- no DB persistence
- no `daily_coach_narrative_jobs` table
- no provider cache
- no normal Today provider call
- no public async narrative display
- no provider output persistence
- no model promotion
- no qwen3 bridge
- deterministic Daily Next Action remains primary
- normal Today Coach Note behavior remains unchanged
- app/wapp/Linux runtime split remains unchanged

## Normal Today behavior

Normal Today behavior remains deterministic and unchanged.

The normal Today card route does not return async job metadata, context identity, runtime metadata, provider execution metadata, or developer lifecycle payloads.

## Validation focus

Required focused validation:

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

## Non-goals

This milestone does not authorize:

- provider runtime
- direct Ollama async runtime
- CrewAI async runtime
- qwen3 use
- qwen3:32b use
- worker / queue / scheduler
- DB persistence
- provider cache behavior
- normal Today provider calls
- public async narrative display
- model promotion
- qwen3 bridge behavior
- report/nutrition/workout changes
- app/wapp command behavior changes

## Proposed final status

`DAILY_COACH_ASYNC_DEVELOPER_ONLY_PROTOTYPE_V1_ACCEPTED`
