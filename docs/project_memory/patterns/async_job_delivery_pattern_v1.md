# Async Job Delivery Pattern / Playbook v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: ASYNC_JOB_DELIVERY_PATTERN_PLAYBOOK_V1_ACCEPTED

Source baseline: 71b14ea Merge feature/daily-coach-async-approved-preview-bridge-qa-v1

This playbook is the reusable delivery pattern harvested from the accepted Daily Coach async provider/runtime/preview path. It is documentation and project-memory guidance only. It does not authorize runtime behavior changes, provider behavior changes, normal Today behavior changes, Streamlit behavior changes, a new async job, worker/queue/scheduler/polling, qwen3, or qwen3:32b.

## 1. Purpose

Async jobs are product architecture, not just background code. They involve lifecycle state, persistence, inspection, validation, fallback, UI display boundaries, provider/runtime boundaries, and QA. A future team should not treat an async job as simply "call a model later" or "add a background task."

The first Daily Coach async path established the canonical pattern:

- contracts and data model before runtime
- service shell before worker/provider behavior
- persistence design before schema implementation
- persistence service shell before display
- Developer Mode inspection before normal UI exposure
- provider runtime only behind Developer Mode/manual gates
- parser/schema/validator/fallback before approved output persistence
- approved preview bridge reads persisted output only
- normal UI remains protected from debug/provider metadata
- QA hardening is required before broader exposure

Future async jobs should reuse this pattern unless Architecture explicitly approves a deviation.

## 2. Canonical Async Job Lifecycle

The canonical lifecycle vocabulary is:

- `not_created`: no durable job exists yet.
- `created`: a durable job record exists.
- `queued`: future-ready state for queue-based execution; optional for v1 unless a queue is explicitly authorized.
- `pending`: job exists and is waiting for a manual/runtime action.
- `running`: execution is actively in progress.
- `provider_attempted`: provider execution was actually attempted.
- `approved`: parsed, validated, public-safe output was accepted.
- `rejected`: provider output or candidate output was rejected by parser/schema/domain validation.
- `fallback`: deterministic fallback was used or remains the selected outcome.
- `failed`: a safe terminal failure state.
- `expired`: job or output exceeded allowed freshness window.
- `stale`: job/output no longer matches current context or freshness gates.

A v1 async job usually requires `created`, `pending`, `running` if execution exists, `approved`, `rejected`, `fallback`, `failed`, `expired`, and `stale`. `queued` is optional/future unless Architecture explicitly authorizes queue behavior.

Keep these concepts separate:

- job lifecycle status
- provider attempt status
- parse status
- validation status
- approval/display status
- preview eligibility status

Do not collapse these into one vague `done` or `success` flag. The QA surface needs to know whether a provider was attempted, whether parsing failed, whether validation failed, whether output is public-safe, and whether preview gates passed.

## 3. Minimum Data Model / Persistence Concepts

Future async jobs should define these concepts before runtime:

- `job_id`
- `user_id`
- `target_date` or `target_context`
- `job_type`
- `status`
- `created_at`
- `updated_at`
- `started_at`
- `completed_at`
- `expires_at`, if applicable
- stale/expired flags or deterministic derivation
- `context_hash` or `context_version`, if compatibility matters
- `provider_attempted`
- `fallback_used`
- `fallback_reason`
- `parse_status`
- `validation_status`
- `final_output_source`
- approved/public-safe output location
- sanitized metadata only

Persistence safety warning:

- Do not store raw provider output by default.
- Do not store rejected provider output.
- Do not store full prompts.
- Do not store raw context.
- Do not store scratchpads.
- Do not store chain-of-thought.
- Do not store secrets or environment values.
- Do not store raw database rows as debug payload.
- Do not store stack traces or tracebacks in user-visible or persistent async records.

If raw output persistence seems necessary for debugging, stop and escalate to Architecture. The default answer is no.

## 4. Backend Service Shell Pattern

The first Backend milestone for a new async job should be boring and non-magical.

Recommended order:

A. Async Contracts + Data Model v1
B. Async Service Shell / No Worker v1
C. Async Persistence Design v1
D. Async Persistence Contracts + Schema v1
E. Async Persistence Service Shell v1
F. Developer Mode Inspection v1
G. Optional Provider Runtime Design v1
H. Optional Provider Runtime Prototype v1 — Developer Mode Only
I. Provider Runtime QA Hardening v1
J. Approved Preview Bridge Design v1
K. Approved Preview Bridge Implementation v1 — Feature Flag Disabled by Default
L. Approved Preview Bridge QA v1
M. Provider Live QA v1 — Developer Mode Only
N. Public/default enablement decision, only if earned

