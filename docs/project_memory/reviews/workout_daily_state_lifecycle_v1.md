# Workout Daily State Lifecycle v1 Review

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

## Summary

Workout Daily State Lifecycle v1 adds a deterministic read-time lifecycle boundary for planned workouts. Prior-date selected or active workouts that were not completed are no longer treated as today's active plan. Transient UI/session substitution state tied to that expired plan is cleared or ignored, while completed workout history remains intact.

## Files changed

- `services/workout_daily_state_service.py`
- `api/routes/workout_plans.py`
- `ui/streamlit_app.py`
- `tests/test_workout_daily_state_lifecycle_v1.py`
- `docs/project_memory/milestones/workout_daily_state_lifecycle_v1.md`
- `docs/project_memory/reviews/workout_daily_state_lifecycle_v1.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

## Behavior

- No workout for today resolves to `no_workout_today`.
- Today's selected workout resolves to `selected_today`.
- Today's started/in-progress workout resolves to `active_today`.
- Today's completed workout resolves to `completed_today`.
- Prior-date selected/active uncompleted workout resolves to `expired_uncompleted_prior`.
- Prior completed workouts remain in history.
- Normal Workout UI shows user-safe reset language and starts clean.
- Developer Mode can show sanitized daily-state metadata through existing diagnostic paths.

## Validation focus

- stale selected workout reset/ignore
- stale active workout reset/ignore
- stale substitution state cleanup
- completed history preservation
- today selected/active/completed preservation
- current-day route behavior
- user-safe UI copy
- workout count/substitution/Today regression tests

## Manual QA notes

Manual QA should confirm stale uncompleted prior-day state no longer appears as today's selected/active plan, completed history remains available, and Quick/Standard/Full generation works from a clean current-day state.

## Boundary confirmation

- No schema changes.
- No destructive history deletion.
- No workout generation changes.
- No substitution algorithm changes.
- No exercise count/default behavior changes beyond clean lifecycle integration.
- No provider/model/default changes.
- No report persistence changes.
- No Daily Coach changes.
- No nutrition/catalog changes.
