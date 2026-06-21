# Daily Coach Same-Session Approved Preview Bridge v1 Retry Review

Status: IMPLEMENTED / AWAITING ARCHITECTURE REVIEW

Proposed accepted status: `DAILY_COACH_SAME_SESSION_APPROVED_PREVIEW_BRIDGE_V1_RETRY_ACCEPTED`

## Summary

Implemented a manual Developer Mode same-session approval bridge for Daily Coach provider narratives.

A qwen2.5:3b provider preview may be approved only after the backend preview contract reports:

- `provider_enabled == true`
- `provider_attempted == true`
- `selected_provider == direct_ollama`
- `selected_model == qwen2.5:3b`
- `parse_success == true`
- `validation_success == true`
- `approved_narrative_returned == true`
- `fallback_used == false`
- no fallback reason
- no forbidden/debug leaks
- approved narrative text is present
- user/date/next-action/workflow-target context is present

The approved narrative is stored in Streamlit session state only and can display in Today Coach Note only while the active context still matches.

## Boundary confirmation

- qwen2.5:3b is used as bridge baseline only
- qwen2.5:3b is not promoted to product default
- qwen2.5:7b is not bridge-enabled
- qwen3:8b is not bridge-enabled
- qwen3:14b is not bridge-enabled
- qwen3:32b is not bridge-enabled
- qwen3:30b-a3b is not bridge-enabled
- no model is promoted
- no provider default changed
- no provider call occurs on normal Today load
- provider preview remains manual Developer Mode only
- approval is manual
- approval is session-only
- approved narrative does not persist
- no DB write
- no report write
- no file write
- no schema change
- no Daily Next Action change
- no nutrition calculation change
- no workout generation/lifecycle change
- no catalog change
- no raw provider output displayed
- no rejected provider output displayed
- no prompt/model context displayed
- Developer Mode diagnostics remain sanitized

## Manual QA still required before acceptance

Manual QA should verify:

- Windows FastAPI + Windows Streamlit + Windows Ollama runtime
- QA user 102 normal Today load remains deterministic
- qwen2.5:3b manual preview is approved
- approval button appears only after eligible preview
- approved narrative displays only after session approval
- normal UI hides provider/model/debug internals
- context/session changes invalidate approval
- no persistence is observed
