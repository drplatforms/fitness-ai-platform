# Async Daily Coach Narrative Implementation Plan v1

Status: Architecture planning implemented
Owner: Architecture
Milestone: Async Daily Coach Narrative Implementation Plan v1
Date: 2026-06-21
Branch: feature/async-daily-coach-narrative-implementation-plan-v1
Previous accepted milestone: Async Daily Coach Narrative Design v1
Previous accepted status: ASYNC_DAILY_COACH_NARRATIVE_DESIGN_V1_ACCEPTED

## 1. Executive Summary

The accepted async Daily Coach Narrative design established the future direction for premium coach language without blocking the Today page and without weakening backend truth boundaries.

This implementation plan converts that design into buildable phases.

The project should not attempt to build the entire async narrative system in one pass. The safe path is to land contracts, data model, service shell, Developer Mode execution, validation, UI surface, and premium model research as separate milestones with explicit acceptance gates.

The deterministic Today Coach Note remains the always-available baseline. Provider-generated narrative remains optional and display-safe only after backend validation.

## 2. Current Baseline

Current accepted behavior:

- Normal Today page load is deterministic.
- No provider call occurs during normal Today load.
- Developer Mode provider preview is manual.
- Same-session approval exists for the accepted bridge path.
- qwen2.5:3b is the only fast manual/session bridge baseline.
- qwen3:32b has shown better language and at least one validated manual preview run, but remains slow and not bridge-approved.
- Raw or rejected provider output is not approved for normal UI.
- Deterministic fallback is always available.

The current bridge solved the first safe user-facing AI language path. It is not the final architecture for premium coach language.

## 3. Implementation Principle

Backend owns truth.

Provider proposes language.

Validator decides what is display-safe.

Fallback remains deterministic.

No provider output should be displayed unless all required validation, model eligibility, context identity, and staleness checks pass.

## 4. Proposed Future Architecture

The future async architecture should separate narrative generation from page load.

High-level lifecycle:

1. Build backend-approved Daily Coach context.
2. Compute a context identity hash.
3. Create or find a narrative job for that user, date, context, provider, model, prompt contract, and validator version.
4. Run provider generation outside the Today page-load path.
5. Parse and validate provider output.
6. Store only approved/sanitized narrative and safe metadata if persistence is approved.
7. Mark failed jobs with sanitized failure classification.
8. Surface approved, context-valid narrative only when available.
9. Fall back to deterministic note when async output is missing, stale, failed, or invalid.

## 5. Phase Breakdown

### Phase 1 — Async Contracts + Data Model v1

Purpose:
Create the foundational contracts for async Daily Coach narrative jobs without executing provider runtime.

Scope:
- Define job status enum.
- Define proposed job model.
- Define context identity and invalidation contract.
- Define approved narrative payload shape.
- Define sanitized diagnostics shape.
- Define status transition rules.
- Add tests for contracts and model behavior.

Non-goals:
- No provider call.
- No background worker.
- No queue.
- No scheduler.
- No normal Today UI behavior change.
- No qwen3 promotion.

Acceptance gate:
Contracts are present, tested, and unused by normal runtime.

### Phase 2 — Async Service Shell / No Worker v1

Purpose:
Add a service-layer shell for creating, reading, expiring, and invalidating narrative jobs without running real provider generation.

Scope:
- Add narrative job service interface.
- Add create/check/latest behavior.
- Add stale-context rejection behavior.
- Add deterministic no-provider placeholder behavior for tests.
- Keep normal Today load deterministic.

Non-goals:
- No background worker.
- No real provider execution.
- No automatic model call.
- No normal UI display of async narrative.

Acceptance gate:
Service shell can manage job state deterministically and tests prove no provider call happens on normal Today load.

### Phase 3 — Developer-Only Async Prototype v1

Purpose:
Allow manual Developer Mode async generation experiments without product display.

Scope:
- Manual Developer Mode trigger only.
- Explicit provider/model selection.
- Timeout configuration by lane.
- Sanitized diagnostics.
- Safe failure classification.
- No raw/rejected output in normal UI.
- No automatic approval.

Non-goals:
- No normal Today provider call.
- No product display.
- No model promotion.
- No qwen3 bridge eligibility.

Acceptance gate:
Developer Mode can launch and inspect sanitized async job status while normal Today remains deterministic.

### Phase 4 — Validated Async Result Surface v1

Purpose:
Display approved async narrative only when context-valid and validation-approved.

