# Daily Coach Async Provider Runtime Design v1

Status: DESIGNED / READY FOR ARCHITECTURE REVIEW

Proposed final status: DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED

Last updated: 2026-06-22

## 1. Purpose

This document defines the safe future runtime boundary for Daily Coach async narrative provider execution.

It is a design-only milestone. It does not implement provider execution, FastAPI provider runtime behavior, Streamlit public display behavior, worker execution, queueing, scheduling, polling, database persistence, model promotion, or qwen3 bridge behavior.

The goal is to decide how a future provider may generate a Daily Coach async narrative without risking normal Today performance, runtime stability, validation safety, raw output leakage, public UI debug leakage, model-policy drift, or deterministic fallback regression.

## 2. Accepted foundation

Daily Coach async now has this accepted foundation:

1. Async Daily Coach Narrative Design v1
2. Async Daily Coach Narrative Implementation Plan v1
3. Daily Coach Async Contracts + Data Model v1
4. Daily Coach Async Service Shell / No Worker v1
5. Project Memory Transition Packet v1
6. Daily Coach Async Developer-Only Prototype v1

Current accepted behavior:

- Developer Mode can manually create and inspect Daily Coach async job shell data.
- Job status, context identity/hash, stale/expired/displayable state, and safe lifecycle transitions can be inspected.
- Normal Today behavior remains unchanged.
- Deterministic Daily Next Action remains primary.
- No provider/model call is attempted.
- No async narrative is shown in normal public UI.
- No provider runtime, worker, queue, scheduler, or DB persistence exists yet.

## 3. Recommended v1 provider execution model

Recommended v1 path:

```text
Daily Coach async provider runtime should not run as same-process hard-timeout provider execution.

The first implementation-ready provider runtime should use an isolated execution boundary, preferably a subprocess-isolated provider worker or a separate local worker process, after persistence/job lifecycle design is accepted.
```

Same-process provider execution is not recommended for Daily Coach async v1 if it requires hard timeout/shutdown control inside the FastAPI process.

Reason:

- Prior CrewAI timeout experimentation in this project showed that same-process timeout/shutdown behavior can destabilize provider runtime internals.
- Observed failures included OpenAI/CrewAI runtime poisoning, event-bus mismatch warnings, and inability to schedule new futures after shutdown.
- Daily Coach normal Today performance must not depend on provider execution completing cleanly.

Recommended sequence:

1. Provider runtime design: this document.
2. Daily Coach Async Persistence Design v1.
3. Subprocess or worker-boundary provider runtime prototype.
4. Developer Mode approved narrative preview only.
5. Public Today integration only after Architecture acceptance, QA pass, persistence rules, and validation gates are proven.

A same-process deterministic-only prototype remains acceptable. A same-process live provider runtime is not recommended as the first provider execution path.

## 4. Future lifecycle statuses

Future Daily Coach async jobs should support these conceptual statuses:

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

### Allowed transitions

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

### Forbidden transitions

Forbidden transitions include:

- `rejected_parse -> approved`
- `rejected_validation -> approved`
- `provider_timeout -> approved`
- `provider_error -> approved`
- `expired -> approved`
- `stale -> approved` without regenerating against the current context identity
- any transition that bypasses parser, schema validation, claim validation, or display-state validation

### Fallback behavior

Deterministic fallback remains mandatory.

Fallback is used when:

- no async job exists
- provider generation has not been requested
- provider generation is queued or generating
- provider times out
- provider errors
- provider output is malformed
- provider output fails schema validation
- provider output fails claim validation
- job context hash no longer matches current Daily Coach context
- job is expired
- no approved narrative exists

Normal Today remains deterministic when fallback is used.

### Rejected jobs

Rejected jobs may be inspectable in Developer Mode only through sanitized metadata.

Normal UI must not show:

- raw provider output
- rejected provider output
- parse errors
- validation internals
- provider/model debug metadata
- stack traces
- raw JSON

## 5. Provider input contract

Provider input must be backend-approved context only.

Allowed provider input areas:

- `user_id`
- `target_date`
- `workflow_target`
- `next_action_id`
- context identity/hash
- approved Daily Coach facts
- approved Daily Next Action summary
- approved recommendation context
- approved training constraints
- approved nutrition constraints
- approved recovery constraints
- allowed coaching moves
- forbidden claims
- output schema/version
- prompt contract version
- validator version

Provider input must not include:

- unbounded raw history
- raw database rows
- raw notes
- private debug internals
- rejected provider output
- mutable UI state
- unapproved targets
- unapproved claims
- model-selection authority
- secrets
- environment variables
- internal stack traces

The provider receives enough truth to write coach-quality language, but not enough authority to invent facts or choose display policy.

## 6. Provider output contract

Future provider output should be strict JSON only.

Recommended v1 output contract:

```text
CandidateDailyCoachNarrative
```

Candidate output should contain bounded fields such as:

- short coach narrative
- optional structured rationale
- confidence
- reason codes
- referenced approved facts / anchor ids
- sanitized diagnostics fields only if explicitly allowlisted

Required output flow:

```text
provider output
→ strict parser
→ schema validation
→ claim validation
→ approved narrative
→ deterministic renderer
→ Developer Mode preview first
→ public UI only in a later milestone
```

Provider output must never be rendered directly.

