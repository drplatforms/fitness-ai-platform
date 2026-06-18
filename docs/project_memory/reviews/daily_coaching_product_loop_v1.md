# Daily Coaching Product Loop v1

Status: PLAN ACCEPTED / FIRST IMPLEMENTATION SLICE APPROVED

Planning result: DAILY_COACHING_PRODUCT_LOOP_V1_PLAN_ACCEPTED

First implementation slice: Daily Next Action Panel v1

## Goal

Turn the existing backend/provider/report architecture into a more useful daily product loop that helps the user answer:

> What should I do today?

This planning milestone does not change runtime behavior, provider semantics, Level 5 maturity, deployment, portfolio positioning, or Streamlit UI yet.

## Product loop definition

The daily loop should connect existing backend-approved workflows into one practical Today-page operating loop:

```text
Open Today
→ check current recovery/training/nutrition state
→ log or update key daily inputs
→ understand what matters most today
→ take one clear action
→ continue into the relevant workflow
```

The loop should feel like one connected coaching system rather than separate tabs.

## Existing capabilities to reuse

The project already has enough backend foundation to make the Today page more actionable:

- health state and report status
- recovery check-in state
- nutrition targets
- nutrition target-vs-actual display
- food logging and canonical food search
- Nutrition food suggestions under backend constraints
- workout preview
- workout logging and execution summaries
- Level 5 Training Report Section
- Level 5 Nutrition Report Section
- deterministic fallback and provider-gated report sections
- sanitized status, debug, and persisted-history boundaries

## Friction points

Current product friction is not provider safety. The main gap is daily usefulness:

- Today page does not yet fully drive the next action.
- Recovery check-in can feel disconnected from workout preview.
- Nutrition target-vs-actual and food logging are useful but not always action-oriented.
- Food suggestions do not yet drive a simple logging path.
- Workout preview and workout execution can feel like adjacent systems instead of one loop.
- Reports are valuable but can feel after-the-fact instead of guiding the next action.

## Recommended first implementation slice

`Daily Next Action Panel v1`

Purpose:

Make the Today page actionable by showing one primary backend-approved action, a short reason, and a pointer to the relevant workflow.

Candidate actions:

| Action | Example reason | Workflow pointer |
|---|---|---|
| Log a meal or snack | Today’s nutrition guidance is limited until more food data is logged. | Quick Log Food |
| Review nutrition target progress | Logged intake and targets are available for comparison. | Nutrition Target vs Actual |
| Review today’s workout | Current recovery/equipment state supports a structured session. | Workout Preview |
| Keep training conservative | Recovery check-in suggests using a lower-intensity plan. | Recovery-aware Workout Preview |
| Complete recovery check-in | Training guidance is limited until recovery is updated. | Recovery Check-in |
| Review today’s report guidance | Enough data exists to review validated report sections. | Full Report / Nutrition Report Section / Training Report Section |

## Truth boundary

Backend owns the next-action decision.

The panel may only use existing backend-approved signals:

- recovery/check-in state
- training state
- nutrition logging completeness
- nutrition target confidence
- workout preview availability
- report status / report section availability
- approved recommendation context

AI/provider output must not independently invent next actions, navigation, food, calorie, macro, workout, fatigue, or recovery claims.

## Proposed deterministic prioritization

The first implementation should use simple, auditable ordering before any scoring complexity:

1. Safety/recovery blockers first.
2. Missing daily inputs second.
3. Nutrition logging completeness third.
4. Workout preview/execution readiness fourth.
5. Report review when enough data exists.
6. Low-confidence/data-quality limitation action when evidence is insufficient.

This can be adjusted after QA observes seeded user behavior.

## Recommended implementation design

Add a backend-owned deterministic service only if implementation is approved:

- `models/daily_next_action_models.py`
- `services/daily_next_action_service.py`
- `tests/test_daily_next_action_service.py`

Recommended model fields:

- `action_id`
- `title`
- `reason`
- `workflow_target`
- `priority`
- `source_signals`
- `confidence_label`
- `limitations`

Streamlit should render the selected action on the Today page and link to existing workflows without rewriting all tabs.

## QA seed scenarios

Initial QA should cover:

| Seed user | Intended scenario |
|---|---|
| 101 | recovery-limited or conservative-training action |
| 102 | aligned-managed / workout-or-report-ready action |
| 105 | data-quality-limited / logging-completeness action |

Exact expected actions should be confirmed during implementation after inspecting current seeded data.

## Non-goals

Do not:

- start deployment work
- add auth/user accounts
- restart portfolio polish
- change Level 5 provider semantics
- make direct_ollama default
- run or promote qwen3
- remove provider gates
- remove deterministic fallback
- loosen validators
- add meal planning
- add new foods
- add RAG, embeddings, or agent orchestration
- merge Nutrition Target Display and Nutrition Report Section
- rewrite the whole UI
- change workout generation behavior
- change nutrition target formulas

## Recommended next milestone

`Daily Next Action Panel v1`

Expected implementation status after that milestone:

`DAILY_NEXT_ACTION_PANEL_V1_READY_FOR_QA`


## Architecture acceptance update

Architecture accepted this planning milestone and approved Daily Next Action Panel v1 for implementation on `feature/daily-coaching-product-loop-v1`. The approved implementation boundary is deterministic backend selection plus Today-page rendering only.
