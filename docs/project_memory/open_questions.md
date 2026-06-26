# Open Questions

## Nutrition Serving Unit Data Model v1 results

Resolved implementation findings:

- Serving-unit model/service/schema support now exists in the active branch.
- Serving units are linked to canonical foods.
- `grams_default` is required and positive.
- `grams_min` / `grams_max` ranges are supported.
- Service/model validation enforces `grams_min <= grams_default <= grams_max` when ranges are present.
- Confidence vocabulary for this milestone is Low / Moderate / High.
- Starter seed is idempotent.
- First seed run inserted 18 serving units.
- Second seed run inserted 0 and updated 18, proving no duplicate rows were created.
- Active serving-unit count is 18.
- Foods with active serving units: 12.
- Missing canonical foods: none.
- Normal nutrition logging remains unchanged.
- Target-vs-Actual remains unchanged.
- Streamlit remains unchanged.
- Provider/Ollama/CrewAI behavior remains unchanged.

## Architecture decision needed after Serving Unit Data Model v1

1. Should the next milestone be Nutrition Serving Unit Logging Contract Design v1?

Recommended answer: yes. Serving-unit metadata exists, but logging by serving unit is intentionally not exposed yet.

2. Should Nutrition Actuals Confidence Model v1 happen before serving-unit logging implementation?

Recommended answer: Architecture should decide. Estimated serving-unit logs need confidence semantics before they are treated the same as weighed gram logs.

3. Should logs preserve original serving quantity/unit and resolved grams?

Recommended answer: yes for future logging, so user intent and backend-calculated grams remain auditable.

4. Should logs preserve `grams_default`, `grams_min`, `grams_max`, confidence, and source at the time of logging?

Recommended answer: likely yes, to avoid historical actuals changing if serving-unit metadata is updated later.

5. Should serving-unit logging mutate existing grams-based behavior?

Recommended answer: no. Serving-unit logging should resolve to grams through backend-owned metadata while preserving estimate/confidence context.

6. Should provider/AI use serving units now?

Recommended answer: not in user-facing output until logging and actuals-confidence contracts are accepted. Provider may eventually explain backend-approved serving units only.


## Nutrition Catalog Diagnostic v1 results

Diagnostic answered the first catalog baseline questions.

Resolved findings:

- The app has both legacy food tables and canonical food tables.
- Legacy food records: 3,475.
- Canonical food records: 222.
- Active canonical foods: 222.
- Raw/source food records: 0.
- Serving-unit tables: none.
- Alias rows: 555.
- Foods with aliases: 222.
- Foods without aliases: 0.
- Canonical core macro completeness: 222 / 222.
- Optional nutrient coverage for fiber/sugar/sodium: 0 in current diagnostic.
- High-value staple coverage: 43 present, 1 missing.
- Missing high-value staple: mixed nuts.
- Logs are grams-based, linked to food id, and do not support quantity/unit or servings.
- Actuals assume grams.
- Confidence is not represented.
- Deterministic food suggestions exist but are limited by missing serving units and confidence.
- Provider grounding is limited until serving units and confidence are added.

## Architecture decision needed after diagnostic

1. Should the next implementation milestone be Nutrition Serving Unit Data Model v1?

Recommended answer: yes, unless Architecture wants a smaller Nutrition Canonical Food Model Review v1 first.

2. Should Nutrition Canonical Food Model Review v1 happen before serving-unit schema work?

Recommended answer: optional. The current diagnostic shows canonical foods, aliases, and nutrients are already usable, but canonical logging still writes through legacy tables and source-confidence semantics are not catalog-level yet.

3. Should curated catalog expansion happen next?

Recommended answer: not yet. Catalog coverage is better than expected. Serving-unit/confidence infrastructure is the bigger blocker.

4. Should ServingUnit include default grams, min/max range, confidence, source, and source note?

Recommended answer: yes.

5. Should serving-unit estimates be allowed in actuals before confidence exists?

Recommended answer: no.

6. Should provider/AI use serving units before backend serving units are approved?

Recommended answer: no.

7. Should missing `mixed nuts` be added in the next catalog expansion?

Recommended answer: yes, but it does not need to block serving-unit model work.

8. Should optional nutrients fiber/sugar/sodium be included in the next model review?

Recommended answer: yes, decide whether they are required for v1 suggestions or deferred.

## Remaining nutrition catalog and serving follow-up questions

- What should the ServingUnit table/model be named?
- Should serving units be global per canonical food or user-overridable from v1?
- Which confidence enum should be shared by logging, suggestions, and provider contracts?
- Should confidence live on serving units, logged actuals, or both?
- Should raw/source staging remain empty until after serving units, or should it be populated before expansion v1?
- Should optional nutrients fiber/sugar/sodium be added to canonical food nutrients before suggestions?
- Should meal type and meal grouping be added before serving-based logging?
- Should canonical logging stop writing through legacy food tables, or is write-through acceptable for now?

## Exercise Eligibility Matrix v1 follow-up

Exercise Eligibility Matrix v1 created an explicit generator-facing eligibility service and developer diagnostic, but it intentionally did not force full catalog reachability.

Current known findings from the diagnostic baseline:

- 240 active catalog exercises.
- 237 equipment-compatible exercises.
- 232 generator-eligible exercises.
- 54 exercises appeared in the 10-variation deterministic sweep.
- 186 generator-eligible exercises did not appear in that sweep.
- top exclusion reason: `not_supported_by_current_generator_candidate_pools` (170).
- weak movement families: arms_biceps, arms_triceps, mobility.

Open follow-up questions:

- Should arms work remain mostly deferred, or should a future accessory slot make limited biceps/triceps work reachable?
- Should mobility exercises stay excluded until warmup/mobility slots exist?
- Should catalog reachability be improved through candidate-pool scoring, slot expansion, or a separate reachability audit first?
- Should the diagnostic eventually consume the eligibility service directly? An optional refactor patch failed to apply during v1 and was deliberately deferred instead of stacked blindly.

## Rolling multi-refresh novelty

- Should rolling multi-refresh novelty be session-only or persisted?
- Should exposure tracking be global, per user, or per generated-workout context?
- Should movement-family exposure count separately from exact exercise exposure?

## Provider strategy

- Should nutrition provider work remain `direct_ollama` only until deterministic food suggestions and serving units are safe?
- Should qwen2.5:3b remain the only approved local nutrition bridge model until an explicit model evaluation milestone?
- Should qwen3/qwen3:32b remain research-only until provider runtime, latency, and validation gates are stronger?
