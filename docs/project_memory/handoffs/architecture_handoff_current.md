# Architecture Handoff Current

Milestone: Nutrition Catalog Diagnostic v1

Status: diagnostic implemented / ready for Architecture review after final validation.

Source baseline: `main` at `94dc8fd`.

Branch: `feature/nutrition-catalog-diagnostic-v1`.

Milestone type: diagnostic / data audit / project memory update.

## Review focus

Architecture should review the diagnostic findings and choose the next nutrition foundation milestone.

Primary decisions:

- whether to accept Nutrition Catalog Diagnostic v1;
- whether Nutrition Serving Unit Data Model v1 should be next;
- whether a smaller Nutrition Canonical Food Model Review v1 is needed before serving-unit model work;
- how to handle canonical/legacy write-through before serving-based logging;
- whether optional nutrients such as fiber, sugar, and sodium are required before deterministic suggestions;
- how confidence should be modeled across serving units, logged actuals, suggestions, and provider contracts.

## Diagnostic findings summary

- 222 active canonical foods are present.
- 222 / 222 canonical foods have complete core macros.
- aliases/search are present for all canonical foods.
- two-layer tables exist, but raw/source staging has 0 records.
- serving-unit tables are not present.
- household units are not supported.
- logs are grams-only and food-id linked.
- actuals assume grams and do not represent confidence.
- high-value staple coverage is broad: 43 present, 1 missing.
- missing high-value staple: mixed nuts.
- deterministic suggestions exist but readiness is limited by missing serving units and confidence.
- provider grounding is limited until serving units and confidence are backend-owned and validated.

## Recommended next milestone

Recommended: Nutrition Serving Unit Data Model v1.

Alternative: Nutrition Canonical Food Model Review v1 if Architecture wants a design checkpoint before schema/model work.

## Acceptance intent

Accept this milestone if Architecture agrees that:

- diagnostic-first process was followed;
- diagnostic tool exists and runs;
- focused tests exist and pass;
- project memory captures the findings;
- no runtime/app behavior changed;
- no catalog expansion, serving units, logging changes, nutrition calculation changes, provider behavior, UI, workouts, recovery, migrations, or dependencies were added.

Proposed final status after successful closeout: `NUTRITION_CATALOG_DIAGNOSTIC_V1_ACCEPTED`.
