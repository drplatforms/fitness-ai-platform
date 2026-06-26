# Open Questions

## Nutrition Serving Unit Logging Contract Design v1

Current active Architecture questions:

1. What should the future companion provenance table be named?

Recommended answer: prefer `nutrition_serving_unit_log_metadata` for clarity, but `food_entry_serving_unit_metadata` is acceptable if Architecture wants the table name to emphasize the `food_entries` bridge.

2. Should serving-unit logs extend `food_entries` directly?

Recommended answer: no for v1. Keep `food_entries` as the grams-based actuals bridge and preserve serving-unit provenance in a companion table.

3. Should a completely new canonical nutrition log table be created now?

Recommended answer: no for v1. A new canonical-first log model may be cleaner long term, but it is too disruptive before serving-unit logging and actuals confidence are proven.

4. Should resolved grams be persisted?

Recommended answer: yes. Historical actuals should use the grams approved at log time even if serving-unit metadata changes later.

5. Should min/max grams and confidence be copied onto the log?

Recommended answer: yes. Store `grams_min`, `grams_max`, and serving-unit confidence in the provenance row for auditability and future actuals-confidence display.

6. Should logs preserve both canonical and legacy identities?

Recommended answer: yes. `food_entries.food_id` remains the current grams/actuals bridge. Companion metadata should store `canonical_food_id` and `serving_unit_id`.

7. Should the future endpoint allow a grams override?

Recommended answer: no for v1. Serving-unit logging should accept serving quantity only and resolve grams through backend-owned metadata.

8. Should user-defined serving overrides exist in v1?

Recommended answer: no. Leave room for `user_saved_serving` later, but v1 should only log backend-approved serving units.

9. Should serving-unit logs affect Target-vs-Actual immediately?

Recommended answer: only through resolved grams. Target-vs-Actual math should not change in the first implementation.

10. Should serving-unit logs affect actuals confidence?

Recommended answer: eventually yes, but through a separate Nutrition Actuals Confidence Model v1 milestone.

11. Should AI/provider receive serving-unit internals immediately?

Recommended answer: no. Provider may later receive approved summaries only after logging and actuals confidence are stable.

12. Should Streamlit be allowed to map servings to grams?

Recommended answer: no. Streamlit should select/display backend-approved serving-unit fields and submit ids/quantity to backend only.

## Nutrition Serving Unit Data Model v1 results

Resolved findings:

- Serving-unit model/service/schema support exists.
- Serving units are linked to canonical foods.
- `grams_default` is required and positive.
- `grams_min` / `grams_max` ranges are supported.
- Service/model validation enforces `grams_min <= grams_default <= grams_max` when ranges are present.
- Confidence vocabulary for serving-unit rows is Low / Moderate / High.
- `Medium` normalizes to `Moderate`.
- Starter seed is idempotent.
- Active serving-unit count is 18.
- Foods with active serving units: 12.
- Missing canonical foods: none.
- Normal nutrition logging remains unchanged.
- Target-vs-Actual remains unchanged.
- Streamlit remains unchanged.
- Provider/Ollama/CrewAI behavior remains unchanged.

## Remaining nutrition catalog and serving follow-up questions

- Should meal type and meal grouping be added before serving-based logging, or after the serving-unit logging path is stable?
- Should canonical logging eventually stop writing through legacy food tables, or is write-through acceptable until a broader nutrition logging v2?
- Should optional nutrients fiber/sugar/sodium be expanded before serving-aware suggestions?
- Should raw/source staging remain empty until serving-unit logging and actuals confidence are stable?
- Should Nutrition Actuals Confidence Model v1 happen immediately after Serving Unit Logging Backend v1, before Streamlit UI?

## Exercise Eligibility Matrix v1 follow-up

Exercise Eligibility Matrix v1 created an explicit generator-facing eligibility service and developer diagnostic, but it intentionally did not force full catalog reachability.

Open follow-up questions:

- Should arms work remain mostly deferred, or should a future accessory slot make limited biceps/triceps work reachable?
- Should mobility exercises stay excluded until warmup/mobility slots exist?
- Should catalog reachability be improved through candidate-pool scoring, slot expansion, or a separate reachability audit first?
- Should the diagnostic eventually consume the eligibility service directly?

## Rolling multi-refresh novelty

- Should rolling multi-refresh novelty be session-only or persisted?
- Should exposure tracking be global, per user, or per generated-workout context?
- Should movement-family exposure count separately from exact exercise exposure?

## Provider strategy

- Should nutrition provider work remain `direct_ollama` only until deterministic food suggestions and serving units are safe?
- Should qwen2.5:3b remain the only approved local nutrition bridge model until an explicit model evaluation milestone?
- Should qwen3/qwen3:32b remain research-only until provider runtime, latency, and validation gates are stronger?
