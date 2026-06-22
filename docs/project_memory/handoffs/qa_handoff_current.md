# QA Handoff Current

Updated: 2026-06-21
Current milestone: Daily Coach Async Contracts + Data Model v1
QA role: Contract and invariant validation

## QA Summary

Async Daily Coach Narrative Design v1 remains the accepted design context.

This is a docs/design milestone.

Persistence is proposed only, not implemented.

This milestone adds async Daily Coach narrative contracts only. There is no runtime provider execution and no UI display behavior to manually test.

## QA Focus

- required job statuses exist
- model lanes exist
- qwen2.5:3b remains bridge baseline only
- qwen3:32b remains future premium async candidate / research-only
- context hash is deterministic
- context hash changes when meaningful context changes
- context hash is insensitive to dictionary key ordering
- raw prompt/output fields are rejected from context hash inputs
- approved narrative payload has no raw-output fields
- sanitized diagnostics has no raw prompt/output fields
- no provider execution or DB schema is introduced by contract files

## Expected Tests

- `pytest tests/test_async_daily_coach_narrative_contracts_v1.py -q`
- `pytest tests/test_project_memory_check.py -q`
- `python tools/dev_assistant.py memory-check`
- `python tools/dev_assistant.py stale-doc-check`
