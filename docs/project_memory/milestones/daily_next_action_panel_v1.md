# Daily Next Action Panel v1

Status: IMPLEMENTED / PENDING QA

Implementation status: DAILY_NEXT_ACTION_PANEL_V1_IMPLEMENTED_PENDING_QA

## Goal

Make the Today page answer:

> What should I do today?

The panel renders exactly one deterministic backend-approved action near the top of Today.

## Implemented files

- `models/daily_next_action_models.py`
- `services/daily_next_action_service.py`
- `api/routes/daily_coach.py`
- `tests/test_daily_next_action_service.py`
- `ui/streamlit_app.py`

## Approved action set

- Complete recovery check-in
- Keep training conservative
- Log a meal or snack
- Review nutrition target progress
- Review today's workout
- Review today's report guidance

## Deterministic priority order

1. Recovery/safety blocker
2. Missing recovery check-in
3. Nutrition logging incompleteness
4. Workout preview/readiness
5. Report guidance readiness
6. Data-quality / nutrition target progress limitation

## Boundary

Backend owns the next-action decision. Streamlit renders the decision. No AI/provider output controls action selection or navigation.

The panel must not invent food, calorie, macro, workout, fatigue, or recovery claims.

## Expected QA status

DAILY_NEXT_ACTION_PANEL_V1_ACCEPTED
