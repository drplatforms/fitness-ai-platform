# Daily Coach Async Persistence Design v1

Status: DESIGNED / READY FOR ARCHITECTURE REVIEW

Proposed final status: DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED

Last updated: 2026-06-22

## 1. Purpose

Daily Coach Async Persistence Design v1 is a design-only milestone that defines the durable persistence boundary for future Daily Coach async jobs and approved narratives.

This design answers the sequencing question raised by Daily Coach Async Provider Runtime Design v1: provider runtime should not proceed until durable async job/narrative storage boundaries are designed.

This document does not implement DB schema, migrations, repositories, services, API routes, Streamlit behavior, provider runtime, workers, queues, schedulers, polling, or persistence code.

## 2. Persistence goals

Persistence is needed before provider runtime because Daily Coach async generation has lifecycle state that should survive app restarts and should be inspectable without relying on ephemeral session state.

Persistence should eventually support:

- durable job state
- safe async lifecycle recovery
- stale and expired job handling
- approved narrative reuse
- safer provider timeout/failure handling
- Developer Mode inspection
- future public display readiness
- continuity across FastAPI/Streamlit restart
- auditable context identity and validator-version decisions

Persistence is not needed to make normal Today load provider-backed yet. Normal Today remains deterministic until a later Architecture-approved public display milestone.

## 3. Persistence non-goals

Persistence does not authorize:

- provider runtime implementation
- direct_ollama calls
- CrewAI calls
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- worker / queue / scheduler / polling
- normal Today provider call
- public async narrative display
- raw provider output storage
- rejected provider output storage
- debug/provider metadata in normal UI

The design is about what future durable storage should allow, forbid, and validate before implementation.

## 4. Proposed data boundaries

Future persistence should be split into clear public-safe concepts:

1. `daily_coach_async_jobs`
   Stores job lifecycle state and allowlisted runtime metadata.

2. `daily_coach_approved_narratives`
   Stores only approved, public-safe narrative content and display metadata.

3. Optional `daily_coach_job_events`
   Stores lightweight sanitized lifecycle events if the repository/service implementation needs an audit trail.

The table names are proposed design names only. This milestone does not create tables or migrations.

## 5. Job persistence model

A future `daily_coach_async_jobs` record should likely contain:

- `job_id`
- `user_id`
- `target_date`
- `workflow_target`
- `next_action_id`
- `context_hash`
- `context_version`
- `prompt_contract_version`
- `validator_version`
- `status`
- `created_at`
- `updated_at`
- `started_at`
- `completed_at`
- `expires_at`
- `stale_after`
- `fallback_used`
- `fallback_reason`
- `provider_attempted`
- `provider_name`
- `provider_model`
- `parse_status`
- `validation_status`
- `final_narrative_source`
- `displayable`
- `public_safe`

The job table should be metadata-first. It should not become a raw provider transcript store.

## 6. Job lifecycle storage policy

A persisted job may represent these conceptual statuses:

- `not_requested`
- `queued`
- `generating`
- `provider_succeeded_pending_validation`
- `approved`
- `rejected_parse`
- `rejected_validation`
- `provider_timeout`
- `provider_error`
- `stale`
- `expired`
- `fallback_available`

Allowed lifecycle transitions should remain consistent with the accepted provider runtime design:

```text
not_requested -> queued
queued -> generating
generating -> provider_succeeded_pending_validation
generating -> provider_timeout
generating -> provider_error
provider_succeeded_pending_validation -> approved
provider_succeeded_pending_validation -> rejected_parse
provider_succeeded_pending_validation -> rejected_validation
approved -> stale
approved -> expired
rejected_parse -> fallback_available
rejected_validation -> fallback_available
provider_timeout -> fallback_available
provider_error -> fallback_available
stale -> fallback_available
expired -> fallback_available
```

Forbidden transitions include:

- `rejected_parse -> approved`
- `rejected_validation -> approved`
- `provider_timeout -> approved`
- `provider_error -> approved`
- `expired -> approved`
- `stale -> approved` without regeneration against the current context identity
- any transition that bypasses parser, schema validation, claim validation, or display-state validation

## 7. Approved narrative persistence model

A future `daily_coach_approved_narratives` record may contain only public-safe approved content:

- approved narrative sections only
- deterministic/public-safe rendered text
- approved reason codes
- approved next-action references
- approved action IDs or anchor IDs
- safe display metadata
- context hash used for approval
- context version used for approval
- prompt contract version
- validator version
- approval timestamp
- expiration/displayability state

Approved narrative storage should be output-of-validation storage, not provider-output storage.

A persisted approved narrative is displayable only when:

- it passed strict parser/schema validation
- it passed claim validation
- it passed public-safe display validation
- its `context_hash` still matches the current Daily Coach context identity
- it is not stale
- it is not expired
- normal/public display has been explicitly authorized by a later milestone

Until public display is authorized, approved persisted narratives may be inspectable in Developer Mode only.

## 8. Data that must never be persisted

The persistence boundary must explicitly forbid storing:

- raw provider output
- rejected provider output
- full prompt text, unless separately approved by Architecture later
- private debug internals
- unbounded raw context
- raw database rows
- raw user notes
- secrets or environment values
- model scratchpad content
- validation bypass artifacts
- stack traces
- provider self-reported reasoning
- mutable UI state
- model-selection authority

Raw provider output must never be persisted.

Rejected provider output must never be persisted.

The project may persist allowlisted failure metadata, but not the unsafe content that caused failure.

## 9. Rejection and failure persistence policy

Failed jobs may persist sanitized metadata only.

Allowed failure metadata examples:

