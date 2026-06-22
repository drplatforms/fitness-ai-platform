# Architecture Handoff Current

Updated: 2026-06-21
Current milestone: Daily Coach Async Contracts + Data Model v1
Owner: Backend Development / Data Layer
Status: Implemented / ready for Architecture review

## Accepted Previous Milestone

Async Daily Coach Narrative Implementation Plan v1 was accepted on `main`.

Accepted status:
ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1_ACCEPTED

## Current Architecture Review Target

Daily Coach Async Contracts + Data Model v1 implements foundational async Daily Coach narrative contracts only.

Review focus:

- job status enum
- model lane / eligibility policy
- context identity contract
- deterministic context hash helper
- approved narrative payload contract
- sanitized diagnostics contract
- tests proving policy and hashing invariants

## Boundary

This milestone does not implement async runtime, provider execution, background workers, queues, schedulers, DB schema, a `daily_coach_narrative_jobs` table, provider cache, normal Today provider calls, UI display behavior, model promotion, or qwen3 bridge eligibility.

## Previous Design Reference

Async Daily Coach Narrative Design v1 remains accepted architecture context.

Primary design doc:

`docs/project_memory/designs/async_daily_coach_narrative_design_v1.md`

No provider call on normal Today load.

qwen3 remains not bridge-enabled.

## Proposed Acceptance

DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED

## Recommended Next Milestone

Daily Coach Async Service Shell / No Worker v1
