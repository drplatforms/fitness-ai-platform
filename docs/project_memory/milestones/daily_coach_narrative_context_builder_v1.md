# Daily Coach Narrative Context Builder v1

Status: IMPLEMENTED / PENDING QA

Implementation status: `DAILY_COACH_NARRATIVE_CONTEXT_BUILDER_V1_IMPLEMENTED_PENDING_QA`

## Purpose

Daily Coach Narrative Context Builder v1 creates the backend-approved context packet that a future Daily Coach Narrative provider may use to explain the deterministic Daily Next Action.

This milestone does not generate narrative copy. It only prepares deterministic, public-safe context.

## Product role

Daily Next Action answers:

```text
What should I do today?
```

Future Daily Coach Narrative may answer:

```text
Why does this matter, and how should I think about it?
```

This slice builds the bridge between those two ideas by converting existing Daily Next Action state into `DailyCoachNarrativeContext`.

## Implemented files

Added:

- `models/daily_coach_narrative_models.py`
- `services/daily_coach_narrative_context_service.py`
- `tests/test_daily_coach_narrative_context_service.py`
- `docs/project_memory/milestones/daily_coach_narrative_context_builder_v1.md`
- `docs/project_memory/reviews/daily_coach_narrative_context_builder_v1.md`

Updated:

- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/architecture/daily_coach_narrative_context_v1.md`

## Context model

`DailyCoachNarrativeContext` contains:

- `user_id`
- `date`
- `next_action_id`
- `next_action_title`
- `next_action_reason`
- `workflow_target`
- `priority`
- `severity`
- `approved_focus`
- `confidence_language`
- `approved_facts`
- `approved_limitations`
- `forbidden_claims`
- `fallback_note`
- `source_metadata`
- `context_status`

## Deterministic builder

The builder:

1. Calls the existing deterministic Daily Next Action service.
2. Preserves the selected action exactly.
3. Preserves the workflow target exactly.
4. Sets `approved_focus` to the deterministic next action title.
5. Creates exact approved fact strings from public-safe action fields and public-safe evidence.
6. Creates approved limitations from recovery/logging/confidence context.
7. Creates deterministic fallback wording from the Daily Next Action title and reason.
8. Adds forbidden claim categories for future provider validation.
9. Validates the context contract before returning it.

## Explicit non-behavior

This milestone does not:

- call qwen
- call direct_ollama
- call CrewAI
- call any model
- produce final narrative copy
- approve model output
- add Today/Streamlit normal UI integration
- add report integration
- add production provider paths
- change Daily Next Action decision logic
- change nutrition formulas
- change workout generation
- change Training Level 5 or Nutrition Level 5 semantics

## Public-safe facts

The context builder intentionally filters evidence to simple scalar public-safe values.

It does not expose:

- raw provider payloads
- debug tracebacks
- validation errors
- raw logs
- raw SQL rows
- model/runtime metadata
- unbounded history
- catalog dumps

## Fallback behavior

The deterministic fallback note is:

```text
{next_action_title}: {next_action_reason}
```

This means a failed future provider can always fall back to the existing backend-owned Daily Next Action wording.

## Validation rules implemented in this slice

The context validator checks:

- required text fields are present
- `approved_focus` does not change the Daily Next Action title
- priority is positive
- approved facts are not sparse
- forbidden claims are present
- fallback note is deterministic
- public-safe payload does not expose raw/debug/provider/model metadata

Future provider validation remains a later milestone.

## Tests

Focused tests prove:

- context preserves Daily Next Action and workflow target exactly
- approved facts and limitations are explicit
- forbidden claims cover the v1 safety boundary
- fallback note is deterministic
- internal evidence keys are filtered out
- changed approved focus is rejected
- non-deterministic fallback wording is rejected
- top-level builder uses Daily Next Action without any model call
- invalid context raises `DailyCoachNarrativeContextValidationError`

## Expected QA status

`DAILY_COACH_NARRATIVE_CONTEXT_BUILDER_V1_ACCEPTED`

## Recommended next milestone

Daily Coach Narrative Offline Provider Runtime QA v1.

This next milestone should use the approved context packet with selected evaluation candidates in an offline/debug-only path. It should still avoid normal Today UI integration until runtime QA is accepted.