Not every async job needs every stage. For example, a deterministic export job may not need provider runtime or approved preview bridge. But no async job should skip safety boundaries casually.

Service shell rules:

- Backend owns truth.
- UI should not mutate raw async state directly.
- Provider runtime should not write raw output directly to display locations.
- Persistence helpers should enforce forbidden-field boundaries.
- Public-safe output should use an approved output path, not a raw provider/debug path.

## 5. Developer Mode Inspection Requirement

Developer Mode inspection is mandatory before normal UI exposure.

Developer Mode inspection should show sanitized state only.

Allowed:

- job id
- job type
- status
- created/started/completed timestamps
- stale/expired state
- provider attempted true/false
- fallback used true/false
- sanitized fallback reason
- parse status
- validation status
- final output source
- public-safe approved output, if appropriate
- sanitized metadata

Forbidden:

- raw provider output
- rejected provider output
- full prompt
- raw context
- scratchpad
- chain-of-thought
- raw database rows
- stack traces
- traceback
- environment values
- secrets

Developer Mode is not a safety bypass. It is an inspection surface for sanitized state.

## 6. Provider Runtime Pattern

Provider runtime must be isolated and earned.

Required rules:

- provider execution disabled by default
- provider execution manually triggered first
- provider runtime Developer Mode-only until QA proves otherwise
- provider output must be parsed
- provider output must be schema-validated
- provider output must pass domain validation
- approved output must be public-safe before persistence/display
- invalid output falls back deterministically
- provider failure does not break normal UI
- provider metadata remains Developer Mode/debug-only
- deterministic fallback is mandatory

Forbidden:

- provider call on normal page render
- provider call on page load
- provider call from preview bridge
- provider output directly rendered
- raw output persistence
- rejected output persistence
- validation bypass
- model promotion through implementation side effect

Provider runtime should return sanitized result objects that clearly distinguish disabled config, missing config/model, provider unavailable, timeout, malformed output, schema mismatch, validation rejection, fallback, and approved output.

## 7. Preview Bridge Pattern

The canonical safe path is:

```text
normal UI render
→ read already-approved persisted output
→ verify preview eligibility gates
→ render secondary preview or fallback/no-preview
```

The forbidden paths are:

```text
normal UI render
→ provider call
```

```text
normal UI render
→ create async job
→ provider call
```

```text
preview bridge render
→ provider call
```

Preview eligibility gates should include:

- feature flag enabled
- approved output exists
- public_safe true
- displayable true
- stale false
- expired false
- context/version compatible
- validator version compatible
- output source allowlisted
- deterministic fallback still available
- no raw/rejected/debug metadata in display path

The preview bridge is a read-only display bridge. It is not a provider launcher, job creator, queue, scheduler, or polling loop.

## 8. Feature Flag Strategy

Feature flags for async UI exposure must default disabled.

Required defaults:

- disabled by default
- isolated environment support in tests
- `environ=None` reads real process environment
- `environ={}` means isolated empty environment
- no hidden inheritance from developer shell during tests

Prior lesson:

A config resolver must not allow `environ={}` tests to inherit real provider-enabled shell env.

This matters because a developer may have provider or preview flags enabled in their shell. Tests must be able to prove default-disabled behavior independent of that shell.

## 9. Normal UI Boundary

Normal UI may show only:

- approved public-safe output
- safe high-level label
- safe fallback/no-preview message, if designed

Normal UI must not show:

- provider name/model
- parse status
- validation status
- raw output length
- markdown wrapper flags
- sanitized error category
- context hash
- prompt contract version
- validator internals
- raw output
- rejected output
- prompt
- raw context
- scratchpad
- stack trace
- traceback
- secrets
- environment values

If normal UI needs an explanation, use user-safe language. Do not expose diagnostic machinery.

## 10. QA Milestone Pattern

Recommended ownership:

- Architecture owns design acceptance and boundaries.
- Backend owns implementation.
- QA owns runtime validation and pass/fail.
- Backend supports QA only if defects require patches.
- DevOps owns command/runtime tooling defects.

Required QA stages:

1. disabled/default smoke
2. Developer Mode inspection smoke
3. provider disabled path smoke
4. provider enabled path smoke, if provider exists
5. failure/fallback smoke
6. preview bridge boundary smoke
7. normal UI metadata leak check
8. Developer Mode diagnostic boundary check
9. regression tests
10. project memory checks
11. fsweep clean

