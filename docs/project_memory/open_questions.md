# Open Questions

Last updated: 2026-06-18

## Product voice

- When should qwen3 be re-tested for Training product voice?
- What validator/evidence improvements are needed before qwen3 can safely sound more natural?

## Nutrition

- Does Nutrition Provider Approved Suggestion Runtime QA v1 reduce or resolve users 101-104 approved-suggestion-present `practical_food_focus` failures?
- Does user 105 remain provider-approved, or safely fallback, without no-approved-suggestion availability regression?
- If qwen2.5 still fails after approved suggestion context tuning, what exact provider wording or diagnostic category remains?
- What additional runtime cases are needed before Architecture considers Level 5 promotion?
- What additional negative validator cases are required after observing real qwen2.5 output in matrix runtime QA?
- When should Nutrition provider metadata be allowed into persisted full-report history, and at what level of detail?
- Should debug/QA-only Nutrition validation diagnostic categories remain limited to `/reports/status/{job_id}/debug`, or should Architecture define a broader debug-only QA surface later?

## Recovery

- What backend-owned recovery evidence is needed before recovery becomes a provider-ready section?

## Grounded Recommendation

- How should cross-domain recommendations consume approved section claims without becoming a monolithic AI-owned summary?

## Developer workflow

- Should the new Windows validation helper eventually be mirrored with a Linux runtime-QA helper?
