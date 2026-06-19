# Daily Coach Narrative v1 Planning

Status: PLANNED / PENDING ARCHITECTURE ACCEPTANCE

Planning status: `DAILY_COACH_NARRATIVE_V1_PLANNED_PENDING_ARCHITECTURE_ACCEPTANCE`

## Purpose

Daily Coach Narrative v1 Planning defines the first safe path for a short coach-style explanation layered over the deterministic Daily Next Action Panel.

This is planning only. It does not implement runtime narrative generation, does not call a model, does not integrate model output into Today or Streamlit, and does not promote any model.

The product goal is to let the future app answer:

```text
Why does this next action matter, and how should I think about it today?
```

The deterministic Daily Next Action service continues to answer:

```text
What should I do today?
```

The narrative may explain the backend-selected action. It may not choose, change, rank, override, or invent the action.

## Current basis

Coach Voice Contract Tightening v1 showed that bounded model language is becoming repeatable under a strict output contract.

Accepted model findings carried into this planning milestone:

- `qwen3:8b` remains the best practical evaluation-only bounded coach voice candidate.
- `qwen3:32b` remains the best offline / chores-mode quality reference.
- `qwen2.5:3b` improved to a compliant small baseline but remains more generic.
- `qwen3:14b` partially improved but remains unreliable.
- `qwen3:30b-a3b` remains incompatible with the strict JSON-only contract.

No model is production-approved.

## Narrative purpose

A Daily Coach Narrative is allowed to:

- explain the backend-selected Daily Next Action
- restate why the action matters today using approved facts
- reflect approved recovery, nutrition, workout, or data-quality state
- acknowledge limited data when confidence is limited
- use concise coach-like framing
- point back to the approved workflow target
- make the deterministic action feel more personal without changing it

A Daily Coach Narrative is not allowed to:

- choose the Daily Next Action
- change the Daily Next Action
- add a second action that backend did not approve
- override backend confidence
- invent facts, foods, exercises, targets, workouts, readiness, fatigue, progression, consistency, or medical claims
- create meal plans, workout substitutions, or training adjustments
- present itself as clinical, medical, diagnostic, or prescriptive authority

## Authority boundary

Backend owns:

- selected next action
- recommended focus
- workflow target
- next action title and reason
- recovery status
- nutrition target/actual state
- workout readiness state
- confidence limits
- approved facts
- approved limitations
- forbidden claims
- fallback behavior
- validator approval

Model owns only:

- wording
- tone
- concise explanation
- coach-like framing

The model never owns truth, action selection, target calculation, confidence level, or validation.

## Proposed context packet

Future implementation should introduce a backend-owned `DailyCoachNarrativeContext` built from existing Daily Next Action state and approved summary services.

Recommended fields:

```text
user_id
date
next_action_id
next_action_title
next_action_reason
workflow_target
severity
priority
approved_focus
approved_facts
approved_limitations
nutrition_status_summary
recovery_status_summary
workout_status_summary
forbidden_claims
confidence_language
```

The context should contain only already-approved, user-safe facts. It should be compact enough for a local model and explicit enough for strict validation.

Do not feed:

- raw logs
- raw provider output
- raw debug payloads
- full catalog dumps
- private diagnostics
- validation internals
- unfiltered history
- raw SQL rows
- raw nutrition source payloads
- raw workout execution notes
- provider/runtime metadata

## Output contract

The future model-facing output contract should reuse or specialize the tightened coach voice object:

```json
{
  "coach_note": "string",
  "key_takeaway": "string",
  "recommended_focus": "string",
  "confidence_language": "string",
  "used_approved_facts": ["string"],
  "avoided_claims": ["string"]
}
```

Required rules:

- JSON only
- no markdown
- no prose wrapper
- no extra keys
- no missing keys
- `recommended_focus` must exactly equal the backend-approved focus
- `used_approved_facts` must exactly match strings from `approved_facts`
- `coach_note` must be compact enough for a Today card
- `confidence_language` must not exceed backend confidence

## Required validators

Future validator rules should reject:

- non-JSON output
- missing or extra keys
- changed `recommended_focus`
- changed action or workflow target
- unapproved facts
- invented numbers
- invented foods
- invented exercises
- meal plans
- unsupported calorie, macro, or target claims
- unsupported recovery, fatigue, readiness, progression, or consistency claims
- medical or clinical nutrition claims
- new workout prescriptions or substitutions
- generic filler that does not use approved context
- coach notes that are too long for the intended UI surface

Validation must not be loosened to make a model pass.

## Fallback behavior

If narrative provider output fails parsing, schema validation, fact matching, or safety validation:

- render deterministic Daily Next Action wording
- do not expose rejected output
- do not expose raw validation errors in normal UI
- do not mark narrative provider-approved
- keep the deterministic title/reason/action visible
- keep normal UI public-safe

The deterministic Daily Next Action Panel remains useful even when narrative generation fails.

## Model candidate strategy

Eligible future runtime candidates:

- Primary practical candidate: `qwen3:8b`
- Small compliant baseline: `qwen2.5:3b`
- Offline quality reference: `qwen3:32b`

Not recommended for v1 runtime:

- `qwen3:14b`
- `qwen3:30b-a3b`

No model is production-approved by this planning milestone.

## UI placement concept

Planning-only future location:

- inside the Daily Next Action Panel
- under the deterministic title and backend-owned reason
- visually subordinate to the deterministic action

The deterministic action remains visible even if narrative fails.

Normal Today UI must not expose raw model output, raw provider metadata, validator internals, or debug payloads.

## What must remain deterministic

The following must remain backend-owned and deterministic:

- action selection
- workflow target
- recommended focus
- nutrition targets
- nutrition actuals
- macro gaps and display permissions
- recovery status
- workout readiness
- confidence language ceiling
- allowed facts
- forbidden claims
- fallback rendering
- provider approval status

## First implementation slice after planning

Recommended next milestone:

`Daily Coach Narrative Context Builder v1`

Goal:

Build the backend-approved narrative context packet from existing Daily Next Action state without calling a model.

Suggested implementation sequence:

1. Planning
2. Context Builder
3. Offline Runtime QA using selected model candidates
4. Provider wrapper behind explicit opt-in flag
5. Streamlit Developer Mode preview only
6. Normal Today UI integration only after validation

## Strict non-goals preserved

This planning milestone does not:

- implement production narrative runtime
- integrate model output into Today
- integrate model output into Streamlit
- integrate model output into reports
- promote qwen3
- approve any model for production
- make direct_ollama default
- change Daily Next Action decision logic
- change provider gates
- loosen validators
- remove deterministic fallback
- add RAG, embeddings, scraping, or agents
- add meal planning
- add AI-generated food suggestions
- add AI-generated exercise suggestions
- change food catalog
- change exercise catalog
- change workout generation
- change nutrition formulas
- change Level 5 Training semantics
- change Level 5 Nutrition semantics
- expose raw model/debug/provider output in normal UI

## Expected acceptance status

If accepted, Architecture should mark this milestone:

`DAILY_COACH_NARRATIVE_V1_PLANNED_PENDING_CONTEXT_BUILDER`