A QA milestone may include bounded safety fixes, but live runtime QA should be QA-owned unless a defect is found.

## 11. Standard Pass Criteria

PASS if:

- disabled by default
- deterministic fallback exists
- no provider call on normal render
- no provider call on page load
- no async job auto-created unless explicitly designed
- Developer Mode inspection exists before normal UI exposure
- provider output cannot bypass parser/schema/validator
- invalid provider output falls back
- approved output is public-safe
- raw output not persisted/displayed
- rejected output not persisted/displayed
- prompt/raw context/scratchpad not persisted/displayed
- normal UI metadata boundary preserved
- Developer Mode diagnostics sanitized
- feature flags default disabled
- tests isolate environment
- project memory updated
- no snapshots committed
- no qa_artifacts committed

## 12. Standard Fail Criteria

FAIL if:

- provider runtime defaults enabled
- provider call occurs on page load
- provider call occurs on normal UI render
- preview bridge calls provider
- raw provider output is persisted
- rejected provider output is persisted
- raw/rejected output is displayed
- prompt/raw context/scratchpad is persisted/displayed
- invalid provider output is approved
- validator is loosened to make provider pass
- deterministic fallback is removed/weakened
- normal UI exposes debug/provider metadata
- model promotion happens implicitly
- worker/queue/scheduler/polling is introduced without design
- public/default display is added before QA gates
- project memory becomes stale

## 13. Standard Milestone Templates

### Async Contracts + Data Model v1

Owner: Architecture + Backend.
Goal: Define job contract, lifecycle states, result objects, and safety boundaries.
Scope: models/contracts only.
Non-goals: runtime, persistence schema, UI display, provider calls.
Tests: model/contract validation and forbidden-state tests.
Acceptance: contracts are deterministic, versioned, and no runtime behavior changed.
Handoff expectations: exact states, required fields, non-goals, next service-shell scope.

### Async Service Shell / No Worker v1

Owner: Backend.
Goal: Add backend service shell around the async contract without worker/provider execution.
Scope: create/read/update in-memory or deterministic service shape as appropriate.
Non-goals: provider, queue, scheduler, polling, public UI display.
Tests: service shell behavior and no-worker boundary.
Acceptance: service composes safely and cannot trigger provider execution.
Handoff expectations: functions, boundaries, tests, next persistence design.

### Async Persistence Design v1

Owner: Architecture.
Goal: Design durable storage, status fields, approved-output path, and forbidden fields.
Scope: design document only.
Non-goals: schema implementation.
Tests: project memory/docs checks only.
Acceptance: schema direction and safety rules are explicit.
Handoff expectations: tables/fields, status model, forbidden persistence list.

### Async Persistence Contracts + Schema v1

Owner: Backend.
Goal: Implement schema/contracts for durable async state.
Scope: database/schema and contract tests.
Non-goals: provider runtime, public UI display.
Tests: schema creation, constraints, forbidden raw/debug fields.
Acceptance: persistence tables exist and unsafe fields are not part of schema.
Handoff expectations: table names, fields, migrations/initialization behavior.

### Async Persistence Service Shell v1

Owner: Backend.
Goal: Add repository/service boundary over persistence.
Scope: create/read/update job state and approved output through backend-owned helpers.
Non-goals: provider runtime, public UI display.
Tests: CRUD, status transitions, approved output gates, forbidden metadata.
Acceptance: service rejects raw/rejected output and only stores sanitized metadata.
Handoff expectations: service functions, safety behavior, next Developer Mode inspection.

### Developer Mode Inspection v1

Owner: Backend + Streamlit UI.
Goal: Expose sanitized read-only async state for QA/developer review.
Scope: Developer Mode only.
Non-goals: normal UI display, provider execution.
Tests: Developer Mode gating, safe empty state, forbidden field exclusion.
Acceptance: sanitized inspection visible only in Developer Mode.
Handoff expectations: what is shown, what is hidden, manual smoke result.

### Provider Runtime Design v1

Owner: Architecture.
Goal: Design optional provider runtime boundary and failure/fallback rules.
Scope: design document only.
Non-goals: implementation, provider calls.
Tests: docs/project-memory checks.
Acceptance: runtime gates and validation pipeline are explicit.
Handoff expectations: allowed provider, feature flags, parser/schema/validator/fallback.

### Provider Runtime Prototype v1 — Developer Mode Only

