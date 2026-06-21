# Async Daily Coach Narrative Design v1

Status: `DESIGN IMPLEMENTED / READY FOR ARCHITECTURE REVIEW`

Design status token proposed for review:

`ASYNC_DAILY_COACH_NARRATIVE_DESIGN_V1_ACCEPTED`

## Purpose

This document defines the future async Daily Coach Narrative architecture.

It is a design-only milestone. It does not implement async provider execution, queues, scheduler behavior, database tables, provider cache, model routing, Streamlit behavior, FastAPI behavior, or persistence behavior.

The design exists because premium local model output can be useful but too slow for page-load usage. A qwen3:32b manual Developer Preview runtime pass showed promising language quality with a latency of approximately 336 seconds, but it remains a future premium async candidate only. It is not bridge-enabled, not promoted, and not approved for normal Today display by this design.

## Non-negotiable product boundary

- Backend owns facts.
- Provider proposes language.
- Validator decides what is display-safe.
- Deterministic fallback remains always available.
- Normal Today load must never wait for a provider.
- Normal Today load must not call the provider.
- Raw or rejected provider output must not appear in normal UI.
- No model is promoted by this design.
- `qwen2.5:3b` remains the manual bridge baseline only.
- `qwen3:32b` remains a future premium async candidate only.

## Current accepted baseline

The accepted bridge path is manual and session-only:

1. Today loads deterministic guidance immediately.
2. Developer Mode may run a manual provider preview.
3. Only a bridge-approved model may be explicitly approved for same-session display.
4. `qwen2.5:3b` is the only bridge baseline.
5. Approved provider narrative remains session-only.
6. Approved provider narrative is not persisted.
7. Rejected, raw, debug, provider, model, and prompt internals are not displayed in normal UI.

Async design must preserve that baseline.

## Model lanes

| Lane | Purpose | Models | User-facing? | Blocking? | Persistence |
| --- | --- | --- | --- | --- | --- |
| Deterministic lane | Always-available Today guidance | Backend deterministic services | Yes | Never | Existing deterministic state only |
| Fast manual bridge lane | Current Developer Mode manual preview and explicit session approval | `qwen2.5:3b` only | Only after explicit session approval | Never on normal load | No persistence |
| Premium async candidate lane | Future slow, higher-quality narrative candidate | `qwen3:32b` or later approved premium model | Future-only after validation and eligibility | Never on normal load | Proposed only, not implemented |
| Experimental probe lane | Characterization and research | `qwen2.5:7b`, `qwen3:8b`, `qwen3:14b`, `qwen3:30b-a3b`, other probes | No product display unless later approved | Manual only | No persistence |

Model lane rules:

- `qwen2.5:3b` remains bridge baseline only.
- `qwen2.5:7b` is not bridge-enabled.
- `qwen3:8b` is not bridge-enabled.
- `qwen3:14b` is not bridge-enabled.
- `qwen3:30b-a3b` is not bridge-enabled.
- `qwen3:32b` is not bridge-enabled.
- No qwen3 model is promoted.
- Any future premium model must pass parse, schema, claim, validation, context identity, and model eligibility gates before display.

## Allowed backend-approved context

Async narrative generation may only receive backend-approved context. The provider must not calculate targets, infer hidden facts, inspect raw database state, or decide eligibility.

Allowed future context inputs:

- `user_id`
- target date
- Daily Next Action identity and text
- workflow target
- deterministic Today Coach Note fallback
- approved Daily Coach Narrative context
- approved recommendation context
- approved nutrition state summary
- approved workout state summary
- approved recovery state summary
- approved training or nutrition claims already derived by backend services
- prompt contract version
- validator version
- model lane and selected model

Not allowed:

- raw rejected provider output
- unvalidated provider text
- hidden model memory
- direct database dumps
- raw prompt/debug data in normal UI
- unsupported trend, adherence, recovery, fatigue, or progression claims that backend has not approved

## Async lifecycle

A future async request should be created only after deterministic Today guidance already exists.

Recommended lifecycle:

1. Build deterministic Today state.
2. Render deterministic Today Coach Note immediately.
3. Optionally request premium async narrative through a future approved trigger.
4. Capture a context identity and context hash.
5. Generate provider candidate out of the page-load path.
6. Parse provider output.
7. Validate schema and language safety.
8. Re-check context identity and staleness.
9. Mark approved or rejected.
10. Surface only approved narrative, otherwise keep deterministic fallback.