Scope:
- Read latest approved async narrative.
- Check context identity and staleness.
- Apply display priority.
- Hide provider/model internals from normal UI.
- Preserve deterministic fallback.

Display priority:
1. Explicit session-approved note, if active and context-valid.
2. Async approved premium note, if available and context-valid.
3. Deterministic Today Coach Note.

Non-goals:
- No raw/rejected output display.
- No automatic provider call on page load.
- No model promotion.

Acceptance gate:
Approved async result can appear safely; stale, failed, rejected, or invalid output never appears.

### Phase 5 — Premium Model Research Lane v1

Purpose:
Evaluate qwen3:32b and future premium candidates for voice/persona quality under strict backend-truth boundaries.

Scope:
- Research-only model lane.
- Developer Mode only at first.
- Persona versioning proposal.
- Voice QA rubric.
- Latency and validation matrix.
- Safety and unsupported-claim tracking.

Non-goals:
- No qwen3 bridge approval.
- No qwen3 product default.
- No automatic display.
- No persistence of raw rejected output.

Acceptance gate:
Architecture and QA receive enough evidence to decide whether any premium model should advance to a future eligibility review.

### Phase 6 — Product Eligibility Review v1

Purpose:
Decide whether any async narrative lane is eligible for normal product surface.

Scope:
- Review validation pass rate.
- Review latency.
- Review voice quality.
- Review unsupported-claim risk.
- Review fallback behavior.
- Review user experience.
- Review rollback controls.

Non-goals:
- No promotion without explicit Architecture decision.
- No silent model default changes.

Acceptance gate:
Architecture either rejects, keeps Developer Mode only, or authorizes a specific product eligibility milestone.

## 6. Proposed Data Model

Future proposed table:

daily_coach_narrative_jobs

Proposed fields:

- id
- user_id
- target_date
- next_action_id
- workflow_target
- provider
- model
- context_hash
- prompt_contract_version
- validator_version
- status
- approved_narrative_json
- sanitized_failure_reason
- latency_ms
- created_at
- updated_at
- expires_at

Status values:

- not_requested
- queued
- generating
- provider_succeeded_pending_validation
- approved
- rejected_validation
- rejected_parse
- provider_timeout
- provider_error
- stale
- fallback_available

Data model rule:
This milestone proposes the model only. It does not implement schema changes.

## 7. Proposed API Contracts

Future proposed endpoints:

- POST /daily-coach/{user_id}/narrative-jobs
- GET /daily-coach/{user_id}/narrative-jobs/{job_id}
- GET /daily-coach/{user_id}/narrative-jobs/latest
- POST /daily-coach/{user_id}/narrative-jobs/{job_id}/approve-session

Contract principles:

- Creating a job must not block Today page load.
- Latest approved narrative must be context-valid.
- Approval must remain explicit.
- Model eligibility must be enforced server-side.
- Normal UI should not receive raw provider output.
- Diagnostics should be sanitized.

API rule:
This milestone proposes endpoints only. It does not implement endpoints.

## 8. Context Identity and Invalidation

Minimum identity inputs:

- user_id
- target_date
- next_action_id
- workflow_target
- selected_provider
- selected_model
- prompt_contract_version
- validator_version
- approved context hash

Potential approved context hash inputs:

- Daily Next Action
- UserHealthState summary
- nutrition state
- workout state
- recovery state
- approved recommendation context
- model lane
- prompt contract version
- validator version

Async narrative becomes stale when:

- user changes
- date changes
- next action changes
- workflow target changes
- approved context changes
- prompt contract changes
- validator version changes
- model changes

Stale output must not display.

## 9. Validation Gates

Required gates:

- provider attempted only in approved lane
- parse success
- schema success
- unsupported-claim rejection
- generic/meta-copy rejection
- raw-output leak rejection
- model eligibility check
- context hash match
- staleness check
- prompt contract version match
- validator version match
- safe diagnostics only

No output displays unless all display gates pass.

## 10. UI Plan

Normal Today UI:

- deterministic Today Coach Note loads immediately
- async status never blocks page load
- provider/model/debug internals hidden
- raw/rejected output hidden
- fallback always available

Developer Mode:

- may show sanitized job status
- may show selected provider/model
- may show validation status
- may show sanitized failure classification
- must not leak secrets, stack traces, raw prompts, or unapproved raw rejected output into normal UI

Potential normal UI labels:

