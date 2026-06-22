# Architecture Handoff Current

Current milestone: Daily Coach Async Provider Runtime Design v1

Status: DESIGNED / READY FOR ARCHITECTURE REVIEW

Proposed final status: DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED

Branch: `feature/daily-coach-async-provider-runtime-design-v1`

Baseline accepted before this milestone: Daily Coach Async Developer-Only Prototype v1

Baseline main commit: `439b7a3 Merge feature-daily-coach-async-developer-only-prototype-v1`

## Summary

Daily Coach Async Provider Runtime Design v1 defines the safe future runtime boundary for Daily Coach async provider execution.

This is a design-only milestone. It does not implement provider execution.

## Design deliverable

- `docs/project_memory/designs/daily_coach_async_provider_runtime_design_v1.md`

## Designed

- provider execution model and recommended isolation strategy
- future async job lifecycle statuses and allowed/forbidden transitions
- provider input contract
- provider output contract
- parser / schema / validation / approval flow
- timeout, provider error, stale context, expiration, and fallback behavior
- sanitized runtime metadata for Developer Mode/debug only
- Developer Mode vs normal Today UI boundary
- model/provider policy
- persistence decision points and recommended future sequencing

## Architecture recommendation

The design recommends that Daily Coach async provider runtime should not proceed to a product-like path until Daily Coach Async Persistence Design v1 resolves durable job/narrative storage.

If provider runtime is implemented before persistence, it should remain Developer Mode-only and isolated from normal Today behavior.

Same-process hard-timeout provider execution is treated as risky because prior provider timeout experimentation destabilized provider runtime internals.

## Boundary confirmation

- design only: CONFIRMED
- no provider execution implemented: CONFIRMED
- no direct_ollama call added: CONFIRMED
- no CrewAI call added: CONFIRMED
- no qwen3 call added: CONFIRMED
- no qwen3 bridge added: CONFIRMED
- no qwen3:32b promotion: CONFIRMED
- no worker added: CONFIRMED
- no queue added: CONFIRMED
- no scheduler added: CONFIRMED
- no polling added: CONFIRMED
- no DB schema added: CONFIRMED
- no normal Today provider call added: CONFIRMED
- no public async narrative display added: CONFIRMED
- deterministic fallback preserved: CONFIRMED
- validation boundary preserved: CONFIRMED
- app/wapp runtime split preserved: CONFIRMED

## Files changed

- `docs/project_memory/designs/daily_coach_async_provider_runtime_design_v1.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/project_continuity_bootstrap.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`
- `tools/project_memory_check.py`
- `tests/test_project_memory_check.py`

## Validation requested

```powershell
git diff --check
pytest tests/test_project_memory_check.py -q
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/project_memory_check.py
. .\scripts\fitness_commands.ps1
fsweep
scripts/dev_commit_check.ps1 -Mode docs-only
```

## Recommended next milestone after acceptance

1. Daily Coach Async Persistence Design v1
2. Daily Coach Async Provider Runtime Prototype v1
3. Daily Coach Narrative Premium Voice Research v1

Architecture recommendation: complete persistence design before provider runtime implementation.