## State machine

Deterministic fallback is available in every state.

| State | Meaning | Display behavior |
| --- | --- | --- |
| `not_requested` | No async narrative has been requested for the current context. | Show deterministic Today Coach Note. |
| `queued` | A future async request exists but generation has not started. | Show deterministic note; optional user-safe pending text. |
| `generating` | Provider generation is running outside page load. | Show deterministic note; optional user-safe pending text. |
| `provider_succeeded_pending_validation` | Provider returned output, but validation has not completed. | Show deterministic note. Do not show provider text. |
| `approved` | Provider output parsed, validated, passed eligibility, and context is current. | Show according to display priority. |
| `rejected_validation` | Output parsed but failed validation. | Show deterministic note; Developer Mode may show sanitized reason. |
| `rejected_parse` | Output could not be parsed into the approved schema. | Show deterministic note; Developer Mode may show sanitized reason. |
| `provider_timeout` | Provider exceeded the model timeout tier. | Show deterministic note; optional unavailable status. |
| `provider_error` | Provider process, network, or runtime failed. | Show deterministic note; optional unavailable status. |
| `stale` | Output no longer matches current context identity. | Do not display. Show deterministic note. |
| `fallback_available` | Explicit reminder state that deterministic fallback remains available. | Show deterministic note when no higher-priority valid note exists. |

## Context identity and invalidation

Minimum identity fields:

- `user_id`
- target date
- Daily Next Action ID
- workflow target
- selected provider
- selected model
- approved context version/hash
- prompt contract version
- validator version

Recommended context hash inputs:

- Daily Next Action payload
- UserHealthState summary
- nutrition state summary
- workout state summary
- recovery state summary
- approved recommendation context
- approved Daily Coach Narrative context
- prompt contract version
- validator version
- selected provider
- selected model

Async narrative becomes stale when any of these change:

- user changes
- date changes
- Daily Next Action changes
- workflow target changes
- approved context changes
- prompt contract changes
- validator version changes
- selected provider changes
- selected model changes
- model lane eligibility changes

Stale output must be rejected before display even if the text itself validated earlier.

## Validation boundary

No output displays unless all required gates pass.

Required validation gates:

1. Provider attempt completed within lane timeout.
2. Output parsed into exactly one allowed JSON object.
3. Schema validation passed.
4. Required fields are present and bounded.
5. Unsupported-claim validation passed.
6. Generic/meta-copy validation passed.
7. Forbidden debug/provider/model/prompt leak validation passed.
8. Context identity still matches.
9. Output is not stale.
10. Selected model is eligible for the target display lane.
11. Raw output is not exposed to normal UI.

Failure classifications:

- `parse_error`
- `schema_error`
- `unsupported_claim`
- `generic_or_meta_copy`
- `debug_leak`
- `context_mismatch`
- `stale_context`
- `model_not_eligible`
- `provider_timeout`
- `provider_error`
- `unknown_failure`

## Raw output policy

Normal UI policy:

- never display raw provider output
- never display rejected provider output
- never display prompts
- never display provider/model/debug internals
- never display validation stack traces

Storage policy:

- raw rejected output is not persisted by default
- raw prompt/response storage is not approved by this design
- sanitized failure reason may be stored only in a future persistence milestone
- Developer Mode may show sanitized diagnostics only

## Persistence recommendation

### Phase 1: no persistence

Recommended first implementation phase after this design:

- no database table
- no provider cache
- no background queue
- no normal-load provider call
- session/dev-only async experiments if explicitly authorized later
- deterministic Today remains primary and immediate

### Phase 2: optional SQLite job table proposal

A future architecture milestone may approve a SQLite-backed job table. This design proposes, but does not implement, a table named:

`daily_coach_narrative_jobs`

Possible fields:

- `id`
- `user_id`
- `target_date`
- `next_action_id`
- `workflow_target`
- `provider`
- `model`
- `context_hash`
- `prompt_contract_version`
- `validator_version`
- `status`
- `approved_narrative_json`
- `sanitized_failure_reason`
- `latency_ms`
- `created_at`
- `updated_at`
- `expires_at`

Storage constraints if later approved:

- store only approved and sanitized narrative JSON
- store only safe metadata
- do not store raw rejected output by default
- store sanitized failure classification only
- expire records by context/date policy
- reject stale records before display

