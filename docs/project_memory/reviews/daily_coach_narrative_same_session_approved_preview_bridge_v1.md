# Daily Coach Narrative Same-Session Approved Preview Bridge v1 Review

Proposed final status: DAILY_COACH_NARRATIVE_SAME_SESSION_APPROVED_PREVIEW_BRIDGE_V1_ACCEPTED

## Summary

Implemented a session-only approval bridge between developer-gated provider preview and the Today Coach Note card.

The implementation allows a validated preview to be explicitly approved for the active Streamlit session. The approved provider text can replace only the coach note body while deterministic backend-owned facts remain authoritative.

## Implementation

- Added `services/daily_coach_same_session_approval_service.py`.
- Added explicit eligibility checks for parse success, validation success, approved narrative presence, no-leak display text, same user, same date, and same action/workflow context.
- Added Streamlit session-state storage for the approved preview.
- Added Developer Mode approval and revert controls.
- Kept normal Today card route deterministic.
- Added service and UI/source tests for approval, rejection, no-provider-call, no-persistence, and no-leak boundaries.

## Validation focus

- valid preview can be approved for same session
- rejected preview cannot be approved
- raw/debug/provider terms cannot appear in normal card text
- approval mismatch is ignored/cleared
- approval is session-state only
- normal Today card does not call provider preview

## Deferred

- provider promotion
- async provider generation
- narrative persistence
- cache/persistence design
- model QA matrix expansion


## Runtime smoke fix

Manual runtime smoke found two Developer Mode issues before acceptance:

- Streamlit diagnostics could crash PyArrow when a mixed boolean/string `Value` column was rendered as a dataframe.
- Some local Ollama/qwen responses can include common wrapper text such as thinking blocks or markdown fences around an otherwise valid JSON object.

The follow-up fix keeps the strict parser and validator in place, but normalizes common wrappers before parsing and exposes only sanitized Developer Mode diagnostics. Raw provider text, rejected output, prompts, and model context remain excluded from normal UI.
