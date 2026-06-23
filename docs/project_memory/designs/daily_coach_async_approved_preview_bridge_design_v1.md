# Daily Coach Async Approved Preview Bridge Design v1

Status: `DESIGNED / READY FOR ARCHITECTURE REVIEW`

Proposed final status: `DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_DESIGN_V1_ACCEPTED`

Source baseline: `3765314 Merge feature/daily-coach-async-provider-runtime-qa-hardening-v1`

Source snapshot: `fitness_ai_snapshot_2026-06-22_3765314_merge-feature-daily-coach-async-provider-runtime-qa-hardening-v1.zip`

Required implementation branch for this design milestone: `feature/daily-coach-async-approved-preview-bridge-design-v1`

## 1. Bridge purpose

The approved preview bridge defines how a future Today experience could read an already-approved, already-validated, already-persisted Daily Coach async narrative and show it as a controlled preview without executing a provider during Today render.

The bridge is needed because the current stack can create, validate, persist, inspect, and harden Developer Mode-only async provider output, but no rule yet defines when that approved persisted narrative is eligible to appear near the Today experience.

The bridge must preserve the product doctrine:

`Sound right and be right.`

The deterministic Daily Next Action remains primary. The async narrative preview, if later implemented, is secondary coach copy around already-approved backend truth. It is not truth, not a replacement for deterministic recommendation, and not a reason to run a model on page load.

## 2. Bridge non-goals

This design does not authorize implementation.

This design does not authorize:

- provider call during normal Today render
- provider call on page load
- automatic async job generation
- public/default async narrative display implementation
- worker / queue / scheduler / polling
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- raw provider output display
- rejected provider output display
- debug/provider metadata in normal UI
- replacing deterministic Daily Next Action
- loosening validation to make provider text pass

## 3. Current accepted foundation

Accepted Daily Coach async stack:

1. Async Daily Coach Narrative Design v1
2. Async Daily Coach Narrative Implementation Plan v1
3. Daily Coach Async Contracts + Data Model v1
4. Daily Coach Async Service Shell / No Worker v1
5. Project Memory Transition Packet v1
6. Daily Coach Async Developer-Only Prototype v1
7. Daily Coach Async Provider Runtime Design v1
8. Project Continuity System v2
9. Daily Coach Async Persistence Design v1
10. Daily Coach Async Persistence Contracts + Schema v1
11. Daily Coach Async Persistence Service Shell v1
12. Developer Mode Persistence Inspection v1
13. Daily Coach Async Provider Runtime Prototype v1 — Developer Mode Only
14. Daily Coach Async Provider Runtime QA Hardening v1

Current accepted behavior:

- Developer Mode async lifecycle prototype exists.
- Persistence schema/contracts exist.
- Persistence service shell exists.
- Developer Mode persistence inspection exists.
- Developer Mode-only provider runtime prototype exists.
- Provider runtime is disabled by default.
- Provider runtime requires explicit manual Developer Mode action.
- Provider failure paths are hardened and sanitized.
- Normal Today behavior remains unchanged.
- Deterministic Daily Next Action remains primary.
- No normal Today provider call exists.
- No public async narrative display exists.
- No worker exists.
- No queue exists.
- No scheduler exists.
- qwen3 remains not bridge-enabled.
- qwen3:32b remains not promoted.

## 4. Approved preview eligibility gates

A persisted async narrative is eligible for a future Today preview only if every required gate passes.

Required job gates:

- job exists in `daily_coach_async_jobs`
- job status is `approved`
- job belongs to the active Today user/date context
- workflow target matches the Daily Coach Today preview lane
- stale is false
- expired is false
- displayable is true
- public_safe is true
- deterministic fallback remains available

Required approved narrative gates:

- narrative exists in `daily_coach_approved_narratives`
- narrative `job_id` matches the eligible job
- narrative `user_id` and `target_date` match the active Today context
- narrative `public_safe` is true
- narrative `displayable` is true
- narrative stale is false
- narrative expired is false
- approved text is present and bounded
- approved narrative JSON is public-safe if rendered or inspected

Required context/version gates:

- context_hash matches the current Today context, or a future Architecture-approved compatibility rule explicitly allows it
- context_version matches expected version, or a future Architecture-approved compatibility rule explicitly allows it
- validator_version is current, or an accepted compatibility rule explicitly allows it
- prompt_contract_version is current, or an accepted compatibility rule explicitly allows it
- final_narrative_source is allowlisted

Allowed future `final_narrative_source` values should remain narrow. Initial bridge implementation should allow only approved deterministic/provider sources already emitted by the accepted persistence/runtime service. Anything new requires Architecture review.

Required safety gates:

- no raw provider output field is present or exposed
- no rejected provider output field is present or exposed
- no full prompt/raw context/scratchpad field is present or exposed
- no unsafe metadata is exposed in normal UI
- no provider/model diagnostics are exposed in normal UI
- no claim is displayed unless it survived the accepted validation path

If any gate fails, the preview is not eligible.

## 5. Today preview boundary

Recommended future path: **B. Today preview behind an explicit experimental feature flag**.

The future preview should be controlled, secondary, and disabled by default.

Recommended future section label:

`AI-assisted coach preview`

Acceptable alternate label:

`Daily Coach Narrative Preview`

Recommended placement:

- below or near the deterministic Daily Next Action
- visually secondary to deterministic Daily Next Action
- clearly labeled as a preview/experimental coach narrative if shown
- no replacement of deterministic recommendation, recovery guidance, training action, nutrition action, or fallback

Recommended display rule:

Today render → read approved persisted narrative → verify gates → render secondary preview or deterministic fallback/no-preview state.

Forbidden display rule:

Today render → provider call.

