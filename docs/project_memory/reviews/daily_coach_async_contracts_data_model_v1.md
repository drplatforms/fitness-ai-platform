# Daily Coach Async Contracts + Data Model v1 Review

Status: Ready for Architecture review
Review target: DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED
Date: 2026-06-21
Branch: feature/daily-coach-async-contracts-data-model-v1

## Review Summary

Daily Coach Async Contracts + Data Model v1 implements the foundational backend contracts for future async Daily Coach Narrative jobs.

The implementation is intentionally narrow. It adds typed contracts and deterministic context identity hashing only. It does not execute providers, persist jobs, add workers, add queues, or change Today UI behavior.

## Files Added or Updated

- `models/async_daily_coach_narrative_models.py`
- `services/async_daily_coach_context_identity.py`
- `tests/test_async_daily_coach_narrative_contracts_v1.py`
- `docs/project_memory/milestones/daily_coach_async_contracts_data_model_v1.md`
- `docs/project_memory/reviews/daily_coach_async_contracts_data_model_v1.md`
- current project-memory and handoff docs
- `tools/project_memory_check.py`
- `tests/test_project_memory_check.py`

## Contract Summary

The milestone defines:

- `DailyCoachNarrativeJobStatus`
- `DailyCoachNarrativeModelLane`
- `DailyCoachNarrativeContextIdentity`
- `DailyCoachNarrativeJob`
- `ApprovedDailyCoachNarrativePayload`
- `SanitizedDailyCoachNarrativeDiagnostics`
- deterministic context hash helper
- model lane helpers for qwen policy boundaries

## Boundary Confirmation

- contracts/data-model foundation only: confirmed
- no async runtime implemented: confirmed
- no provider execution added: confirmed
- no background worker added: confirmed
- no queue added: confirmed
- no scheduler added: confirmed
- no DB schema change: confirmed
- no `daily_coach_narrative_jobs` table created: confirmed
- no provider cache table: confirmed
- no provider call on normal Today load: confirmed
- no UI display behavior changed: confirmed
- no model promoted: confirmed
- `qwen2.5:3b` remains bridge baseline only: confirmed
- `qwen3` remains not bridge-enabled: confirmed
- `qwen3:32b` remains future premium async candidate / research-only: confirmed
- deterministic fallback remains always available: confirmed
- validation boundary preserved: confirmed
- raw/rejected output not approved for normal UI: confirmed
- docs/project memory updated: confirmed
- no qa_artifacts committed: confirmed
- no snapshots committed: confirmed
- workflow contract followed: confirmed
- script safety addendum followed: confirmed
