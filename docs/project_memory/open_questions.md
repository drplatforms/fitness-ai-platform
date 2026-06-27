# Open Questions — Nutrition Actuals Provenance Debug / Integration Design v1

Current milestone: Nutrition Actuals Provenance Debug / Integration Design v1.

Status: backend implementation complete / ready for Architecture review.

## Current Architecture question

Should Architecture accept `GET /nutrition/{user_id}/actuals-confidence/debug?date=YYYY-MM-DD` as the first downstream integration surface for NutritionActualInterpretation?

Requested final status:

`NUTRITION_ACTUALS_PROVENANCE_DEBUG_INTEGRATION_DESIGN_V1_ACCEPTED`.

## Resolved implementation choice

Architecture preferred surfacing actuals provenance/confidence first through a narrow backend debug/integration path rather than normal user UI.

Backend implemented the user/date route because it lets QA compare actuals interpretation against Target-vs-Actual and recent logged foods.

## Future product questions preserved

These remain future scoping questions and are not authorized by this milestone:

1. Should actuals confidence next surface in Streamlit Developer Mode?
2. Should Target-vs-Actual eventually include confidence/provenance companion notes?
3. Should Nutrition Today Summary annotate incomplete/estimated/ranged actuals?
4. Should DailyCoachSynthesis receive confidence/provenance context?
5. Should AI nutrition explanations receive public-safe confidence context after a provider-specific design?
6. Which limitations should be user-visible versus Developer Mode only?

## Current answer boundary

This milestone exposes interpretation for backend/debug integration only.

It does not redesign nutrition analysis or authorize normal UI display.

## Historical continuity anchors — reference-only

- Daily Coach Async Provider Runtime Design v1
- Daily Coach Async Persistence Design v1
- qwen3:32b is research / future premium async candidate only
- deterministic fallback remains mandatory
- backend owns truth
- AI explains backend-approved truth