The bridge should not be Developer Mode-only forever, because the purpose of the bridge is to design a controlled Today preview path. However, the first implementation must be disabled by default and should be acceptable for local/test-user QA before any broader enablement. A test-user-only guard may be added as an extra safety belt, but it is not a substitute for feature flagging and eligibility gates.

## 6. Provider execution boundary

Today preview must never execute provider runtime.

Provider execution remains separate from Today render:

- Developer Mode manual provider runtime prototype, or
- future async worker/queue/scheduler process only after separate Architecture authorization.

Allowed future bridge concept:

```text
Today render
→ read approved persisted narrative
→ verify preview eligibility gates
→ render secondary preview or fallback/no-preview state
```

Forbidden bridge concept:

```text
Today render
→ build provider input
→ call provider/model
→ parse output
→ show output
```

This rule holds even when the preview feature flag is enabled.

## 7. Fallback behavior

If no approved narrative exists or any gate fails:

- deterministic Today behavior remains unchanged
- deterministic Daily Next Action remains visible and primary
- no provider call is attempted
- no automatic async job is created
- no raw/debug details are shown
- no provider/model diagnostics are shown in normal UI

Normal UI may show either no preview section or a user-safe message such as:

`AI-assisted coach preview is not available yet. Your deterministic daily action is still ready.`

Developer Mode may show sanitized gate-failure diagnostics, but normal UI must not show debug internals.

## 8. Debug and metadata boundary

Normal Today may eventually show:

- approved preview text
- safe high-level preview label
- safe fallback/no-preview message

Normal Today must not show:

- provider name/model
- parse status
- validation status
- raw_output_length
- markdown_wrapper_detected
- sanitized_error_category
- context hash
- prompt contract version
- validator internals
- raw output
- rejected output
- full prompt
- raw context
- scratchpad
- stack traces
- environment values
- secrets

Developer Mode may continue showing sanitized diagnostics through the accepted Developer Persistence Inspection and Provider Runtime panels.

## 9. Feature flag strategy

Future implementation must require a disabled-by-default flag.

Recommended flag:

`DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED=false`

Required flag behavior:

- default disabled
- normal Today unchanged when disabled
- no provider execution regardless of flag value
- read-only persisted approved narrative preview only
- Developer Mode diagnostics remain separate
- flag enablement does not bypass eligibility gates
- flag enablement does not authorize public/default rollout

Optional extra guards for early implementation:

- test-user allowlist
- local-only environment label
- Developer Mode diagnostic mirror for gate failures

Optional guards must not replace the primary feature flag and eligibility gates.

## 10. QA gates before implementation

A future implementation must prove:

- normal Today unchanged when feature flag disabled
- no provider call on Today render
- no provider call on page load
- no automatic async job creation
- approved narrative preview appears only when all gates pass
- stale narrative hidden
- expired narrative hidden
- non-displayable narrative hidden
- non-public-safe narrative hidden
- context mismatch hidden
- validator version mismatch behavior is defined and tested
- prompt contract version mismatch behavior is defined and tested
- fallback behavior safe when gates fail
- no raw provider output visible
- no rejected provider output visible
- no full prompt/raw context/scratchpad visible
- no provider/model diagnostics in normal UI
- Developer Mode diagnostics remain gated
- deterministic Daily Next Action remains primary
- qwen3/qwen3:32b remain unused

## 11. Implementation sequencing

Recommended sequence:

A. Daily Coach Async Approved Preview Bridge Design v1

B. Daily Coach Async Approved Preview Bridge Implementation v1 — Feature Flag Disabled by Default

C. Daily Coach Async Approved Preview Bridge QA v1

D. Daily Coach Async Provider Live QA v1 — Developer Mode Only

E. Later public/default enablement decision, only after separate Architecture/Product approval

Do not combine design and implementation.

## 12. Suggested future implementation shape

Future implementation should be read-only and backend-owned.

Likely backend helper:

`services/daily_coach_async_approved_preview_bridge_service.py`

Likely responsibilities:

- read current Today context
- query latest approved narrative through persistence service shell
- evaluate eligibility gates
- return safe preview result object
- return safe fallback/no-preview result object when gates fail
- return sanitized Developer Mode diagnostics separately from normal UI payload

Likely UI behavior:

- normal Today reads safe preview result only if feature flag enabled
- no provider runtime service call from Today
- no job creation from Today
- no raw diagnostics in normal UI
- Developer Mode can show sanitized gate-failure reasons

## 13. Boundary confirmation

Design only: CONFIRMED

No Today preview bridge implemented: CONFIRMED

No normal Today behavior changed: CONFIRMED

No normal Today provider call added: CONFIRMED

No provider call on Today render authorized: CONFIRMED

No provider call on page load authorized: CONFIRMED

No public async narrative display added: CONFIRMED

No automatic async job generation added: CONFIRMED

No worker added: CONFIRMED

No queue added: CONFIRMED

No scheduler added: CONFIRMED

No polling added: CONFIRMED

No qwen3 call added: CONFIRMED

No qwen3 bridge added: CONFIRMED

No qwen3:32b promotion: CONFIRMED

Deterministic fallback preserved: CONFIRMED

Model/provider policy preserved: CONFIRMED

Raw/rejected provider output remains forbidden: CONFIRMED

Debug/provider metadata remains forbidden in normal UI: CONFIRMED

## 14. Next milestone recommendation

Likely next milestone after Architecture accepts this design:

`Daily Coach Async Approved Preview Bridge Implementation v1 — Feature Flag Disabled by Default`

Purpose:

Implement read-only display of already-approved, already-persisted async narrative preview through strict eligibility gates, behind a disabled-by-default feature flag.

Still do not authorize:

- provider execution from Today
- provider execution on page load
- automatic async job generation
- public/default async narrative display
- worker / queue / scheduler
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
