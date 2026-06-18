# Open Questions

Last updated: 2026-06-18

## Product voice

- When should qwen3 be re-tested for Training product voice?
- What validator/evidence improvements are needed before qwen3 can safely sound more natural?

## Nutrition

- Should Architecture approve `Nutrition Provider Implementation v1` / `Nutrition Provider Opt-In Implementation v1` next?
- Should the future implementation add both `nutrition_report_section_direct_ollama_provider.py` and `nutrition_report_section_provider_service.py` in one milestone or split them?
- Should Nutrition provider execution be tested first as section-only runtime QA before any full-report integration?
- What exact runtime QA matrix is required before Nutrition can move from Level 3 to Level 4?
- What additional negative validator cases are required after observing real qwen2.5 output?

## Recovery

- What backend-owned recovery evidence is needed before recovery becomes a provider-ready section?

## Grounded Recommendation

- How should cross-domain recommendations consume approved section claims without becoming a monolithic AI-owned summary?

## Developer workflow

- Should the new Windows validation helper eventually be mirrored with a Linux runtime-QA helper?
