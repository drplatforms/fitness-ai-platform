# Daily Coach Async Approved Preview Bridge Design v1

Status: `DESIGNED / READY FOR ARCHITECTURE REVIEW`

Proposed final status: `DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_DESIGN_V1_ACCEPTED`

Branch: `feature/daily-coach-async-approved-preview-bridge-design-v1`

Source baseline: `3765314 Merge feature/daily-coach-async-provider-runtime-qa-hardening-v1`

## Scope

Design-only milestone to define a future controlled bridge from Developer Mode-only approved Daily Coach async narratives into a possible Today preview path.

This milestone creates the required design document:

- `docs/project_memory/designs/daily_coach_async_approved_preview_bridge_design_v1.md`

## Design decisions

- Future preview reads only already-approved, already-validated, already-persisted async narratives.
- Today preview must not run provider execution.
- Today preview must not create async jobs.
- Deterministic Daily Next Action remains primary.
- Preview is secondary and disabled by default.
- Future implementation requires `DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED=false` or a repo-consistent equivalent.
- Eligibility gates require approved job state, approved narrative persistence, public_safe/displayable true, stale/expired false, current or compatible context/version metadata, allowlisted source, and no unsafe metadata exposure.
- Normal Today must not show provider/model diagnostics, parse status, validation status, raw output length, context hash, prompt contract, validator internals, raw output, rejected output, full prompt, raw context, scratchpad, stack traces, secrets, or environment values.
- Developer Mode may continue to show sanitized diagnostics.

## Explicit non-goals

- no Today preview bridge implemented
- no normal Today behavior change
- no normal Today provider call
- no provider execution on Today render
- no provider execution on page load
- no automatic async job generation
- no public async narrative display
- no worker / queue / scheduler / polling
- no qwen3 bridge
- no qwen3 promotion
- no qwen3:32b promotion
- no validation loosening
- no raw/rejected provider output display
- no debug/provider metadata in normal UI

## Validation expectation

Docs-only validation:

- `git diff --check`
- `pytest tests/test_project_memory_check.py -q`
- `python tools/dev_assistant.py memory-check`
- `python tools/dev_assistant.py stale-doc-check`
- `python tools/project_memory_check.py`
- `python tools/dev_assistant.py continuity-brief`
- `scripts/dev_commit_check.ps1 -Mode docs-only`
- `fsweep`

If project-memory tooling changed:

- focused Ruff/Black check for `tools/project_memory_check.py` and `tests/test_project_memory_check.py`
- `python -m py_compile tools/project_memory_check.py`

## Delivery boundary

Design only. Runtime restart is not required.
