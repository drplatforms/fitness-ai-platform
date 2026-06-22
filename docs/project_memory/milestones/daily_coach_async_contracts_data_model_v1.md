# Daily Coach Async Contracts + Data Model v1 Milestone

Status: Implemented for Architecture review
Owner: Backend Development / Data Layer
Date: 2026-06-21
Branch: feature/daily-coach-async-contracts-data-model-v1
Previous accepted milestone: Async Daily Coach Narrative Implementation Plan v1
Previous accepted status: ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1_ACCEPTED

## Purpose

Create foundational async Daily Coach narrative contracts without implementing async runtime behavior.

This milestone establishes typed, tested, importable backend contracts for future async work:

- job status enum: `DailyCoachNarrativeJobStatus`
- model lane enum and eligibility helpers: `DailyCoachNarrativeModelLane`
- context identity contract
- deterministic context hash helper
- in-memory job contract
- approved narrative payload contract
- sanitized diagnostics contract
- tests for policy and contract invariants

## Scope Completed

- Added `models/async_daily_coach_narrative_models.py`.
- Added `services/async_daily_coach_context_identity.py`.
- Added `tests/test_async_daily_coach_narrative_contracts_v1.py`.
- Updated project memory and current handoffs.
- Updated project-memory enforcement for this milestone.

## Boundary

This is contracts/data-model foundation only.

No async runtime is implemented.
No provider execution is added.
No background worker is added.
No queue is added.
No scheduler is added.
No database schema is changed.
No `daily_coach_narrative_jobs` table is created.
No provider cache table is added.
No provider call is added to normal Today load.
No Streamlit Today behavior changes.
No model is promoted.
`qwen2.5:3b` remains bridge baseline only.
`qwen3` remains not bridge-enabled.
`qwen3:32b` remains a future premium async candidate / research-only.

## Proposed Acceptance Status

DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED
