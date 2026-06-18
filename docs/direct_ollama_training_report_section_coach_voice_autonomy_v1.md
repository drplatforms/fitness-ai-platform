# Direct Ollama Training Report Section Coach Voice Autonomy v1

Status: implemented as a provider-focused spike refinement.

## Purpose

Product Voice Polish v1 made the training report section safer and less stiff, but runtime QA showed that qwen2.5:3b and qwen3:8b could sound nearly identical. That was a product-voice warning: the model-facing `approved_coaching_frames` were too close to finished user-facing copy.

Coach Voice Autonomy v1 keeps the Provider v1 safety contract intact while moving the model-facing style source from finished coaching sentences to semantic coaching moves.

## Architecture position

The backend still owns:

- workout and exercise names
- logged sets, reps, loads, and RIR values
- required fact anchors
- approved interpretation claims
- approved semantic coaching moves
- forbidden claim categories
- validation and deterministic fallback

The model owns:

- phrasing
- tone
- transitions
- concise synthesis
- coach-like user-facing language

The validator still prevents unsupported claims and rejects copied backend guidance.

## What changed

The model-facing quote context now includes `approved_coaching_moves` as the primary coaching-style source.

`approved_coaching_frames` remains present only as a compatibility field and is intentionally empty in this milestone.

Each coaching move provides semantic ingredients such as:

- `allowed_meaning`
- `required_names`
- `required_terms`
- `allowed_terms`
- `forbidden_claims`

The prompt instructs the model to use coaching moves as ingredients and not copy `allowed_meaning` wording directly.

## Validation additions

Coach Voice Autonomy v1 adds validation for:

- required coaching-move coverage in narrative fields
- direct-copy detection against semantic move wording
- direct-copy detection against the legacy finished coaching frames
- scope-limit coverage in fatigue/recovery and limitations fields
- generic safe-but-weak coaching copy

Existing validation remains in place:

- exact required anchor placement
- approved workout/exercise name checks
- unapproved number rejection
- unsupported progression rejection
- unsupported fatigue/recovery rejection
- unsupported form/control rejection
- unsupported plan-alignment rejection
- unsupported adherence/completion rejection
- debug/meta/internal copy rejection
- deterministic fallback on invalid output

## Non-goals

This milestone does not:

- make direct Ollama default
- wire the provider into full report assembly
- change Streamlit
- change report persistence
- loosen parser behavior
- loosen validation
- require qwen3 to pass
- call live Ollama in pytest

## Runtime QA expectation

After applying this milestone, run qwen2.5:3b and qwen3:8b manually against the standard seeded scenario:

- user_id: 102
- date: 2026-06-06

Success is not only `validation_status: approved`.

The output should also:

- preserve the first two exact anchors
- avoid unsupported claims
- avoid debug/meta/internal wording
- avoid near-copying backend coaching guidance
- sound more like coaching than copied frames
- show more room for qwen3 to produce stronger prose if it stays inside boundaries

If qwen3 fails safely, that is acceptable. If qwen3 passes but still sounds identical to qwen2.5, continue iterating on model-facing semantic guidance.
