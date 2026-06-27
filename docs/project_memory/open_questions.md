# Open Questions

## Project Memory Warning Review v1

Current maintenance question:

- Which recurring project-memory warnings are current/actionable, and which are accepted historical/archive noise?

Current answer:

- Current canonical files should point to `main` at `4abf453`, Nutrition Serving Unit Logging Contract Design v1 accepted/merged, and Nutrition Serving Unit Logging Backend v1 as the next implementation milestone.
- Warnings in archived milestone/review/design files are accepted historical/archive noise unless they contradict current canonical files.
- The warning summary is not a failing check as long as `FAIL=0` and remaining warnings are documented.

## Nutrition Serving Unit Logging Contract Design v1

Status: accepted and merged.

Resolved Architecture decisions:

1. Companion provenance table direction is accepted for future implementation.

Recommended future name: prefer `nutrition_serving_unit_log_metadata` for clarity, with `food_entry_serving_unit_metadata` still acceptable if Architecture wants the table name to emphasize the `food_entries` bridge.

2. Serving-unit logs should not extend `food_entries` directly in v1.

`food_entries` remains the grams-based actuals bridge. Serving-unit provenance should be preserved in a companion table.

3. A completely new canonical nutrition log table should not be created for v1.

A canonical-first log model may be cleaner long term, but it is too disruptive before serving-unit logging and actuals confidence are proven.

4. Resolved grams should be persisted.

Historical actuals should use the grams approved at log time even if serving-unit metadata changes later.

5. Min/max grams and confidence should be copied onto the log provenance.

Store `grams_min`, `grams_max`, and serving-unit confidence in the provenance row for auditability and future actuals-confidence display.

6. Logs should preserve both canonical and legacy identities.

`food_entries.food_id` remains the current grams/actuals bridge. Companion metadata should store `canonical_food_id` and `serving_unit_id`.

7. The future serving-unit endpoint should not allow grams override in v1.

Serving-unit logging should accept serving quantity only and resolve grams through backend-owned metadata.

8. User-defined serving overrides should not exist in v1.

Leave room for `user_saved_serving` later, but v1 should only log backend-approved serving units.

9. Serving-unit logs should affect Target-vs-Actual only through resolved grams in v1.

Target-vs-Actual math should not change in the first implementation.

10. Serving-unit logs should eventually affect actuals confidence.

That should happen through a separate Nutrition Actuals Confidence Model v1 milestone.

11. AI/provider should not receive serving-unit internals immediately.

Provider may later receive approved summaries only after logging and actuals confidence are stable.

12. Streamlit must not map servings to grams.

Streamlit should select/display backend-approved serving-unit fields and submit ids/quantity to backend only.

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