## UI proposal

Today UI must remain useful before, during, and after any async work.

Required normal UI principles:

- deterministic Today Coach Note appears immediately
- async premium narrative never blocks Today load
- raw/rejected provider output is never shown
- provider/model/debug internals are never shown
- fallback language remains clear, not apologetic
- user can keep deterministic guidance

Possible future user-safe status copy:

- `Premium coach note preparing`
- `Premium coach note ready`
- `Premium coach note unavailable; using standard guidance`

Developer Mode may show sanitized diagnostics such as status, failure class, and latency. Developer Mode must not make rejected raw text normal-user visible.

## Display priority

Recommended display priority:

1. Explicit session-approved note, if active and context-valid.
2. Async approved premium note, if available, context-valid, and display-eligible.
3. Deterministic Today Coach Note.

Architecture should confirm this priority before implementation. The reasoning is that explicit session approval is user-directed and current-session scoped, while async premium output may have been generated earlier and must be checked for staleness.

## Operational constraints

Local runtime realities:

- Windows Ollama is the model host.
- Linux runtime reaches Windows Ollama through the LAN URL.
- `qwen3:32b` can take several minutes.
- user may navigate away
- Streamlit session may refresh
- FastAPI may restart
- provider generation may fail
- provider generation may timeout
- deterministic fallback must always remain available

Suggested timeout tiers for future implementation:

| Lane/model class | Suggested timeout |
| --- | --- |
| `qwen2.5:3b` bridge/manual | 240 seconds |
| `qwen3:8b` / `qwen3:14b` probes | 300 to 600 seconds |
| `qwen3:32b` premium async candidate | 600 to 900 seconds |

These are design targets only and do not change runtime behavior.

## API and data contract proposal

Future implementation may define a contract shaped like this:

```json
{
  "job_id": "string",
  "user_id": 102,
  "target_date": "YYYY-MM-DD",
  "workflow_target": "nutrition_logging",
  "next_action_id": "string",
  "provider": "direct_ollama",
  "model": "qwen3:32b",
  "model_lane": "premium_async_candidate",
  "context_hash": "string",
  "prompt_contract_version": "daily_coach_narrative_vN",
  "validator_version": "daily_coach_narrative_validator_vN",
  "status": "approved",
  "approved_narrative": {
    "coach_note": "string",
    "key_takeaway": "string",
    "recommended_focus": "string"
  },
  "sanitized_failure_reason": null,
  "latency_ms": 336000,
  "expires_at": "timestamp"
}
```

This proposal is not an implementation contract until Architecture authorizes it in an implementation milestone.

## Implementation phases

### Phase 0: accepted design

This milestone.

- document lifecycle
- document state machine
- document invalidation
- document validation boundary
- document raw output policy
- document UI priority
- document persistence options

### Phase 1: implementation plan

Recommended next milestone:

`Async Daily Coach Narrative Implementation Plan v1`

Purpose:

- break this design into small implementation milestones
- decide whether Phase 1 remains session/dev-only
- decide whether a job table is required
- define tests before code

### Phase 2: developer-only async prototype

Possible later milestone only after Architecture approval:

- manual trigger only
- no normal-load provider call
- no DB persistence unless separately approved
- deterministic fallback always primary

### Phase 3: persisted async job table

Possible later milestone only after Architecture approval:

- SQLite job table
- approved/sanitized output only
- stale checking
- sanitized diagnostics
- no raw rejected output by default

### Phase 4: product UI surfacing

Possible later milestone only after Architecture and QA approval:

- normal UI can surface approved async premium note
- no provider/model/debug internals
- user-safe status copy
- deterministic note remains fallback

## Acceptance criteria for this design

Pass if:

- design is clearly marked design-only
- deterministic fallback remains always available
- no normal-load provider call is proposed
- state machine is defined
- invalidation keys are defined
- persistence is proposed, not implemented
- raw-output policy is defined
- model lanes are defined
- qwen3:32b is future premium async candidate only
- qwen3 is not bridge-enabled
- qwen2.5:3b remains bridge baseline only
- UI priority is proposed
- validation boundary is preserved
- future milestones are broken down

Fail if:

- runtime implementation is added
- DB schema changes are added
- provider cache is added
- queues or background workers are added
- model promotion is implied
- deterministic fallback is weakened
- raw/rejected provider output is allowed in normal UI
- qwen3 is bridge-enabled
