# QA Handoff Current

Current milestone: Daily Coach Async Developer-Only Prototype v1

Status: IMPLEMENTED / READY FOR QA REVIEW

Branch: `feature/daily-coach-async-developer-only-prototype-v1`

Baseline accepted before this milestone: Daily Coach Async Service Shell / No Worker v1

## QA focus

QA should verify that the developer-only async lifecycle harness works while normal Today behavior remains unchanged.

This is not a provider runtime milestone.

## Expected Developer Mode behavior

The Developer Mode panel:

`Developer Prototype: Async Daily Coach Lifecycle`

should allow manual testing of:

- create async job shell
- inspect latest async job shell
- inspect display state
- inspect context identity/hash metadata
- inspect requested provider/model metadata as metadata only
- simulate deterministic approval
- simulate stale state
- simulate expired state

## Expected normal Today behavior

Normal Today behavior should remain unchanged:

- Daily Next Action remains deterministic and primary.
- Today Coach Note remains deterministic unless an existing accepted session-only bridge approval is active.
- Normal Today page load must not create an async job.
- Normal Today page load must not call a provider.
- Normal Today card response must not expose async job metadata, context identity, provider execution metadata, or runtime/debug internals.

## Boundary checks

- no provider execution
- no direct_ollama call
- no CrewAI call
- no qwen3 call
- no qwen3:32b call
- no worker
- no queue
- no scheduler
- no polling
- no DB/schema creation
- no async persistence
- no provider cache
- no normal Today provider call
- no public async narrative display
- no model promotion
- qwen3 remains not bridge-enabled
- app/wapp Linux runtime split remains intact

## Recommended validation

```powershell
git diff --check
pytest tests/test_daily_coach_async_developer_only_prototype_v1.py -q
pytest tests/test_daily_coach_async_service_shell_v1.py -q
pytest tests/test_async_daily_coach_narrative_contracts_v1.py -q
pytest tests/test_streamlit_daily_coach_narrative_developer_panel.py -q
pytest tests/test_local_developer_command_menu_v1.py -q
pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python -m py_compile ui/streamlit_app.py
```

Manual QA suggestion:

1. Start app normally.
2. Confirm Today loads without async job creation.
3. Turn on Developer Mode.
4. Open `Developer Preview: Daily Coach Narrative`.
5. Open `Developer Prototype: Async Daily Coach Lifecycle`.
6. Create job shell.
7. Inspect display state and context hash.
8. Simulate deterministic approval.
9. Simulate stale/expired state.
10. Confirm no provider runtime is attempted.
