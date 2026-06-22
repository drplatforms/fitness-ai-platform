# QA Handoff Current

Current milestone: Project Memory Transition Packet v1

Status: IMPLEMENTED / READY FOR QA REVIEW

Baseline accepted before this milestone: Daily Coach Async Service Shell / No Worker v1

## QA focus

This is a docs/project-memory continuity milestone. QA should verify consistency and boundary preservation, not new runtime behavior.

Required checks:

- Verify `docs/project_memory/project_continuity_bootstrap.md` exists and is project-wide, not Architecture-only.
- Verify `current_state.md` no longer claims Async Daily Coach Narrative Design v1 is the current active milestone.
- Verify the Current Accepted Milestone Stack lists:
  1. Local Developer Command Menu App Runtime Correction v1
  2. Async Daily Coach Narrative Design v1
  3. Async Daily Coach Narrative Implementation Plan v1
  4. Daily Coach Async Contracts + Data Model v1
  5. Daily Coach Async Service Shell / No Worker v1
- Verify project-memory checks pass.
- Verify no snapshots or `qa_artifacts` are committed.
- Verify `fsweep` is clean locally if available.

## Daily Coach Async Service Shell expected behavior remains unchanged

- Approved matching job can be selected as displayable.
- queued/generating/provider_succeeded_pending_validation jobs are not displayable.
- rejected_parse/rejected_validation/provider_timeout/provider_error/stale/fallback_available jobs are not displayable.
- approved job without payload is not displayable.
- expired job is not displayable.
- context hash mismatch is not displayable.
- target date, next action, workflow target, prompt contract, validator version, provider, and model mismatches are not displayable.

## Boundary checks

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

## Recommended validation

```powershell
git diff --check
pytest tests/test_project_memory_check.py -q
pytest -q
python tools/project_memory_check.py
python -m py_compile ui/streamlit_app.py
```
