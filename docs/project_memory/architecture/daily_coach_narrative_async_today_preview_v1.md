# Daily Coach Narrative Async Today Preview v1 Design

Status: ACCEPTED WITH REQUIRED MULTI-TIER ADDENDUM

Related milestone: `Daily Coach Narrative Async Today Preview Design v1`

Related accepted milestone: `Daily Coach Narrative Developer Preview v1`

## Architecture decision

Daily Coach Narrative is not approved for synchronous normal Today UI integration.

Daily Coach Narrative is approved to move into an async/background-safe Today Preview design with an explicit multi-tier model-lane addendum.

Reason: `qwen3:8b` has passed developer/debug preview QA and produces bounded approved narrative output, but observed latency around 40-50 seconds is not acceptable for blocking the normal Today page load.

The required product pattern is:

```text
Today page loads immediately
→ deterministic Daily Next Action remains primary
→ deterministic fallback coach note is available immediately
→ provider narrative may be generated only through an async/developer-gated path
→ approved provider narrative may replace fallback only after parse + validation success
→ failed or rejected provider output silently keeps fallback
→ provider can be disabled without breaking Today
```

## Multi-tier addendum requirement

Architecture accepted the fallback-first async design but requires the Today preview architecture to support multiple model lanes from the beginning.

The revised design must not over-center `qwen3:8b` as the only practical path. It must explicitly support:

- deterministic fallback as the immediate/default lane
- `qwen3:8b` as the fast developer-preview lane
- `qwen3:32b` as the premium-quality developer-preview lane
- `qwen2.5:3b` as the small baseline/regression lane

See: `docs/project_memory/architecture/daily_coach_narrative_multi_tier_async_preview_addendum_v1.md`.

The core product rule remains unchanged: Today must never block on provider generation, but slow premium generation is allowed in manual developer-preview lanes where waiting is acceptable.

## Design intent

This design bridges the accepted backend debug endpoint to a future limited Today surface without approving normal user-facing integration yet.

It defines the behavior that a later implementation must follow before any provider narrative can appear near the Today page.

This is a design-only milestone. It does not add code, Streamlit UI, background workers, caching, persistence, report integration, or provider defaults.

## Placement recommendation

The eventual Today surface should be visually subordinate to the deterministic Daily Next Action card.

Recommended section:

```text
Daily Next Action
- deterministic title
- deterministic reason
- deterministic workflow target

Coach Note
- deterministic fallback text immediately
- optional developer-mode status
- approved provider narrative may replace fallback after validation
```

The deterministic Daily Next Action remains the source of truth. The provider narrative only explains the action. It cannot choose, change, reroute, or prioritize the action.

## Immediate render behavior

The Today page must never wait for the model.

On initial page load, render:

- deterministic Daily Next Action title
- deterministic backend reason
- deterministic workflow target
- deterministic fallback coach note

Provider status should be hidden from normal users in the first implementation. In developer mode, the UI may show a compact status such as:

- `fallback_ready`
- `preview_pending`
- `provider_approved`
- `fallback_kept`
- `provider_disabled`

Do not show raw model progress, prompt text, raw provider output, validation internals, or exception details.

## Trigger mode decision

First implementation should use Option A: manual developer-triggered refresh.

### Option A — manual developer-triggered preview

Recommended first implementation.

Behavior:

- Today page loads with deterministic fallback immediately.
- Developer Mode exposes a button or explicit preview action.
- The preview action calls the accepted backend debug endpoint.
- Approved provider output may replace fallback only in the developer panel or developer-only preview area.
- Normal users do not trigger provider calls.

Pros:

- safest
- simplest
- easiest to QA
- avoids surprise latency
- avoids repeated expensive calls
- preserves the developer/debug boundary

Cons:

- not fully product-like yet
- does not exercise automatic background UX

### Option B — automatic background request after Today loads

Design path only; not first implementation.

Behavior:

- Today page loads deterministic fallback immediately.
- A background request starts after page render if provider is enabled.
- Approved output replaces fallback only after validation succeeds.
- Failure leaves fallback in place.

Risks:

- repeated calls across reruns or refreshes
- user confusion if note changes late
- expensive/slow qwen3 calls
- needs dedupe/status/cancel semantics

Use only after Developer Panel v1 is accepted.

### Option C — backend precompute/cache

Not approved for first Today preview.

This may eventually be the best product UX, but it requires a cache/persistence policy, invalidation rules, stale-output handling, and a stronger user-facing history boundary.

## Provider default

Provider must remain disabled by default.

Default Today behavior:

- provider is not attempted
- deterministic fallback is shown
- `direct_ollama` is not called
- normal UI does not depend on provider availability

Provider preview requires explicit developer/debug opt-in.

## Approved output display behavior

Provider output can display only when all are true:

1. provider was explicitly requested by an approved developer/debug path
2. provider returned parseable structured output
3. Daily Coach Narrative validation succeeded
4. output preserved the Daily Next Action
5. output preserved workflow target
6. `recommended_focus` matched exactly
7. `used_approved_facts` were exact approved strings
8. forbidden claims were absent
9. meta/process/internal architecture language was absent
10. no raw/debug/provider leakage occurred