Owner: Backend + Streamlit UI.
Goal: Add manual provider trigger behind Developer Mode only.
Scope: disabled by default, manual trigger, sanitized result.
Non-goals: normal UI provider call, worker/queue/scheduler/polling.
Tests: disabled path, manual trigger path, parser/validator/fallback, forbidden persistence.
Acceptance: no provider call on page load or normal render.
Handoff expectations: commit/snapshot, disabled-path smoke, boundaries.

### Provider Runtime QA Hardening v1

Owner: QA + Backend support.
Goal: Harden disabled/missing config, provider unavailable, timeout, malformed output, validation failure, and fallback behavior.
Scope: tests and bounded safety fixes.
Non-goals: product expansion.
Tests: all failure modes and forbidden output persistence/display.
Acceptance: failures are sanitized and deterministic fallback remains available.
Handoff expectations: test matrix and smoke result.

### Approved Preview Bridge Design v1

Owner: Architecture.
Goal: Design safe path from approved persisted output to possible normal UI preview.
Scope: design only.
Non-goals: implementation, provider execution.
Tests: docs/project-memory checks.
Acceptance: preview eligibility gates and no-provider-call boundary are explicit.
Handoff expectations: gates, feature flag, QA requirements.

### Approved Preview Bridge Implementation v1 — Feature Flag Disabled by Default

Owner: Backend + Streamlit UI.
Goal: Implement read-only preview of already-approved persisted output behind disabled flag.
Scope: feature flag, read-only helper, secondary preview render.
Non-goals: provider call, job creation, public/default display.
Tests: disabled flag, eligible/ineligible gates, no provider call, no async job creation.
Acceptance: normal UI unchanged when disabled; preview only when enabled and eligible.
Handoff expectations: feature flag, tests, smoke result.

### Approved Preview Bridge QA v1

Owner: QA + Backend support.
Goal: Hard-test enabled/disabled behavior, eligibility gates, metadata boundary, no-provider-call, and no-job-creation guarantees.
Scope: tests and bounded safety fixes.
Non-goals: product expansion.
Tests: QA matrix across all gates and normal UI leakage checks.
Acceptance: all gates covered; normal UI safe; Developer Mode diagnostics gated.
Handoff expectations: QA coverage summary and manual smoke.

### Provider Live QA v1 — Developer Mode Only

Owner: QA + Backend support.
Goal: Test actual provider generation in Developer Mode only.
Scope: live provider smoke, sanitized success/failure, deterministic fallback.
Non-goals: normal Today provider execution or public/default display.
Tests: manual live QA and regression tests.
Acceptance: live provider path works safely or fails safely in Developer Mode only.
Handoff expectations: provider/model used, results, failures, boundaries.

## 14. Daily Coach Async Case Study

The Daily Coach async path proved the project can move from design to persisted provider-assisted preview safely, but only by respecting boundaries.

Accepted statuses from the path include:

- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_PROTOTYPE_V1_ACCEPTED
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_QA_HARDENING_V1_ACCEPTED
- DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_DESIGN_V1_ACCEPTED
- DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_IMPLEMENTATION_V1_ACCEPTED
- DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_QA_V1_ACCEPTED
- DAILY_COACH_ASYNC_PROVIDER_LIVE_QA_V1_ACCEPTED

Case study summary:

- direct_ollama/qwen2.5:3b was validated as a Developer Mode-only live QA path.
- direct_ollama/qwen2.5:3b was not promoted to normal Today/default public behavior.
- qwen3 remains not bridge-enabled.
- qwen3:32b remains not promoted.
- deterministic Daily Next Action remains primary.
- approved preview bridge reads persisted approved output only.
- provider execution from Today remains unauthorized.
- public/default async narrative display remains unauthorized.

## 15. Backlog / Tooling Lessons

lstop/lrestart/app are Windows PowerShell helper commands that SSH into Linux.

Do not present them as Linux bash commands.

Known tooling backlog:

Fix lstop/lrestart/app SSH command CRLF handling in scripts/fitness_commands.ps1 so SSH command blocks are normalized to LF before execution.

This is backlog only for this milestone. Do not fix lstop/lrestart/app inside Async Job Delivery Pattern / Playbook v1 unless Architecture explicitly expands scope.

## Final boundary confirmation

- Docs/pattern only.
- No runtime behavior changed.
- No provider behavior changed.
- No normal Today behavior changed.
- No Streamlit behavior changed.
- No new async job implemented.
- No worker added.
- No queue added.
- No scheduler added.
- No polling added.
- No qwen3/qwen3:32b promotion.
- lstop/lrestart/app CRLF issue recorded as backlog only.
- No Codex used by default.
