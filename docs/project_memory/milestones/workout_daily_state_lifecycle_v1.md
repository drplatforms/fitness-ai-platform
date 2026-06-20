# Workout Daily State Lifecycle v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

## Purpose

Workout Daily State Lifecycle v1 prevents stale prior-date selected or active workout plans from appearing as today's active workout when the user did not complete/log the prior workout.

The milestone preserves completed workout history and keeps Workout Exercise Count Preference v1 and Workout Substitution UX v1 behavior intact.

## Implemented scope

- Added deterministic workout daily state resolution.
- Added a current-day workout route for selected/active/completed state.
- Treated prior-date uncompleted selected/active plans as expired for today's UI.
- Cleared transient Streamlit workout and substitution state when stale prior workout state is detected.
- Added user-safe reset messaging.
- Preserved completed workout plan/history records.
- Added lifecycle tests for no-workout, selected, active, completed, expired, substitution cleanup, and route behavior.

## State model

- `no_workout_today`: no current-day selected, active, or completed workout plan.
- `selected_today`: a current-day workout plan is selected but not started/completed.
- `active_today`: a current-day workout is started or in progress.
- `completed_today`: a current-day completed planned workout exists.
- `expired_uncompleted_prior`: an older selected/active workout exists but is not completed and should not display as today's plan.

## User-safe stale-state message

```text
An unfinished workout from a previous day was cleared so you can start fresh today.
```

## Boundaries preserved

- No database schema changes.
- No destructive completed-history deletion.
- No workout generation algorithm changes.
- No workout exercise count preference behavior changes except clean daily-state integration.
- No substitution algorithm changes.
- No catalog changes.
- No provider/model changes.
- No report persistence changes.
- No Daily Coach changes.
- No nutrition changes.