- Standard guidance
- Premium coach note preparing
- Premium coach note ready
- Premium coach note unavailable; using standard guidance

Display priority proposal:

1. Explicit session-approved note, if active and context-valid.
2. Async approved premium note, if available and context-valid.
3. Deterministic Today Coach Note.

## 11. Timeout and Retry Policy

Suggested timeout tiers:

- qwen2.5:3b: 240 seconds
- qwen3:8b and qwen3:14b: 300 to 600 seconds
- qwen3:32b: 600 to 900 seconds

Retry policy:

- no hidden repeated provider calls during normal Today load
- retries are explicit in Developer Mode at first
- failed async generation falls back to deterministic note
- timeout results store sanitized failure classification only if persistence is approved

## 12. Persistence Policy

Phase 1 recommendation:

- no DB persistence
- no async runtime execution
- no normal-load provider call
- deterministic fallback remains primary

Future persistence recommendation:

- store approved/sanitized narrative JSON only
- store safe metadata
- store sanitized failure classification
- do not store raw rejected output by default
- do not expose prompt/provider internals in normal UI
- require a separate implementation milestone before schema changes

## 13. QA Strategy by Phase

Phase 1 tests:

- job status enum tests
- narrative job model tests
- context hash tests
- stale identity tests
- validator version mismatch tests
- model lane policy tests

Phase 2 tests:

- service create/read/latest tests
- deterministic shell behavior tests
- no-provider-call-on-normal-Today tests
- stale job rejection tests
- fallback availability tests

Phase 3 tests:

- Developer Mode trigger tests
- timeout classification tests
- provider error classification tests
- rejected parse classification tests
- rejected validation classification tests
- sanitized diagnostics tests
- no product display tests

Phase 4 tests:

- approved async display tests
- stale result does not display tests
- rejected result does not display tests
- raw output does not display tests
- display priority tests
- session approval priority tests
- deterministic fallback priority tests

Phase 5 tests:

- premium model QA matrix
- persona rubric
- unsupported-claim risk matrix
- latency matrix
- validation pass-rate matrix

Phase 6 tests:

- product eligibility checklist
- rollback checklist
- no-default-model-change proof
- no-normal-load-provider-call proof

## 14. Rollback Strategy

Rollback requirements:

- async lane can be disabled
- deterministic Today remains functional
- provider failures do not affect Today
- bad async output cannot display unless validator-approved
- no model promotion without explicit Architecture approval
- persistence can be ignored or disabled if later implemented
- normal UI falls back to deterministic guidance

## 15. Model Policy

Bridge baseline:

- qwen2.5:3b only

Research/probe only:

- qwen2.5:7b
- qwen3:8b
- qwen3:14b
- qwen3:30b-a3b
- qwen3:32b

qwen3:32b may be treated as a future premium async candidate because it has shown promising language and at least one successful validated Developer Preview run.

qwen3:32b remains:

- not bridge-approved
- not product default
- not normal-load blocking
- not auto-displayed
- not persisted
- not promoted

## 16. Safest Minimum Viable Async Implementation

Recommended first implementation milestone after this plan:

Daily Coach Async Contracts + Data Model v1

Build only:

- status enum
- narrative job contract/model
- context identity/hash contract
- validation result references
- safe metadata shape
- tests

Do not build first:

- worker
- queue
- scheduler
- provider runtime
- UI display
- DB persistence unless Architecture explicitly includes it in that milestone

## 17. Open Questions

- Should the first runtime prototype use in-process background tasks, a simple polling service, or wait for an external queue?
- When should SQLite persistence be authorized?
- How long should approved async narratives live?
- Should generation be user-triggered, scheduled, or opportunistic?
- Should qwen3:32b voice research happen before the service shell or after the service shell?
- How should persona versions be named and validated?
- Should the premium async note replace the standard note or sit as an expandable enhancement?
- What is the minimum product-quality voice rubric for coach persona acceptance?

## 18. Boundary Confirmation

Confirmed for this milestone:

- planning-only milestone
- no async runtime implemented
- no background worker added
- no queue added
- no scheduler added
- no DB schema change
- no provider cache table
- no provider call on normal Today load
- no model promoted
- qwen2.5:3b remains bridge baseline only
- qwen3 remains not bridge-enabled
- qwen3:32b documented only as future premium async candidate
- deterministic fallback remains always available
- validation boundary preserved
- raw/rejected output not approved for normal UI
- proposed persistence only, not implemented
- proposed APIs only, not implemented
