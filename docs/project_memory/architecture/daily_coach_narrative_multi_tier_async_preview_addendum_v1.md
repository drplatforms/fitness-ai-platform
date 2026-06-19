# Daily Coach Narrative Multi-Tier Async Preview Addendum v1

Status: COMPLETE / READY FOR ARCHITECTURE REVIEW

Related design: `Daily Coach Narrative Async Today Preview Design v1`

Revised accepted status target: `DAILY_COACH_NARRATIVE_MULTI_TIER_ASYNC_TODAY_PREVIEW_DESIGN_V1_ACCEPTED_WITH_ADDENDUM`

## Purpose

This addendum extends the accepted fallback-first async Today preview design with explicit multi-tier model lanes.

The original async Today preview design correctly prevents blocking Today page load on provider generation. This addendum clarifies that the product architecture should not be shaped only around the current fastest practical model. The preview architecture must also support a slow premium lane where the developer explicitly accepts the wait.

The rule remains:

```text
Never block the core Today page on provider generation.
Absolutely allow slow premium generation in developer/manual preview lanes where waiting is acceptable.
```

## Accepted model lanes

### Lane 1 — Deterministic fallback

Primary implementation: deterministic backend fallback

Purpose:

- immediate Today-safe display
- default behavior
- no provider call
- always available
- production-safe fallback

Status:

- default lane
- safe for immediate display
- required in all preview flows

Behavior:

- shown immediately on Today load
- remains visible while any provider preview runs
- remains visible if provider generation fails, times out, or is rejected

### Lane 2 — Fast provider preview

Primary model: `qwen3:8b`

Purpose:

- faster developer preview
- practical runtime QA
- lower-latency experimentation
- likely first provider lane to inspect in the panel

Status:

- evaluation/developer-preview only
- not production-approved
- not a final-quality coach voice target

Behavior:

- manual developer trigger only
- approved output may replace fallback only after parse + validation success
- failed/rejected output keeps fallback

### Lane 3 — Premium provider preview

Primary model: `qwen3:32b`

Purpose:

- higher-quality coach narrative lane
- manual generation
- long-running developer preview
- future better-hardware target
- possible later overnight/precompute/cache candidate after separate Architecture approval

Status:

- evaluation/developer-preview only
- not production-approved
- slow but valuable
- first-class preview lane despite latency

Behavior:

- manual developer trigger only
- clear latency warning required
- fallback remains visible during generation
- approved output may replace fallback only after parse + validation success
- failed, rejected, or timed-out output keeps fallback

Recommended developer-facing status language:

```text
Premium generation may take several minutes. Fallback remains visible while generation runs. Approved output appears only after validation. If generation fails or times out, fallback remains.
```

### Lane 4 — Small baseline

Primary model: `qwen2.5:3b`

Purpose:

- validator regression
- compliance baseline
- low-resource comparison
- guardrail sanity checks

Status:

- baseline only
- not product voice target
- not production-approved

Behavior:

- manual developer trigger only
- approved output may display only if validation passes
- rejection keeps fallback
- useful for verifying that validators reject or contain weaker model behavior

## Revised Today preview product pattern

The future Today preview should support:

1. Today loads immediately.
2. Deterministic Daily Next Action remains primary.
3. Deterministic fallback Coach Note appears immediately.
4. Developer Mode may show manual preview controls.
5. Developer may select one of the accepted lanes:
   - deterministic fallback
   - `qwen3:8b` fast preview
   - `qwen3:32b` premium preview
   - `qwen2.5:3b` baseline preview
6. Approved provider output replaces fallback only after parse + validation success.
7. Failed or rejected provider output keeps fallback.
8. Rejected/raw/debug/provider internals remain hidden.
9. Provider remains disabled by default.
10. No user-facing persistence occurs in v1.

## Developer panel implication

The next implementation should not be single-lane `qwen3:8b` only.

Required panel controls for `Daily Coach Narrative Today Developer Panel v1`:

- deterministic fallback lane
- `qwen3:8b` fast lane
- `qwen3:32b` premium lane
- `qwen2.5:3b` baseline lane
- manual trigger button
- public-safe status display
- deterministic fallback visible before and during provider generation
- approved provider narrative visible only after validation success
- fallback kept on timeout, validation failure, parse failure, or provider failure

The premium lane can be slow. Slow is acceptable in a developer/manual lane as long as Today is never blocked and the fallback remains visible.

## Display and leakage boundary

The multi-tier panel may display:

- selected lane
- selected model
- deterministic fallback note
- approved provider narrative after validation pass
- public-safe provider status
- public-safe fallback reason
- public-safe latency
- context summary/counts if useful in Developer Mode

The multi-tier panel must never display:

- rejected provider text
- raw model output
- raw prompt
- raw provider payload
- raw model-facing schema
- raw validation internals
- raw stack traces
- provider exception internals
- hidden/internal architecture language
- production-only debug secrets

## Persistence and caching boundary

No user-facing persistence is approved in the first Today preview.

The premium lane may motivate later precompute/cache work, but that requires a separate Architecture decision covering:

- cache policy
- invalidation policy
- stale-output behavior
- storage boundary
- user-facing history implications
- provider disable and rollback behavior

Until then, premium output is runtime preview only.

## QA addendum for future implementation

Future QA must test all lanes:

Users:

- 101
- 102
- 105

Lanes:

1. deterministic fallback
2. `qwen3:8b` fast provider preview
3. `qwen3:32b` premium provider preview
4. `qwen2.5:3b` small baseline

Required checks:

- Today/fallback display is immediate
- model generation is manual/developer-triggered only
- selected lane is public-safe
- provider attempt occurs only for provider lanes
- deterministic lane never calls provider
- approved output displays only after parse + validation success
- rejected output is never displayed
- raw prompt/provider/debug internals are never displayed
- timeout keeps fallback
- validation failure keeps fallback
- provider disabled keeps fallback
- no user-facing persistence occurs
- no report integration occurs
- no model promotion occurs

## Strict non-goals reaffirmed

Still not approved:

- normal Today UI integration
- synchronous model call from Today
- automatic background generation
- persistent narrative cache
- report integration
- production provider path
- model promotion
- qwen3 production approval
- direct_ollama default change
- Daily Next Action logic changes
- DailyCoachNarrativeContext truth-field changes
- validator loosening
- deterministic fallback weakening
- raw/rejected/debug/provider leakage

## Final addendum position

The async Today preview design is accepted as the fallback-first foundation.

This addendum makes the design explicitly multi-tier:

- deterministic fallback is the immediate/default lane
- `qwen3:8b` is the fast developer-preview lane
- `qwen3:32b` is the premium-quality developer-preview lane
- `qwen2.5:3b` is the small baseline/regression lane

The next implementation should be `Daily Coach Narrative Today Developer Panel v1` with a model-lane selector from the beginning.
