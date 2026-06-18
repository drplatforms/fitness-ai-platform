# Daily Next Action Panel v1 Review

Status: IMPLEMENTED / READY FOR QA REVIEW

Implementation status: DAILY_NEXT_ACTION_PANEL_V1_IMPLEMENTED_PENDING_QA

## Summary

Daily Next Action Panel v1 implements the first slice of the Daily Coaching Product Loop.

The backend now returns a deterministic `DailyNextAction` object through `/daily-coach/{user_id}/next-action`. Streamlit renders the action card near the top of Today.

## Contract

The returned action includes:

- action_id
- title
- summary
- reason
- priority
- workflow_target
- severity
- evidence
- is_available
- blocked_reason

The service returns one primary action only.

## QA coverage

Focused tests cover:

- recovery/safety priority winning over nutrition/workout/report actions
- missing recovery check-in priority
- incomplete nutrition logging action
- workout review action
- report guidance action
- low-confidence/data-quality fallback action
- seeded users 101, 102, and 105 through the API route
- rejection of raw/debug/provider evidence keys

## Boundary review

Preserved:

- provider semantics
- Level 5 Training semantics
- Level 5 Nutrition semantics
- deterministic fallback
- provider gates
- validator strictness
- Nutrition Target Display / Nutrition Report Section separation
- Streamlit tab structure

No LLM call is used for next-action selection.