Markdown, code fences, prose wrappers, extra keys, missing required fields, internal guardrail language, or model/provider self-reference should cause rejection or deterministic fallback.

## 7. Validation boundary

The validation boundary preserves the project doctrine:

```text
Backend owns truth.
Provider proposes language.
Validator decides display safety.
Deterministic fallback remains mandatory.
UI renders approved fields only.
```

Validation must reject:

- invented facts
- unsupported training claims
- unsupported nutrition targets
- unsupported recovery claims
- medical claims
- overconfident trend claims
- model/provider self-reference
- internal guardrail language
- raw JSON/debug leakage
- qwen3 promotion assumptions
- output that contradicts backend-approved context
- output that implies deterministic fallback is optional
- output that implies provider text is source of truth

Validation must not be loosened to make a model pass.

## 8. Timeout and failure strategy

Failure behavior must be explicit and safe.

Failure cases:

- timeout
- provider exception
- malformed output
- schema mismatch
- validation failure
- stale context
- expired job
- model unavailable
- Ollama unavailable
- provider returns markdown/prose instead of JSON
- provider returns extra keys
- provider returns valid JSON but unsafe claims

Expected metadata:

```text
fallback_used: true
fallback_reason: <specific reason>
```

Expected user-facing behavior:

- normal Today remains deterministic
- approved async narrative is absent unless validation succeeds
- deterministic fallback or deterministic Daily Next Action remains available
- raw output never appears in normal UI

Hard timeout enforcement should happen outside the provider runtime process if a live provider is used.

## 9. Sanitized runtime metadata

Runtime metadata is Developer Mode / debug only.

Potential fields:

- configured_provider
- selected_provider
- configured_model
- selected_model
- provider_attempted
- fallback_used
- fallback_reason
- parse_status
- validation_status
- final_narrative_source
- raw_output_length
- raw_output_preview_truncated
- markdown_wrapper_detected
- context_hash
- prompt_contract_version
- validator_version

Normal Today UI must not expose this metadata.

Raw provider output should not be stored or displayed by default. If a future debug build captures a preview, it must be sanitized, truncated, Developer Mode only, and never committed to normal persistence without Architecture approval.

## 10. Model/provider policy

Current policy remains:

- `qwen2.5:3b` is bridge baseline only.
- `qwen3:32b` is research / future premium async candidate only.
- qwen3 is not bridge-enabled.
- no model is promoted without Architecture approval.
- deterministic fallback remains mandatory.
- validation must not be loosened to make a model pass.

This design may inform future premium voice research, but it does not authorize qwen3 promotion, qwen3 bridge behavior, qwen3:32b promotion, or normal Today provider execution.

## 11. Developer Mode vs normal UI boundary

Developer Mode may eventually show:

- manual async job trigger
- job status
- sanitized runtime metadata
- approved narrative preview if validation passes
- fallback reason
- context identity/hash inspection
- prompt/validator version inspection

Normal Today UI is still not authorized to show:

- automatic provider call
- automatic async job creation
- public async narrative display
- raw provider output
- debug metadata
- model/provider controls
- qwen3/qwen3:32b output
- rejected provider output

Public async narrative display requires a later Architecture-approved milestone.

## 12. Persistence recommendation

Provider runtime should not proceed to a product-like path until Daily Coach Async Persistence Design v1 answers durable storage questions.

In-memory provider runtime may be acceptable only as a developer-only prototype, but it should not be the public Today path.

Recommended persistence position:

- design durable job storage before any durable provider runtime
- persist approved public-safe narrative only after validation succeeds
- persist approved display state and allowlisted runtime metadata only
- persist context identity/version fields that support staleness checks
- do not persist raw provider output by default
- do not persist rejected/raw output as normal app data

Questions for Daily Coach Async Persistence Design v1:

- What is the durable job table shape?
- Which statuses are persisted?
- Which metadata is public-safe?
- How are context hashes compared at read time?
- How are expired/stale jobs hidden from public UI?
- How are rejected jobs inspectable in Developer Mode without raw output leakage?

## 13. Recommended implementation sequence

Recommended next steps after this design is accepted:

1. Daily Coach Async Persistence Design v1
2. Daily Coach Async Provider Runtime Prototype v1 behind Developer Mode only
3. Daily Coach Narrative Premium Voice Research v1 using approved context only
4. Daily Coach Async Approved Narrative Preview v1 in Developer Mode only
5. Normal Today async display only after explicit Architecture acceptance

## 14. Boundary confirmation

This design confirms:

- design only
- no provider execution implemented
- no direct_ollama call added
- no CrewAI call added
- no qwen3 call added
- no qwen3 bridge added
- no qwen3:32b promotion
- no worker added
- no queue added
- no scheduler added
- no DB schema added
- no normal Today provider call added
- no public async narrative display added
- deterministic fallback preserved
- validation boundary preserved
- app/wapp/Linux runtime split preserved

## 15. Final recommendation

Accept this as the provider runtime design baseline only if Architecture agrees with the sequencing:

```text
provider runtime design
→ persistence design
→ isolated/developer-only provider runtime prototype
→ validated Developer Mode preview
→ public Today integration later
```

The design intentionally keeps Daily Coach async provider execution unimplemented until the persistence/runtime boundary is explicitly approved.
