# Direct Ollama Training Report Section — Bounded Coaching Claims v1

## Status

Implemented as a provider-path spike refinement after Coach Voice Autonomy v1.1.

This milestone keeps the existing safety contract and adds backend-derived bounded training claims so the model has more truthful coaching material to synthesize.

## Why this exists

Coach Voice Autonomy moved the training report section away from finished approved coaching frames and toward semantic coaching moves. Runtime QA showed that qwen3 could produce more natural coaching language, but it also tried to express ideas like steady reps and effort context before the backend had explicitly approved those meanings.

The fix is not to ban every natural phrase. The fix is to promote narrow, single-session observations into approved backend claims.

## Architecture

The flow remains:

```text
backend-approved quote context
→ required fact anchors
→ semantic coaching moves
→ backend-derived bounded training claims
→ structured model candidate
→ strict parser
→ strict validator
→ approved section or deterministic fallback
```

Backend owns:

- workout and exercise names
- loads, reps, sets, and RIR values
- required anchors
- bounded training claim derivation
- forbidden scopes
- validation and fallback

AI owns:

- phrasing
- tone
- concise synthesis
- user-facing coaching feel

## New model-facing payload field

`approved_bounded_training_claims` is added to the quote-only model-facing context.

Each claim can include:

- `claim_id`
- `claim_type`
- `approved_meaning`
- `required_names`
- `required_terms`
- `allowed_terms`
- `forbidden_scope`

## Claim types

### `single_session_rep_pattern`

Generated when one exercise has at least two logged sets and all logged sets use the same rep count.

Allowed examples:

- same rep count across logged sets
- steady reps in this session
- consistent rep counts, if clearly scoped to the logged sets/session

Still forbidden:

- consistent performance over time
- consistency trend
- you are consistent
- progression confirmed

### `single_session_effort`

Generated when a final logged set is at 0–1 RIR.

Allowed examples:

- close to failure based on the logged RIR
- high effort within this logged session
- effort context for this workout

Still forbidden:

- strong execution
- good form
- recovery handled it well
- effort is consistently high

### `complete_reference_lift`

Generated for logged lifts with complete load, set, rep, and RIR detail.

Allowed examples:

- best reference lifts from this workout
- clearest signal from this session
- use these as anchors for the next training decision

Still forbidden:

- proves progress
- proves the plan worked
- shows recovery is good
- shows form is strong

### `scope_limit`

Generated when a named workout/session exists.

Allowed examples:

- single-session reference point
- one workout can guide the next choice
- useful, but not enough to call it a trend

Still forbidden:

- progression confirmed
- recovery pattern
- fatigue pattern

## Validator behavior

The validator now distinguishes narrow single-session language from broad claims.

Allowed only when backed by an approved bounded claim:

- same rep count / steady reps / consistent rep counts scoped to logged sets
- close to failure / high effort scoped to this session and logged RIR
- reference lift language based on complete logged details
- single-session scope limitations

Still rejected:

- broad consistency claims
- trend/progression claims
- form/control claims
- recovery/fatigue claims
- adherence/completion claims
- plan-alignment claims
- debug/meta copy
- generic safe copy

## Non-goals

This milestone does not:

- make direct_ollama default
- make qwen3 required
- wire the provider into full report assembly
- change Streamlit
- change persistence
- loosen parser behavior
- loosen unsupported-claim validation broadly
- call live Ollama in pytest

## Runtime QA focus

After applying this milestone, run qwen2.5:3b and qwen3:8b against user 102 / 2026-06-06.

Success means:

- qwen2.5 remains safe and acceptable
- qwen3 may pass or fail safely
- approved outputs can use bounded single-session claims naturally
- broad consistency/progression/recovery/form claims still fail
- fallback remains deterministic and public-safe
