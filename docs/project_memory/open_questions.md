# Open Questions

Last updated: 2026-06-18

## Daily Coaching Product Loop

- Which backend-owned signals should drive the first deterministic `Daily Next Action Panel v1` ranking order?
- Should the first action priority be data completeness first, safety/recovery first, or workout readiness first?
- Which existing Today-page workflows should the panel link to first: recovery check-in, quick food logging, workout preview, or report generation?
- Should the next-action service expose a stable API/model before Streamlit renders it, or should the first implementation remain UI-local with backend helper functions?
- How should seeded users 101, 102, and 105 map to QA scenarios for recovery-limited, aligned-managed, and data-quality-limited daily actions?

## Product voice

- When should qwen3 be re-tested for Training product voice?
- What validator/evidence improvements are needed before qwen3 can safely sound more natural?

## Nutrition

- After accepted forced-fallback runtime QA, should public claims be updated to say Nutrition fallback semantics are runtime-validated through a QA-only forced-invalid provider mode?
- Should a future production-like fallback QA scenario be designed, or is the QA-only forced-invalid mode sufficient for portfolio claims and regression protection?
- Should Nutrition remain opt-in indefinitely after Level 5 runtime validation, or should a separate future default-provider readiness review be planned?
- What additional non-seeded runtime cases are required after Level 5 promotion, if any?
- What additional negative validator cases are required after observing real qwen2.5 approved output in matrix runtime QA?
- When should Nutrition provider metadata be allowed into persisted full-report history, and at what level of detail?
- Should debug/QA-only Nutrition validation diagnostic categories remain limited to `/reports/status/{job_id}/debug`, or should Architecture define a broader debug-only QA surface later?

## Recovery

- What backend-owned recovery evidence is needed before recovery becomes a provider-ready section?

## Grounded Recommendation

- How should cross-domain recommendations consume approved section claims without becoming a monolithic AI-owned summary?

## Developer workflow

- Should the new Windows validation helper eventually be mirrored with a Linux runtime-QA helper?
