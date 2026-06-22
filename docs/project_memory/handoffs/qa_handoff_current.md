# QA Handoff Current

Current milestone: Daily Coach Async Service Shell / No Worker v1

Status: IMPLEMENTED / READY FOR QA REVIEW

QA focus:

- Verify `tests/test_daily_coach_async_service_shell_v1.py` passes.
- Verify `tests/test_async_daily_coach_narrative_contracts_v1.py` still passes.
- Verify `tests/test_local_developer_command_menu_v1.py` still passes so app/wapp Linux runtime hotfix remains intact.
- Verify project-memory checks pass.
- Verify fsweep is clean.

Expected behavior:

- Approved matching job can be selected as displayable.
- queued/generating/provider_succeeded_pending_validation jobs are not displayable.
- rejected_parse/rejected_validation/provider_timeout/provider_error/stale/fallback_available jobs are not displayable.
- approved job without payload is not displayable.
- expired job is not displayable.
- context hash mismatch is not displayable.
- target date, next action, workflow target, prompt contract, validator version, provider, and model mismatches are not displayable.

Boundary checks:

- no provider execution
- no FastAPI route addition
- no Streamlit async display addition
- no DB/schema creation
- no worker/queue/scheduler
- no normal Today provider call
- no model promotion
- app/wapp Linux runtime hotfix remains intact
- Local Command Menu App Runtime Correction v1 remains intact
- `app` means Linux canonical app runtime
- wapp remains the explicit Windows-local escape hatch
- fports remains Windows-side port visibility only
