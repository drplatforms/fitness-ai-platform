# Daily Coach Narrative Product Readiness Review v1

Status: PRODUCT READINESS DECISION RECORDED

Related accepted milestone: `Daily Coach Narrative Developer Preview v1`

Related design milestone: `Daily Coach Narrative Async Today Preview Design v1`

## Review question

Is Daily Coach Narrative ready for limited normal Today UI integration?

## Decision

Not yet.

Daily Coach Narrative is not approved for synchronous normal Today UI integration.

Daily Coach Narrative is approved to move into async/background Today Preview design.

## Rationale

The developer/debug endpoint is accepted and useful.

`qwen3:8b` produced approved bounded narrative output through the developer/debug endpoint for users 101, 102, and 105.

However, observed qwen3:8b latency around 40-50 seconds is not acceptable for blocking normal Today page load.

The project should not let model latency degrade the primary Today experience.

## Accepted current state

Accepted foundations:

- Daily Coach Narrative v1 Planning
- Daily Coach Narrative Context Builder v1
- Daily Coach Narrative Offline Provider Runtime QA v1
- Daily Coach Narrative Provider Contract Tightening v1.1
- Daily Coach Narrative Developer Preview v1

Accepted backend debug endpoint:

```text
GET /daily-coach/{user_id}/narrative-preview/debug
```

Accepted behavior:

- deterministic fallback by default
- provider disabled by default
- explicit `direct_ollama` opt-in only
- approved narrative returned only after parse + validation success
- fallback returned on provider failure or validation failure
- rejected/raw/provider/debug internals not exposed

## Product readiness finding

Daily Coach Narrative is promising but not product-ready for synchronous normal UI.

Ready for:

- developer/debug endpoint usage
- manual developer-triggered preview design
- async/background-safe Today Preview design
- fallback-first UI planning

Not ready for:

- blocking normal Today page load
- automatic normal user provider calls
- report integration
- user-facing narrative persistence
- model promotion
- qwen3 production approval

## Required product pattern

A product-safe Today pattern must be:

- fallback-first
- non-blocking
- provider-disabled safe
- approved-output only
- rejected-output hidden
- public-safe status only
- easy to disable
- latency-aware

The Today page must remain useful if the provider is slow, unavailable, disabled, or rejected.

## Approved design direction

Proceed to:

`Daily Coach Narrative Async Today Preview Design v1`

Design should prefer:

- manual developer-triggered preview first
- deterministic fallback visible immediately
- provider narrative generated outside initial page load
- provider output displayed only after validation
- failure keeps fallback
- no user-facing persistence

## Not approved

This review does not approve:

- normal Today UI implementation
- synchronous provider call from Today
- Streamlit normal user surface integration
- report integration
- model promotion
- qwen3 production approval
- direct_ollama default change
- provider narrative persistence as user-facing history
- background task runner implementation
- cache/persistence layer
- validator loosening
- deterministic fallback weakening

## QA required before normal UI can be reconsidered

Before normal Today UI integration can be reconsidered, the project needs:

- repeated qwen3:8b runtime QA
- provider-disabled fallback QA
- timeout/failure QA
- leakage review
- latency review
- UI copy review
- UX review
- provider disable switch validation
- async/background handling recommendation
- rollback/disable behavior

## Decision summary

Final Product Readiness position:

```text
Daily Coach Narrative is accepted for developer/debug preview.
Daily Coach Narrative is not accepted for synchronous normal Today UI.
Daily Coach Narrative should proceed through async/background Today Preview design.
```

## Multi-tier model-lane addendum

Architecture accepts the async Today preview design with a required multi-tier model-lane addendum.

The product should not be architected only around current hardware latency or `qwen3:8b`. The design must support high-quality slow generation wherever waiting is acceptable.

Accepted lanes:

- deterministic fallback: immediate/default, production-safe fallback
- `qwen3:8b`: fast developer-preview lane, not production-approved
- `qwen3:32b`: premium-quality developer-preview lane, slow but valuable, not production-approved
- `qwen2.5:3b`: small baseline/regression lane, not product voice target

Implementation implication:

The next milestone should be `Daily Coach Narrative Today Developer Panel v1` with a model-lane selector from the beginning. It must not be implemented as a single-lane `qwen3:8b` panel.