- `job_id`
- `status`
- `fallback_reason`
- `parse_status`
- `validation_status`
- `provider_attempted`
- `provider_name`
- `provider_model`
- `raw_output_length`
- `raw_output_preview_truncated` flag only
- sanitized error class/category
- created/started/completed timestamps
- context hash/version
- prompt contract version
- validator version

Not allowed:

- raw failed output
- rejected text excerpts
- full prompts
- raw database rows
- stack traces in public fields
- private debug payloads

Persist allowlisted failure metadata only.

## 10. Stale / expired / displayable policy

A job or approved narrative becomes stale when the current Daily Coach context identity no longer matches the identity used for generation/approval.

Stale triggers include:

- `context_hash` changes
- `target_date` changes
- `next_action_id` changes
- workflow target changes
- approved facts/constraints change in a way that changes the context identity
- validator version changes in a way that invalidates prior approval

A job or narrative becomes expired when:

- `expires_at` is in the past
- the target date is no longer relevant
- the approved display window has elapsed
- Architecture-approved retention/display policy says it is too old to display

Display policy:

- stale approved narratives may remain inspectable in Developer Mode as historical approved artifacts
- stale approved narratives must be hidden from normal UI
- expired approved narratives must be hidden from normal UI
- deterministic fallback remains primary whenever the approved async narrative is stale, expired, missing, or not public-display-authorized

## 11. Context hash and versioning strategy

Persistence must include context identity fields so approved output cannot drift away from backend truth.

Required identity/version concepts:

- `context_hash`
- `context_version`
- `prompt_contract_version`
- `validator_version`
- `output_schema_version`
- `workflow_target`
- `target_date`
- `next_action_id`

Displayability checks should compare persisted metadata against current backend-approved context before any approved narrative is displayed.

If any identity-critical field changes, the persisted narrative is stale and deterministic fallback remains available.

## 12. Developer Mode boundary

Persistence may support future Developer Mode inspection.

Developer Mode may eventually show:

- job status
- sanitized runtime metadata
- approved narrative preview
- fallback reason
- context hash/version
- stale/expired/displayable flags
- parse/validation status
- provider attempted/name/model metadata when sanitized

Developer Mode must not show raw provider output unless a later Architecture milestone explicitly authorizes a safe local-only inspection mechanism. The default policy is no raw output persistence and no raw output display.

## 13. Normal Today UI boundary

Normal Today UI must not show persisted async narrative yet.

Normal Today UI remains restricted from showing:

- persisted async narrative
- provider runtime controls
- raw output
- rejected output
- debug metadata
- model/provider controls
- parse/validation internals
- sanitized runtime metadata that belongs in Developer Mode

Normal Today remains deterministic until later Architecture acceptance authorizes public async narrative display.

## 14. Cleanup and retention considerations

Future implementation should define retention for:

- completed approved jobs
- failed jobs
- expired jobs
- stale jobs
- allowlisted failure metadata
- approved narratives
- optional sanitized job events

Initial retention should be conservative:

- keep current-day active job state
- retain recent approved public-safe narratives long enough for Developer Mode QA
- purge or archive old failed metadata based on a fixed retention window
- never retain raw/rejected provider output because it should never be persisted

Cleanup should be deterministic, testable, and not tied to normal Today page load unless explicitly authorized.

## 15. Migration sequencing

Recommended future sequence after this design is accepted:

1. Daily Coach Async Persistence Contracts + Schema v1
   Define and implement durable schema/contracts only. No provider runtime.

2. Daily Coach Async Persistence Repository / Service Shell v1
   Add repository/service shell around persisted jobs and approved narratives. No provider runtime.

3. Daily Coach Async Developer Mode Persistence Inspection v1
   Let Developer Mode inspect persisted job/narrative metadata safely.

4. Daily Coach Async Provider Runtime Prototype v1
   Add provider runtime only if Architecture approves the persistence boundary and runtime execution boundary.

5. Public Display Design v1
   Decide whether and how approved persisted async narratives can appear in normal Today.

Do not jump directly from persistence design to normal Today provider runtime.

## 16. Validation gates before implementation

Before implementation of persistence, Architecture should require:

- accepted persistence design
- explicit schema contract tests
- explicit no-raw-output-persistence tests
- explicit stale/expired/displayability tests
- explicit Developer Mode vs normal UI tests
- explicit fsweep artifact safety pass
- explicit project-memory update

Before provider runtime, Architecture should require:

- accepted persistence schema/contracts
- accepted repository/service shell
- accepted runtime isolation strategy
- parser/validator contract tests
- timeout/failure/fallback tests
- sanitized metadata tests
- no normal Today provider-call tests

## 17. Boundary confirmation

This design confirms:

- design only
- no DB schema implemented
- no migrations added
- no tables created
- no repositories added
- no services added
- no API routes added
- no Streamlit behavior changed
- no provider runtime implemented
- no direct_ollama call added
- no CrewAI call added
- no qwen3 call added
- no qwen3 bridge added
- no qwen3:32b promotion
- no worker added
- no queue added
- no scheduler added
- no polling added
- no normal Today provider call added
- no public async narrative display added
- deterministic fallback preserved
- model/provider policy preserved
- raw provider output persistence forbidden
- rejected provider output persistence forbidden

## 18. Recommended next milestone

Recommended next milestone after acceptance:

```text
Daily Coach Async Persistence Contracts + Schema v1
```

Purpose:

Implement the durable job/narrative schema and contract tests after design acceptance, without provider runtime or normal Today behavior changes.

Alternative:

```text
Daily Coach Async Persistence Repository / Service Shell v1
```

Only choose this after schema/contracts are explicitly accepted or folded into a combined Architecture-approved persistence implementation milestone.
