# Open Questions

## Weekly Coach Summary Async Contracts + Data Model v1

Current status:
Weekly Coach Summary Async Contracts + Data Model v1 is implemented and ready for Architecture review.

Open after acceptance:

- Architecture should authorize or revise Weekly Coach Summary Async Service Shell / No Worker v1.
- Backend should keep the next milestone deterministic-only and avoid persistence/provider/UI work unless explicitly authorized.
- QA should review model constraints, public_safe/displayable consistency, and absence of raw provider/debug/internal fields.

## Deferred Weekly Coach Summary decisions

- When should persistence schema be introduced?
- What exact Developer Mode inspection surface will weekly summaries need?
- Should any normal UI preview exist later, and behind what feature flag?
- Provider runtime remains deferred until deterministic service/persistence boundaries are accepted.

## Portfolio / LinkedIn / GitHub

Portfolio / LinkedIn / GitHub update remains deferred until a stable end-to-end persisted async workflow is ready to describe cleanly.
