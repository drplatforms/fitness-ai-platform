# QA Handoff — Daily Coach Async Approved Preview Bridge Design v1

Status: `DESIGNED / READY FOR QA / ARCHITECTURE REVIEW`

Branch: `feature/daily-coach-async-approved-preview-bridge-design-v1`

## QA review focus

Review the design for testability and future QA coverage.

The design requires future implementation tests for:

- feature flag disabled path leaves normal Today unchanged
- no provider call on Today render
- no provider call on page load
- stale/expired/non-displayable/non-public-safe/context-mismatch narratives hidden
- deterministic Daily Next Action remains primary
- fallback/no-preview behavior safe
- raw/rejected provider output not visible
- provider/model diagnostics absent in normal UI
- Developer Mode diagnostics gated
- qwen3/qwen3:32b unused

## QA non-goals for this milestone

No manual app smoke required unless unexpected runtime files changed. This milestone is docs/design only.