If any condition fails, keep deterministic fallback.

## Failure behavior

Failure is silent and safe for normal users.

Failure cases:

- provider disabled
- provider unavailable
- provider timeout
- parse failed
- validation failed
- exception occurred
- user/date context unavailable

Required behavior:

```text
show deterministic fallback
hide rejected output
hide raw errors
hide stack traces
hide validation internals
record public-safe status only
```

Allowed public-safe fallback reasons:

- `provider_disabled`
- `provider_timeout`
- `provider_parse_failed`
- `provider_validation_failed`
- `provider_unavailable`

## Status-state design

The implementation should use a small public-safe state model.

Recommended states:

| State | Meaning | Normal user display | Developer display |
|---|---|---|---|
| `fallback_ready` | deterministic fallback is available | show fallback | show fallback + status |
| `provider_disabled` | provider not attempted | show fallback | show disabled status |
| `preview_pending` | developer-triggered provider request is running | show fallback | show pending status |
| `provider_approved` | provider output passed validation | optional later; not normal v1 | show approved narrative |
| `fallback_kept` | provider failed or was rejected | show fallback | show safe fallback reason |

Do not expose raw validation errors, provider exception details, or rejected text in any state.

## Public-safe payload boundary

Future UI code may consume only the accepted preview payload fields:

- `user_id`
- `date`
- `next_action_id`
- `next_action_title`
- `workflow_target`
- `provider_enabled`
- `provider_attempted`
- `selected_provider`
- `selected_model`
- `parse_success`
- `validation_success`
- `fallback_used`
- `fallback_reason`
- `approved_narrative`
- `deterministic_fallback_note`
- context summary/count fields
- public-safe `latency_ms`

Do not consume or display raw provider internals.

## Persistence decision

No user-facing persistence in the first Today preview implementation.

First implementation should be runtime response only.

Rationale:

- avoids storing slow experimental copy as history
- avoids stale narrative policy questions
- keeps developer preview clearly bounded
- prevents provider output from becoming a product record before readiness review

A later precompute/cache design may revisit persistence under a separate Architecture decision.

## Disable switch behavior

Provider disable must be safe and boring.

When disabled:

- Today still loads
- Daily Next Action still displays
- fallback coach note still displays
- provider is not attempted
- no error is shown to normal users
- developer mode may show `provider_disabled`

The disable switch is required before normal UI integration can be approved.

## Latency rule

The model must never block Today page load.

Observed qwen3:8b latency around 40-50 seconds is acceptable for developer/debug preview only. It is not acceptable for synchronous normal Today UI.

Future normal UI requires one of:

- manual developer/user refresh with clear non-blocking fallback
- automatic background generation after initial render
- backend precompute/cache with explicit freshness rules

## QA matrix for future implementation

Required users:

- 101
- 102
- 105

Required paths:

1. Provider disabled default path
   - fallback shown immediately
   - provider not attempted
   - no model call

2. qwen3:8b developer preview path
   - explicit opt-in
   - approved output shown only after validation
   - failure keeps fallback

3. qwen2.5:3b baseline path
   - explicit opt-in
   - output approved only if validation passes
   - rejected output hidden

4. Timeout/failure path
   - provider timeout or unavailable condition
   - fallback kept
   - no stack traces or raw exception leakage

5. Leakage review
   - no rejected text
   - no raw model output
   - no raw prompts
   - no provider payloads
   - no validation internals
   - no hidden architecture language

6. Rerun/repeated-call behavior
   - no repeated automatic expensive calls in first implementation
   - manual trigger only unless explicitly approved

## Recommended next implementation slice

Recommended next milestone:

`Daily Coach Narrative Today Developer Panel v1`

Scope:

- Streamlit Developer Mode only
- uses accepted backend debug endpoint
- manual trigger button
- displays deterministic fallback immediately
- displays approved provider narrative only if validated
- displays public-safe status only
- no normal Today card integration
- no report integration
- no provider default change
- no persistence

Alternative backend-first implementation:

`Daily Coach Narrative Async Preview Backend v1`

Scope:

- backend status helper only
- no normal UI
- no Streamlit normal surface
- no persistence/cache

## Strict non-goals

This design does not approve:

- synchronous model call from Today
- normal Today UI integration
- Streamlit normal user surface integration
- background task runner implementation
- cache/persistence layer
- report integration
- production provider path
- model promotion
- qwen3 production approval
- direct_ollama default change
- Daily Next Action logic changes
- DailyCoachNarrativeContext truth-field changes
- validator loosening
- fallback weakening
- RAG
- embeddings
- scraping
- agents
- meal planning
- AI-generated food suggestions
- AI-generated exercise suggestions
- nutrition formula changes
- workout generation changes
- Training Level 5 behavior changes
- Nutrition Level 5 behavior changes

## Acceptance recommendation

Accept this design if Architecture agrees that the first Today-adjacent implementation should be developer-gated, manually triggered, fallback-first, and non-blocking.

Final proposed status:

`DAILY_COACH_NARRATIVE_ASYNC_TODAY_PREVIEW_DESIGN_V1_COMPLETE`
