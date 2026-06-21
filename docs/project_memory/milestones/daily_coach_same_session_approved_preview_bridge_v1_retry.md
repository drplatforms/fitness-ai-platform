# Daily Coach Same-Session Approved Preview Bridge v1 Retry

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Branch: `feature/daily-coach-same-session-approved-preview-bridge-v1-retry`

## Goal

Implement a manual Developer Mode bridge that allows a validated Daily Coach provider narrative to be approved for display in the current Streamlit session only.

## Approved boundary

This milestone is intentionally narrow:

- provider preview remains manual and Developer Mode-only
- `qwen2.5:3b` is the only bridge baseline model
- normal Today load remains deterministic and does not call provider preview
- approval is explicit and manual
- approval is stored only in `st.session_state`
- approval is invalidated by user/date/next-action/workflow-target/provider/model context
- approved narrative may display in Today Coach Note only for the active Streamlit session
- nothing is persisted to SQLite, reports, files, cache tables, or project artifacts

## Not approved

- no provider call on normal Today load
- no automatic approval
- no provider/model default change
- no model promotion
- no qwen2.5:7b bridge use
- no qwen3 bridge use
- no database/schema/report persistence change
- no Daily Next Action, nutrition, workout, lifecycle, or catalog behavior change
- no raw provider output, rejected output, prompt, or model context in normal UI

## Implementation notes

The bridge uses `ui/daily_coach_session_approval.py` for testable session-only approval behavior:

- approval eligibility
- context-key construction
- session-state storage
- active-context retrieval
- stale context invalidation

Streamlit Developer Mode displays the approval button only after an approved preview is eligible. Normal Today UI may show a user-facing `Session-approved coach note` label after manual approval, without provider/model/debug internals.

## Validation expectations

- focused same-session bridge tests
- provider matrix tests
- provider reliability tests
- Daily Coach preview route/service tests
- Developer Preview stabilization tests
- Today card tests
- Daily Next Action tests
- report persistence boundary tests
- project memory tests
- memory-check
- stale-doc-check
- artifact sweep
