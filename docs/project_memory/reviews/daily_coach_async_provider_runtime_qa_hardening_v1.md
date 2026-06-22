# Daily Coach Async Provider Runtime QA Hardening v1 Review

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: `DAILY_COACH_ASYNC_PROVIDER_RUNTIME_QA_HARDENING_V1_ACCEPTED`

This milestone hardens the Developer Mode-only Daily Coach async provider runtime prototype across predictable failure modes.

Implemented hardening:

- disabled runtime remains safe and does not call provider
- enabled runtime with missing provider config fails safely before provider call
- enabled runtime with missing model config fails safely before provider call
- missing job fails safely before provider call
- stale job fails safely before provider call
- expired job fails safely before provider call
- provider unavailable path is sanitized
- timeout path remains sanitized
- malformed/prose output records parse failure with sanitized metadata only
- markdown-wrapped output remains safely rejected by strict parser unless future Architecture approves unwrapping
- schema mismatch remains safely rejected by strict parser
- validation rejection persists sanitized metadata only
- persistence failure after validation returns sanitized failure result
- Developer Mode UI uses sanitized exception labels instead of raw exception text

Boundary confirmation:

- QA hardening only
- Developer Mode-only runtime remains gated
- manual trigger only remains preserved
- provider disabled by default
- no provider call on normal Today render
- no provider call on page load
- no normal Today provider call added
- no public async narrative display added
- no automatic async job creation outside Developer Mode
- no worker/queue/scheduler/polling added
- no qwen3 call or bridge added
- no qwen3:32b promotion
- raw provider output not persisted or displayed
- rejected provider output not persisted or displayed
- full prompt/raw context/scratchpad not persisted or displayed
- deterministic fallback preserved
- model/provider policy preserved
- no Codex used

Recommended next milestone after acceptance: Daily Coach Async Approved Preview Bridge Design v1.

Do not authorize normal Today provider calls yet. Design the bridge before implementation.
