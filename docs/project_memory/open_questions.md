# Open Questions

## Weekly Coach Summary Async Service Shell / No Worker v1

Current status:
Weekly Coach Summary Async Service Shell / No Worker v1 is implemented and ready for Architecture review.

Open after acceptance:

- Architecture should choose Weekly Coach Summary Async Persistence Design v1 or Weekly Coach Summary Developer Mode Inspection v1.
- Backend should keep persistence/provider/UI work out of the service-shell milestone unless separately authorized.
- QA should verify deterministic output, fallback behavior, absence of provider/runtime dependencies, and public-safe language boundaries.

## Deferred Weekly Coach Summary decisions

- What exact weekly summary persistence schema will be used?
- What Developer Mode inspection surface will weekly summaries need?
- Should any normal UI preview exist later, and behind what feature flag?
- Provider runtime remains deferred until deterministic service/persistence boundaries are accepted.

## Portfolio / LinkedIn / GitHub

Portfolio / LinkedIn / GitHub update remains deferred until a stable end-to-end persisted async workflow is ready to describe cleanly.
