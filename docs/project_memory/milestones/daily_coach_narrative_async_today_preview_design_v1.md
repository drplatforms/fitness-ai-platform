# Daily Coach Narrative Async Today Preview Design v1

Status: ACCEPTED WITH REQUIRED MULTI-TIER ADDENDUM

Implementation status: `DAILY_COACH_NARRATIVE_MULTI_TIER_ASYNC_TODAY_PREVIEW_DESIGN_V1_ACCEPTED_WITH_ADDENDUM`

## Goal

Create the architecture/design plan for limited Daily Coach Narrative Today Preview integration using an async/background-safe pattern.

This milestone is design-only. It does not implement normal Today UI integration, background jobs, Streamlit panels, persistence, report integration, provider promotion, or model defaults.

## Product readiness decision

Daily Coach Narrative is not approved for synchronous normal Today UI integration.

Accepted reason:

- `qwen3:8b` passed developer/debug preview QA and produced approved bounded narrative output.
- Observed latency around 40-50 seconds is acceptable for developer/debug preview.
- That latency is not acceptable for blocking the normal Today page load.

Required product direction:

```text
Today loads immediately
→ deterministic Daily Next Action remains primary
→ deterministic fallback narrative is available immediately
→ provider narrative may generate asynchronously or through explicit developer-gated preview
→ approved narrative may replace fallback only after parse + validation success
→ failed provider output keeps fallback
→ provider can be disabled without breaking Today
```

## Design artifacts added

- `docs/project_memory/architecture/daily_coach_narrative_async_today_preview_v1.md`
- `docs/project_memory/reviews/daily_coach_narrative_product_readiness_review_v1.md`

## Design decisions

### 1. Where would the narrative appear?

Future placement should be subordinate to the deterministic Daily Next Action card.

Recommended future section:

```text
Daily Next Action
Coach Note
```

Daily Next Action remains deterministic and primary. Coach Note may explain the action but cannot choose or change it.

### 2. What appears immediately?

The deterministic fallback coach note appears immediately.

The page must not wait on provider runtime.

### 3. How is provider generation triggered?

First implementation should be manually triggered from Developer Mode or an explicit developer preview action.

Automatic background generation is a later design path, not the first implementation.

### 4. Is generation automatic, manual, or developer-gated?

First implementation: manual and developer-gated.

Normal user automatic generation is not approved yet.

### 5. How does UI show loading/pending/failed states?

Normal users should see fallback and no raw status details in the first implementation.

Developer Mode may show public-safe states:

- `fallback_ready`
- `provider_disabled`
- `preview_pending`
- `provider_approved`
- `fallback_kept`

### 6. How is fallback displayed?

Fallback is displayed immediately and remains the default.

If provider fails, fallback remains displayed.

### 7. How is approved provider output displayed?

Approved provider output may be displayed only after parse and validation success.

It may replace fallback only inside an approved developer-only panel or future non-blocking Today preview surface.

### 8. How is rejected provider output hidden?

Rejected provider output is never displayed.

Preview surfaces may show only public-safe fallback reason metadata.

### 9. How is provider disabled globally?

Provider disabled remains the default behavior.

Disabled behavior must still return deterministic fallback and must not break Today.

### 10. What QA must pass before implementation?

Future implementation must test:

- users 101, 102, 105
- provider-disabled fallback path
- qwen3:8b opt-in path
- qwen2.5:3b baseline path
- timeout/failure path
- leakage review
- repeated-call/rerun behavior

## Recommended option selection

Accepted design recommendation:

`Option A — Manual developer-triggered refresh first`

Why:

- safest bridge from debug endpoint to UI
- avoids blocking Today
- avoids repeated expensive model calls
- keeps provider calls explicitly developer-gated
- fits current qwen3 latency limits

Future path:

`Option B — Automatic background request after Today loads`

Only after the developer panel proves fallback/approval/leakage behavior.

Not approved:

`Option C — Backend precompute/cache`

Reason: persistence/cache/freshness policy is not approved yet.

## Non-goals preserved

No changes to:

- normal Today UI
- Streamlit normal surface
- reports
- provider defaults
- provider runtime code
- model promotion
- persistence/cache
- background worker implementation
- Daily Next Action logic
- DailyCoachNarrativeContext truth fields
- validators
- deterministic fallback
- food/exercise catalogs
- workout generation
- nutrition formulas
- Training Level 5
- Nutrition Level 5

## Validation

Docs/design-only validation expected:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode docs-only
```

## Expected final status

`DAILY_COACH_NARRATIVE_ASYNC_TODAY_PREVIEW_DESIGN_V1_COMPLETE`

## Recommended next milestone

`Daily Coach Narrative Today Developer Panel v1`

Recommended scope:

- Streamlit Developer Mode only
- uses accepted backend debug endpoint
- manual trigger button
- displays deterministic fallback immediately
- displays approved provider narrative only if validated
- public-safe status only
- no normal Today user card yet
- no report integration
- no model promotion
- no direct_ollama default change

## Required multi-tier addendum

Architecture accepted the docs-only async Today preview design as the correct fallback-first foundation, with one required addendum before implementation.

The next implementation must support model lanes from the beginning:

- deterministic fallback: immediate/default lane
- `qwen3:8b`: fast developer-preview lane
- `qwen3:32b`: premium-quality developer-preview lane
- `qwen2.5:3b`: small baseline/regression lane

The implementation must not be single-lane `qwen3:8b` only.

Addendum doc:

- `docs/project_memory/architecture/daily_coach_narrative_multi_tier_async_preview_addendum_v1.md`
